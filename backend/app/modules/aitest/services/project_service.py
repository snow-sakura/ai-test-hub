"""
测试项目管理服务

提供项目查询（含成员/版本计数）、成员管理、权限校验等业务逻辑。
"""

from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.common.schemas.common import PaginationMeta
from app.modules.aitest.models.project import ProjectMember, TestProject
from app.modules.aitest.models.test_case import TestCase
from app.modules.aitest.models.version import TestVersion


def _count_subqueries():
    """构建成员数、版本数、用例数的标量子查询"""
    member_count_sub = (
        select(func.count(ProjectMember.id))
        .where(ProjectMember.project_id == TestProject.id)
        .correlate(TestProject)
        .scalar_subquery()
    )
    version_count_sub = (
        select(func.count(TestVersion.id))
        .where(TestVersion.project_id == TestProject.id)
        .correlate(TestProject)
        .scalar_subquery()
    )
    case_count_sub = (
        select(func.count(TestCase.id))
        .where(TestCase.project_id == TestProject.id)
        .correlate(TestProject)
        .scalar_subquery()
    )
    return member_count_sub, version_count_sub, case_count_sub


async def get_project_with_counts(
    db: AsyncSession, project_id: int,
) -> TestProject | None:
    """获取项目详情（含成员数、版本数、用例数）"""
    member_count_sub, version_count_sub, case_count_sub = _count_subqueries()
    stmt = (
        select(
            TestProject,
            member_count_sub.label("member_count"),
            version_count_sub.label("version_count"),
            case_count_sub.label("case_count"),
        )
        .where(TestProject.id == project_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    if row is None:
        return None
    project, member_count, version_count, case_count = row
    project.member_count = member_count
    project.version_count = version_count
    project.case_count = case_count
    return project


async def list_projects_with_counts(
    db: AsyncSession,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[TestProject], PaginationMeta]:
    """获取项目列表（含成员数和版本数聚合，分页返回）"""
    # 先计算总数
    count_stmt = select(func.count(TestProject.id))
    if search:
        count_stmt = count_stmt.where(
            TestProject.name.ilike(f"%{search}%") |
            TestProject.leader.ilike(f"%{search}%")
        )
    if status:
        count_stmt = count_stmt.where(TestProject.status == status)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    total_pages = ceil(total / page_size) if page_size > 0 else 0
    offset = (page - 1) * page_size

    member_count_sub, version_count_sub, case_count_sub = _count_subqueries()
    stmt = (
        select(
            TestProject,
            member_count_sub.label("member_count"),
            version_count_sub.label("version_count"),
            case_count_sub.label("case_count"),
        )
        .order_by(TestProject.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if search:
        stmt = stmt.where(
            TestProject.name.ilike(f"%{search}%") |
            TestProject.leader.ilike(f"%{search}%")
        )
    if status:
        stmt = stmt.where(TestProject.status == status)

    result = await db.execute(stmt)
    rows = result.all()
    projects = []
    for row in rows:
        project, member_count, version_count, case_count = row
        project.member_count = member_count
        project.version_count = version_count
        project.case_count = case_count
        projects.append(project)

    pagination = PaginationMeta(
        page=page, page_size=page_size,
        total=total, total_pages=total_pages,
    )
    return projects, pagination


async def get_project_stats(
    db: AsyncSession,
) -> dict[str, int]:
    """获取项目全量统计数据（各状态计数）"""
    total_result = await db.execute(select(func.count(TestProject.id)))
    total = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(TestProject.id)).where(TestProject.status == "active")
    )
    active = active_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(TestProject.id)).where(TestProject.status == "completed")
    )
    completed = completed_result.scalar() or 0

    archived_result = await db.execute(
        select(func.count(TestProject.id)).where(TestProject.status == "archived")
    )
    archived = archived_result.scalar() or 0

    return {"total": total, "active": active, "completed": completed, "archived": archived}


async def get_members_with_user(db: AsyncSession, project_id: int) -> list[ProjectMember]:
    """获取项目成员列表（关联 User 表）"""
    stmt = (
        select(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
