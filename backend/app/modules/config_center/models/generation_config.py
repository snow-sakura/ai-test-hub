"""生成行为配置模型"""

from sqlalchemy import Boolean, Column, Integer, String

from app.common.models.base import BaseModel, TimestampMixin


class GenerationConfig(BaseModel, TimestampMixin):
    """生成行为配置"""
    __tablename__ = 'generation_config'

    name = Column(
        String(100), default='默认生成配置', comment='配置名称',
    )
    default_output_mode = Column(
        String(10), default='stream',
        comment='默认输出模式（stream/complete）',
    )
    enable_auto_review = Column(
        Boolean, default=True, comment='启用AI评审和改进',
    )
    review_timeout = Column(
        Integer, default=120, comment='评审和改进超时时间（秒）',
    )
    is_active = Column(Boolean, default=True, comment='是否启用')

    def __repr__(self) -> str:
        return f"<GenerationConfig(id={self.id}, name='{self.name}')>"
