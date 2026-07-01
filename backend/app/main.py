"""
FastAPI 应用入口模块

创建 FastAPI 应用实例，注册中间件、路由和事件处理器。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.config import settings

# 开发模式下可通过 app.database.Base.metadata.create_all 自动建表
# 生产环境建议使用 Alembic 管理迁移


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时：打印启动信息
    关闭时：清理资源
    """
    # ---------- 启动事件 ----------
    print(f"🚀 AI-HUB API Server 启动中...")
    print(f"📋 调试模式: {'开启' if settings.DEBUG else '关闭'}")
    print(f"🗄️  数据库: {settings.DATABASE_URL}")

    yield

    # ---------- 关闭事件 ----------
    print("🛑 AI-HUB API Server 正在关闭...")
    from app.database import engine
    await engine.dispose()


# 创建 FastAPI 应用实例
app = FastAPI(
    title="AI-HUB API",
    description="AI-HUB 后端服务接口",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc
)

# ---------- CORS 中间件 ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],        # 允许所有 HTTP 方法
    allow_headers=["*"],        # 允许所有请求头
)

# ---------- 注册路由 ----------
app.include_router(api_v1_router)


@app.get("/")
async def root():
    """根路径，返回服务基础信息"""
    return {
        "message": "AI-HUB API Server",
        "version": "1.0.0",
    }
