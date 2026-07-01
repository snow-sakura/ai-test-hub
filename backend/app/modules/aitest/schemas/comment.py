"""
用例评论 Pydantic 模型

定义 CaseComment 相关的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    """创建评论请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="评论内容")


class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="评论内容")


class CommentResponse(BaseModel):
    """评论响应"""
    id: int
    case_id: int
    content: str
    author_id: int
    author_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
