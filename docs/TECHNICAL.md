# AI-HUB 技术设计文档

> 面向开发者的架构与实现说明。配套文档：[需求文档](REQUIREMENTS.md) · [技术规格](SPEC-v1.1.md) · [使用手册](USER_GUIDE.md)

## 1. 总体架构

```
┌─────────────────────────────────────────────────────────┐
│  前端 Vue 3 + TypeScript + Element Plus (Vite)          │
│  axios(/api, 自动token刷新)  ·  useSSE / EventSource    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────┐
│  FastAPI (uvicorn, async)  /api/v1/*                    │
│  ├─ 路由汇集: app/api/v1/__init__.py include_router     │
│  ├─ 模块四层: api / models / schemas / services         │
│  ├─ 执行调度器: generation_scheduler.py (进程内单例)     │
│  └─ 生成管线: 传统顺序 / LangGraph DAG / AutoGen        │
└───────┬───────────────────────────┬─────────────────────┘
        │ SQLAlchemy 2.0 async      │ LangChain ChatOpenAI
┌───────▼─────────┐        ┌────────▼───────────────────┐
│ MySQL 8 (ai_hub │        │ OpenAI 兼容 LLM Provider    │
│ _test / ai_hub) │        │ DeepSeek/Qwen/OpenAI/Mock… │
└─────────────────┘        └────────────────────────────┘
   Redis 7: 缓存 / 会话辅助
```

- **双目录分离**：`backend/`（FastAPI async）+ `frontend/`（Vue 3）。
- **统一响应**：`ResponseModel(code, message, data)`；分页 `PaginatedResponse`。
- **鉴权**：JWT（access + refresh），axios 401 自动刷新并重放请求队列。

## 2. 后端模块模式

每个业务模块遵循四层结构：

```
app/modules/<module>/
├── api/        # 路由（可多文件），在 app/api/v1/__init__.py 注册
├── models/     # SQLAlchemy ORM
├── schemas/    # Pydantic 模型
└── services/   # 业务逻辑 / 调度器 / AI 客户端
```

主要模块：`aitest`（用例生成/评审/报告）、`api_testing`（接口测试）、`auth`、`system`、`chat`、`knowledge` 等。

### SQLAlchemy Async 关键约束（易错点）

1. **禁止懒加载**：async 上下文访问关系属性必须 `joinedload` / `selectinload`，否则抛 `MissingGreenlet`。
2. **commit 语义**：`app/database.py` 会话配置 `expire_on_commit=False`，commit 后属性仍可读；业务代码不要再 `db.refresh(task)`。
3. **只取外键值时访问 `xxx_id` 列**，不触发关系加载。

## 3. AI 用例生成管线

入口：`POST /api/v1/ai/generate`（单任务）/ `POST /api/v1/ai/generate/batch`（生成序列）。

### 3.1 阶段流转

```
queued → analyzing → generating → reviewing → revising → completed
   │            （任一阶段可 cancel → cancelled / error → failed）
```

| 管线 | 开关 | 实现 | SSE 事件 |
|------|------|------|----------|
| 传统顺序管线（默认） | `use_langgraph=false` | `api/ai.py::_run_generation_pipeline` 顺序调用 `ai_service` | `status` / `chunk` / `review_chunk` / `revise_chunk` / `complete` |
| LangGraph DAG | `use_langgraph=true` | `graph/sse_stream.py` StateGraph | `testing_stage` / `testing_review` / `testing_done` + 各阶段 `chunk` |
| AutoGen | 配置选择 | `graph/autogen_pipeline.py` | 同传统事件对齐 |

管线逐段提交：每个阶段结束即 `db.commit()`（阶段产物持久化，崩溃可续写/排查）；完成前重新读取任务当前状态，若已被取消则保留 `cancelled`，防止覆盖。

### 3.2 输出持久化

- `ai_generation_task`：任务元数据（状态/进度/计费快照/batch_id）。
- `ai_generation_result`：各阶段产物（analysis / generate / review / revise JSON）。
- `generated_case_item`：解析后的结构化用例行（7 列：编号/模块/标题/优先级/前置条件/操作/预期）。

## 4. 执行调度器（生成序列核心）

`app/modules/aitest/services/generation_scheduler.py`，进程内单例。

### 4.1 计费类型驱动的执行策略

`AIModelConfig.billing_type`：

| billing_type | 调度策略 | 并发 |
|--------------|----------|------|
| `free`（免费） | **单任务串行**：同批次任务严格依次执行，避免高频调用触发限流 | 全局 1 |
| `paid`（付费） | **并行执行**：多任务同时生成 | `PAID_MODEL_CONCURRENCY`（默认 4） |

任务创建时把模型计费类型快照进任务记录（`billing_type`），后续调度不再回查配置。

### 4.2 准入队列（显式、无竞态）

