"""知识库 API 路由"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.deps import get_current_user, get_db
from app.common.models.user import User
from app.modules.knowledge_base.schemas.kb import (
    KBDocumentResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    KBSearchRequest,
    KBSearchResult,
)
from app.modules.knowledge_base.services.kb_service import (
    create_knowledge_base,
    delete_kb_document,
    delete_knowledge_base,
    get_kb_document_count,
    get_kb_documents,
    get_knowledge_base,
    get_knowledge_bases,
    search_knowledge_base,
    update_knowledge_base,
    upload_kb_document,
)

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["知识库"])


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库列表"""
    kbs = await get_knowledge_bases(db, current_user)
    results = []
    for kb in kbs:
        doc_count = await get_kb_document_count(db, kb.id)
        results.append(KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            status=kb.status,
            embedding_model=kb.embedding_model,
            document_count=doc_count,
            created_by=kb.created_by,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
        ))
    return results


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_kb(
    body: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建知识库"""
    kb = await create_knowledge_base(db, body, current_user)
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        status=kb.status,
        embedding_model=kb.embedding_model,
        document_count=0,
        created_by=kb.created_by,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_kb(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库详情"""
    kb = await get_knowledge_base(db, kb_id, current_user)
    doc_count = await get_kb_document_count(db, kb.id)
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        status=kb.status,
        embedding_model=kb.embedding_model,
        document_count=doc_count,
        created_by=kb.created_by,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_kb(
    kb_id: int,
    body: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新知识库"""
    kb = await update_knowledge_base(db, kb_id, body, current_user)
    doc_count = await get_kb_document_count(db, kb.id)
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        status=kb.status,
        embedding_model=kb.embedding_model,
        document_count=doc_count,
        created_by=kb.created_by,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_kb(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除知识库"""
    await delete_knowledge_base(db, kb_id, current_user)


@router.get("/{kb_id}/documents", response_model=list[KBDocumentResponse])
async def list_kb_documents(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识库文档列表"""
    docs = await get_kb_documents(db, kb_id, current_user)
    return [KBDocumentResponse(
        id=doc.id,
        knowledge_base_id=doc.knowledge_base_id,
        filename=doc.filename,
        file_path=doc.file_path,
        file_size=doc.file_size,
        status=doc.status,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    ) for doc in docs]


@router.post("/{kb_id}/documents", response_model=KBDocumentResponse)
async def upload_documents(
    kb_id: int,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量上传知识库文档"""
    results = []
    for file in files:
        file_content = await file.read()
        doc = await upload_kb_document(db, kb_id, file_content, file.filename, current_user)
        results.append(KBDocumentResponse(
            id=doc.id,
            knowledge_base_id=doc.knowledge_base_id,
            filename=doc.filename,
            file_path=doc.file_path,
            file_size=doc.file_size,
            status=doc.status,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        ))

    if len(results) == 1:
        return results[0]
    return results


@router.delete("/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_kb_document(
    kb_id: int,
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除知识库文档"""
    await delete_kb_document(db, kb_id, doc_id, current_user)


@router.post("/{kb_id}/search", response_model=list[KBSearchResult])
async def search_kb(
    kb_id: int,
    body: KBSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """搜索知识库"""
    return await search_knowledge_base(db, kb_id, body, current_user)


@router.post("/{kb_id}/reindex", response_model=KnowledgeBaseResponse)
async def reindex_kb(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新索引知识库"""
    kb = await get_knowledge_base(db, kb_id, current_user)
    docs = await get_kb_documents(db, kb_id, current_user)

    from app.modules.knowledge_base.services.kb_service import process_kb_document
    for doc in docs:
        await process_kb_document(db, doc)

    doc_count = await get_kb_document_count(db, kb.id)
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        status=kb.status,
        embedding_model=kb.embedding_model,
        document_count=doc_count,
        created_by=kb.created_by,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )