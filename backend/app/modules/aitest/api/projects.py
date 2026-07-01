"""
项目 CRUD 接口模块

提供项目的增删改查 RESTful 接口，用于 AI 用例生成时的项目下拉选择。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.common.models.user import User
from app.common.models.project import Project
from app.common.schemas.common import ResponseModel
from app.modules.aitest.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectSummary,
    ProjectUpdate,
)

router = APIRouter(prefix="/api/v1/projects", tags=["项目管理"])


@router.get("", response_model=ResponseModel[list[ProjectSummary]])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取项目列表

    按创建时间倒序返回所有项目。
    """
    stmt = select(Project).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()

    return ResponseModel(
        data=[ProjectSummary.model_validate(p) for p in projects],
    )


@router.post("", response_model=ResponseModel[ProjectResponse], status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建项目
    """
    project = Project(
        name=body.name,
        description=body.description,
        created_by=current_user.id,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    return ResponseModel(data=ProjectResponse.model_validate(project))


@router.put("/{project_id}", response_model=ResponseModel[ProjectResponse])
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新项目
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.flush()
    await db.refresh(project)

    return ResponseModel(data=ProjectResponse.model_validate(project))


@router.delete("/{project_id}", response_model=ResponseModel)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除项目
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    await db.delete(project)
    await db.flush()

    return ResponseModel(message="删除成功")
