"""
系统管理模型模块

定义操作日志等系统管理相关 ORM 模型。
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class OperationLog(BaseModel, TimestampMixin):
    """操作日志模型"""

    __tablename__ = "operation_log"  # 显式指定表名

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="操作用户ID")
    username = Column(String(50), nullable=False, comment="用户名")
    action = Column(String(50), nullable=False, comment="操作类型(create/update/delete/login/logout)")
    module = Column(String(50), nullable=False, comment="操作模块")
    target_type = Column(String(50), nullable=True, comment="操作对象类型")
    target_id = Column(Integer, nullable=True, comment="操作对象ID")
    detail = Column(Text, nullable=True, comment="操作详情")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    status = Column(String(20), default="success", comment="操作状态(success/failure)")

    # 关联用户
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return (
            f"<OperationLog(id={self.id}, user='{self.username}', "
            f"action='{self.action}', module='{self.module}')>"
        )
