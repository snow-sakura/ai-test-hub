"""
API 定时任务模型模块

定义 API 接口测试的定时调度任务模型，支持 Cron 表达式和通知配置。
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey

from app.common.models.base import BaseModel, TimestampMixin


class ApiSchedule(BaseModel, TimestampMixin):
    """API 测试定时任务"""

    __tablename__ = "api_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(200), nullable=False, comment="任务名称")
    suite_id = Column(Integer, ForeignKey("api_test_suite.id"), nullable=False, comment="关联测试套件ID")
    environment_id = Column(Integer, ForeignKey("api_environment.id"), nullable=True, comment="关联环境ID")
    cron_expression = Column(String(100), nullable=False, comment="Cron表达式")
    status = Column(String(20), default="running", comment="状态（running/paused/stopped）")
    notify = Column(JSON, nullable=True, comment="通知配置（{email, webhook, on_failure_only}）")
    last_run_at = Column(DateTime, nullable=True, comment="上次执行时间")
    next_run_at = Column(DateTime, nullable=True, comment="下次执行时间")
