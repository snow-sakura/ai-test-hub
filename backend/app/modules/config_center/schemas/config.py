"""
配置中心 Pydantic 模型

定义 AI 模型配置、提示词配置、生成行为配置的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ======================================================================
# AI 模型配置 CRUD
# ======================================================================

class AIModelConfigSummary(BaseModel):
    """AI 模型配置概要（用于下拉选择）"""
    id: int
    name: str
    model_type: str
    role: str
    model_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class AIModelConfigCreate(BaseModel):
    """创建 AI 模型配置"""
    name: str = Field(..., min_length=1, max_length=100, description='配置名称')
    model_type: str = Field(..., description='模型类型（deepseek/qwen/siliconflow/openai/anthropic/other）')
    role: str = Field(..., description='角色（writer/reviewer/browser_use_text）')
    api_key: str | None = Field(None, description='API Key')
    base_url: str = Field(..., description='API Base URL')
    model_name: str = Field(..., description='模型名称')
    max_tokens: int = Field(4096, description='最大Token数')
    temperature: float = Field(0.7, description='温度参数')
    top_p: float = Field(0.9, description='Top P参数')


class AIModelConfigUpdate(BaseModel):
    """更新 AI 模型配置"""
    name: str | None = Field(None, max_length=100, description='配置名称')
    model_type: str | None = Field(None, description='模型类型')
    role: str | None = Field(None, description='角色')
    api_key: str | None = Field(None, description='API Key')
    base_url: str | None = Field(None, description='API Base URL')
    model_name: str | None = Field(None, description='模型名称')
    max_tokens: int | None = Field(None, description='最大Token数')
    temperature: float | None = Field(None, description='温度参数')
    top_p: float | None = Field(None, description='Top P参数')
    is_active: bool | None = Field(None, description='是否启用')


class AIModelConfigDetail(BaseModel):
    """AI 模型配置详情"""
    id: int
    name: str
    model_type: str
    role: str
    api_key: str | None = None
    base_url: str
    model_name: str
    max_tokens: int
    temperature: float
    top_p: float
    is_active: bool
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ======================================================================
# 提示词配置 CRUD
# ======================================================================

class PromptConfigSummary(BaseModel):
    """提示词配置概要（用于下拉选择）"""
    id: int
    name: str
    prompt_type: str
    is_active: bool

    model_config = {"from_attributes": True}


class PromptConfigCreate(BaseModel):
    """创建提示词配置"""
    name: str = Field(..., min_length=1, max_length=100, description='配置名称')
    prompt_type: str = Field(..., description='提示词类型（writer/reviewer）')
    content: str = Field(..., min_length=1, description='提示词内容')


class PromptConfigUpdate(BaseModel):
    """更新提示词配置"""
    name: str | None = Field(None, max_length=100, description='配置名称')
    prompt_type: str | None = Field(None, description='提示词类型')
    content: str | None = Field(None, description='提示词内容')
    is_active: bool | None = Field(None, description='是否启用')


class PromptConfigDetail(BaseModel):
    """提示词配置详情"""
    id: int
    name: str
    prompt_type: str
    content: str
    is_active: bool
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ======================================================================
# 生成行为配置
# ======================================================================

class GenerationConfigUpdate(BaseModel):
    """更新生成行为配置"""
    name: str | None = Field(None, max_length=100, description='配置名称')
    default_output_mode: str | None = Field(None, description='默认输出模式（stream/complete）')
    enable_auto_review: bool | None = Field(None, description='启用AI评审和改进')
    review_timeout: int | None = Field(None, description='评审和改进超时时间（秒）')


class GenerationConfigDetail(BaseModel):
    """生成行为配置详情"""
    id: int
    name: str
    default_output_mode: str
    enable_auto_review: bool
    review_timeout: int
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
