"""AI 生成候选用例模型（用于采纳/丢弃/保存到用例库）"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class GeneratedCaseItem(BaseModel, TimestampMixin):
    """AI 生成候选用例"""
    __tablename__ = "generated_case_item"

    task_id = Column(Integer, ForeignKey("ai_generation_task.id"), nullable=False, comment="生成任务ID")
    title = Column(String(300), nullable=False, comment="用例标题")
    priority = Column(String(5), default="P2", comment="优先级（P0/P1/P2/P3）")
    module = Column(String(100), nullable=True, comment="所属模块")
    precondition = Column(Text, nullable=True, comment="前置条件")
    test_steps = Column(Text, nullable=True, comment="测试步骤")
    expected_result = Column(Text, nullable=True, comment="预期结果")
    tags = Column(String(500), nullable=True, comment="标签（逗号分隔）")
    status = Column(
        String(20), default="pending",
        comment="状态（pending=待定/adopted=已采纳/discarded=已丢弃）",
    )
    sort_order = Column(Integer, default=0, comment="排序号")

    # 关系
    task = relationship("AIGenerationTask", back_populates="generated_case_items")
