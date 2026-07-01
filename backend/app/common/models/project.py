"""
项目模型

定义项目 ORM 模型，用于 AI 测试项目管理和下拉选择。
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class Project(BaseModel, TimestampMixin):
    """项目模型"""
    __tablename__ = 'project'

    name = Column(String(100), nullable=False, comment='项目名称')
    description = Column(Text, nullable=True, comment='项目描述')
    created_by = Column(
        Integer, ForeignKey('users.id'), nullable=False, comment='创建者ID',
    )

    # 关系
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"
