"""
认证接口模块

提供用户注册、登录、Token 刷新、登出、用户信息管理等 RESTful 接口。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_active_user
from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.common.schemas.user import (
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.common.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["认证管理"])


@router.post("/register", response_model=ResponseModel[UserResponse])
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册接口"""
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == body.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被注册",
        )

    # 检查邮箱是否已存在
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册",
        )

    # 创建用户
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()  # 刷新以获取 id
    await db.refresh(user)

    # 预加载 roles 关联
    result = await db.execute(
        select(User).where(User.id == user.id).options(selectinload(User.roles))
    )
    user = result.scalar_one()

    return ResponseModel(data=UserResponse.model_validate(user))


@router.post("/login", response_model=ResponseModel[TokenResponse])
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录接口，返回 access_token 和 refresh_token"""
    user = await authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该账户已被禁用",
        )

    # 更新最后登录时间
    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    # 生成 token，payload 中包含 user_id 和 username
    token_data = {"user_id": user.id, "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return ResponseModel(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    )


@router.post("/refresh", response_model=ResponseModel[TokenResponse])
async def refresh_token(body: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """刷新 access token"""
    payload = decode_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token 无效或已过期",
        )

    # 确保是 refresh 类型的 token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 类型错误，需要 refresh token",
        )

    user_id = payload.get("user_id")
    username = payload.get("username")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload 无效",
        )

    # 验证用户仍然存在且活跃
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    # 生成新的 token
    token_data = {"user_id": user_id, "username": username}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return ResponseModel(
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
    )


@router.post("/logout", response_model=ResponseModel)
async def logout(
    current_user: User = Depends(get_current_active_user),
):
    """用户登出接口（当前为无状态实现，由前端清除 token）"""
    return ResponseModel(message="登出成功")


@router.get("/me", response_model=ResponseModel[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户信息"""
    # 重新查询以预加载 roles 关联（避免懒加载 MissingGreenlet 错误）
    result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.roles))
    )
    user = result.scalar_one()
    return ResponseModel(data=UserResponse.model_validate(user))


@router.put("/me", response_model=ResponseModel[UserResponse])
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前登录用户信息"""
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.flush()
    await db.refresh(current_user)

    # 重新查询以预加载 roles 关联
    result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.roles))
    )
    user = result.scalar_one()
    return ResponseModel(data=UserResponse.model_validate(user))