```
create_batch → N 个任务入队（queued）
_launch():    同步占用 _running 名额（先占位后异步执行 → 无同批超限竞态）
_start_next(): FIFO 出队，空位即调度
_emit_positions(): 向批次内所有任务推 queue_position 事件（位次实时收缩）
cancel(queued): 直接从队列移除，不启动
```

- **SSE 位次事件**：`{"type":"queue_position","position":2,"queue_size":3}`，前端渲染「排队中 · 第 N 位」。
- **僵尸恢复**：应用启动 lifespan 扫描进行中任务 → 置 `failed`（进程重启导致的假运行）。

### 4.3 StreamBroker（流总线）

解决的问题：SSE 断线丢事件、事件类型混杂（`chunk`/`status`/`testing_stage`…）、多消费者。

- 每任务一个 broker：**全量事件回放**（`GET /generate/{id}/stream?since=<seq>`）+ 实时广播。
- 任务完成后事件保留 600s，支持结果页秒开回放。
- 任务已到终态但内存事件丢失时，从 DB 阶段产物**合成 complete 终态**兜底，前端永不挂死。
- 事件类型归一化：broker 统一包 `type` + `seq`，前端 `useSSE` 按 type 分发。

## 5. AI Provider 与密钥解析

`base_url` 自动追加 `/v1`（LangChain ChatOpenAI 约定）。API Key 解析链：

1. `AIModelConfig.api_key`（数据库，密文存储，回显 `****` 掩码）
2. 掩码/为空 → 回退 `.env`：`DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `QWEN_API_KEY` 等
3. `POST /ai/config/test-connection` 可验证连通性

前端模型下拉与记录页均展示 `计费类型` 标签（免费·串行 / 付费·并行）。

## 6. 时间约定（重要）

所有业务时间列统一写入 **本地 naive datetime**（`app/common/utils/time.py::local_now()`），与 MySQL `CURRENT_TIMESTAMP`（会话时区）口径一致。历史教训：混用 `utcnow` naive 与 MySQL local naive 导致「完成时间比创建时间早 8 小时」。新增代码一律使用 `local_now()`，禁止 `datetime.now(timezone.utc)` 直接落库。

## 7. 数据库初始化与迁移

### 初始化（新环境）

```bash
cd backend
.venv/bin/python scripts/init_db.py     # 建库建表（create_all）+ alembic stamp head
.venv/bin/python scripts/seed_demo.py   # 幂等种子：管理员/角色/模型配置/提示词/生成设置
```

> ⚠️ 已知技术债：核心表（users、ai_generation_task 等）由早期 create_all 建立，历史迁移链**从零重放不可行**。新库统一 `init_db.py` 建表并 stamp 到 head；此后增量变更正常使用 `alembic revision --autogenerate`。

### 本地无真实 Key 联调

```bash
.venv/bin/python scripts/mock_llm_server.py   # OpenAI 兼容 Mock，127.0.0.1:8030
```

种子数据内置 Mock 免费/付费两个模型（base_url `http://127.0.0.1:8030/v1`），确定输出 6 条用例，用于回归验证串行/并行调度。

## 8. SSE 接口清单（aitest）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/ai/generate` | 创建单任务（立即返回 task_id，后台执行） |
| POST | `/api/v1/ai/generate/batch` | 创建生成序列（每行需求独立任务，共享 batch_id） |
| GET | `/api/v1/ai/generate/{task_id}/stream` | SSE 事件流（StreamBroker 回放 + 实时） |
| POST | `/api/v1/ai/generate/{task_id}/cancel` | 取消（运行中→中断标记；排队→移出队列） |
| GET | `/api/v1/ai/generate/{task_id}/results` | 阶段产物 + 结构化用例 |
| GET | `/api/v1/ai/scheduler/status` | 调度器快照（运行数/队列/并发上限） |

SSE 流使用 `EventSource`（无法带 header），该路径按只读事件流开放；写操作接口均需 JWT。

## 9. 前端要点

- axios `baseURL=/api`，token 注入 + 401 刷新重放队列。
- `useSSE(url, onMessage)`：`done`/`error` 自动关闭；生成页另用原生 EventSource 消费高事件量任务流并做重连。
- 序列模式：`GenerationView` 提交批次后渲染序列看板（完成/进行/排队计数 + 每条需求位次徽标），轮询 `getGenerationBatchStatus` 兜底。
- ESLint flat config（`eslint.config.mjs`），验证顺序：`vue-tsc --noEmit` → `npm run lint` → 后端 `py_compile`。

## 10. 部署

```bash
docker compose up -d mysql redis      # 基础设施
# 后端（开发）
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
# 前端
cd frontend && npm run dev            # 端口占用时自动顺延（如 5199）
# 生产构建
cd frontend && npm run build          # vue-tsc + vite build
```

`.env` 位置：`backend/.env`（pydantic-settings，CWD 读取），根目录 `.env` 供 docker compose。敏感项（DB 密码、API Key）一律不入库。
