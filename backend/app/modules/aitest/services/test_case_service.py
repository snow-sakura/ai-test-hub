"""
测试用例服务（跨模块共享接口）

其他模块（AI智能测试、API接口测试、UI自动化、APP自动化）
通过此模块与测试管理关联，调用测试用例数据的增删改查。

使用方法:
    from app.modules.aitest.services.test_case_service import (
        create_test_case, batch_create_test_cases, get_test_case,
        list_test_cases, get_test_case_stats,
    )
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.aitest.models.test_case import TestCase
from app.modules.aitest.schemas.test_case import TestCaseCreate


async def create_test_case(db: AsyncSession, data: TestCaseCreate, created_by: int) -> TestCase:
    """创建单个测试用例"""
    values = data.model_dump(exclude_unset=True)
    values["created_by"] = created_by
    case = TestCase(**values)
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


async def batch_create_test_cases(
    db: AsyncSession, data_list: list[TestCaseCreate], created_by: int,
) -> list[TestCase]:
    """批量创建测试用例（AI生成后调用）"""
    cases = []
    for d in data_list:
        values = d.model_dump()
        values["created_by"] = created_by
        cases.append(TestCase(**values))
    db.add_all(cases)
    await db.flush()
    for c in cases:
        await db.refresh(c)
    return cases


async def get_test_case(db: AsyncSession, case_id: int) -> TestCase | None:
    """获取用例详情"""
    stmt = (
        select(TestCase)
        .options(joinedload(TestCase.project), joinedload(TestCase.version))
        .where(TestCase.id == case_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_test_cases(
    db: AsyncSession,
    project_id: int | None = None,
    version_id: int | None = None,
    test_type: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
) -> list[TestCase]:
    """获取用例列表（支持多维度过滤，供其他模块调用）"""
    stmt = select(TestCase).order_by(TestCase.id.desc())
    if project_id is not None:
        stmt = stmt.where(TestCase.project_id == project_id)
    if version_id is not None:
        stmt = stmt.where(TestCase.version_id == version_id)
    if test_type:
        stmt = stmt.where(TestCase.test_type == test_type)
    if status:
        stmt = stmt.where(TestCase.status == status)
    if priority:
        stmt = stmt.where(TestCase.priority == priority)
    if search:
        stmt = stmt.where(TestCase.name.ilike(f"%{search}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_test_case_stats(db: AsyncSession, project_id: int) -> dict:
    """获取项目测试用例统计（按类型/优先级/状态分组）"""
    total_result = await db.execute(
        select(func.count(TestCase.id)).where(TestCase.project_id == project_id),
    )
    total = total_result.scalar() or 0

    type_rows = await db.execute(
        select(TestCase.test_type, func.count(TestCase.id))
        .where(TestCase.project_id == project_id)
        .group_by(TestCase.test_type),
    )
    priority_rows = await db.execute(
        select(TestCase.priority, func.count(TestCase.id))
        .where(TestCase.project_id == project_id)
        .group_by(TestCase.priority),
    )
    status_rows = await db.execute(
        select(TestCase.status, func.count(TestCase.id))
        .where(TestCase.project_id == project_id)
        .group_by(TestCase.status),
    )
    return {
        "total": total,
        "by_type": dict(type_rows.all()),
        "by_priority": dict(priority_rows.all()),
        "by_status": dict(status_rows.all()),
    }
