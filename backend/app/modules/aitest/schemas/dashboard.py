"""
仪表盘统计 Pydantic 模型

定义 DashboardStatsResponse 模型，
用于返回 AI 测试模块仪表盘聚合统计数据。
"""

from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """仪表盘统计响应"""
    project_count: int = Field(0, description="项目总数")
    case_count: int = Field(0, description="用例总数")
    version_count: int = Field(0, description="版本总数")
    review_count: int = Field(0, description="评审总数")
    task_count: int = Field(0, description="AI 生成任务总数")
    completed_task_count: int = Field(0, description="已完成任务数")
    member_count: int = Field(0, description="成员总数")
    case_by_priority: dict[str, int] = Field(
        default_factory=dict, description="按优先级统计",
    )
    case_by_type: dict[str, int] = Field(
        default_factory=dict, description="按测试类型统计",
    )
    case_by_status: dict[str, int] = Field(
        default_factory=dict, description="按状态统计",
    )
    recent_activities: list = Field(
        default_factory=list, description="最近操作记录",
    )
