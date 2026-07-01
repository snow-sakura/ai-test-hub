"""
API 环境模型模块

定义 API 接口测试的环境配置模型，存储环境名称、基础 URL、变量和请求头。
"""

from sqlalchemy import Column, Integer, String, JSON

from app.common.models.base import BaseModel, TimestampMixin


class ApiEnvironment(BaseModel, TimestampMixin):
    """API 测试环境配置"""

    __tablename__ = "api_environment"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="环境名称")
    base_url = Column(String(500), nullable=False, comment="基础URL")
    variables = Column(JSON, nullable=True, comment="环境变量（键值对）")
    headers = Column(JSON, nullable=True, comment="请求头（键值对）")
    status = Column(String(20), default="active", comment="状态（active/inactive）")
