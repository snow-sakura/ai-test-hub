"""知识库模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class KnowledgeBase(BaseModel, TimestampMixin):
    """知识库"""
    __tablename__ = "knowledge_base"

    name = Column(String(255), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="描述")
    status = Column(String(20), default="active", comment="状态（active/disabled）")
    embedding_model = Column(String(100), default="", comment="嵌入模型")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")

    creator = relationship("User", foreign_keys=[created_by])
    documents = relationship(
        "KBDocument", back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )