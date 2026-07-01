"""API 端点模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.common.models.base import BaseModel, TimestampMixin


class ApiEndpoint(BaseModel, TimestampMixin):
    """API 端点（接口）"""
    __tablename__ = "api_endpoint"

    project_id = Column(
        Integer, ForeignKey("api_project.id"), nullable=False, comment="所属项目 ID",
    )
    name = Column(String(200), nullable=False, comment="接口名称")
    path = Column(String(500), nullable=False, comment="接口路径")
    method = Column(String(10), nullable=False, comment="HTTP 方法（GET/POST/PUT/DELETE/PATCH）")
    tag = Column(String(100), nullable=True, comment="接口标签/分类")
    description = Column(Text, nullable=True, comment="接口描述")
    request_params = Column(JSON, nullable=True, comment="请求参数（JSON）")
    request_headers = Column(JSON, nullable=True, comment="请求头（JSON）")
    request_body = Column(JSON, nullable=True, comment="请求体 Schema（JSON）")
    response_example = Column(JSON, nullable=True, comment="响应示例（JSON）")
    status = Column(String(20), default="active", comment="状态（active/disabled）")

    # 关系
    project = relationship("ApiProject", back_populates="endpoints")

    def __repr__(self) -> str:
        return f"<ApiEndpoint(id={self.id}, name='{self.name}', method='{self.method}', path='{self.path}')>"
