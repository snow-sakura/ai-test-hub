"""
测试项目 CRUD API 路由

提供项目的增删改查以及成员管理接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import PaginatedResponse, ResponseModel
from app.database import get_db
from app.deps import get_current_active_user


class _IdListRequest(BaseModel):
    """批量操作 ID 列表"""
    ids: list[int]
from app.modules.aitest.models.project import ProjectMember, TestProject
from sqlalchemy import delete as sa_delete
from app.modules.aitest.schemas.test_project import (
    MemberAdd,
    MemberResponse,
    MemberUpdate,
    ProjectStatsResponse,
    TestProjectCreate,
    TestProjectResponse,
    TestProjectUpdate,
)
from app.modules.aitest.services.project_service import (
    get_members_with_user,
    get_project_stats,
    get_project_with_counts,
    list_projects_with_counts,
)

# 合法角色集合：与 ProjectMember 模型 comment 对齐
VALID_ROLES = {"admin", "tester", "viewer"}

router = APIRouter(prefix="/api/v1/test-projects", tags=["测试项目管理"])


@router.get("", response_model=PaginatedResponse[TestProjectResponse])
async def list_projects(
    search: str | None = Query(None, description="搜索关键词（名称/负责人）"),
    status: str | None = Query(None, description="项目状态（active/completed/archived）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目列表"""
    projects, pagination = await list_projects_with_counts(
        db, search=search, status=status, page=page, page_size=page_size,
    )
    return PaginatedResponse(
        data=[TestProjectResponse.model_validate(p) for p in projects],
        pagination=pagination,
    )


@router.get("/stats", response_model=ResponseModel[ProjectStatsResponse])
async def get_project_stats_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目全量统计数据"""
    stats = await get_project_stats(db)
    return ResponseModel(data=ProjectStatsResponse(**stats))


@router.post("", response_model=ResponseModel[TestProjectResponse], status_code=status.HTTP_201_CREATED)
async def create_project(
    body: TestProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建测试项目（自动将创建者设为 admin 成员）"""
    project = TestProject(
        name=body.name,
        description=body.description,
        leader=body.leader,
        start_date=body.start_date,
        end_date=body.end_date,
        created_by=current_user.id,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    # 自动将创建者添加为 admin 成员
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="admin",
    )
    db.add(member)
    await db.flush()

    project.member_count = 1
    project.version_count = 0
    return ResponseModel(data=TestProjectResponse.model_validate(project))


@router.get("/{project_id}", response_model=ResponseModel[TestProjectResponse])
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目详情"""
    project = await get_project_with_counts(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )
    return ResponseModel(data=TestProjectResponse.model_validate(project))


@router.put("/{project_id}", response_model=ResponseModel[TestProjectResponse])
async def update_project(
    project_id: int,
    body: TestProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新项目"""
    project = await get_project_with_counts(db, project_id)
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
    project.member_count = len(project.members) if hasattr(project, "members") else 0
    project.version_count = len(project.versions) if hasattr(project, "versions") else 0
    return ResponseModel(data=TestProjectResponse.model_validate(project))


@router.delete("/{project_id}", response_model=ResponseModel)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除项目（只能删除 active 状态的项目）"""
    result = await db.execute(select(TestProject).where(TestProject.id == project_id))
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    if project.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能删除 active 状态的项目",
        )

    await db.delete(project)
    await db.flush()
    return ResponseModel(message="删除成功")


@router.post("/batch-delete", response_model=ResponseModel)
async def batch_delete_projects(
    body: _IdListRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量删除项目（仅允许删除 active 状态的项目）"""
    result = await db.execute(
        select(TestProject).where(TestProject.id.in_(body.ids))
    )
    projects = result.scalars().all()

    if not projects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    for project in projects:
        if project.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"项目「{project.name}」不是 active 状态，无法删除",
            )
        await db.delete(project)

    await db.flush()
    return ResponseModel(message=f"已删除 {len(projects)} 个项目")


class _BatchUpdateRequest(BaseModel):
    """批量更新项目请求"""
    ids: list[int]
    data: TestProjectUpdate


@router.post("/batch-update", response_model=ResponseModel)
async def batch_update_projects(
    body: _BatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量更新项目状态"""
    result = await db.execute(
        select(TestProject).where(TestProject.id.in_(body.ids))
    )
    projects = result.scalars().all()

    if not projects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    update_data = body.data.model_dump(exclude_unset=True)
    for project in projects:
        for field, value in update_data.items():
            setattr(project, field, value)

    await db.flush()
    return ResponseModel(message=f"已更新 {len(projects)} 个项目")


@router.get("/{project_id}/members", response_model=ResponseModel[list[MemberResponse]])
async def list_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目成员列表"""
    result = await db.execute(select(TestProject).where(TestProject.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    members = await get_members_with_user(db, project_id)
    member_list = []
    for m in members:
        member_list.append(MemberResponse(
            id=m.id,
            user_id=m.user_id,
            username=m.user.username if m.user else None,
            email=m.user.email if m.user else None,
            department=m.user.department if m.user else None,
            position=m.user.position if m.user else None,
            role=m.role,
            created_at=m.created_at,
        ))
    return ResponseModel(data=member_list)


@router.post("/{project_id}/members", response_model=ResponseModel[MemberResponse], status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: int,
    body: MemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """添加项目成员（需校验用户存在且未重复添加）"""
    # 校验项目存在
    result = await db.execute(select(TestProject).where(TestProject.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    # 校验用户存在
    user_result = await db.execute(
        select(User).where(User.id == body.user_id),
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 校验角色
    if body.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效角色，可选值: {', '.join(sorted(VALID_ROLES))}",
        )

    # 检查是否已存在
    exist_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == body.user_id,
        ),
    )
    if exist_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该用户已是项目成员",
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=body.user_id,
        role=body.role,
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)

    return ResponseModel(data=MemberResponse(
        id=member.id,
        user_id=member.user_id,
        username=user.username,
        email=user.email,
        department=user.department,
        position=user.position,
        role=member.role,
        created_at=member.created_at,
    ))


@router.put("/{project_id}/members/{user_id}", response_model=ResponseModel[MemberResponse])
async def update_member_role(
    project_id: int,
    user_id: int,
    body: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新项目成员角色"""
    # 校验项目存在
    result = await db.execute(select(TestProject).where(TestProject.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    # 校验成员存在
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ),
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    # 校验角色
    if body.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效角色，可选值: {', '.join(sorted(VALID_ROLES))}",
        )

    member.role = body.role
    await db.flush()
    await db.refresh(member)

    # 获取用户信息
    user_result = await db.execute(select(User).where(User.id == member.user_id))
    user = user_result.scalar_one_or_none()

    return ResponseModel(data=MemberResponse(
        id=member.id,
        user_id=member.user_id,
        username=user.username if user else None,
        email=user.email if user else None,
        department=user.department if user else None,
        position=user.position if user else None,
        role=member.role,
        created_at=member.created_at,
    ))


@router.delete("/{project_id}/members/{user_id}", response_model=ResponseModel)
async def remove_member(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """移除项目成员（不能移除自己）"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除自己",
        )

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ),
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    await db.delete(member)
    await db.flush()
    return ResponseModel(message="移除成功")


@router.post("/{project_id}/batch-remove-members", response_model=ResponseModel)
async def batch_remove_members(
    project_id: int,
    body: _IdListRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量移除项目成员（不能移除自己）"""
    ids_to_remove = [uid for uid in body.ids if uid != current_user.id]

    if not ids_to_remove:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可移除的成员（不能包含自己）",
        )

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id.in_(ids_to_remove),
        ),
    )
    members_to_delete = result.scalars().all()

    if not members_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    for member in members_to_delete:
        await db.delete(member)

    await db.flush()
    return ResponseModel(message=f"已移除 {len(members_to_delete)} 个成员")
