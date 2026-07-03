"""AI 聊天室会话模型"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class ChatSession(BaseModel, TimestampMixin):
    """AI 聊天室会话"""
    __tablename__ = "ai_chat_session"

    name = Column(String(255), default="新会话", comment="会话名称")
    model = Column(String(100), default="", comment="使用的模型")
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_base.id"), nullable=True, comment="关联知识库ID")
    message_count = Column(Integer, default=0, comment="消息数")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")

    creator = relationship("User", foreign_keys=[created_by])
    knowledge_base = relationship("KnowledgeBase", foreign_keys=[knowledge_base_id])
    messages = relationship(
        "ChatMessage", back_populates="session",
        cascade="all, delete-orphan", order_by="ChatMessage.id",
    )