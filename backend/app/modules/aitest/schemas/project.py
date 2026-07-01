"""
项目 Pydantic 模型

定义项目相关的请求/响应模型，用于下拉选择及 CRUD 操作。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """创建项目请求体"""
    name: str = Field(..., min_length=1, max_length=100, description='项目名称')
    description: str | None = Field(None, description='项目描述')


class ProjectUpdate(BaseModel):
    """更新项目请求体"""
    name: str | None = Field(None, min_length=1, max_length=100, description='项目名称')
    description: str | None = Field(None, description='项目描述')


class ProjectSummary(BaseModel):
    """项目概要信息（用于下拉选择）"""
    id: int = Field(..., description='项目ID')
    name: str = Field(..., description='项目名称')
    description: str | None = Field(None, description='项目描述')

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    """项目详细响应体"""
    id: int
    name: str
    description: str | None = None
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
