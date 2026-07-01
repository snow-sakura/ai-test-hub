"""
测试版本 ORM 模型

定义 TestVersion（测试版本）模型，关联测试项目。
对应原型：版本管理.html
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class TestVersion(BaseModel, TimestampMixin):
    """测试版本"""
    __tablename__ = "test_version"

    project_id = Column(
        Integer, ForeignKey("test_project.id"), nullable=False, comment="关联项目ID",
    )
    name = Column(String(100), nullable=False, comment="版本号/版本名称")
    description = Column(Text, nullable=True, comment="版本描述")
    changelog = Column(Text, nullable=True, comment="变更内容")
    status = Column(
        String(20), default="in_progress",
        comment="状态（released=已发布/in_progress=进行中/obsolete=已废弃）",
    )
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID",
    )

    # 关系
    project = relationship("TestProject", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])
    test_cases = relationship("TestCase", back_populates="version", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TestVersion(id={self.id}, name='{self.name}', status='{self.status}')>"
