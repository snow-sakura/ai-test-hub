"""
测试版本 Pydantic 模型

定义 TestVersion 相关的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TestVersionCreate(BaseModel):
    """创建测试版本请求"""
    project_id: int = Field(..., description="关联项目ID")
    name: str = Field(..., min_length=1, max_length=100, description="版本号")
    description: str | None = Field(None, description="版本描述")
    changelog: str | None = Field(None, description="变更内容")


class TestVersionUpdate(BaseModel):
    """更新测试版本请求"""
    name: str | None = Field(None, min_length=1, max_length=100, description="版本号")
    description: str | None = Field(None, description="版本描述")
    changelog: str | None = Field(None, description="变更内容")
    status: str | None = Field(
        None, description="版本状态（released/in_progress/obsolete）",
    )


class TestVersionResponse(BaseModel):
    """测试版本响应"""
    id: int
    project_id: int
    name: str
    description: str | None = None
    changelog: str | None = None
    status: str = "in_progress"
    project_name: str | None = None
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
