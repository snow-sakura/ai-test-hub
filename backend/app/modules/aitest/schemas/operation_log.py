"""
操作日志 Pydantic 模型

定义 OperationLog 相关的响应模型，
用于展示实体变更历史和操作记录查询。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OperationLogResponse(BaseModel):
    """操作日志响应"""
    id: int
    entity_type: str
    entity_id: int
    action: str
    operator_id: int | None = None
    detail: dict | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
