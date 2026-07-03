"""知识库服务层"""

import os
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException

from app.common.models.user import User
from app.modules.knowledge_base.models.kb_document import KBDocument
from app.modules.knowledge_base.models.knowledge_base import KnowledgeBase
from app.modules.knowledge_base.schemas.kb import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KBSearchRequest,
    KBSearchResult,
)

KB_UPLOAD_DIR = Path("uploads/kb_documents")
KB_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = {
    ".docx", ".doc", ".xmind", ".md", ".xlsx", ".xls",
    ".csv", ".txt", ".htm", ".html", ".pdf", ".xml"
}


async def create_knowledge_base(
    db: AsyncSession,
    body: KnowledgeBaseCreate,
    current_user: User,
) -> KnowledgeBase:
    """创建知识库"""
    kb = KnowledgeBase(
        name=body.name,
        description=body.description,
        embedding_model=body.embedding_model,
        created_by=current_user.id,
    )
    db.add(kb)
    await db.flush()
    await db.commit()
    await db.refresh(kb)
    return kb


async def get_knowledge_bases(db: AsyncSession, current_user: User) -> list[KnowledgeBase]:
    """获取知识库列表"""
    stmt = (
        select(KnowledgeBase)
        .order_by(KnowledgeBase.updated_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_knowledge_base(
    db: AsyncSession,
    kb_id: int,
    current_user: User,
) -> KnowledgeBase:
    """获取知识库详情"""
    kb = await db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


async def update_knowledge_base(
    db: AsyncSession,
    kb_id: int,
    body: KnowledgeBaseUpdate,
    current_user: User,
) -> KnowledgeBase:
    """更新知识库"""
    kb = await get_knowledge_base(db, kb_id, current_user)
    if body.name is not None:
        kb.name = body.name
    if body.description is not None:
        kb.description = body.description
    if body.status is not None:
        kb.status = body.status
    if body.embedding_model is not None:
        kb.embedding_model = body.embedding_model
    await db.flush()
    await db.commit()
    await db.refresh(kb)
    return kb


async def delete_knowledge_base(
    db: AsyncSession,
    kb_id: int,
    current_user: User,
):
    """删除知识库"""
    kb = await get_knowledge_base(db, kb_id, current_user)
    await db.delete(kb)
    await db.commit()


async def get_kb_documents(
    db: AsyncSession,
    kb_id: int,
    current_user: User,
) -> list[KBDocument]:
    """获取知识库文档列表"""
    await get_knowledge_base(db, kb_id, current_user)
    stmt = (
        select(KBDocument)
        .where(KBDocument.knowledge_base_id == kb_id)
        .order_by(KBDocument.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def upload_kb_document(
    db: AsyncSession,
    kb_id: int,
    file_content: bytes,
    filename: str,
    current_user: User,
) -> KBDocument:
    """上传知识库文档"""
    kb = await get_knowledge_base(db, kb_id, current_user)

    # 安全验证文件名
    if not filename or filename.strip() != filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    # 防止路径遍历攻击
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="文件名包含非法字符")

    # 检查文件扩展名
    file_ext = Path(filename).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，支持的格式: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # 验证文件大小
    max_size = 100 * 1024 * 1024  # 100MB
    if len(file_content) > max_size:
        raise HTTPException(status_code=400, detail="文件大小超过100MB限制")

    # 生成安全的文件名
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = KB_UPLOAD_DIR / unique_name

    # 确保上传目录存在
    KB_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 写入文件（使用二进制模式确保安全性）
    try:
        file_path.write_bytes(file_content)
    except (OSError, IOError) as e:
        raise HTTPException(status_code=500, detail="文件写入失败")

    document = KBDocument(
        knowledge_base_id=kb_id,
        filename=filename,
        file_path=str(file_path),
        file_size=len(file_content),
        status="processing",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    await process_kb_document(db, document)

    return document


async def process_kb_document(db: AsyncSession, document: KBDocument):
    """处理知识库文档（模拟向量化）"""
    try:
        content = Path(document.file_path).read_text(encoding="utf-8", errors="ignore")
        chunks = []
        chunk_size = 1000
        for i in range(0, len(content), chunk_size):
            chunks.append(content[i:i + chunk_size])

        document.chunk_count = len(chunks)
        document.status = "completed"
    except Exception as e:
        document.status = "failed"
        document.error_message = str(e)

    await db.flush()
    await db.commit()


async def delete_kb_document(
    db: AsyncSession,
    kb_id: int,
    doc_id: int,
    current_user: User,
):
    """删除知识库文档"""
    await get_knowledge_base(db, kb_id, current_user)
    document = await db.get(KBDocument, doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    if document.knowledge_base_id != kb_id:
        raise HTTPException(status_code=403, detail="文档不属于此知识库")

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    await db.delete(document)
    await db.commit()


async def search_knowledge_base(
    db: AsyncSession,
    kb_id: int,
    request: KBSearchRequest,
    current_user: User,
) -> list[KBSearchResult]:
    """搜索知识库"""
    kb = await get_knowledge_base(db, kb_id, current_user)

    docs_stmt = (
        select(KBDocument)
        .where(KBDocument.knowledge_base_id == kb_id)
        .where(KBDocument.status == "completed")
    )
    result = await db.execute(docs_stmt)
    documents = result.scalars().all()

    results = []
    query_lower = request.query.lower()
    for doc in documents:
        try:
            content = Path(doc.file_path).read_text(encoding="utf-8", errors="ignore")
            if query_lower in content.lower():
                snippet_start = content.lower().find(query_lower)
                snippet = content[max(0, snippet_start - 50):snippet_start + len(request.query) + 100]
                results.append(KBSearchResult(
                    id=len(results) + 1,
                    knowledge_base_id=kb_id,
                    knowledge_base_name=kb.name,
                    document_id=doc.id,
                    document_name=doc.filename,
                    content=snippet,
                    score=0.8,
                ))
        except Exception:
            continue

    return results[:request.top_k]


async def get_kb_document_count(db: AsyncSession, kb_id: int) -> int:
    """获取知识库文档数量"""
    stmt = select(func.count()).select_from(KBDocument).where(KBDocument.knowledge_base_id == kb_id)
    result = await db.execute(stmt)
    return result.scalar() or 0