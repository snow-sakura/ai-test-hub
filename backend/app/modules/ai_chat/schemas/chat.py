"""AI 聊天室请求/响应模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ChatSessionCreate(BaseModel):
    """创建 AI 聊天室会话请求"""
    name: str = "新会话"
    model: str = ""
    knowledge_base_id: int | None = None


class ChatSessionUpdate(BaseModel):
    """更新 AI 聊天室会话请求"""
    name: str = Field(..., min_length=1, max_length=200)
    model: str | None = None
    knowledge_base_id: int | None = None


class ChatSessionResponse(BaseModel):
    """AI 聊天室会话响应"""
    id: int
    name: str
    model: str
    knowledge_base_id: int | None = None
    knowledge_base_name: str | None = None
    message_count: int
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    first_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageBody(BaseModel):
    """发送消息请求体"""
    content: str = Field(..., min_length=1, max_length=10000)
    model: str = Field("", description="使用的模型，空则使用会话的模型")
    file_ids: list[int] = Field([], description="上传的文件ID列表")
    knowledge_base_id: int | None = None


class ChatMessageFileResponse(BaseModel):
    """消息文件响应"""
    id: int
    file_name: str
    file_size: int
    file_type: str
    is_image: bool

    model_config = ConfigDict(from_attributes=True)


class ChatMessageResponse(BaseModel):
    """AI 聊天室消息响应"""
    id: int
    session_id: int
    role: str
    content: str
    rating: str | None = None
    created_at: datetime | None = None
    files: list[ChatMessageFileResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRatingUpdate(BaseModel):
    """消息评分更新请求"""
    rating: str | None = Field(None, description="评分: up/down/null 清除")