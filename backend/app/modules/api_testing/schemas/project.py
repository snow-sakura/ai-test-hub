"""
API 项目 Pydantic 模型

定义 API 项目管理相关的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ApiProjectCreate(BaseModel):
    """创建 API 项目请求体"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: str | None = Field(None, description="项目描述")
    base_url: str | None = Field(None, description="基础 URL")
    swagger_url: str | None = Field(None, description="Swagger URL")
    version: str | None = Field(None, description="API 版本")


class ApiProjectUpdate(BaseModel):
    """更新 API 项目请求体"""
    name: str | None = Field(None, min_length=1, max_length=100, description="项目名称")
    description: str | None = Field(None, description="项目描述")
    base_url: str | None = Field(None, description="基础 URL")
    swagger_url: str | None = Field(None, description="Swagger URL")
    version: str | None = Field(None, description="API 版本")
    status: str | None = Field(None, description="状态")


class ApiProjectResponse(BaseModel):
    """API 项目响应体"""
    id: int
    name: str
    description: str | None = None
    base_url: str | None = None
    swagger_url: str | None = None
    version: str | None = None
    status: str = "active"
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiProjectSummary(BaseModel):
    """API 项目概要（用于下拉选择）"""
    id: int
    name: str
    description: str | None = None
    base_url: str | None = None
    version: str | None = None
    status: str = "active"
    endpoint_count: int = 0

    model_config = {"from_attributes": True}
