"""
用例评审 ORM 模型

定义 TestReview（用例评审）和 ReviewAssignment（评审分配）两个模型。
对应原型：用例评审.html
参考：testhub 的 ReviewAssignment 模式
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class TestReview(BaseModel, TimestampMixin):
    """用例评审"""
    __tablename__ = "test_review"

    project_id = Column(
        Integer, ForeignKey("test_project.id"), nullable=False, comment="关联项目ID",
    )
    name = Column(String(200), nullable=False, comment="评审名称")
    status = Column(
        String(20), default="pending",
        comment="状态（pending=待评审/passed=通过/rejected=驳回）",
    )
    cases = Column(JSON, nullable=True, comment="用例列表（JSON格式）")
    conclusion = Column(Text, nullable=True, comment="评审结论")
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID",
    )

    # 关系
    project = relationship("TestProject", back_populates="reviews")
    creator = relationship("User", foreign_keys=[created_by])
    assignments = relationship(
        "ReviewAssignment", back_populates="review",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TestReview(id={self.id}, name='{self.name}', status='{self.status}')>"


class ReviewAssignment(BaseModel, TimestampMixin):
    """评审分配（记录每个评审人的状态和意见）"""
    __tablename__ = "review_assignment"

    review_id = Column(
        Integer, ForeignKey("test_review.id"), nullable=False, comment="评审ID",
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="评审人ID",
    )
    status = Column(
        String(20), default="pending",
        comment="状态（pending=待评审/approved=通过/rejected=驳回）",
    )
    comment = Column(Text, nullable=True, comment="评审意见")

    # 关系
    review = relationship("TestReview", back_populates="assignments")
    reviewer = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<ReviewAssignment(id={self.id}, review_id={self.review_id}, user_id={self.user_id})>"
