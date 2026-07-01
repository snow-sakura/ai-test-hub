"""
用例评审 CRUD API 路由

提供用例评审的增删改查、提交审批、审批操作和逐用例评审接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.database import get_db
from app.deps import get_current_active_user


class _IdListRequest(BaseModel):
    """批量操作 ID 列表"""
    ids: list[int]
from app.modules.aitest.models.project import TestProject
from app.modules.aitest.models.review import TestReview
from app.modules.aitest.models.execution import TestCaseExecution
from app.modules.aitest.models.test_case import TestCase
from app.modules.aitest.schemas.review import (
    ReviewCaseItem,
    ReviewCaseUpdate,
    ReviewStatsResponse,
    TestReviewApprove,
    TestReviewCreate,
    TestReviewDetail,
    TestReviewUpdate,
)
from app.modules.aitest.services.review_service import (
    create_review_assignments,
    get_review_cases,
    get_review_stats,
    get_review_with_assignments,
    list_reviews,
    update_review_case_assignment,
)

router = APIRouter(prefix="/api/v1/test-reviews", tags=["用例评审"])


@router.get("", response_model=ResponseModel[list[TestReviewDetail]])
async def list_reviews_api(
    project_id: int | None = Query(None, description="按项目筛选"),
    search: str | None = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取评审列表"""
    reviews = await list_reviews(db, project_id=project_id, search=search)
    return ResponseModel(
        data=[TestReviewDetail.model_validate(r) for r in reviews],
    )


@router.get("/stats", response_model=ResponseModel[ReviewStatsResponse])
async def review_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取评审统计概览（总数/待评审/已通过/已驳回）"""
    stats = await get_review_stats(db)
    return ResponseModel(data=ReviewStatsResponse(**stats))


@router.post("", response_model=ResponseModel[TestReviewDetail], status_code=status.HTTP_201_CREATED)
async def create_review(
    body: TestReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建评审（需校验项目存在，可选分配评审人）"""
    result = await db.execute(
        select(TestProject).where(TestProject.id == body.project_id),
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    review = TestReview(
        project_id=body.project_id,
        name=body.name,
        cases=body.cases,
        created_by=current_user.id,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)

    if body.reviewer_ids:
        await create_review_assignments(db, review.id, body.reviewer_ids)

    review = await get_review_with_assignments(db, review.id)
    return ResponseModel(data=TestReviewDetail.model_validate(review))


@router.get("/{review_id}", response_model=ResponseModel[TestReviewDetail])
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取评审详情"""
    review = await get_review_with_assignments(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评审不存在",
        )
    return ResponseModel(data=TestReviewDetail.model_validate(review))


@router.put("/{review_id}", response_model=ResponseModel[TestReviewDetail])
async def update_review(
    review_id: int,
    body: TestReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新评审"""
    result = await db.execute(
        select(TestReview).where(TestReview.id == review_id),
    )
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评审不存在",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    await db.flush()

    review_full = await get_review_with_assignments(db, review_id)
    return ResponseModel(data=TestReviewDetail.model_validate(review_full))


@router.delete("/{review_id}", response_model=ResponseModel)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除评审"""
    result = await db.execute(
        select(TestReview).where(TestReview.id == review_id),
    )
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评审不存在",
        )

    await db.delete(review)
    await db.flush()
    return ResponseModel(message="删除成功")


@router.post("/batch-delete", response_model=ResponseModel)
async def batch_delete_reviews(
    body: _IdListRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量删除评审"""
    result = await db.execute(
        delete(TestReview).where(TestReview.id.in_(body.ids)),
    )
    await db.flush()
    return ResponseModel(
        message=f"已删除 {result.rowcount} 个评审",
    )


@router.get("/{review_id}/cases", response_model=ResponseModel[list[ReviewCaseItem]])
async def list_review_cases(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取评审中的用例列表及评审状态"""
    result = await db.execute(
        select(TestReview).where(TestReview.id == review_id),
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="评审不存在")

    cases = await get_review_cases(db, review)

    # 批量查询最新执行结果
    exec_map: dict[int, str] = {}
    if cases:
        case_ids = [c.id for c in cases]
        exec_result = await db.execute(
            select(TestCaseExecution)
            .where(TestCaseExecution.case_id.in_(case_ids))
            .order_by(TestCaseExecution.case_id, TestCaseExecution.created_at.desc()),
        )
        for exec_record in exec_result.scalars().all():
            if exec_record.case_id not in exec_map:
                exec_map[exec_record.case_id] = exec_record.status

    return ResponseModel(
        data=[ReviewCaseItem(
            id=c.id,
            name=c.name,
            module=c.module,
            priority=c.priority,
            status=c.status,
            latest_execution_status=exec_map.get(c.id),
        ) for c in cases],
    )


@router.put("/{review_id}/cases/{case_id}", response_model=ResponseModel)
async def update_review_case(
    review_id: int,
    case_id: int,
    body: ReviewCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新评审中单个用例的评审状态（逐用例审批）"""
    result = await db.execute(
        select(TestReview).where(TestReview.id == review_id),
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="评审不存在")

    assignment = await update_review_case_assignment(
        db, review_id, case_id,
        status=body.status,
        comment=body.comment,
        reviewer_id=current_user.id,
    )
    return ResponseModel(data={
        "assignment_id": assignment.id if assignment else None,
        "case_id": case_id,
        "status": body.status,
    })


@router.post("/{review_id}/submit", response_model=ResponseModel[TestReviewDetail])
async def submit_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """提交评审（pending → passed）"""
    result = await db.execute(
        select(TestReview).where(TestReview.id == review_id),
    )
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评审不存在",
        )
    if review.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有 pending 状态的评审可以提交",
        )

    review.status = "passed"

    # 自动将关联的草稿用例状态改为 active
    if review.cases:
        case_ids = [c for c in review.cases if isinstance(c, int)]
        if case_ids:
            case_result = await db.execute(
                select(TestCase).where(
                    TestCase.id.in_(case_ids),
                    TestCase.status == "draft",
                ),
            )
            for case in case_result.scalars().all():
                case.status = "active"

    await db.flush()

    review_full = await get_review_with_assignments(db, review_id)
    return ResponseModel(data=TestReviewDetail.model_validate(review_full))


@router.post("/{review_id}/approve", response_model=ResponseModel[TestReviewDetail])
async def approve_review(
    review_id: int,
    body: TestReviewApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """审批评审（action='pass' → passed, action='reject' → rejected）"""
    result = await db.execute(
        select(TestReview).where(TestReview.id == review_id),
    )
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评审不存在",
        )
    if review.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有 pending 状态的评审可以审批",
        )

    if body.action == "pass":
        review.status = "passed"
        review.conclusion = body.conclusion

        # 自动将关联的草稿用例状态改为 active
        if review.cases:
            case_ids = [c for c in review.cases if isinstance(c, int)]
            if case_ids:
                case_result = await db.execute(
                    select(TestCase).where(
                        TestCase.id.in_(case_ids),
                        TestCase.status == "draft",
                    ),
                )
                for case in case_result.scalars().all():
                    case.status = "active"
    elif body.action == "reject":
        if not body.conclusion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="驳回时必须填写评审结论",
            )
        review.status = "rejected"
        review.conclusion = body.conclusion
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的审批动作，可选值: pass, reject",
        )

    await db.flush()

    review_full = await get_review_with_assignments(db, review_id)
    return ResponseModel(data=TestReviewDetail.model_validate(review_full))
