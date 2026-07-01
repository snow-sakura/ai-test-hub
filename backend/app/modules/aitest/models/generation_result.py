"""AI 生成阶段结果模型 — 记录 LangGraph pipeline 各阶段中间结果"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.common.models.base import BaseModel, TimestampMixin


class AIGenerationResult(BaseModel, TimestampMixin):
    """AI 生成阶段结果"""
    __tablename__ = 'ai_generation_result'

    task_id = Column(
        Integer, ForeignKey('ai_generation_task.id'), nullable=False,
        comment='关联任务ID',
    )
    stage = Column(
        String(20), nullable=False,
        comment='阶段标识（analyze/write/review/revise/final）',
    )
    content = Column(Text, nullable=True, comment='阶段输出内容')
    metadata_json = Column(Text, nullable=True, comment='额外元数据（如评分JSON）')

    def __repr__(self) -> str:
        return f"<AIGenerationResult(id={self.id}, task_id={self.task_id}, stage='{self.stage}')>"
