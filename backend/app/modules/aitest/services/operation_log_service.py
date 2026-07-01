"""
操作日志服务

提供操作日志的创建和查询能力，
用于记录和追溯各个实体（用例/项目/评审/任务）的操作历史。
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.aitest.models.operation_log import OperationLog


async def create_log(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    action: str,
    operator_id: int | None = None,
    detail: dict | None = None,
) -> OperationLog:
    """创建操作日志记录"""
    log = OperationLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        operator_id=operator_id,
        detail=detail,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def list_logs(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[OperationLog], int]:
    """获取指定实体的操作日志列表（分页，按创建时间倒序）"""
    # 查询总数（使用 SQL COUNT 避免全表加载）
    count_stmt = (
        select(func.count(OperationLog.id))
        .where(
            OperationLog.entity_type == entity_type,
            OperationLog.entity_id == entity_id,
        )
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # 分页查询，关联 operator 信息，按时间倒序
    stmt = (
        select(OperationLog)
        .options(joinedload(OperationLog.operator))
        .where(
            OperationLog.entity_type == entity_type,
            OperationLog.entity_id == entity_id,
        )
        .order_by(OperationLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    logs = list(result.unique().scalars().all())
    return logs, total


async def list_recent_activities(
    db: AsyncSession,
    limit: int = 10,
) -> list[OperationLog]:
    """获取最近操作记录（跨所有实体，用于仪表盘）"""
    stmt = (
        select(OperationLog)
        .options(joinedload(OperationLog.operator))
        .order_by(OperationLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())
