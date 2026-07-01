"""
API 定时任务管理路由模块

提供定时任务的 CRUD 操作：创建、查询、更新、删除。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.modules.api_testing.models.schedule import ApiSchedule
from app.modules.api_testing.schemas.schedule import (
    ApiScheduleCreate,
    ApiScheduleUpdate,
    ApiScheduleResponse,
)

router = APIRouter(prefix="/api/v1/api-schedules", tags=["API定时任务"])


@router.get("", response_model=ResponseModel[list[ApiScheduleResponse]])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取所有 API 定时任务列表"""
    stmt = select(ApiSchedule).order_by(ApiSchedule.id.asc())
    result = await db.execute(stmt)
    schedules = result.scalars().all()
    return ResponseModel(
        data=[ApiScheduleResponse.model_validate(s) for s in schedules],
    )


@router.post("", response_model=ResponseModel[ApiScheduleResponse])
async def create_schedule(
    body: ApiScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建新的 API 定时任务"""
    schedule = ApiSchedule(
        name=body.name,
        suite_id=body.suite_id,
        environment_id=body.environment_id,
        cron_expression=body.cron_expression,
        status="running",
        notify=body.notify,
    )
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    return ResponseModel(data=ApiScheduleResponse.model_validate(schedule))


@router.put("/{schedule_id}", response_model=ResponseModel[ApiScheduleResponse])
async def update_schedule(
    schedule_id: int,
    body: ApiScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新 API 定时任务"""
    stmt = select(ApiSchedule).where(ApiSchedule.id == schedule_id)
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)

    await db.flush()
    await db.refresh(schedule)
    return ResponseModel(data=ApiScheduleResponse.model_validate(schedule))


@router.delete("/{schedule_id}", response_model=ResponseModel)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除 API 定时任务"""
    stmt = select(ApiSchedule).where(ApiSchedule.id == schedule_id)
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="定时任务不存在")

    await db.delete(schedule)
    await db.flush()
    return ResponseModel(message="定时任务已删除")
