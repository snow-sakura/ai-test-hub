"""
分页工具模块

提供通用的分页查询功能，简化分页接口的实现。
"""

from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.common.schemas.common import PaginationMeta


async def paginate(
    db: AsyncSession,
    query: Select,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list, PaginationMeta]:
    """
    通用分页查询

    Args:
        db: 异步数据库会话
        query: SQLAlchemy Select 语句
        page: 当前页码（从 1 开始）
        page_size: 每页记录数

    Returns:
        (结果列表, 分页元信息) 的元组

    Example:
        query = select(User).where(User.is_active == True)
        users, pagination = await paginate(db, query, page=1, page_size=10)
    """
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 计算总页数
    total_pages = ceil(total / page_size) if page_size > 0 else 0

    # 执行分页查询
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = list(result.scalars().all())

    # 构建分页元信息
    pagination = PaginationMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )

    return items, pagination
