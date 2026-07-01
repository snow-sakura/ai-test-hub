"""
API 定时任务 Pydantic 模型

定义定时任务的创建、更新和响应数据结构。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiScheduleCreate(BaseModel):
    """创建 API 定时任务请求"""
    name: str
    suite_id: int
    environment_id: int | None = None
    cron_expression: str
    notify: dict | None = None


class ApiScheduleUpdate(BaseModel):
    """更新 API 定时任务请求"""
    name: str | None = None
    suite_id: int | None = None
    environment_id: int | None = None
    cron_expression: str | None = None
    status: str | None = None
    notify: dict | None = None


class ApiScheduleResponse(BaseModel):
    """API 定时任务响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    suite_id: int
    environment_id: int | None
    cron_expression: str
    status: str
    notify: dict | None
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime
