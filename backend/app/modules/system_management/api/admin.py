"""
系统管理路由模块

提供用户管理、角色权限、系统设置、审计日志等系统管理 RESTful 接口。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_active_user, get_current_user
from app.common.models.role import Role, UserRole
from app.modules.system_management.models.system import OperationLog
from app.common.models.user import User
from app.common.schemas.common import PaginatedResponse, PaginationMeta, ResponseModel
from app.common.schemas.user import (
    AdminUserCreate,
    AdminUserUpdate,
    AuditLogResponse,
    ResetPasswordRequest,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    SystemSettingsResponse,
    SystemSettingsUpdate,
    UserResponse,
)
from app.common.services.auth_service import hash_password
from app.common.utils.pagination import paginate

router = APIRouter(prefix="/api/v1/admin", tags=["系统管理"])


# ====================================================================
# 操作日志记录中间件（辅助函数，各端点主动调用）
# ====================================================================


async def _log_operation(
    db: AsyncSession,
    user: User,
    action: str,
    module: str,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    status: str = "success",
) -> None:
    """记录操作日志到数据库"""
    log = OperationLog(
        user_id=user.id,
        username=user.username,
        action=action,
        module=module,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address,
        status=status,
    )
    db.add(log)
    await db.flush()


def _get_client_ip(request: Request) -> str:
    """从请求中提取客户端 IP 地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# ====================================================================
# 用户管理
# ====================================================================


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    keyword: str | None = Query(None, description="搜索关键词(用户名/邮箱)"),
    is_active: bool | None = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表（分页，支持搜索）"""
    query = select(User).options(selectinload(User.roles))

    # 搜索过滤
    if keyword:
        query = query.where(
            (User.username.like(f"%{keyword}%"))
            | (User.email.like(f"%{keyword}%"))
            | (User.phone.like(f"%{keyword}%"))
        )
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.order_by(User.created_at.desc())
    users, pagination = await paginate(db, query, page=page, page_size=page_size)

    return PaginatedResponse(
        data=[UserResponse.model_validate(u) for u in users],
        pagination=pagination,
    )


@router.post("/users", response_model=ResponseModel[UserResponse])
async def create_user(
    body: AdminUserCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建用户（管理员）"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被占用",
        )

    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被占用",
        )

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        phone=body.phone,
        department=body.department,
        position=body.position,
        is_active=body.is_active,
        is_superuser=body.is_superuser,
    )
    db.add(user)
    await db.flush()

    # 处理角色关联
    if body.role_ids:
        roles_result = await db.execute(
            select(Role).where(Role.id.in_(body.role_ids))
        )
        roles = roles_result.scalars().all()
        for role in roles:
            db.add(UserRole(user_id=user.id, role_id=role.id))
        await db.flush()

    await db.refresh(user)

    # 重新加载用户以包含角色关系
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user.id)
    )
    user = result.scalar_one()

    # 记录操作日志
    await _log_operation(
        db=db,
        user=current_user,
        action="create",
        module="user_management",
        target_type="User",
        target_id=user.id,
        detail=f"创建用户：{user.username} ({user.email})",
        ip_address=_get_client_ip(request),
    )

    return ResponseModel(data=UserResponse.model_validate(user))


@router.put("/users/{user_id}", response_model=ResponseModel[UserResponse])
async def update_user(
    user_id: int,
    body: AdminUserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """修改用户信息（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 处理角色关联（单独处理，不通过 setattr）
    if body.role_ids is not None:
        # 清除旧的角色关联
        old_roles = await db.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        for old_role in old_roles.scalars().all():
            await db.delete(old_role)
        await db.flush()

        # 添加新的角色关联
        if body.role_ids:
            roles_result = await db.execute(
                select(Role).where(Role.id.in_(body.role_ids))
            )
            roles = roles_result.scalars().all()
            for role in roles:
                db.add(UserRole(user_id=user_id, role_id=role.id))
            await db.flush()

    # 更新用户基本字段（排除 role_ids）
    update_data = body.model_dump(exclude_unset=True, exclude={"role_ids"})
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)

    # 重新加载用户以包含角色关系
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user.id)
    )
    user = result.scalar_one()

    # 记录操作日志
    await _log_operation(
        db=db,
        user=current_user,
        action="update",
        module="user_management",
        target_type="User",
        target_id=user.id,
        detail=f"修改用户信息：{user.username}",
        ip_address=_get_client_ip(request),
    )

    return ResponseModel(data=UserResponse.model_validate(user))


