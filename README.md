# AI-HUB 智能测试工作台

> AI 驱动的一站式软件测试平台，集成用例生成、评审、API 测试、UI 自动化等能力。

## 功能概览

| 模块 | 说明 | 状态 |
|------|------|------|
| AI 用例生成 | 输入需求 → AI 流式生成测试用例 → 自动评审 → 改进输出 | ✅ 已完成 |
| 用例管理 | 用例 CRUD、导入导出、版本管理 | ✅ 已完成 |
| 用例评审 | 自动/人工评审流程、评审记录 | ✅ 已完成 |
| 配置中心 | AI 模型配置、提示词配置、生成行为配置 | ✅ 已完成 |
| 系统管理 | 用户/角色/权限、审计日志、系统设置 | ✅ 已完成 |
| API 接口测试 | 项目管理、接口管理、自动化测试套件 | 🔧 开发中 |
| UI 自动化 | 元素管理、脚本生成、套件执行 | 📋 计划中 |
| APP 自动化 | 设备管理、用例编排、执行记录 | 📋 计划中 |
| AI 聊天室 | 多会话流式对话、上下文管理、Markdown渲染 | ✅ 已完成 |
| 知识库 | 文档上传切片、RAG 搜索 | ✅ 已完成 |

## 技术栈

**后端**
- Python 3.12+ / FastAPI 0.115+ / SQLAlchemy 2.0 (async)
- LangChain + LangGraph（AI 管线编排）
- Alembic（数据库迁移）/ Redis 7 / MySQL 8.0

**前端**
- Vue 3.5+ / TypeScript 5.6+ / Vite 6
- Element Plus 2.9+ / Pinia / Vue Router / vue-i18n

**基础设施**
- Docker Compose（MySQL + Redis + App）

## 快速开始

### 前置条件

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- （可选）antiword：解析旧版 .doc 文件

### 1. 克隆项目

```bash
git clone git@github.com:snow-sakura/ai-test-hub.git
cd ai-test-hub
```

### 2. 启动基础设施

```bash
docker compose up -d mysql redis
```

### 3. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 复制并编辑环境变量（数据库连接、AI API Key 等）
cp .env.example .env

# 执行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

后端访问地址：http://localhost:8000  
API 文档：http://localhost:8000/docs

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端访问地址：http://localhost:5173

## 项目结构

```
ai-test-hub/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 入口 + lifespan
│   │   ├── config.py       # 配置（pydantic-settings）
│   │   ├── database.py     # SQLAlchemy async engine
│   │   ├── deps.py         # 依赖注入
│   │   ├── api/v1/         # 路由注册
│   │   ├── common/         # 通用模块（认证、模型基类、响应格式）
│   │   └── modules/        # 业务模块
│   │       ├── aitest/          # AI 智能测试（核心）
│   │       ├── config_center/   # 配置中心
│   │       ├── api_testing/     # API 接口测试
│   │       ├── ui_automation/   # UI 自动化
│   │       ├── app_automation/  # APP 自动化
│   │       ├── ai_chat/         # AI 聊天室
│   │       ├── knowledge_base/  # 知识库
│   │       └── system_management/ # 系统管理
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # Axios 请求封装
│   │   ├── components/     # 共享组件
│   │   ├── composables/    # 组合式函数（SSE、流式生成）
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── types/          # TypeScript 类型定义
│   │   └── views/          # 页面视图
│   └── package.json
└── docker-compose.yml      # 基础设施编排
```

## 环境变量

在 `backend/.env` 中配置（关键项）：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | MySQL 连接串 | `mysql+aiomysql://snow:Wxh123456!@localhost:3306/ai_hub_test` |
| `REDIS_URL` | Redis 连接串 | `redis://:redis123@localhost:6379/0` |
| `SECRET_KEY` | JWT 签名密钥 | 随机字符串 |
| `QWEN_API_KEY` | 阿里云百炼千问 API Key | 用于 AI 生成（默认） |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 用于 AI 生成（可选） |
| `OPENAI_API_KEY` | OpenAI API Key | 用于 AI 生成（可选） |

## AI 生成管线

支持两种管线模式：

- **传统管线**（默认）：顺序执行 分析 → 生成 → 评审 → 改进
- **LangGraph 管线**（可选）：基于 StateGraph 的 DAG 执行，支持更灵活的节点编排

通过 SSE（Server-Sent Events）实时推送各阶段进度到前端。

## 版本规划

| 版本 | 阶段 | 内容 | 状态 |
|------|------|------|------|
| v0.1.0 | P0 | 基础架构 + AI 核心 | ✅ 已发布 |
| v0.2.0 | P1 | API 接口测试 + 测试管理 | 🔧 开发中 |
| v0.3.0 | P2 | UI 自动化 + AI 聊天 + 知识库 | 📋 计划中 |
| v0.4.0 | P3 | APP 自动化 + 通知系统 | 📋 计划中 |

## 许可证

私有项目，保留所有权利。
