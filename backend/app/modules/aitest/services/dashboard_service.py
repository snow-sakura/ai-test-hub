"""
仪表盘统计服务

提供 AI 测试模块仪表盘所需的聚合数据，
从多个表中汇总项目、用例、版本、评审、任务和成员数据。
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.aitest.models.ai_task import AIGenerationTask
from app.modules.aitest.models.project import ProjectMember, TestProject
from app.modules.aitest.models.review import TestReview
from app.modules.aitest.models.test_case import TestCase
from app.modules.aitest.models.version import TestVersion
from app.modules.aitest.services.operation_log_service import list_recent_activities


async def get_dashboard_stats(db: AsyncSession) -> dict:
    """获取仪表盘聚合统计数据"""
    # 项目总数
    project_count_result = await db.execute(
        select(func.count(TestProject.id)),
    )
    project_count = project_count_result.scalar() or 0

    # 用例总数
    case_count_result = await db.execute(
        select(func.count(TestCase.id)),
    )
    case_count = case_count_result.scalar() or 0

    # 版本总数
    version_count_result = await db.execute(
        select(func.count(TestVersion.id)),
    )
    version_count = version_count_result.scalar() or 0

    # 评审总数
    review_count_result = await db.execute(
        select(func.count(TestReview.id)),
    )
    review_count = review_count_result.scalar() or 0

    # AI 生成任务统计
    task_count_result = await db.execute(
        select(func.count(AIGenerationTask.id)),
    )
    task_count = task_count_result.scalar() or 0

    completed_task_count_result = await db.execute(
        select(func.count(AIGenerationTask.id))
        .where(AIGenerationTask.status == "completed"),
    )
    completed_task_count = completed_task_count_result.scalar() or 0

    # 成员总数（所有项目成员之和）
    member_count_result = await db.execute(
        select(func.count(ProjectMember.id)),
    )
    member_count = member_count_result.scalar() or 0

    # 用例按优先级分组
    priority_rows = await db.execute(
        select(TestCase.priority, func.count(TestCase.id))
        .group_by(TestCase.priority),
    )
    case_by_priority = dict(priority_rows.all())

    # 用例按测试类型分组
    type_rows = await db.execute(
        select(TestCase.test_type, func.count(TestCase.id))
        .group_by(TestCase.test_type),
    )
    case_by_type = dict(type_rows.all())

    # 用例按状态分组
    status_rows = await db.execute(
        select(TestCase.status, func.count(TestCase.id))
        .group_by(TestCase.status),
    )
    case_by_status = dict(status_rows.all())

    # 最近操作记录
    recent_activities = await list_recent_activities(db, limit=10)

    return {
        "project_count": project_count,
        "case_count": case_count,
        "version_count": version_count,
        "review_count": review_count,
        "task_count": task_count,
        "completed_task_count": completed_task_count,
        "member_count": member_count,
        "case_by_priority": case_by_priority,
        "case_by_type": case_by_type,
        "case_by_status": case_by_status,
        "recent_activities": recent_activities,
    }