@router.delete("/users/{user_id}", response_model=ResponseModel)
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除用户（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 不允许删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录用户",
        )

    # 先清除用户角色关联
    old_roles = await db.execute(
        select(UserRole).where(UserRole.user_id == user_id)
    )
    for old_role in old_roles.scalars().all():
        await db.delete(old_role)
    await db.flush()

    username = user.username
    await db.delete(user)
    await db.flush()

    # 记录操作日志
    await _log_operation(
        db=db,
        user=current_user,
        action="delete",
        module="user_management",
        target_type="User",
        target_id=user_id,
        detail=f"删除用户：{username}",
        ip_address=_get_client_ip(request),
    )

    return ResponseModel(message="用户已删除")


@router.put("/users/{user_id}/reset-password", response_model=ResponseModel)
async def reset_password(
    user_id: int,
    body: ResetPasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """重置用户密码（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    user.hashed_password = hash_password(body.password)
    await db.flush()

    # 记录操作日志
    await _log_operation(
        db=db,
        user=current_user,
        action="update",
        module="user_management",
        target_type="User",
        target_id=user_id,
        detail=f"重置用户密码：{user.username}",
        ip_address=_get_client_ip(request),
    )

    return ResponseModel(message="密码重置成功")


# ====================================================================
# 角色权限
# ====================================================================


@router.get("/roles", response_model=ResponseModel[list[RoleResponse]])
async def list_roles(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有角色列表"""
    result = await db.execute(
        select(Role).order_by(Role.created_at.asc())
    )
    roles = result.scalars().all()
    return ResponseModel(
        data=[RoleResponse.model_validate(r) for r in roles]
    )


@router.post("/roles", response_model=ResponseModel[RoleResponse])
async def create_role(
    body: RoleCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建角色"""
    # 检查名称是否重复
    result = await db.execute(select(Role).where(Role.name == body.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="角色名称已存在",
        )

    # 检查编码是否重复
    result = await db.execute(select(Role).where(Role.code == body.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="角色编码已存在",
        )

    role = Role(
        name=body.name,
        code=body.code,
        description=body.description,
        permissions=body.permissions or {},
    )
    db.add(role)
    await db.flush()
    await db.refresh(role)

    # 记录操作日志
    await _log_operation(
        db=db,
        user=current_user,
        action="create",
        module="role_permission",
        target_type="Role",
        target_id=role.id,
        detail=f"创建角色：{role.name} ({role.code})",
        ip_address=_get_client_ip(request),
    )

    return ResponseModel(data=RoleResponse.model_validate(role))


@router.put("/roles/{role_id}", response_model=ResponseModel[RoleResponse])
async def update_role(
    role_id: int,
    body: RoleUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新角色信息"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    await db.flush()
    await db.refresh(role)

    # 记录操作日志
    await _log_operation(
        db=db,
        user=current_user,
        action="update",
        module="role_permission",
        target_type="Role",
        target_id=role_id,
        detail=f"更新角色：{role.name}",
        ip_address=_get_client_ip(request),
    )

    return ResponseModel(data=RoleResponse.model_validate(role))


@router.delete("/roles/{role_id}", response_model=ResponseModel)
async def delete_role(
    role_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除角色"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在",
        )

    # 不允许删除系统内置角色
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置角色不可删除",
        )

    role_name = role.name
    await db.delete(role)
    await db.flush()

    # 记录操作日志
    await _log_operation(
        db=db,
        user=current_user,
        action="delete",
        module="role_permission",
        target_type="Role",
        target_id=role_id,
        detail=f"删除角色：{role_name}",
        ip_address=_get_client_ip(request),
    )

    return ResponseModel(message="角色已删除")


# ====================================================================
# 系统设置（存储在数据库 AISettings 表中）
# ====================================================================


@router.get("/settings", response_model=ResponseModel[SystemSettingsResponse])
async def get_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取系统设置"""
    from app.modules.aitest.models.ai_settings import AISettings

    result = await db.execute(select(AISettings).limit(1))
    settings = result.scalar_one_or_none()

    # 如果还没有设置记录，返回默认值
    if not settings:
        return ResponseModel(data=SystemSettingsResponse())

    return ResponseModel(
        data=SystemSettingsResponse(
            site_name=settings.site_name or "AI-HUB",
            site_description=settings.site_description or "",
            logo_url=settings.logo_url,
            icp_beian=settings.icp_beian,
            password_min_length=settings.password_min_length or 6,
            password_complexity=settings.password_complexity or "letter_digit",
            max_login_attempts=settings.max_login_attempts or 5,
            login_lock_minutes=settings.login_lock_minutes or 30,
            session_timeout_minutes=settings.session_timeout_minutes or 60,
            password_expire_days=settings.password_expire_days or 90,
            upload_max_size_mb=settings.upload_max_size_mb or 100,
            allowed_file_types=settings.allowed_file_types or "pdf,doc,docx,md",
        )
    )


@router.put("/settings", response_model=ResponseModel[SystemSettingsResponse])
async def update_settings(
    body: SystemSettingsUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新系统设置"""
    from app.modules.aitest.models.ai_settings import AISettings

    result = await db.execute(select(AISettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = AISettings()
        db.add(settings)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.flush()
    await db.refresh(settings)

    # 记录操作日志
    await _log_operation(
        db=db,
        user=current_user,
        action="update",
        module="system_settings",
        detail="更新系统设置",
        ip_address=_get_client_ip(request),
    )

    return ResponseModel(
        data=SystemSettingsResponse(
            site_name=settings.site_name or "AI-HUB",
            site_description=settings.site_description or "",
            logo_url=settings.logo_url,
            icp_beian=settings.icp_beian,
            password_min_length=settings.password_min_length or 6,
            password_complexity=settings.password_complexity or "letter_digit",
            max_login_attempts=settings.max_login_attempts or 5,
            login_lock_minutes=settings.login_lock_minutes or 30,
            session_timeout_minutes=settings.session_timeout_minutes or 60,
            password_expire_days=settings.password_expire_days or 90,
            upload_max_size_mb=settings.upload_max_size_mb or 100,
            allowed_file_types=settings.allowed_file_types or "pdf,doc,docx,md",
        )
    )


# ====================================================================
# 审计日志
# ====================================================================


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    action: str | None = Query(None, description="操作类型筛选"),
    module: str | None = Query(None, description="操作模块筛选"),
    username: str | None = Query(None, description="用户名筛选"),
    keyword: str | None = Query(None, description="关键词搜索(详情/用户名/IP)"),
    start_date: str | None = Query(None, description="开始时间(ISO格式)"),
    end_date: str | None = Query(None, description="结束时间(ISO格式)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取审计日志列表（分页，支持搜索）"""
    query = select(OperationLog)

    # 筛选条件
    if action:
        query = query.where(OperationLog.action == action)
    if module:
        query = query.where(OperationLog.module == module)
    if username:
        query = query.where(OperationLog.username.like(f"%{username}%"))
    if keyword:
        query = query.where(
            (OperationLog.detail.like(f"%{keyword}%"))
            | (OperationLog.username.like(f"%{keyword}%"))
            | (OperationLog.ip_address.like(f"%{keyword}%"))
        )
    if start_date:
        try:
            dt = datetime.fromisoformat(start_date)
            query = query.where(OperationLog.created_at >= dt)
        except ValueError:
            pass
    if end_date:
        try:
            dt = datetime.fromisoformat(end_date)
            query = query.where(OperationLog.created_at <= dt)
        except ValueError:
            pass

    query = query.order_by(OperationLog.created_at.desc())
    logs, pagination = await paginate(db, query, page=page, page_size=page_size)

    return PaginatedResponse(
        data=[AuditLogResponse.model_validate(l) for l in logs],
        pagination=pagination,
    )
