"""
数据库模型基类模块

定义 ORM 模型的基础类和混入类，所有数据模型应继承自 BaseModel。
"""

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类，提供 created_at 和 updated_at 字段"""

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class BaseModel(Base):
    """
    ORM 模型基类

    所有业务数据模型都应继承此类，自动包含：
    - id: 自增主键
    - __tablename__: 根据类名自动生成（转为小写）
    - created_at / updated_at: 时间戳（通过 TimestampMixin）
    """

    __abstract__ = True  # 声明为抽象类，不创建对应的数据库表

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    @declared_attr
    def __tablename__(cls) -> str:
        """自动将类名转为小写作为表名"""
        return cls.__name__.lower()
