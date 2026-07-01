"""
仪表盘统计 API 路由

提供 AI 测试模块仪表盘所需的聚合统计数据接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.database import get_db
from app.deps import get_current_active_user
from app.modules.aitest.schemas.dashboard import DashboardStatsResponse
from app.modules.aitest.schemas.operation_log import OperationLogResponse
from app.modules.aitest.services.dashboard_service import get_dashboard_stats

router = APIRouter(prefix="/api/v1/ai", tags=["AI 仪表盘"])


@router.get(
    "/dashboard/stats",
    response_model=ResponseModel[DashboardStatsResponse],
)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取仪表盘聚合统计数据"""
    stats = await get_dashboard_stats(db)

    # 将近期活动的 OperationLog ORM 对象转为 dict
    recent_activities = [
        OperationLogResponse.model_validate(log).model_dump()
        for log in stats.pop("recent_activities", [])
    ]

    return ResponseModel(
        data=DashboardStatsResponse(
            **stats,
            recent_activities=recent_activities,
        ),
    )
