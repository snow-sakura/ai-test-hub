"""
测试项目 ORM 模型

定义 TestProject（测试项目）和 ProjectMember（项目成员）两个模型。
对应原型：项目管理.html、成员管理.html
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class TestProject(BaseModel, TimestampMixin):
    """测试项目"""
    __tablename__ = "test_project"

    name = Column(String(200), nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    leader = Column(String(50), nullable=True, comment="负责人")
    start_date = Column(Date, nullable=True, comment="开始日期")
    end_date = Column(Date, nullable=True, comment="结束日期")
    status = Column(
        String(20), default="active",
        comment="状态（active=进行中/completed=已完成/archived=已归档）",
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    versions = relationship("TestVersion", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("TestReview", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TestProject(id={self.id}, name='{self.name}', status='{self.status}')>"


class ProjectMember(BaseModel, TimestampMixin):
    """项目成员"""
    __tablename__ = "project_member"

    project_id = Column(
        Integer, ForeignKey("test_project.id"), nullable=False, comment="项目ID",
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID",
    )
    role = Column(
        String(20), default="tester",
        comment="角色（admin=管理员/tester=测试工程师/viewer=访客）",
    )

    # 关系
    project = relationship("TestProject", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<ProjectMember(id={self.id}, project_id={self.project_id}, user_id={self.user_id})>"
