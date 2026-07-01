"""操作日志模型（记录实体变更历史）"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.common.models.base import Base


class OperationLog(Base):
    """操作日志（AI 测试模块实体变更记录）"""
    __tablename__ = "ai_operation_log"
    __table_args__ = {"comment": "AI 测试模块操作日志表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(20), nullable=False, comment="实体类型（case/project/review/task）")
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    action = Column(String(100), nullable=False, comment="操作描述")
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作者ID")
    detail = Column(JSON, nullable=True, comment="操作详情")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")

    # 关系
    operator = relationship("User", foreign_keys=[operator_id])
