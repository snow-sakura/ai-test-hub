"""
操作日志 API 路由

提供按实体查询操作日志的接口，
用于追踪用例、项目等实体的变更历史。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import PaginatedResponse, PaginationMeta, ResponseModel
from app.database import get_db
from app.deps import get_current_active_user
from app.modules.aitest.models.project import TestProject
from app.modules.aitest.models.test_case import TestCase
from app.modules.aitest.schemas.operation_log import OperationLogResponse
from app.modules.aitest.services.operation_log_service import list_logs

router = APIRouter(prefix="/api/v1", tags=["操作日志"])


@router.get(
    "/cases/{case_id}/logs",
    response_model=PaginatedResponse,
)
async def list_case_logs(
    case_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用例的操作日志列表"""
    # 校验用例存在
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id),
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用例不存在",
        )

    logs, total = await list_logs(
        db, entity_type="case", entity_id=case_id,
        page=page, page_size=page_size,
    )

    return PaginatedResponse(
        data=[OperationLogResponse.model_validate(log).model_dump() for log in logs],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, (total + page_size - 1) // page_size),
        ),
    )


@router.get(
    "/projects/{project_id}/logs",
    response_model=PaginatedResponse,
)
async def list_project_logs(
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目的操作日志列表"""
    # 校验项目存在
    result = await db.execute(
        select(TestProject).where(TestProject.id == project_id),
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    logs, total = await list_logs(
        db, entity_type="project", entity_id=project_id,
        page=page, page_size=page_size,
    )

    return PaginatedResponse(
        data=[OperationLogResponse.model_validate(log).model_dump() for log in logs],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, (total + page_size - 1) // page_size),
        ),
    )
