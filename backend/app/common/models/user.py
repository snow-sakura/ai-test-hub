"""
用户模型模块

定义用户 ORM 模型，使用 bcrypt 密码哈希存储。
"""

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class User(BaseModel, TimestampMixin):
    """用户模型"""

    __tablename__ = "users"  # 显式指定表名

    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(200), nullable=False, comment="密码哈希")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar = Column(String(200), nullable=True, comment="头像URL")
    department = Column(String(100), nullable=True, comment="部门")
    position = Column(String(100), nullable=True, comment="职位")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")

    # 多对多关系：User ↔ Role
    roles = relationship("Role", secondary="user_role", back_populates="users")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
