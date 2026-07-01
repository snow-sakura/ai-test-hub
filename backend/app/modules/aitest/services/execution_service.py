"""
测试用例执行服务

提供创建执行记录、查询执行历史等业务逻辑。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.aitest.models.execution import TestCaseExecution
from app.modules.aitest.models.test_case import TestCase
from app.modules.aitest.schemas.execution import TestCaseExecuteRequest


async def create_execution(
    db: AsyncSession, case_id: int, data: TestCaseExecuteRequest, executed_by: int,
) -> TestCaseExecution:
    """创建执行记录（仅 active 状态的用例允许执行）"""
    # 校验用例存在且状态为 active
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id),
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise ValueError("用例不存在")
    if case.status != "active":
        raise ValueError("仅 active 状态的用例可以执行")

    execution = TestCaseExecution(
        case_id=case_id,
        status=data.status,
        actual_result=data.actual_result,
        executed_by=executed_by,
    )
    db.add(execution)
    await db.flush()
    await db.refresh(execution)
    return execution


async def list_executions(
    db: AsyncSession, case_id: int,
) -> list[TestCaseExecution]:
    """获取用例执行历史（按时间倒序）"""
    result = await db.execute(
        select(TestCaseExecution)
        .options(joinedload(TestCaseExecution.executor))
        .where(TestCaseExecution.case_id == case_id)
        .order_by(TestCaseExecution.id.desc()),
    )
    return list(result.scalars().all())


async def get_latest_execution(
    db: AsyncSession, case_id: int,
) -> TestCaseExecution | None:
    """获取用例最新执行结果"""
    result = await db.execute(
        select(TestCaseExecution)
        .where(TestCaseExecution.case_id == case_id)
        .order_by(TestCaseExecution.id.desc())
        .limit(1),
    )
    return result.scalar_one_or_none()
