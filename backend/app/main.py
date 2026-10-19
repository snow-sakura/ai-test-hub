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


async def _recover_zombie_tasks() -> None:
    """服务启动时把上一次进程遗留的进行中任务标记为失败（可一键重新生成）"""
    try:
        from sqlalchemy import select, update

        from app.database import async_session_factory
        from app.modules.aitest.models.ai_task import AIGenerationTask

        async with async_session_factory() as db:
            result = await db.execute(
                update(AIGenerationTask)
                .where(AIGenerationTask.status.in_([
                    "queued", "pending", "analyzing", "generating",
                    "reviewing", "revising",
                ]))
                .values(
                    status="failed",
                    error_message="服务重启导致任务中断，请点击「重新生成」重试",
                )
            )
            await db.commit()
            if result.rowcount:
                print(f"♻️  已恢复 {result.rowcount} 个重启遗留任务（置为失败）")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  遗留任务恢复失败: {e!r}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时：打印启动信息、恢复重启遗留的僵尸任务
    关闭时：清理资源
    """
    # ---------- 启动事件 ----------
    print(f"🚀 AI-HUB API Server 启动中...")
    print(f"📋 调试模式: {'开启' if settings.DEBUG else '关闭'}")
    print(f"🗄️  数据库: {settings.DATABASE_URL}")

    await _recover_zombie_tasks()

    yield

    # ---------- 关闭事件 ----------
    print("🛑 AI-HUB API Server 正在关闭...")
    try:
        from app.modules.aitest.services.generation_scheduler import get_scheduler

        await get_scheduler().shutdown()
    except Exception:  # noqa: BLE001
        pass
    from app.database import engine

    await engine.dispose()


# 创建 FastAPI 应用实例
app = FastAPI(
    title="AI-HUB API",
    description="AI-HUB 后端服务接口",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# ---------- CORS 中间件 ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
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
