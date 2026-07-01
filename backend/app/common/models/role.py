"""
角色与权限模型模块

定义角色模型、用户-角色关联表。
"""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.common.models.base import Base, BaseModel, TimestampMixin


class Role(BaseModel, TimestampMixin):
    """角色模型"""

    __tablename__ = "role"  # 显式指定表名

    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    code = Column(String(50), unique=True, nullable=False, comment="角色编码")
    description = Column(String(200), nullable=True, comment="角色描述")
    permissions = Column(JSON, nullable=True, comment="权限列表")
    is_system = Column(Boolean, default=False, comment="是否系统内置")

    # 多对多关系：Role ↔ User
    users = relationship("User", secondary="user_role", back_populates="roles")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}', code='{self.code}')>"


class UserRole(Base):
    """用户角色关联表"""

    __tablename__ = "user_role"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, comment="用户ID")
    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True, comment="角色ID")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
