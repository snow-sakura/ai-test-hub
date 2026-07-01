"""
AI 生成候选用例 API 路由

提供对 GeneratedCaseItem 的查询、批量状态更新和保存到用例库接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.models.user import User
from app.common.schemas.common import PaginatedResponse, PaginationMeta, ResponseModel
from app.database import get_db
from app.deps import get_current_active_user
from app.modules.aitest.models.ai_task import AIGenerationTask
from app.modules.aitest.models.generated_case_item import GeneratedCaseItem
from app.modules.aitest.models.test_case import TestCase
from app.modules.aitest.schemas.generated_case import (
    BatchUpdateCasesRequest,
    GeneratedCaseItemResponse,
    SaveToLibraryRequest,
)
from app.modules.aitest.schemas.test_case import TestCaseResponse
from app.modules.aitest.services.operation_log_service import create_log

router = APIRouter(prefix="/api/v1/ai", tags=["AI 候选用例管理"])


async def _get_task_or_404(
    task_id: str,
    db: AsyncSession,
) -> AIGenerationTask:
    """根据 UUID task_id 获取生成任务，不存在则 404"""
    result = await db.execute(
        select(AIGenerationTask).where(AIGenerationTask.task_id == task_id),
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生成任务不存在",
        )
    return task


@router.get(
    "/generate/tasks/{task_id}/generated-cases",
    response_model=PaginatedResponse,
)
async def list_generated_cases(
    task_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: str | None = Query(None, description="按状态筛选（pending/adopted/discarded）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取生成任务的候选用例列表（分页）"""
    # 校验任务存在，获取 DB ID
    task = await _get_task_or_404(task_id, db)

    # 构建查询
    base_where = [GeneratedCaseItem.task_id == task.id]
    if status:
        base_where.append(GeneratedCaseItem.status == status)

    # 统计总数（使用 SQL COUNT 避免全表加载）
    count_stmt = (
        select(func.count(GeneratedCaseItem.id))
        .where(*base_where)
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # 分页查询
    stmt = (
        select(GeneratedCaseItem)
        .where(*base_where)
        .order_by(GeneratedCaseItem.sort_order, GeneratedCaseItem.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return PaginatedResponse(
        data=[GeneratedCaseItemResponse.model_validate(item).model_dump() for item in items],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, (total + page_size - 1) // page_size),
        ),
    )


@router.post(
    "/generate/tasks/{task_id}/batch-update-cases",
    response_model=ResponseModel,
)
async def batch_update_cases(
    task_id: str,
    body: BatchUpdateCasesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量更新候选用例状态（采纳/丢弃/待定）"""
    # 校验任务存在，获取 DB ID
    task = await _get_task_or_404(task_id, db)

    # 校验候选用例列表属于该任务
    result = await db.execute(
        select(GeneratedCaseItem)
        .where(
            GeneratedCaseItem.id.in_(body.case_ids),
            GeneratedCaseItem.task_id == task.id,
        ),
    )
    exists = list(result.scalars().all())
    if len(exists) != len(body.case_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部分候选用例不存在或不属于该任务",
        )

    # 批量更新状态
    await db.execute(
        update(GeneratedCaseItem)
        .where(GeneratedCaseItem.id.in_(body.case_ids))
        .values(status=body.status),
    )
    await db.flush()

    # 记录操作日志
    await create_log(
        db,
        entity_type="task",
        entity_id=task.id,
        action=f"批量更新候选用例状态为「{body.status}」",
        operator_id=current_user.id,
        detail={
            "case_ids": body.case_ids,
            "status": body.status,
            "count": len(body.case_ids),
        },
    )

    return ResponseModel(message=f"已更新 {len(body.case_ids)} 个候选用例状态为 {body.status}")


@router.post(
    "/generate/tasks/{task_id}/save-to-library",
    response_model=ResponseModel[list[TestCaseResponse]],
    status_code=status.HTTP_201_CREATED,
)
async def save_to_library(
    task_id: str,
    body: SaveToLibraryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """将已采纳的候选用例保存到测试用例库"""
    # 校验任务存在
    task = await _get_task_or_404(task_id, db)

    # 查询已采纳的候选用例
    query = (
        select(GeneratedCaseItem)
        .where(
            GeneratedCaseItem.task_id == task.id,
            GeneratedCaseItem.status == "adopted",
        )
        .order_by(GeneratedCaseItem.sort_order, GeneratedCaseItem.id)
    )
    # 如果指定了 case_ids，仅保存选中的用例
    if body.case_ids:
        query = query.where(GeneratedCaseItem.id.in_(body.case_ids))
    result = await db.execute(query)
    adopted_items = list(result.scalars().all())

    if not adopted_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有已采纳的候选用例，请先通过批量更新接口标记用例为 adopted",
        )

    # 确定目标项目 ID：优先使用请求中的，回退到任务关联的项目
    target_project_id = body.project_id or task.project_id

    # 批量创建 TestCase 记录
    new_cases: list[TestCase] = []
    for item in adopted_items:
        # 将 tags 从逗号分隔字符串转为列表
        tags_list = None
        if item.tags:
            tags_list = [t.strip() for t in item.tags.split(",") if t.strip()]

        case = TestCase(
            project_id=target_project_id,
            name=item.title,
            module=item.module,
            priority=item.priority.lower() if item.priority else "p2",
            precondition=item.precondition,
            test_steps=item.test_steps,
            expected_result=item.expected_result,
            tags=tags_list,
            source="ai_generated",
            test_type="functional",
            status="active",
            created_by=current_user.id,
        )
        db.add(case)
        new_cases.append(case)

    await db.flush()
    for c in new_cases:
        await db.refresh(c)

    # 标记任务已保存到用例库
    task.saved_to_library = True
    await db.flush()

    # 记录操作日志
    await create_log(
        db,
        entity_type="task",
        entity_id=task.id,
        action=f"保存 {len(new_cases)} 个候选用例到用例库",
        operator_id=current_user.id,
        detail={
            "project_id": target_project_id,
            "case_count": len(new_cases),
            "case_ids": [c.id for c in new_cases],
        },
    )

    return ResponseModel(
        data=[TestCaseResponse.model_validate(c) for c in new_cases],
        message=f"成功将 {len(new_cases)} 个候选用例保存到用例库",
    )
