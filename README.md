# AI-HUB 智能测试工作台

> AI 驱动的一站式软件测试平台：需求进、用例出，覆盖生成 → 评审 → 入库 → 报告全流程。

[![](https://img.shields.io/badge/backend-FastAPI-009688)](backend/) [![](https://img.shields.io/badge/frontend-Vue%203-42b883)](frontend/) [![](https://img.shields.io/badge/docs-使用手册-blue)](docs/USER_GUIDE.md) [![](https://img.shields.io/badge/docs-技术文档-blue)](docs/TECHNICAL.md)

## ✨ 核心特性

- **AI 用例生成**：粘贴需求或上传 PDF/Word/MD → 流式输出「分析 → 生成 → 评审 → 改进」四阶段产物 → 存入用例库 / 导出 Excel。
- **生成序列（批量）**：一次提交 N 行需求，每条独立任务；**序列看板** 实时展示 完成/进行/排队位次，随时单独取消。
- **计费类型调度**：模型标记 `免费` → 全局单任务**严格串行**（防限流）；标记 `付费` → 最多 4 任务**并行**生成。
- **可靠流式**：SSE 断线自动重连 + 事件回放（StreamBroker），刷新页面不丢进度；进程重启自动回收僵尸任务。
- **多模型接入**：DeepSeek / 通义千问 / OpenAI 及任意 OpenAI 兼容服务；密钥数据库密文 + 环境变量双级回退，内置 Mock Server 可离线体验全流程。
- **完整测试平台**：用例管理与评审、API 接口测试、AI 聊天室、知识库 RAG、用户/角色/审计的系统管理。

## 🎬 界面演示

| 首页 | AI 生成记录 |
|---|---|
| ![首页](docs/images/01-home.png) | ![记录](docs/images/07-records.png) |

**生成序列看板**（免费模型 · 严格串行 · 排队位次实时收缩）：

![序列看板](docs/images/05-batch-queue-board.png)

**单任务生成**（流式阶段日志 + 结构化用例结果）：

![生成完成](docs/images/04-generation-done.png)

**模型配置**（计费类型决定 串行/并行 调度）：

![模型配置](docs/images/06-model-billing.png)

## 🧱 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12+ · FastAPI · SQLAlchemy 2.0 (async) · LangChain/LangGraph · Alembic |
| 前端 | Vue 3.5 · TypeScript · Vite · Element Plus · Pinia · vue-i18n |
| 基础设施 | MySQL 8 · Redis 7 · Docker Compose |

## 🚀 快速开始

```bash
git clone git@github.com:snow-sakura/ai-test-hub.git && cd ai-test-hub

# 1. 基础设施（MySQL 3306 / Redis 6379）
docker compose up -d mysql redis

# 2. 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # 填写数据库连接与 AI API Key（可留空用 Mock）

python scripts/init_db.py            # 建库建表 + 迁移基线
python scripts/seed_demo.py          # 演示数据：管理员/模型配置/提示词（幂等）

# 3.（可选）Mock LLM —— 无需真实 Key 体验全流程
python scripts/mock_llm_server.py    # 新开终端，监听 127.0.0.1:8030

# 4. 启动后端 http://localhost:8000/docs
uvicorn app.main:app --reload --port 8000

# 5. 启动前端
cd ../frontend && npm install && npm run dev
```

默认账号 `admin / admin123`（来自 seed）。无真实 API Key 时，在生成页选择 **Mock**– 开头的模型即可完整体验 并行/串行 调度与序列看板。

## 📖 文档

| 文档 | 内容 |
|------|------|
| [使用手册](docs/USER_GUIDE.md) | 登录、模型配置、单任务生成、生成序列、记录与 FAQ |
| [技术文档](docs/TECHNICAL.md) | 架构、生成管线、执行调度器与 StreamBroker、迁移策略 |
| [需求文档](docs/REQUIREMENTS.md) · [技术规格](docs/SPEC-v1.1.md) | 产品需求与规格 |

## 🗂 项目结构

```
ai-test-hub/
├── backend/
│   ├── app/
│   │   ├── main.py          # 入口 + lifespan（僵尸恢复/调度器关闭）
│   │   ├── common/          # 认证、响应模型、AI 客户端、时间约定
│   │   └── modules/         # 业务模块四层 api/models/schemas/services
│   │       ├── aitest/      # AI 测试核心：生成/评审/调度器/管线
│   │       ├── api_testing/ # 接口测试
│   │       └── ...          # chat / knowledge / system 等
│   ├── scripts/             # init_db.py / seed_demo.py / mock_llm_server.py
│   └── alembic/
├── frontend/src/            # views/modules 按业务模块组织 api/ stores/ composables/
├── docs/                    # 文档与截图
└── docker-compose.yml
```

## ⚙️ 环境变量（backend/.env 关键项）

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 如 `mysql+aiomysql://<user>:<password>@localhost:3306/ai_hub_test` |
| `REDIS_URL` | 如 `redis://:<password>@localhost:6379/0` |
| `SECRET_KEY` | JWT 签名密钥 |
| `DEEPSEEK_API_KEY` / `QWEN_API_KEY` / `OPENAI_API_KEY` | 数据库配置缺失时的回退 Key |
| `PAID_MODEL_CONCURRENCY` | 付费模型并行上限（默认 4） |

## 🧭 版本规划

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.1.0 | 基础架构 + AI 用例生成核心 | ✅ 已发布 |
| v0.2.0 | 生成序列调度 + 计费策略 + 接口测试完善 | ✅ 当前 |
| v0.3.0 | UI 自动化 + 知识库增强 | 📋 计划中 |
| v0.4.0 | APP 自动化 + 通知系统 | 📋 计划中 |

## 许可证

私有项目，保留所有权利。
