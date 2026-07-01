"""
用例附件服务

提供附件上传、列表、删除等业务逻辑。
"""

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.aitest.models.case_attachment import CaseAttachment

# 允许上传的文件扩展名白名单
ALLOWED_EXTENSIONS: set[str] = {
    "jpg", "jpeg", "png", "gif", "webp", "svg",
    "pdf", "txt", "md", "doc", "docx",
    "xls", "xlsx", "csv",
    "json", "xml",
    "zip", "tar", "gz",
}

# 最大文件大小：50MB
MAX_FILE_SIZE: int = 50 * 1024 * 1024


async def create_attachment(
    db: AsyncSession,
    case_id: int,
    file: UploadFile,
    uploaded_by: int,
) -> CaseAttachment:
    """
    上传附件

    1. 校验文件扩展名是否在白名单内
    2. 校验文件大小是否超过限制（50MB）
    3. 读取文件内容，生成 UUID 文件名，保存到磁盘
    4. 创建数据库记录并返回
    """
    # ---------- 校验扩展名 ----------
    original_filename = file.filename or "unknown"
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: .{ext}，允许的类型: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    # ---------- 读取文件内容并校验大小 ----------
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"文件大小超过限制（最大 50MB），当前大小: {len(content) / 1024 / 1024:.2f}MB")

    # ---------- 生成存储路径 ----------
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR) / "case_attachments"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名，保留原始扩展名
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = upload_dir / unique_name

    # ---------- 写入文件 ----------
    file_path.write_bytes(content)

    # ---------- 创建数据库记录 ----------
    attachment = CaseAttachment(
        case_id=case_id,
        file_name=original_filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=file.content_type or "",
        uploaded_by=uploaded_by,
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)
    return attachment


async def list_attachments(db: AsyncSession, case_id: int) -> list[CaseAttachment]:
    """获取用例的附件列表"""
    stmt = (
        select(CaseAttachment)
        .where(CaseAttachment.case_id == case_id)
        .order_by(CaseAttachment.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_attachment(db: AsyncSession, attachment_id: int) -> CaseAttachment | None:
    """获取单个附件详情"""
    stmt = select(CaseAttachment).where(CaseAttachment.id == attachment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_attachment(db: AsyncSession, attachment_id: int) -> bool:
    """
    删除附件

    删除物理文件 + 数据库记录。如果附件不存在则返回 False。
    """
    stmt = select(CaseAttachment).where(CaseAttachment.id == attachment_id)
    result = await db.execute(stmt)
    attachment = result.scalar_one_or_none()
    if attachment is None:
        return False

    # 删除物理文件
    file_path = Path(attachment.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(attachment)
    await db.flush()
    return True
