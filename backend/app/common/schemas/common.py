"""
通用响应模型模块

定义项目中复用的 Pydantic 响应模型，保持 API 返回格式统一。
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """通用 API 响应模型"""

    code: int = 0               # 业务状态码，0 表示成功
    message: str = "success"    # 提示信息
    data: T | None = None       # 响应数据


class PaginationMeta(BaseModel):
    """分页元信息"""

    page: int = 1               # 当前页码
    page_size: int = 20         # 每页条数
    total: int = 0              # 总记录数
    total_pages: int = 0        # 总页数


class PaginatedResponse(ResponseModel):
    """分页响应模型"""

    data: list[Any] = []
    pagination: PaginationMeta
