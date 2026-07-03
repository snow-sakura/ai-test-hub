"""
测试版本 CRUD API 路由

提供测试版本的增删改查接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import PaginatedResponse, ResponseModel, IdListRequest
from app.database import get_db
from app.deps import get_current_active_user

from app.modules.aitest.models.project import TestProject
from app.modules.aitest.models.version import TestVersion
from app.modules.aitest.schemas.version import (
    TestVersionCreate,
    TestVersionResponse,
    TestVersionUpdate,
)
from app.modules.aitest.services.version_service import get_version, list_versions

router = APIRouter(prefix="/api/v1/test-versions", tags=["版本管理"])


@router.get("", response_model=PaginatedResponse[TestVersionResponse])
async def list_versions_api(
    project_id: int | None = Query(None, description="按项目筛选"),
    search: str | None = Query(None, description="搜索关键词"),
    status: str | None = Query(None, description="版本状态（released/in_progress/obsolete）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取版本列表"""
    versions, pagination = await list_versions(
        db, project_id=project_id, search=search, status=status,
        page=page, page_size=page_size,
    )
    return PaginatedResponse(
        data=[TestVersionResponse.model_validate(v) for v in versions],
        pagination=pagination,
    )


@router.post("", response_model=ResponseModel[TestVersionResponse], status_code=status.HTTP_201_CREATED)
async def create_version(
    body: TestVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建版本（需校验项目存在）"""
    result = await db.execute(
        select(TestProject).where(TestProject.id == body.project_id),
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    version = TestVersion(
        project_id=body.project_id,
        name=body.name,
        description=body.description,
        changelog=body.changelog,
        created_by=current_user.id,
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)

    return ResponseModel(data=TestVersionResponse.model_validate(version))


@router.put("/{version_id}", response_model=ResponseModel[TestVersionResponse])
async def update_version(
    version_id: int,
    body: TestVersionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新版本"""
    result = await db.execute(
        select(TestVersion).where(TestVersion.id == version_id),
    )
    version = result.scalar_one_or_none()

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版本不存在",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(version, field, value)

    await db.flush()
    await db.refresh(version)

    return ResponseModel(data=TestVersionResponse.model_validate(version))


@router.delete("/{version_id}", response_model=ResponseModel)
async def delete_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除版本（只能删除 in_progress/obsolete 状态的版本）"""
    result = await db.execute(
        select(TestVersion).where(TestVersion.id == version_id),
    )
    version = result.scalar_one_or_none()

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版本不存在",
        )

    if version.status not in ("in_progress", "obsolete"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能删除 in_progress 或 obsolete 状态的版本",
        )

    await db.delete(version)
    await db.flush()
    return ResponseModel(message="删除成功")


@router.post("/batch-delete", response_model=ResponseModel)
async def batch_delete_versions(
    body: IdListRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量删除版本"""
    result = await db.execute(
        delete(TestVersion).where(TestVersion.id.in_(body.ids)),
    )
    await db.flush()
    return ResponseModel(
        message=f"已删除 {result.rowcount} 个版本",
    )
