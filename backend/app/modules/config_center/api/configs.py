"""
配置中心 API 路由模块

提供 AI 模型配置、提示词配置、生成行为配置的 CRUD 功能。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.modules.config_center.models.ai_model_config import AIModelConfig
from app.modules.config_center.models.prompt_config import PromptConfig
from app.modules.config_center.models.generation_config import GenerationConfig
from app.common.models.user import User
from app.modules.config_center.schemas.config import (
    AIModelConfigCreate,
    AIModelConfigDetail,
    AIModelConfigUpdate,
    PromptConfigCreate,
    PromptConfigDetail,
    PromptConfigUpdate,
    GenerationConfigDetail,
    GenerationConfigUpdate,
)
from app.common.schemas.common import ResponseModel

class _IdListRequest(BaseModel):
    """批量操作 ID 列表"""
    ids: list[int]

router = APIRouter(prefix="/api/v1/configs", tags=["配置中心"])


# ======================================================================
# AI 模型配置 CRUD
# ======================================================================

@router.get("/models/all", response_model=ResponseModel[list[AIModelConfigDetail]])
async def list_all_ai_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取所有 AI 模型配置（用于配置管理页面）

    不论是否启用，返回完整配置信息（含 API Key 脱敏）。
    """
    stmt = select(AIModelConfig).order_by(AIModelConfig.id.asc())
    result = await db.execute(stmt)
    models = result.scalars().all()

    # API Key 脱敏：仅显示前 4 + 后 4 字符
    for m in models:
        if m.api_key and len(m.api_key) > 8:
            m.api_key = m.api_key[:4] + "****" + m.api_key[-4:]
        elif m.api_key:
            m.api_key = "****"

    return ResponseModel(
        data=[AIModelConfigDetail.model_validate(m) for m in models],
    )


