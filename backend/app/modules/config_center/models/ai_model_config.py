"""AI 模型配置模型"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class AIModelConfig(BaseModel, TimestampMixin):
    """AI 模型配置"""
    __tablename__ = 'ai_model_config'

    name = Column(String(100), nullable=False, comment='配置名称')
    model_type = Column(
        String(20), nullable=False,
        comment='模型类型（deepseek/qwen/siliconflow/openai/anthropic/other）',
    )
    role = Column(
        String(20), nullable=False,
        comment='角色（writer/reviewer/browser_use_text）',
    )
    api_key = Column(String(500), nullable=True, comment='API Key')
    base_url = Column(String(500), nullable=False, comment='API Base URL')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    max_tokens = Column(Integer, default=4096, comment='最大Token数')
    temperature = Column(Float, default=0.7, comment='温度参数')
    top_p = Column(Float, default=0.9, comment='Top P参数')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(
        Integer, ForeignKey('users.id'), nullable=False, comment='创建者ID',
    )

    # 关系
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<AIModelConfig(id={self.id}, name='{self.name}')>"
