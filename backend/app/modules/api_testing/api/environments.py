"""
API 环境管理路由模块

提供测试环境的 CRUD 操作：创建、查询、更新、删除。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.modules.api_testing.models.environment import ApiEnvironment
from app.modules.api_testing.schemas.environment import (
    ApiEnvironmentCreate,
    ApiEnvironmentUpdate,
    ApiEnvironmentResponse,
)

router = APIRouter(prefix="/api/v1/api-environments", tags=["API环境管理"])


@router.get("", response_model=ResponseModel[list[ApiEnvironmentResponse]])
async def list_environments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取所有 API 测试环境列表"""
    stmt = select(ApiEnvironment).order_by(ApiEnvironment.id.asc())
    result = await db.execute(stmt)
    environments = result.scalars().all()
    return ResponseModel(
        data=[ApiEnvironmentResponse.model_validate(env) for env in environments],
    )


@router.post("", response_model=ResponseModel[ApiEnvironmentResponse])
async def create_environment(
    body: ApiEnvironmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建新的 API 测试环境"""
    env = ApiEnvironment(
        name=body.name,
        base_url=body.base_url,
        variables=body.variables,
        headers=body.headers,
        status="active",
    )
    db.add(env)
    await db.flush()
    await db.refresh(env)
    return ResponseModel(data=ApiEnvironmentResponse.model_validate(env))


@router.put("/{env_id}", response_model=ResponseModel[ApiEnvironmentResponse])
async def update_environment(
    env_id: int,
    body: ApiEnvironmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新 API 测试环境"""
    stmt = select(ApiEnvironment).where(ApiEnvironment.id == env_id)
    result = await db.execute(stmt)
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="环境不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(env, key, value)

    await db.flush()
    await db.refresh(env)
    return ResponseModel(data=ApiEnvironmentResponse.model_validate(env))


@router.delete("/{env_id}", response_model=ResponseModel)
async def delete_environment(
    env_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除 API 测试环境"""
    stmt = select(ApiEnvironment).where(ApiEnvironment.id == env_id)
    result = await db.execute(stmt)
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="环境不存在")

    await db.delete(env)
    await db.flush()
    return ResponseModel(message="环境已删除")
