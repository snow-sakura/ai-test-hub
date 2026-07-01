"""
API 测试套件 Pydantic 模型

定义 API 自动化测试相关的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ApiTestSuiteCreate(BaseModel):
    """创建测试套件请求体"""
    project_id: int = Field(..., description="所属项目 ID")
    name: str = Field(..., min_length=1, max_length=200, description="套件名称")
    description: str | None = Field(None, description="套件描述")
    endpoints_config: list | None = Field(None, description="接口顺序和配置")
    assertions: dict | None = Field(None, description="断言规则")


class ApiTestSuiteUpdate(BaseModel):
    """更新测试套件请求体"""
    name: str | None = Field(None, min_length=1, max_length=200, description="套件名称")
    description: str | None = Field(None, description="套件描述")
    endpoints_config: list | None = Field(None, description="接口顺序和配置")
    assertions: dict | None = Field(None, description="断言规则")
    status: str | None = Field(None, description="状态")


class ApiTestSuiteResponse(BaseModel):
    """测试套件响应体"""
    id: int
    project_id: int
    name: str
    description: str | None = None
    endpoints_config: list | None = None
    assertions: dict | None = None
    status: str = "draft"
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiExecutionResult(BaseModel):
    """单接口执行结果"""
    endpoint_id: int
    endpoint_name: str
    method: str
    path: str
    status_code: int | None = None
    response_body: dict | None = None
    response_headers: dict | None = None
    elapsed_ms: float = 0
    assertions_passed: int = 0
    assertions_failed: int = 0
    assertion_details: list[dict] = []
    passed: bool = False
    error: str | None = None


class ApiTestReport(BaseModel):
    """测试执行报告"""
    execution_id: str
    suite_id: int
    suite_name: str
    status: str
    started_at: str
    finished_at: str | None = None
    total_endpoints: int = 0
    passed: int = 0
    failed: int = 0
    results: list[ApiExecutionResult] = []


class ApiTestReportSummary(BaseModel):
    """测试报告概要"""
    execution_id: str
    suite_id: int
    suite_name: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    total_endpoints: int = 0
    passed: int = 0
    failed: int = 0

    model_config = {"from_attributes": True}
