"""AI 评测师消息模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class AITesterMessage(BaseModel, TimestampMixin):
    """AI 评测师消息"""
    __tablename__ = "ai_tester_message"

    session_id = Column(Integer, ForeignKey("ai_tester_session.id"), nullable=False, comment="会话ID")
    role = Column(String(10), nullable=False, comment="角色（user/assistant）")
    content = Column(Text, nullable=False, comment="消息内容")
    rating = Column(String(10), nullable=True, comment="评分（up/down/null）")

    # 关系
    session = relationship("AITesterSession", back_populates="messages")
