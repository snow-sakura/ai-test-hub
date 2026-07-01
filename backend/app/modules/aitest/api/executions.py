"""
测试用例执行记录 API 路由

提供执行用例、查询执行历史等接口。
仅 active 状态的用例允许执行。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.database import get_db
from app.deps import get_current_active_user
from app.modules.aitest.schemas.execution import (
    TestCaseExecuteRequest,
    TestCaseExecutionResponse,
)
from app.modules.aitest.services.execution_service import (
    create_execution,
    get_latest_execution,
    list_executions,
)

router = APIRouter(prefix="/api/v1/test-cases", tags=["测试用例执行"])


@router.post("/{case_id}/executions", response_model=ResponseModel[TestCaseExecutionResponse])
async def execute_test_case(
    case_id: int,
    body: TestCaseExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """执行测试用例（记录执行结果），仅 active 状态的用例允许执行"""
    # 校验执行结果值
    valid_statuses = {"pass", "fail", "blocked", "skip"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的执行结果：{body.status}，可选值：{'/'.join(valid_statuses)}",
        )
    try:
        execution = await create_execution(db, case_id, body, executed_by=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return ResponseModel(data=TestCaseExecutionResponse.model_validate(execution))


@router.get("/{case_id}/executions", response_model=ResponseModel[list[TestCaseExecutionResponse]])
async def list_case_executions(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用例执行历史"""
    executions = await list_executions(db, case_id)
    # 构造响应，注入执行人名称
    result = []
    for e in executions:
        resp = TestCaseExecutionResponse.model_validate(e)
        resp.executor_name = getattr(e.executor, "username", None) if e.executor else None
        result.append(resp)
    return ResponseModel(data=result)


@router.get("/{case_id}/executions/latest", response_model=ResponseModel[TestCaseExecutionResponse | None])
async def get_case_latest_execution(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用例最新执行结果"""
    execution = await get_latest_execution(db, case_id)
    if execution is None:
        return ResponseModel(data=None)
    resp = TestCaseExecutionResponse.model_validate(execution)
    resp.executor_name = getattr(execution.executor, "username", None) if execution.executor else None
    return ResponseModel(data=resp)
