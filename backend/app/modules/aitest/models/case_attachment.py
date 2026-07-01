"""用例附件模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class CaseAttachment(BaseModel, TimestampMixin):
    """用例附件"""
    __tablename__ = "case_attachment"

    case_id = Column(Integer, ForeignKey("test_case.id"), nullable=False, comment="关联用例ID")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="存储路径")
    file_size = Column(Integer, default=0, comment="文件大小（字节）")
    file_type = Column(String(100), default="", comment="MIME类型")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="上传者ID")

    # 关系
    uploader = relationship("User", foreign_keys=[uploaded_by])
    case = relationship("TestCase", back_populates="attachments")
