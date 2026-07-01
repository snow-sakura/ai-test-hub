"""
测试用例执行记录 Pydantic 模型

定义 TestCaseExecution 相关的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TestCaseExecuteRequest(BaseModel):
    """执行用例请求"""
    status: str = Field(..., description="执行结果（pass/fail/blocked/skip）")
    actual_result: str | None = Field(None, description="实际结果描述")


class TestCaseExecutionResponse(BaseModel):
    """执行记录响应"""
    id: int
    case_id: int
    status: str = "pass"
    actual_result: str | None = None
    executed_by: int
    executor_name: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
