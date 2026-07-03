"""知识库请求/响应模型"""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    embedding_model: str = ""


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    embedding_model: str | None = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: str | None = None
    status: str
    embedding_model: str
    document_count: int = 0
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class KBDocumentResponse(BaseModel):
    """知识库文档响应"""
    id: int
    knowledge_base_id: int
    filename: str
    file_path: str
    file_size: int
    status: str
    chunk_count: int = 0
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class KBSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(5, ge=1, le=20)


class KBSearchResult(BaseModel):
    """知识库搜索结果"""
    id: int
    knowledge_base_id: int
    knowledge_base_name: str
    document_id: int
    document_name: str
    content: str
    score: float