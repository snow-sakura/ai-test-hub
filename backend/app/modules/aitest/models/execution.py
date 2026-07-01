"""
测试用例执行记录 ORM 模型

记录每次用例执行的结果（pass/fail/blocked/skip）。
仅 active 状态的用例允许执行。
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class TestCaseExecution(BaseModel, TimestampMixin):
    """测试用例执行记录"""
    __tablename__ = "test_case_execution"

    case_id = Column(
        Integer, ForeignKey("test_case.id"), nullable=False, comment="关联用例ID",
    )
    status = Column(
        String(20), default="pass",
        comment="执行结果（pass/fail/blocked/skip）",
    )
    actual_result = Column(Text, nullable=True, comment="实际结果描述")
    executed_by = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="执行人ID",
    )

    # 关系
    case = relationship("TestCase", back_populates="executions")
    executor = relationship("User", foreign_keys=[executed_by])

    def __repr__(self) -> str:
        return f"<TestCaseExecution(id={self.id}, case_id={self.case_id}, status='{self.status}')>"
