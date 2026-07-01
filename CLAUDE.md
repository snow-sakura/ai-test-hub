# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 后端启动（开发）
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# 前端启动（开发）
cd frontend && npm run dev

# 前端类型检查
cd frontend && npx vue-tsc --noEmit

# 前端构建
cd frontend && npm run build

# 数据库迁移（升级）
cd backend && alembic upgrade head

# 数据库迁移（新建）
cd backend && alembic revision --autogenerate -m "描述"

# 数据库迁移（回退一步）
cd backend && alembic downgrade -1

# 启动基础设施（MySQL + Redis）
docker compose up -d mysql redis

# 安装后端依赖
cd backend && pip install -r requirements.txt

# 安装前端依赖
cd frontend && npm install
```

## Project Architecture

### 双目录结构（前后端分离）
- `backend/` — FastAPI + SQLAlchemy 异步后端
- `frontend/` — Vue 3 + Element Plus + TypeScript 前端

### 后端架构

```
app/
  main.py                 # FastAPI 入口 + lifespan
  config.py               # pydantic-settings（支持 .env 覆盖）
  database.py             # SQLAlchemy async engine + session_factory
  deps.py                 # FastAPI 依赖注入（get_db, get_current_active_user）
  api/v1/__init__.py      # 汇总所有模块路由，每个模块一个 include_router
  common/                 # 跨模块共享
    models/base.py        # declarative_base + BaseModel(id, timestamps) + TimestampMixin
    schemas/              # 通用响应模型（ResponseModel, PaginatedResponse）
    api/                  # 通用 API（health, auth, dashboard）
  modules/                # 9 大业务模块，每模块独立分层
    aitest/               # AI 智能测试（核心模块：用例生成/管理/评审）
      api/*.py            # FastAPI 路由（ai, projects, test_cases, reviews...）
      models/*.py         # SQLAlchemy ORM 模型
      schemas/*.py        # Pydantic 请求/响应
      services/*.py       # 业务逻辑层（ai_service, review_service...）
      graph/              # LangGraph 管线
        graph.py          # StateGraph 定义（analyze→write→review→revise）
        state.py          # GenerationState TypedDict
        nodes/            # 四个节点 analyze / write / review / revise
        sse_stream.py     # SSE 流式协调器，包装 LangGraph 执行
        llm_adapter.py    # AIModelConfig → ChatOpenAI 适配器
        prompts.py        # 各阶段默认提示词常量
      utils/              # 工具函数
    config_center/        # 配置中心（AI 模型配置、提示词配置）
    api_testing/          # API 接口测试
    app_automation/       # APP 自动化测试
    ui_automation/        # UI 自动化测试
    system_management/    # 系统管理
    ai_chat/              # AI 对话
    knowledge_base/       # 知识库
```

### 前端架构

```
src/
  api/*.ts                # axios 请求封装（每模块一个文件：aitest.ts, project.ts...）
  router/index.ts         # 路由（双布局：HomeLayout + ModuleLayout）
  stores/                 # Pinia 状态管理
  composables/            # useSSE.ts, useGenerationStream.ts, useMarkdownRenderer.ts
  types/                  # TypeScript 类型定义（每模块一个文件）
  components/             # 跨视图共享组件
    layout/               # HomeLayout, ModuleLayout, Sidebar, Topbar
    aitest/               # 共享组件（StepIndicator, ReviewVisualization...）
  views/modules/aitest/   # 页面视图
    generation/           # AI 用例生成
    project/              # 项目管理
    testcase/             # 测试用例
    review/               # 用例评审
    dashboard/            # 数据看板
    config/               # 配置中心
```

### 数据流

```
前端输入需求 → POST /api/v1/ai/generate → AIGenerationTask 创建
  → asyncio.create_task 执行 pipeline（传统顺序流 / LangGraph DAG）
  → 各阶段 SSE 事件推入 asyncio.Queue
  → FastAPI StreamingResponse 消费队列 → 前端 useSSE composable 接收
  → 2×2 阶段卡片 + 实时日志面板展示
```

## 关键模式

- **认证**: JWT token，`get_current_active_user` 依赖注入，token 存 `localStorage`
- **数据库**: SQLAlchemy async + aiomysql，`get_db()` 提供 AsyncSession
- **模型基类**: `BaseModel` (id, created_at, updated_at) → 各模块模型继承 `BaseModel + TimestampMixin`
- **API 响应**: 统一 `ResponseModel` 包裹，`code`/`message`/`data` 结构
- **模块注册**: `api/v1/__init__.py` 中 `include_router` 注册每个模块路由
- **SSE 流式**: `asyncio.Queue` 作为事件缓冲，`StreamingResponse` 逐个推送，以 `None` 作为结束信号
- **pydantic-settings**: `Settings` 类从 `.env` 读取配置，所有 AI 提供商 API key 通过环境变量注入
- **Alembic**: 自动迁移生成，分支合并需手动指定 `down_revision`

## SQLAlchemy Async 注意事项

- **禁止懒加载**: async 上下文中不能使用 lazy loading。访问关系属性前必须用 `joinedload` 或 `selectinload`
- **commit 后对象过期**: `db.commit()` 后所有属性被标记过期，需在 commit 前完成数据读取
- **write_only 规避**: 如果只需要外键值，直接访问 `xxx_id` 列而非 `xxx` 关系属性
- **MissingGreenlet 异常**: 出现 `greenlet_spawn has not been called` 必定是访问了未 eager load 的关系属性

## AI API Key 解析链

1. 优先使用 `AIModelConfig.api_key`（数据库配置）
2. 若 DB key 为空或含 `****`（掩码），回退到 `.env` 中的 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` 等
3. 若两者都为空，`build_chat_openai` 使用 `fallback_api_key` 参数
4. 模型基地址 `base_url` 自动追加 `/v1` 后缀（LangChain ChatOpenAI 要求）

## AI 生成管线

- **传统 pipeline**（默认，`use_langgraph=false`）: 顺序调用 `ai_service.py` 中各方法，`_run_generation_pipeline` 管理全流程
- **LangGraph pipeline**（可选，`use_langgraph=true`）: `sse_stream.py` 的 `run_langgraph_pipeline` 使用 LangGraph StateGraph 执行 DAG
- **两套 SSE 兼容**: 传统 pipeline 发送 `status`/`chunk`/`review_chunk`/`revise_chunk` 事件；LangGraph 发送 `testing_stage`/`testing_review`/`testing_done` 事件 + 各阶段独立 `chunk` 事件
- **提示词**: `PromptConfig.prompt_type` 是 `String(20)` 无 CHECK 约束，新增类型无需改表结构
- **SSECallbackHandler**: 每个 LLM 实例绑定独立回调，`stage` 字段区分前端 2×2 卡片

## UI 设计规范

aitest 模块所有页面需遵循暖色主题和布局规范，详见 [docs/aitest/](frontend/docs/aitest/)：

| 文档 | 覆盖内容 |
|------|---------|
| [`general.md`](frontend/docs/aitest/general.md) | 通用规则：容器、标题、统计卡片、筛选栏、表格、列宽、CSS 变量 |
| [`generation.md`](frontend/docs/aitest/generation.md) | AI 用例生成页面、生成记录列表、SSE 事件 |
| [`config.md`](frontend/docs/aitest/config.md) | AI 模式配置、模型配置列表、提示词配置列表 |
| [`project.md`](frontend/docs/aitest/project.md) | 项目列表、详情、成员管理 |
| [`testcase.md`](frontend/docs/aitest/testcase.md) | 测试用例列表、详情、编辑 |
| [`review.md`](frontend/docs/aitest/review.md) | 用例评审列表、详情、新建弹窗 |
| [`dashboard.md`](frontend/docs/aitest/dashboard.md) | 数据看板统计卡片、图表、活动时间线 |

核心要点：
- 页面容器不设 `max-width`，padding `24px 16px`
- 表格包裹在 `el-card.config-table-card` 暖色卡片内
- 列宽全用 `min-width` 比例分配，不用固定 `width`
- 文字列加 `show-overflow-tooltip` 防换行
- 搜索框 `flex: 1` 填充右侧空白
- 添加成员弹窗宽度 ≥ 540px
- 后端 MemberResponse 需包含 `department`、`position`、`phone`

## Harness Kit 工作流

- `.harvest/config.json` — 项目验证配置（构建/类型检查/分层规则/指标）
- `docs/plans/` — 计划目录（`active/` 进行中、`completed/` 已完成）
- 执行 `/harness-kit:evaluate` 完成代码变更后触发评价器
- 执行 `/harness-kit:verify` 手动运行验证大门
