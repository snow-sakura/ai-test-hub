"""
API 端点 Pydantic 模型

定义 API 接口管理相关的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ApiEndpointCreate(BaseModel):
    """创建 API 端点请求体"""
    name: str = Field(..., min_length=1, max_length=200, description="接口名称")
    path: str = Field(..., min_length=1, max_length=500, description="接口路径")
    method: str = Field(..., description="HTTP 方法")
    tag: str | None = Field(None, description="接口标签")
    description: str | None = Field(None, description="接口描述")
    request_params: list | None = Field(None, description="请求参数")
    request_headers: list | None = Field(None, description="请求头")
    request_body: dict | None = Field(None, description="请求体 Schema")
    response_example: dict | None = Field(None, description="响应示例")


class ApiEndpointUpdate(BaseModel):
    """更新 API 端点请求体"""
    name: str | None = Field(None, min_length=1, max_length=200, description="接口名称")
    path: str | None = Field(None, min_length=1, max_length=500, description="接口路径")
    method: str | None = Field(None, description="HTTP 方法")
    tag: str | None = Field(None, description="接口标签")
    description: str | None = Field(None, description="接口描述")
    request_params: list | None = Field(None, description="请求参数")
    request_headers: list | None = Field(None, description="请求头")
    request_body: dict | None = Field(None, description="请求体 Schema")
    response_example: dict | None = Field(None, description="响应示例")
    status: str | None = Field(None, description="状态")


class ApiEndpointResponse(BaseModel):
    """API 端点响应体"""
    id: int
    project_id: int
    name: str
    path: str
    method: str
    tag: str | None = None
    description: str | None = None
    request_params: list | None = None
    request_headers: list | None = None
    request_body: dict | None = None
    response_example: dict | None = None
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiEndpointSummary(BaseModel):
    """API 端点概要"""
    id: int
    project_id: int
    name: str
    path: str
    method: str
    tag: str | None = None
    status: str = "active"

    model_config = {"from_attributes": True}
