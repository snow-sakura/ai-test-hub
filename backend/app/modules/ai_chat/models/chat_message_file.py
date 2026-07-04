"""AI 聊天室消息文件模型"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class ChatMessageFile(BaseModel, TimestampMixin):
    """AI 聊天室消息附件文件"""
    __tablename__ = "ai_chat_message_file"

    message_id = Column(Integer, ForeignKey("ai_chat_message.id"), nullable=True, comment="消息ID（先上传后关联）")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(Integer, nullable=False, comment="文件大小")
    file_type = Column(String(50), nullable=False, comment="文件类型")
    is_image = Column(Boolean, default=False, comment="是否图片")

    message = relationship("ChatMessage", back_populates="files")