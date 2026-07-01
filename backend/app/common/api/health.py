"""
健康检查接口

用于监控系统运行状态，检查 API 和数据库连接是否正常。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/api/v1", tags=["健康检查"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    健康检查接口

    返回 API 状态及数据库连接状态。
    """
    db_status = "connected"
    try:
        # 执行一次简单的数据库查询验证连接
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return {
        "status": "ok",
        "database": db_status,
    }
