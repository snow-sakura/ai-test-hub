"""API 测试套件模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class ApiTestSuite(BaseModel, TimestampMixin):
    """API 测试套件"""
    __tablename__ = "api_test_suite"

    project_id = Column(
        Integer, ForeignKey("api_project.id"), nullable=False, comment="所属项目 ID",
    )
    name = Column(String(200), nullable=False, comment="套件名称")
    description = Column(Text, nullable=True, comment="套件描述")
    endpoints_config = Column(JSON, nullable=True, comment="接口顺序和配置（JSON）")
    assertions = Column(JSON, nullable=True, comment="断言规则（JSON）")
    status = Column(
        String(20), default="draft",
        comment="状态（draft/ready/running/completed/failed）",
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者 ID")

    # 关系
    project = relationship("ApiProject", back_populates="test_suites")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<ApiTestSuite(id={self.id}, name='{self.name}', status='{self.status}')>"
