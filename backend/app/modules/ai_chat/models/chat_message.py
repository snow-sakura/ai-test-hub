"""AI 聊天室消息模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class ChatMessage(BaseModel, TimestampMixin):
    """AI 聊天室消息"""
    __tablename__ = "ai_chat_message"

    session_id = Column(Integer, ForeignKey("ai_chat_session.id"), nullable=False, comment="会话ID")
    role = Column(String(10), nullable=False, comment="角色（user/assistant/system）")
    content = Column(Text, nullable=False, comment="消息内容")
    rating = Column(String(10), nullable=True, comment="评分（up/down）")

    session = relationship("ChatSession", back_populates="messages")
    files = relationship(
        "ChatMessageFile", back_populates="message",
        cascade="all, delete-orphan",
    )