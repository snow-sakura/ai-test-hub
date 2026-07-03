"""AI 聊天室 API 路由"""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.deps import get_current_user, get_db
from app.common.models.user import User

logger = logging.getLogger(__name__)
from app.modules.ai_chat.schemas.chat import (
    ChatMessageBody,
    ChatMessageFileResponse,
    ChatMessageRatingUpdate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
)
from app.modules.ai_chat.services.chat_service import (
    create_message,
    create_session,
    delete_session,
    get_messages,
    get_session,
    get_sessions,
    save_message_file,
    stream_chat_response,
    update_message_rating,
    update_session,
)
from app.modules.knowledge_base.services.kb_service import get_kb_document_count

router = APIRouter(prefix="/api/v1/ai-chat", tags=["AI 聊天室"])


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话列表"""
    sessions = await get_sessions(db, current_user)
    results = []
    for session in sessions:
        kb_name = None
        doc_count = 0
        if session.knowledge_base:
            kb_name = session.knowledge_base.name
            doc_count = await get_kb_document_count(db, session.knowledge_base.id)

        first_msg = None
        if session.messages:
            first_msg = session.messages[0].content[:20] if session.messages else None

        results.append(ChatSessionResponse(
            id=session.id,
            name=session.name,
            model=session.model,
            knowledge_base_id=session.knowledge_base_id,
            knowledge_base_name=kb_name,
            message_count=session.message_count,
            created_by=session.created_by,
            created_at=session.created_at,
            updated_at=session.updated_at,
            first_message=first_msg,
        ))
    return results


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    body: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建会话"""
    session = await create_session(db, body, current_user)
    return ChatSessionResponse(
        id=session.id,
        name=session.name,
        model=session.model,
        knowledge_base_id=session.knowledge_base_id,
        message_count=session.message_count,
        created_by=session.created_by,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话详情"""
    session = await get_session(db, session_id, current_user)
    kb_name = None
    if session.knowledge_base:
        kb_name = session.knowledge_base.name

    first_msg = None
    if session.messages:
        first_msg = session.messages[0].content[:20] if session.messages else None

    return ChatSessionResponse(
        id=session.id,
        name=session.name,
        model=session.model,
        knowledge_base_id=session.knowledge_base_id,
        knowledge_base_name=kb_name,
        message_count=session.message_count,
        created_by=session.created_by,
        created_at=session.created_at,
        updated_at=session.updated_at,
        first_message=first_msg,
    )


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: int,
    body: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新会话"""
    session = await update_session(db, session_id, body, current_user)
    return ChatSessionResponse(
        id=session.id,
        name=session.name,
        model=session.model,
        knowledge_base_id=session.knowledge_base_id,
        message_count=session.message_count,
        created_by=session.created_by,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除会话"""
    await delete_session(db, session_id, current_user)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def list_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话消息列表"""
    messages = await get_messages(db, session_id, current_user)
    results = []
    for msg in messages:
        files = [ChatMessageFileResponse(
            id=f.id,
            file_name=f.file_name,
            file_size=f.file_size,
            file_type=f.file_type,
            is_image=f.is_image,
        ) for f in msg.files]
        results.append(ChatMessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            rating=msg.rating,
            created_at=msg.created_at,
            files=files,
        ))
    return results


@router.post("/messages/files", response_model=ChatMessageFileResponse)
async def upload_message_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传消息附件"""
    file_content = await file.read()
    file_record = await save_message_file(db, file_content, file.filename)
    return ChatMessageFileResponse(
        id=file_record.id,
        file_name=file_record.file_name,
        file_size=file_record.file_size,
        file_type=file_record.file_type,
        is_image=file_record.is_image,
    )


@router.post("/sessions/{session_id}/messages/stream")
async def stream_message(
    session_id: int,
    body: ChatMessageBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送消息（流式响应）"""

    async def event_generator():
        try:
            user_message = await create_message(db, session_id, "user", body.content, body.file_ids)

            session = await get_session(db, session_id, current_user)
            session.message_count += 1
            await db.flush()
            await db.commit()

            yield f"data: {json.dumps({'type': 'user_message', 'message': {'id': user_message.id, 'content': body.content}})}\n\n"

            assistant_content = ""
            async for event_type, data in stream_chat_response(
                session_id, body.content, body.model, db, current_user, body.knowledge_base_id
            ):
                if event_type == "token":
                    assistant_content += data
                    yield f"data: {json.dumps({'type': 'token', 'content': data})}\n\n"
                elif event_type == "complete":
                    yield f"data: {json.dumps({'type': 'complete', 'content': assistant_content})}\n\n"

            yield "data: [DONE]\n\n"
            await create_message(db, session_id, "assistant", assistant_content)
        except Exception as e:
            # 记录完整错误日志到服务端，但不返回 traceback 给前端（安全考虑）
            logger.error("聊天流式响应异常: %s", str(e), exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': '服务异常，请稍后重试'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@router.put("/messages/{message_id}/rating", response_model=ChatMessageResponse)
async def rate_message(
    message_id: int,
    body: ChatMessageRatingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新消息评分"""
    message = await update_message_rating(db, message_id, body.rating, current_user)
    return ChatMessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        rating=message.rating,
        created_at=message.created_at,
    )