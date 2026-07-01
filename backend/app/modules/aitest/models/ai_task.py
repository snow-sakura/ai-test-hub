"""AI 生成任务模型"""

import sqlalchemy
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class AIGenerationTask(BaseModel, TimestampMixin):
    """AI 生成任务"""
    __tablename__ = 'ai_generation_task'

    task_id = Column(String(50), unique=True, nullable=False, comment='任务ID')
    title = Column(String(200), nullable=False, comment='任务标题')
    requirement_text = Column(Text, nullable=False, comment='需求描述')
    status = Column(
        String(20), default='pending',
        comment='状态（pending/generating/reviewing/revising/completed/failed/cancelled）',
    )
    progress = Column(Integer, default=0, comment='进度百分比')
    pipeline_type = Column(
        String(20), default='traditional',
        comment='管线类型（traditional/langgraph/autogen）',
    )
    output_mode = Column(
        String(10), default='stream',
        comment='输出模式（stream/complete）',
    )
    enable_auto_review = Column(
        sqlalchemy.Boolean, default=True,
        comment='是否启用自动评审',
    )

    # 外键
    project_id = Column(
        Integer, ForeignKey('project.id'), nullable=True, comment='关联项目ID',
    )
    writer_model_config_id = Column(
        Integer, ForeignKey('ai_model_config.id'), nullable=True,
        comment='编写模型配置ID',
    )
    reviewer_model_config_id = Column(
        Integer, ForeignKey('ai_model_config.id'), nullable=True,
        comment='评审模型配置ID',
    )
    writer_prompt_config_id = Column(
        Integer, ForeignKey('prompt_config.id'), nullable=True,
        comment='编写提示词配置ID',
    )
    reviewer_prompt_config_id = Column(
        Integer, ForeignKey('prompt_config.id'), nullable=True,
        comment='评审提示词配置ID',
    )
    analyzer_prompt_config_id = Column(
        Integer, ForeignKey('prompt_config.id'), nullable=True,
        comment='需求分析提示词配置ID',
    )
    improver_prompt_config_id = Column(
        Integer, ForeignKey('prompt_config.id'), nullable=True,
        comment='用例改进提示词配置ID',
    )
    created_by = Column(
        Integer, ForeignKey('users.id'), nullable=False, comment='创建者ID',
    )

    # 结果（存储为 JSON）
    generated_content = Column(
        JSON, nullable=True, comment='生成的测试用例（JSON格式）',
    )
    review_feedback = Column(Text, nullable=True, comment='评审反馈')
    final_content = Column(
        JSON, nullable=True, comment='最终结果（JSON格式）',
    )

    # 元数据
    generation_log = Column(Text, nullable=True, comment='生成日志')
    error_message = Column(Text, nullable=True, comment='错误信息')
    saved_to_library = Column(
        sqlalchemy.Boolean, default=False,
        comment='是否已保存到用例库',
    )
    completed_at = Column(DateTime, nullable=True, comment='完成时间')

    # 关系
    writer_model_config = relationship(
        "AIModelConfig", foreign_keys=[writer_model_config_id],
    )
    reviewer_model_config = relationship(
        "AIModelConfig", foreign_keys=[reviewer_model_config_id],
    )
    writer_prompt_config = relationship(
        "PromptConfig", foreign_keys=[writer_prompt_config_id],
    )
    reviewer_prompt_config = relationship(
        "PromptConfig", foreign_keys=[reviewer_prompt_config_id],
    )
    analyzer_prompt_config = relationship(
        "PromptConfig", foreign_keys=[analyzer_prompt_config_id],
    )
    improver_prompt_config = relationship(
        "PromptConfig", foreign_keys=[improver_prompt_config_id],
    )
    creator = relationship("User", foreign_keys=[created_by])
    generated_test_cases = relationship(
        "GeneratedTestCase", back_populates="task",
        cascade="all, delete-orphan",
    )
    generated_case_items = relationship(
        "GeneratedCaseItem", back_populates="task",
        cascade="all, delete-orphan", order_by="GeneratedCaseItem.sort_order",
    )

    def __repr__(self) -> str:
        return f"<AIGenerationTask(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"


class GeneratedTestCase(BaseModel, TimestampMixin):
    """生成的测试用例"""
    __tablename__ = 'generated_test_case'

    task_id = Column(
        Integer, ForeignKey('ai_generation_task.id'), nullable=False,
        comment='关联任务ID',
    )
    case_id = Column(String(50), nullable=False, comment='用例编号')
    title = Column(String(300), nullable=False, comment='用例标题')
    module = Column(String(100), nullable=True, comment='所属模块')
    priority = Column(
        String(5), default='P2',
        comment='优先级（P0/P1/P2/P3）',
    )
    precondition = Column(Text, nullable=True, comment='前置条件')
    test_steps = Column(Text, nullable=True, comment='测试步骤')
    expected_result = Column(Text, nullable=True, comment='预期结果')
    status = Column(
        String(20), default='generated',
        comment='状态（generated/reviewing/reviewed/approved/rejected/adopted）',
    )

    # 关系
    task = relationship("AIGenerationTask", back_populates="generated_test_cases")

    def __repr__(self) -> str:
        return f"<GeneratedTestCase(id={self.id}, case_id='{self.case_id}')>"
