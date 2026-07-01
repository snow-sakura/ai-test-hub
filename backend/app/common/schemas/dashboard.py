"""
仪表盘 Pydantic 响应模型模块

定义统计数据、功能模块等仪表盘相关 API 的响应结构。
"""

from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    """仪表盘统计数据响应体"""

    total_projects: int = Field(default=0, description="项目总数")
    total_test_cases: int = Field(default=0, description="测试用例总数")
    today_executions: int = Field(default=0, description="今日执行次数")
    pass_rate: float = Field(default=0.0, description="通过率（百分比）")


class ModuleInfo(BaseModel):
    """功能模块信息响应体"""

    key: str = Field(..., description="模块唯一标识")
    name: str = Field(..., description="模块显示名称")
    description: str = Field(..., description="模块功能描述")
    icon: str = Field(..., description="Element Plus 图标名称")
    color: str = Field(..., description="模块卡片主题色")
    path: str = Field(..., description="前端路由路径")
    meta: str | None = Field(default=None, description="额外信息（如 API 数量等）")
