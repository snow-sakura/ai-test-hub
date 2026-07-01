"""
用例附件 API 路由

提供附件上传、列表、删除、下载接口。
"""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.database import get_db
from app.deps import get_current_active_user
from app.modules.aitest.models.case_attachment import CaseAttachment
from app.modules.aitest.schemas.attachment import AttachmentResponse
from app.modules.aitest.services.attachment_service import (
    create_attachment,
    list_attachments,
    get_attachment,
    delete_attachment,
)

router = APIRouter(prefix="/api/v1", tags=["用例附件管理"])


@router.post(
    "/cases/{case_id}/attachments",
    response_model=ResponseModel[AttachmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    case_id: int,
    file: UploadFile = File(..., description="附件文件"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """上传用例附件"""
    try:
        attachment = await create_attachment(db, case_id, file, uploaded_by=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ResponseModel(data=AttachmentResponse.model_validate(attachment))


@router.get(
    "/cases/{case_id}/attachments",
    response_model=ResponseModel[list[AttachmentResponse]],
)
async def list_case_attachments(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用例的附件列表"""
    attachments = await list_attachments(db, case_id)
    return ResponseModel(
        data=[AttachmentResponse.model_validate(a) for a in attachments],
    )


@router.delete(
    "/attachments/{attachment_id}",
    response_model=ResponseModel,
)
async def delete_case_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除附件（同时删除物理文件）"""
    deleted = await delete_attachment(db, attachment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在",
        )
    return ResponseModel(message="删除成功")


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    下载附件

    以流式方式返回文件内容，支持大文件下载。
    包含 Content-Disposition 头，触发浏览器下载。
    """
    attachment = await get_attachment(db, attachment_id)
    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在",
        )

    file_path = Path(attachment.file_path)

    # 路径穿越防护：确保文件路径在预期的上传目录内
    try:
        file_path = file_path.resolve(strict=True)
    except (FileNotFoundError, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件文件不存在",
        )

    # 检查文件是否存在于磁盘
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件文件不存在",
        )

    # 流式读取文件（64KB 块）
    async def file_iterator():
        with open(file_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                yield chunk

    # 安全处理文件名：移除路径信息，仅保留原始文件名
    safe_filename = os.path.basename(attachment.file_name)

    return StreamingResponse(
        file_iterator(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Content-Length": str(file_path.stat().st_size),
        },
    )
