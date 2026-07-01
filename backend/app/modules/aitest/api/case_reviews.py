"""
用例关联的评审历史查询 API

提供反向查询：给定一个用例 ID，找出所有包含该用例的评审记录。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.database import get_db
from app.deps import get_current_active_user
from app.modules.aitest.models.review import TestReview

router = APIRouter(prefix="/api/v1/test-cases", tags=["测试用例管理"])


@router.get("/{case_id}/reviews", response_model=ResponseModel[list])
async def get_case_reviews(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用例关联的评审历史（查询所有包含该用例的评审记录）"""
    from app.modules.aitest.schemas.review import CaseReviewSummary

    # 使用 MySQL JSON_CONTAINS 扫描 cases 字段
    stmt = (
        select(TestReview)
        .options(
            joinedload(TestReview.project),
            joinedload(TestReview.creator),
        )
        .where(
            func.JSON_CONTAINS(TestReview.cases, str(case_id)),
        )
        .order_by(TestReview.created_at.desc())
    )
    result = await db.execute(stmt)
    reviews = result.unique().scalars().all()

    data = []
    for r in reviews:
        creator_name = r.creator.username if r.creator else None
        data.append(CaseReviewSummary(
            id=r.id,
            name=r.name,
            status=r.status,
            conclusion=r.conclusion,
            creator_name=creator_name,
            created_at=r.created_at,
        ))

    return ResponseModel(data=data)
