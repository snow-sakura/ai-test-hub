"""
测试用例 ORM 模型

定义 TestCase（测试用例）模型，是跨模块共享的核心实体。
其他模块（AI智能测试、API接口测试、UI自动化、APP自动化）
通过此模型与测试管理关联。

参考：testhub 的 TestCase 模型
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class TestCase(BaseModel, TimestampMixin):
    """测试用例（跨模块共享）"""
    __tablename__ = "test_case"

    project_id = Column(
        Integer, ForeignKey("test_project.id"), nullable=True, comment="关联项目ID",
    )
    version_id = Column(
        Integer, ForeignKey("test_version.id"), nullable=True, comment="关联版本ID",
    )
    module = Column(String(100), nullable=True, comment="模块名称")
    name = Column(String(200), nullable=False, comment="用例标题")
    description = Column(Text, nullable=True, comment="用例描述")
    priority = Column(
        String(20), default="p2",
        comment="优先级（p0/p1/p2/p3）",
    )
    precondition = Column(Text, nullable=True, comment="前置条件")
    test_steps = Column(Text, nullable=True, comment="测试步骤")
    expected_result = Column(Text, nullable=True, comment="预期结果")
    status = Column(
        String(20), default="active",
        comment="状态（draft/active/deprecated）",
    )
    test_type = Column(
        String(20), default="functional",
        comment="测试类型（functional/api/ui/app）",
    )
    source = Column(
        String(20), default="manual",
        comment="来源（ai_generated/manual/imported）",
    )
    tags = Column(JSON, nullable=True, comment="标签列表")
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID",
    )

    # 关系
    project = relationship("TestProject", back_populates="test_cases")
    version = relationship("TestVersion", back_populates="test_cases")
    creator = relationship("User", foreign_keys=[created_by])
    attachments = relationship(
        "CaseAttachment", back_populates="case",
        cascade="all, delete-orphan", order_by="CaseAttachment.id",
    )
    comments = relationship(
        "CaseComment", back_populates="case",
        cascade="all, delete-orphan", order_by="CaseComment.id",
    )
    executions = relationship(
        "TestCaseExecution", back_populates="case",
        cascade="all, delete-orphan",
        order_by="TestCaseExecution.id.desc()",
    )

    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, name='{self.name}', priority='{self.priority}')>"
