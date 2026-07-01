"""
测试用例 Pydantic 模型

定义 TestCase 相关的请求/响应模型。
TestCase 是跨模块共享的核心实体，其他模块通过此模型与测试管理交互。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExcelImportResult(BaseModel):
    """Excel 导入结果"""
    imported: int = 0
    errors: list[str] = Field(default_factory=list)


class TestCaseCreate(BaseModel):
    """创建测试用例请求"""
    project_id: int | None = Field(None, description="关联项目ID")
    version_id: int | None = Field(None, description="关联版本ID")
    module: str | None = Field(None, max_length=100, description="模块名称")
    name: str = Field(..., min_length=1, max_length=200, description="用例标题")
    description: str | None = Field(None, description="用例描述")
    priority: str = Field("p2", description="优先级（p0/p1/p2/p3）")
    precondition: str | None = Field(None, description="前置条件")
    test_steps: str | None = Field(None, description="测试步骤")
    expected_result: str | None = Field(None, description="预期结果")
    status: str = Field("active", description="状态（draft/active/deprecated）")
    test_type: str = Field("functional", description="测试类型（functional/api/ui/app）")
    source: str = Field("manual", description="来源（ai_generated/manual/imported）")
    tags: list[str] | None = Field(None, description="标签列表")


class TestCaseBatchCreate(BaseModel):
    """批量创建测试用例请求（供 AI 模块调用）"""
    cases: list[TestCaseCreate]


class TestCaseUpdate(BaseModel):
    """更新测试用例请求"""
    module: str | None = Field(None, max_length=100, description="模块名称")
    name: str | None = Field(None, min_length=1, max_length=200, description="用例标题")
    description: str | None = Field(None, description="用例描述")
    priority: str | None = Field(None, description="优先级（p0/p1/p2/p3）")
    precondition: str | None = Field(None, description="前置条件")
    test_steps: str | None = Field(None, description="测试步骤")
    expected_result: str | None = Field(None, description="预期结果")
    status: str | None = Field(None, description="状态（draft/active/deprecated）")
    test_type: str | None = Field(None, description="测试类型（functional/api/ui/app）")
    tags: list[str] | None = Field(None, description="标签列表")


class TestCaseResponse(BaseModel):
    """测试用例响应"""
    id: int
    project_id: int | None = None
    version_id: int | None = None
    module: str | None = None
    name: str
    description: str | None = None
    priority: str = "p2"
    precondition: str | None = None
    test_steps: str | None = None
    expected_result: str | None = None
    status: str = "draft"
    test_type: str = "functional"
    source: str = "manual"
    tags: list | None = None
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    latest_execution_status: str | None = Field(
        None, description="最新执行结果（pass/fail/blocked/skip），查询时注入",
    )

    model_config = ConfigDict(from_attributes=True)


class TestCaseStats(BaseModel):
    """测试用例统计"""
    total: int = 0
    by_type: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_status: dict[str, int] = {}
