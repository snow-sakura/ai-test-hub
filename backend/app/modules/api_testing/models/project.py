"""API 项目管理模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class ApiProject(BaseModel, TimestampMixin):
    """API 项目"""
    __tablename__ = "api_project"

    name = Column(String(100), nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    base_url = Column(String(500), nullable=True, comment="基础 URL")
    swagger_url = Column(String(500), nullable=True, comment="Swagger URL")
    version = Column(String(50), nullable=True, comment="API 版本")
    status = Column(String(20), default="active", comment="状态（active/archived）")

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者 ID")

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    endpoints = relationship(
        "ApiEndpoint", back_populates="project",
        cascade="all, delete-orphan",
    )
    test_suites = relationship(
        "ApiTestSuite", back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ApiProject(id={self.id}, name='{self.name}')>"
