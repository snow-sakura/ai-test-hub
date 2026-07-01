"""
API 环境 Pydantic 模型

定义环境配置的创建、更新和响应数据结构。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiEnvironmentCreate(BaseModel):
    """创建 API 环境请求"""
    name: str
    base_url: str
    variables: dict | None = None
    headers: dict | None = None


class ApiEnvironmentUpdate(BaseModel):
    """更新 API 环境请求"""
    name: str | None = None
    base_url: str | None = None
    variables: dict | None = None
    headers: dict | None = None
    status: str | None = None


class ApiEnvironmentResponse(BaseModel):
    """API 环境响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str
    variables: dict | None
    headers: dict | None
    status: str
    created_at: datetime
    updated_at: datetime
