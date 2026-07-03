"""知识库文档模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class KBDocument(BaseModel, TimestampMixin):
    """知识库文档"""
    __tablename__ = "kb_document"

    knowledge_base_id = Column(Integer, ForeignKey("knowledge_base.id"), nullable=False, comment="知识库ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_size = Column(Integer, nullable=False, comment="文件大小")
    status = Column(String(20), default="pending", comment="状态（pending/processing/completed/failed）")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    error_message = Column(Text, nullable=True, comment="错误信息")

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")