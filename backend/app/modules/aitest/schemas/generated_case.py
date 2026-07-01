"""
AI 生成候选用例 Pydantic 模型

定义 GeneratedCaseItem 相关的请求/响应模型，
用于 AI 生成的候选用例的展示、采纳/丢弃操作及保存到用例库。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GeneratedCaseItemResponse(BaseModel):
    """AI 生成候选用例响应"""
    id: int
    task_id: int
    title: str
    priority: str
    module: str | None = None
    precondition: str | None = None
    test_steps: str | None = None
    expected_result: str | None = None
    tags: str | None = None
    status: str = "pending"
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BatchUpdateCasesRequest(BaseModel):
    """批量更新候选用例状态请求"""
    case_ids: list[int] = Field(..., min_length=1, description="候选用例ID列表")
    status: str = Field(
        ..., pattern=r"^(adopted|discarded|pending)$",
        description="目标状态（adopted=已采纳/discarded=已丢弃/pending=待定）",
    )


class SaveToLibraryRequest(BaseModel):
    """保存候选用例到用例库请求"""
    project_id: int | None = Field(None, description="目标项目ID（为空则使用任务关联的项目）")
    case_ids: list[int] | None = Field(None, description="指定保存的用例ID列表（为空则保存全部已采纳用例）")
