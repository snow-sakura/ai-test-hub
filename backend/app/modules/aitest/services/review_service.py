"""
用例评审管理服务

提供评审 CRUD、审批流转、评审分配等业务逻辑。
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.aitest.models.review import ReviewAssignment, TestReview
from app.modules.aitest.models.test_case import TestCase


async def get_review_with_assignments(db: AsyncSession, review_id: int) -> TestReview | None:
    """获取评审详情（含项目名、创建者、分配信息）"""
    stmt = (
        select(TestReview)
        .options(
            joinedload(TestReview.project),
            joinedload(TestReview.creator),
            joinedload(TestReview.assignments).joinedload(ReviewAssignment.reviewer),
        )
        .where(TestReview.id == review_id)
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def list_reviews(
    db: AsyncSession,
    project_id: int | None = None,
    search: str | None = None,
) -> list[TestReview]:
    """获取评审列表（含关联数据）"""
    stmt = (
        select(TestReview)
        .options(
            joinedload(TestReview.project),
            joinedload(TestReview.creator),
            joinedload(TestReview.assignments).joinedload(ReviewAssignment.reviewer),
        )
        .order_by(TestReview.created_at.desc())
    )
    if project_id is not None:
        stmt = stmt.where(TestReview.project_id == project_id)
    if search:
        stmt = stmt.where(TestReview.name.ilike(f"%{search}%"))
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())


async def create_review_assignments(
    db: AsyncSession, review_id: int, reviewer_ids: list[int],
) -> list[ReviewAssignment]:
    """创建评审分配记录"""
    assignments = []
    for uid in reviewer_ids:
        assignment = ReviewAssignment(review_id=review_id, user_id=uid)
        db.add(assignment)
        assignments.append(assignment)
    await db.flush()
    return assignments


async def get_review_stats(db: AsyncSession) -> dict:
    """获取评审统计概览"""
    rows = await db.execute(
        select(TestReview.status, func.count(TestReview.id))
        .group_by(TestReview.status),
    )
    stats = dict(rows.all())
    return {
        "total": sum(stats.values()),
        "pending": stats.get("pending", 0),
        "passed": stats.get("passed", 0),
        "rejected": stats.get("rejected", 0),
    }


async def get_review_cases(db: AsyncSession, review: TestReview) -> list[TestCase]:
    """获取评审关联的测试用例列表"""
    case_ids = review.cases or []
    if not case_ids:
        return []

    result = await db.execute(
        select(TestCase).where(TestCase.id.in_(case_ids)),
    )
    return list(result.scalars().all())


async def update_review_case_assignment(
    db: AsyncSession,
    review_id: int,
    case_id: int,
    status: str,
    comment: str | None = None,
    reviewer_id: int | None = None,
) -> ReviewAssignment | None:
    """更新评审中某个用例的审批状态"""
    if not reviewer_id:
        return None

    stmt = select(ReviewAssignment).where(
        ReviewAssignment.review_id == review_id,
        ReviewAssignment.user_id == reviewer_id,
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()

    if assignment is None:
        assignment = ReviewAssignment(
            review_id=review_id,
            user_id=reviewer_id,
            status=status,
            comment=comment or "",
        )
        db.add(assignment)
    else:
        assignment.status = status
        if comment:
            assignment.comment = comment

    await db.flush()
    return assignment
