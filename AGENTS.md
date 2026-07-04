# AGENTS.md

## 开发命令

```bash
# 后端开发
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# 仅启动基础设施（MySQL + Redis）
docker compose up -d mysql redis

# 数据库迁移
cd backend && alembic upgrade head              # 升级
cd backend && alembic revision --autogenerate -m "描述"  # 新建
cd backend && alembic downgrade -1              # 回退

# 前端开发
cd frontend && npm run dev
cd frontend && npx vue-tsc --noEmit             # 类型检查（较慢）
cd frontend && npm run build                    # 构建（含类型检查）
cd frontend && npm run lint                     # ESLint
```

## 架构要点

- **双目录分离**：`backend/` (FastAPI async) + `frontend/` (Vue 3 + Element Plus)
- **路由注册**：所有后端路由在 `backend/app/api/v1/__init__.py` 通过 `include_router` 汇集，新增模块必须在此注册
- **模块模式**：每模块独立 `api/models/schemas/services/` 四层，`api/` 内可有多文件路由
- **通用响应**：统一 `ResponseModel(code, message, data)` 包裹；分页用 `PaginatedResponse`
- **SSE 流式**：AI 生成使用 `asyncio.Queue` + `StreamingResponse`，前端 `useSSE` composable 消费，以 `None` 做结束信号

## 关键约束

### SQLAlchemy Async（⚠️ 常见错误来源）
- **禁止懒加载**：async 上下文中访问关系属性必须预先 `joinedload` / `selectinload`
- **commit 后数据过期**：`db.commit()` 会使所有属性过期，必须在 commit 前读取完数据
- **外键用 `_id` 列**：如果只需外键值，访问 `xxx_id` 而非 `xxx` 关系属性
- **MissingGreenlet 异常**：`greenlet_spawn has not been called` 说明访问了未 eager load 的关系

### AI API Key 解析链
1. 优先 `AIModelConfig.api_key`（数据库）
2. 若含 `****` 掩码或为空，回退 `.env` 变量（`DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `QWEN_API_KEY` 等）
3. `base_url` 自动追加 `/v1` 后缀（LangChain ChatOpenAI 约定）

### SSE 流式
- **传统管线**（`use_langgraph=false`，默认）：顺序调用 `ai_service.py` 方法，SSE 事件类型 `status` / `chunk` / `review_chunk` / `revise_chunk`
- **LangGraph 管线**（`use_langgraph=true`）：StateGraph DAG，SSE 事件类型 `testing_stage` / `testing_review` / `testing_done` + 各阶段独立 `chunk`
- **AI 聊天室**：使用 `StreamingResponse` + 异步生成器，事件类型 `user_message` / `token` / `complete` / `error`，以 `[DONE]` 作为结束信号
- 提示词类型 `PromptConfig.prompt_type` 是 `String(20)` 无 CHECK 约束，新增类型无需改表

### 前端
- **axios baseURL**: `/api`，自动 token 注入，支持自动刷新 token 和请求队列
- **路径别名**: `@/` → `src/`（tsconfig 配置）
- **Element Plus** 使用中文 locale：`ElementPlus, { locale: zhCn }`
- **SSE composable**：`useSSE(url, onMessage)`，收到 `done` / `error` 事件自动关闭连接

### 环境 & 配置
- **`.env 文件位置**：`backend/.env`（pydantic-settings 从 CWD 读取 `.env`），根目录 `.env` 为 Docker Compose 使用
- **pydantic-settings**：`SettingsConfigDict(case_sensitive=True)`
- **Docker Compose** 端口：MySQL `3306`，Redis `6379`（密码 `redis123`），后端 `8000`

### UI 设计规范（aitest 模块）
见 `frontend/docs/aitest/` 各文档，核心规则：
- 页面容器 padding `24px 16px`，不设 `max-width`
- 表格用 `el-card.config-table-card` 暖色卡片包裹
- 列宽用 `min-width` 比例分配，文字列加 `show-overflow-tooltip`
- 搜索框 `flex: 1` 填充

## 验证顺序
修改代码后按此顺序检查：
1. `cd frontend && npx vue-tsc --noEmit`（前端类型检查）
2. `cd frontend && npm run lint`（前端 lint）
3. `cd backend && python -m py_compile app/` 或运行服务验证（后端无独立 lint）
