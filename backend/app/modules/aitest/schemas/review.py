"""
用例评审 Pydantic 模型

定义 TestReview 和 ReviewAssignment 相关的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaseReviewSummary(BaseModel):
    """用例关联的评审摘要（用于 GET /v1/test-cases/{case_id}/reviews）"""
    id: int
    name: str
    status: str
    conclusion: str | None = None
    creator_name: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


def _resolve_project_name(review: object) -> str | None:
    """从 review.project 关系中读取项目名称"""
    project = getattr(review, "project", None)
    return getattr(project, "name", None) if project else None


def _resolve_creator_name(review: object) -> str | None:
    """从 review.creator 关系中读取创建者用户名"""
    creator = getattr(review, "creator", None)
    return getattr(creator, "username", None) if creator else None


def _resolve_username(assignment: object) -> str | None:
    """从 assignment.reviewer 关系中读取评审人用户名"""
    reviewer = getattr(assignment, "reviewer", None)
    return getattr(reviewer, "username", None) if reviewer else None


class TestReviewCreate(BaseModel):
    """创建评审请求"""
    project_id: int = Field(..., description="关联项目ID")
    name: str = Field(..., min_length=1, max_length=200, description="评审名称")
    cases: list | None = Field(None, description="用例列表")
    reviewer_ids: list[int] | None = Field(None, description="评审人ID列表")


class TestReviewUpdate(BaseModel):
    """更新评审请求"""
    name: str | None = Field(None, min_length=1, max_length=200, description="评审名称")
    status: str | None = Field(None, description="评审状态（pending/passed/rejected/cancelled）")
    cases: list | None = Field(None, description="用例列表")


class ReviewAssignmentResponse(BaseModel):
    """评审分配响应"""
    id: int
    review_id: int
    user_id: int
    username: str | None = None
    status: str = "pending"
    comment: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_username(cls, data: object) -> dict:
        """从 reviewer 关系中解析用户名"""
        if isinstance(data, dict):
            return data
        return {
            **{k: getattr(data, k, None) for k in cls.model_fields},
            "username": _resolve_username(data),
        }


class TestReviewDetail(BaseModel):
    """评审详情响应"""
    id: int
    project_id: int
    project_name: str | None = None
    name: str
    status: str = "pending"
    cases: list | None = None
    conclusion: str | None = None
    created_by: int
    creator_name: str | None = None
    assignments: list[ReviewAssignmentResponse] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_related_names(cls, data: object) -> dict:
        """从 project/creator 关系中解析项目名称和创建者用户名"""
        if isinstance(data, dict):
            return data
        return {
            **{k: getattr(data, k, None) for k in cls.model_fields},
            "project_name": _resolve_project_name(data),
            "creator_name": _resolve_creator_name(data),
        }


class TestReviewApprove(BaseModel):
    """审批评审请求"""
    action: str = Field(..., description="审批动作（pass/reject）")
    conclusion: str | None = Field(None, description="评审结论（reject 时必填）")


class ReviewStatsResponse(BaseModel):
    """评审统计数据"""
    total: int = 0
    pending: int = 0
    passed: int = 0
    rejected: int = 0


class ReviewCaseUpdate(BaseModel):
    """评审用例状态更新"""
    status: str = Field(..., description="用例评审状态（approved/rejected）")
    comment: str | None = Field(None, description="评审意见")


class ReviewCaseItem(BaseModel):
    """评审用例条目"""
    id: int
    name: str
    module: str | None = None
    priority: str = "p2"
    status: str = "active"  # 用例生命周期状态（draft/active/deprecated）
    review_status: str = "pending"
    review_comment: str | None = None
    reviewer_id: int | None = None
    latest_execution_status: str | None = Field(
        None, description="最新执行结果（pass/fail/blocked/skip），查询时注入",
    )

    model_config = ConfigDict(from_attributes=True)