@router.post("/models", response_model=ResponseModel[AIModelConfigDetail])
async def create_ai_model(
    body: AIModelConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建 AI 模型配置"""
    model = AIModelConfig(
        name=body.name,
        model_type=body.model_type,
        role=body.role,
        api_key=body.api_key or "",
        base_url=body.base_url,
        model_name=body.model_name,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        top_p=body.top_p,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return ResponseModel(data=AIModelConfigDetail.model_validate(model))


@router.put("/models/{model_id}", response_model=ResponseModel[AIModelConfigDetail])
async def update_ai_model(
    model_id: int,
    body: AIModelConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新 AI 模型配置"""
    stmt = select(AIModelConfig).where(AIModelConfig.id == model_id)
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在")

    # 只更新提供的字段
    update_data = body.model_dump(exclude_unset=True)
    # 后端防护：拒绝保存脱敏或空的 API Key，避免前端脱敏值覆盖真实 Key
    if "api_key" in update_data:
        val = update_data["api_key"]
        if not val or "****" in val:
            logger.warning("跳过 API Key 更新：值为脱敏或空 (model_id=%s)", model_id)
            del update_data["api_key"]
    for key, value in update_data.items():
        setattr(model, key, value)

    await db.flush()
    await db.refresh(model)
    return ResponseModel(data=AIModelConfigDetail.model_validate(model))


@router.delete("/models/{model_id}", response_model=ResponseModel)
async def delete_ai_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除 AI 模型配置"""
    stmt = select(AIModelConfig).where(AIModelConfig.id == model_id)
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在")

    await db.delete(model)
    await db.flush()
    return ResponseModel(message="模型配置已删除")


@router.post("/models/batch-delete", response_model=ResponseModel)
async def batch_delete_ai_models(
    body: _IdListRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量删除 AI 模型配置"""
    result = await db.execute(
        select(AIModelConfig).where(AIModelConfig.id.in_(body.ids))
    )
    models = result.scalars().all()

    if not models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在")

    for model in models:
        await db.delete(model)

    await db.flush()
    return ResponseModel(message=f"已删除 {len(models)} 个模型配置")


@router.post("/models/{model_id}/activate", response_model=ResponseModel[AIModelConfigDetail])
async def activate_ai_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """设为活跃模型（将同一角色下的所有模型设为非活跃，再将当前模型设为活跃）"""
    stmt = select(AIModelConfig).where(AIModelConfig.id == model_id)
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在")

    # 同一角色下的其他模型设为非活跃
    await db.execute(
        update(AIModelConfig)
        .where(AIModelConfig.role == model.role)
        .where(AIModelConfig.id != model_id)
        .values(is_active=False)
    )
    # 当前模型设为活跃
    model.is_active = True
    await db.flush()
    await db.refresh(model)
    return ResponseModel(data=AIModelConfigDetail.model_validate(model))


# ======================================================================
# 提示词配置 CRUD
# ======================================================================

@router.get("/prompts", response_model=ResponseModel[list[PromptConfigDetail]])
async def list_all_prompts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取所有提示词配置（用于配置管理页面）

    返回完整配置信息，不论是否启用。
    """
    stmt = select(PromptConfig).order_by(PromptConfig.id.asc())
    result = await db.execute(stmt)
    prompts = result.scalars().all()

    return ResponseModel(
        data=[PromptConfigDetail.model_validate(p) for p in prompts],
    )


@router.post("/prompts", response_model=ResponseModel[PromptConfigDetail])
async def create_prompt_config(
    body: PromptConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建提示词配置"""
    prompt = PromptConfig(
        name=body.name,
        prompt_type=body.prompt_type,
        content=body.content,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(prompt)
    await db.flush()
    await db.refresh(prompt)
    return ResponseModel(data=PromptConfigDetail.model_validate(prompt))


@router.put("/prompts/{prompt_id}", response_model=ResponseModel[PromptConfigDetail])
async def update_prompt_config(
    prompt_id: int,
    body: PromptConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新提示词配置"""
    stmt = select(PromptConfig).where(PromptConfig.id == prompt_id)
    result = await db.execute(stmt)
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词配置不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prompt, key, value)

    await db.flush()
    await db.refresh(prompt)
    return ResponseModel(data=PromptConfigDetail.model_validate(prompt))


@router.delete("/prompts/{prompt_id}", response_model=ResponseModel)
async def delete_prompt_config(
    prompt_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除提示词配置"""
    stmt = select(PromptConfig).where(PromptConfig.id == prompt_id)
    result = await db.execute(stmt)
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词配置不存在")

    await db.delete(prompt)
    await db.flush()
    return ResponseModel(message="提示词配置已删除")


@router.post("/prompts/batch-delete", response_model=ResponseModel)
async def batch_delete_prompt_configs(
    body: _IdListRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量删除提示词配置"""
    result = await db.execute(
        select(PromptConfig).where(PromptConfig.id.in_(body.ids))
    )
    prompts = result.scalars().all()

    if not prompts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词配置不存在")

    for prompt in prompts:
        await db.delete(prompt)

    await db.flush()
    return ResponseModel(message=f"已删除 {len(prompts)} 个提示词配置")


# ======================================================================
# 生成行为配置
# ======================================================================

@router.get("/generation-config", response_model=ResponseModel[GenerationConfigDetail])
async def get_generation_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前生效的生成行为配置"""
    stmt = select(GenerationConfig).where(GenerationConfig.is_active.is_(True)).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生成行为配置不存在")
    return ResponseModel(data=GenerationConfigDetail.model_validate(config))


@router.put("/generation-config", response_model=ResponseModel[GenerationConfigDetail])
async def update_generation_config(
    body: GenerationConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新生成行为配置

    仅更新提供的字段。如果当前没有配置记录，会自动创建一条新的默认配置再更新。
    """
    stmt = select(GenerationConfig).where(GenerationConfig.is_active.is_(True)).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if config is None:
        # 没有现有配置，创建默认配置再更新
        config = GenerationConfig(name="默认生成配置", is_active=True)
        db.add(config)
        await db.flush()

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    # 确保是活跃状态
    config.is_active = True

    await db.flush()
    await db.refresh(config)
    return ResponseModel(data=GenerationConfigDetail.model_validate(config))
