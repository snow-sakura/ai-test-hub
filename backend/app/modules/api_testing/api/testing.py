"""
API 测试套件 CRUD + 执行接口

提供测试套件的增删改查，以及异步执行和报告查询功能。
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.modules.api_testing.models.project import ApiProject
from app.modules.api_testing.models.test_suite import ApiTestSuite
from app.modules.api_testing.schemas.test_suite import (
    ApiTestSuiteCreate,
    ApiTestSuiteResponse,
    ApiTestSuiteUpdate,
    ApiTestReport,
)
from app.modules.api_testing.services.executor import execute_suite

router = APIRouter(prefix="/api/v1/api-test-suites", tags=["API自动化测试"])

# 内存存储的执行报告（生产环境应改为数据库或 Redis 持久化）
_execution_reports: dict[str, ApiTestReport] = {}


@router.get("", response_model=ResponseModel[list[ApiTestSuiteResponse]])
async def list_test_suites(
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取测试套件列表，支持按项目筛选"""
    stmt = select(ApiTestSuite)

    if project_id is not None:
        stmt = stmt.where(ApiTestSuite.project_id == project_id)

    stmt = stmt.order_by(ApiTestSuite.created_at.desc())
    result = await db.execute(stmt)
    suites = result.scalars().all()

    return ResponseModel(
        data=[ApiTestSuiteResponse.model_validate(s) for s in suites],
    )


@router.post("", response_model=ResponseModel[ApiTestSuiteResponse], status_code=status.HTTP_201_CREATED)
async def create_test_suite(
    body: ApiTestSuiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建测试套件"""
    # 验证项目存在
    project_stmt = select(ApiProject).where(ApiProject.id == body.project_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    suite = ApiTestSuite(
        project_id=body.project_id,
        name=body.name,
        description=body.description,
        endpoints_config=body.endpoints_config,
        assertions=body.assertions,
        created_by=current_user.id,
    )
    db.add(suite)
    await db.flush()
    await db.refresh(suite)

    return ResponseModel(data=ApiTestSuiteResponse.model_validate(suite))


@router.put("/{suite_id}", response_model=ResponseModel[ApiTestSuiteResponse])
async def update_test_suite(
    suite_id: int,
    body: ApiTestSuiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新测试套件"""
    stmt = select(ApiTestSuite).where(ApiTestSuite.id == suite_id)
    result = await db.execute(stmt)
    suite = result.scalar_one_or_none()

    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(suite, field, value)

    await db.flush()
    await db.refresh(suite)

    return ResponseModel(data=ApiTestSuiteResponse.model_validate(suite))


@router.delete("/{suite_id}", response_model=ResponseModel)
async def delete_test_suite(
    suite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除测试套件"""
    stmt = select(ApiTestSuite).where(ApiTestSuite.id == suite_id)
    result = await db.execute(stmt)
    suite = result.scalar_one_or_none()

    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在",
        )

    await db.delete(suite)
    await db.flush()

    return ResponseModel(message="删除成功")


@router.post("/{suite_id}/execute", response_model=ResponseModel)
async def execute_test_suite(
    suite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """执行测试套件（异步执行）"""
    # 验证套件存在
    stmt = select(ApiTestSuite).where(ApiTestSuite.id == suite_id)
    result = await db.execute(stmt)
    suite = result.scalar_one_or_none()

    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在",
        )

    # 执行套件
    try:
        report = await execute_suite(db, suite_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 保存执行报告
    _execution_reports[report.execution_id] = report

    return ResponseModel(
        message="执行完成",
        data={
            "execution_id": report.execution_id,
            "status": report.status,
            "total_endpoints": report.total_endpoints,
            "passed": report.passed,
            "failed": report.failed,
        },
    )


@router.get("/{suite_id}/reports", response_model=ResponseModel[list[dict]])
async def list_test_reports(
    suite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取测试套件的执行报告列表"""
    # 验证套件存在
    stmt = select(ApiTestSuite).where(ApiTestSuite.id == suite_id)
    result = await db.execute(stmt)
    suite = result.scalar_one_or_none()

    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在",
        )

    # 从内存中查找属于该套件的报告
    reports = []
    for report in _execution_reports.values():
        if report.suite_id == suite_id:
            reports.append({
                "execution_id": report.execution_id,
                "suite_id": report.suite_id,
                "suite_name": report.suite_name,
                "status": report.status,
                "started_at": report.started_at,
                "finished_at": report.finished_at,
                "total_endpoints": report.total_endpoints,
                "passed": report.passed,
                "failed": report.failed,
                "results": [
                    {
                        "endpoint_id": r.endpoint_id,
                        "endpoint_name": r.endpoint_name,
                        "method": r.method,
                        "path": r.path,
                        "status_code": r.status_code,
                        "elapsed_ms": r.elapsed_ms,
                        "passed": r.passed,
                        "error": r.error,
                        "assertions_passed": r.assertions_passed,
                        "assertions_failed": r.assertions_failed,
                        "assertion_details": r.assertion_details,
                        "response_body": r.response_body,
                    }
                    for r in report.results
                ],
            })

    return ResponseModel(data=reports)
