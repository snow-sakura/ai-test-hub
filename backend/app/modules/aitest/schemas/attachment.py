"""
用例附件 Pydantic 模型

定义 CaseAttachment 相关的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    """附件响应"""
    id: int
    case_id: int
    file_name: str
    file_size: int
    file_type: str
    uploaded_by: int | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AttachmentDownloadResponse(BaseModel):
    """附件下载响应（当文件无法直接流式返回时使用）"""
    download_url: str
