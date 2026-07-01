"""
测试版本管理服务

提供测试版本的业务查询逻辑。
"""

from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.schemas.common import PaginationMeta
from app.modules.aitest.models.project import TestProject
from app.modules.aitest.models.version import TestVersion


async def get_version(db: AsyncSession, version_id: int) -> TestVersion | None:
    """获取版本详情"""
    result = await db.execute(
        select(TestVersion).where(TestVersion.id == version_id),
    )
    return result.scalar_one_or_none()


async def list_versions(
    db: AsyncSession,
    project_id: int | None = None,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[TestVersion], PaginationMeta]:
    """获取版本列表（支持按项目和状态过滤，分页返回）"""
    # 先计算总数
    count_stmt = select(func.count(TestVersion.id))
    if project_id is not None:
        count_stmt = count_stmt.where(TestVersion.project_id == project_id)
    if search:
        count_stmt = count_stmt.where(TestVersion.name.ilike(f"%{search}%"))
    if status:
        count_stmt = count_stmt.where(TestVersion.status == status)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    total_pages = ceil(total / page_size) if page_size > 0 else 0
    offset = (page - 1) * page_size

    # 主查询，预加载项目名称
    stmt = (
        select(TestVersion)
        .options(joinedload(TestVersion.project))
        .order_by(TestVersion.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if project_id is not None:
        stmt = stmt.where(TestVersion.project_id == project_id)
    if search:
        stmt = stmt.where(TestVersion.name.ilike(f"%{search}%"))
    if status:
        stmt = stmt.where(TestVersion.status == status)

    result = await db.execute(stmt)
    versions = list(result.unique().scalars().all())

    # 填充 project_name
    for v in versions:
        if v.project:
            v.project_name = v.project.name

    pagination = PaginationMeta(
        page=page, page_size=page_size,
        total=total, total_pages=total_pages,
    )
    return versions, pagination
