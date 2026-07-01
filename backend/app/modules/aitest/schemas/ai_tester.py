"""
AI 评测师会话/消息/评分 Pydantic 模型

定义 AI 评测师功能的请求/响应模型，包含会话管理、消息发送、评分等。
"""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ======================================================================
# 会话管理
# ======================================================================


class AITesterSessionCreate(BaseModel):
    """创建 AI 评测师会话请求"""
    name: str = "新会话"
    model: str = ""


class AITesterSessionUpdate(BaseModel):
    """更新 AI 评测师会话请求（重命名）"""
    name: str = Field(..., min_length=1, max_length=200)


class AITesterSessionResponse(BaseModel):
    """AI 评测师会话响应"""
    id: int
    name: str
    model: str
    message_count: int
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    first_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BatchDeleteSessionsRequest(BaseModel):
    """批量删除会话请求"""
    ids: list[int]


# ======================================================================
# 消息
# ======================================================================


class AITesterMessageBody(BaseModel):
    """发送消息请求体"""
    content: str = Field(..., min_length=1, max_length=10000)
    model: str = Field("", description="使用的模型，空则使用会话的模型")


class AITesterMessageResponse(BaseModel):
    """AI 评测师消息响应"""
    id: int
    session_id: int
    role: str
    content: str
    rating: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AITesterMessageRatingUpdate(BaseModel):
    """消息评分更新请求"""
    rating: str | None = Field(None, description="评分: up/down/null 清除")
