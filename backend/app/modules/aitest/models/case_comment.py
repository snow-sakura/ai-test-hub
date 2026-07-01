"""用例评论模型"""

from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class CaseComment(BaseModel, TimestampMixin):
    """用例评论"""
    __tablename__ = "case_comment"

    case_id = Column(Integer, ForeignKey("test_case.id"), nullable=False, comment="关联用例ID")
    content = Column(Text, nullable=False, comment="评论内容")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="作者ID")

    # 关系
    author = relationship("User", foreign_keys=[author_id])
    case = relationship("TestCase", back_populates="comments")
