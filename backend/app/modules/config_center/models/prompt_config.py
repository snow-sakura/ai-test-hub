"""提示词配置模型"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class PromptConfig(BaseModel, TimestampMixin):
    """提示词配置"""
    __tablename__ = 'prompt_config'

    name = Column(String(100), nullable=False, comment='配置名称')
    prompt_type = Column(
        String(20), nullable=False,
        comment='提示词类型（writer/reviewer）',
    )
    content = Column(Text, nullable=False, comment='提示词内容')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(
        Integer, ForeignKey('users.id'), nullable=False, comment='创建者ID',
    )

    # 关系
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<PromptConfig(id={self.id}, name='{self.name}')>"
