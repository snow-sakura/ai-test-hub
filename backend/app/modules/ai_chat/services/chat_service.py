"""AI 聊天室服务层"""

import os
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from app.common.models.user import User
from app.modules.ai_chat.models.chat_message import ChatMessage
from app.modules.ai_chat.models.chat_message_file import ChatMessageFile
from app.modules.ai_chat.models.chat_session import ChatSession
from app.modules.ai_chat.schemas.chat import ChatMessageBody, ChatSessionCreate
from app.modules.knowledge_base.models.knowledge_base import KnowledgeBase

UPLOAD_DIR = Path("uploads/chat_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


async def create_session(
    db: AsyncSession,
    body: ChatSessionCreate,
    current_user: User,
) -> ChatSession:
    """创建会话"""
    session = ChatSession(
        name=body.name or "新会话",
        model=body.model or "",
        knowledge_base_id=body.knowledge_base_id,
        created_by=current_user.id,
    )
    db.add(session)
    await db.flush()
    await db.commit()
    await db.refresh(session)
    return session


async def get_sessions(db: AsyncSession, current_user: User) -> list[ChatSession]:
    """获取会话列表"""
    from sqlalchemy.orm import joinedload

    stmt = (
        select(ChatSession)
        .where(ChatSession.created_by == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .options(joinedload(ChatSession.messages), joinedload(ChatSession.knowledge_base))
    )
    result = await db.execute(stmt)
    return result.scalars().unique().all()


async def get_session(db: AsyncSession, session_id: int, current_user: User) -> ChatSession:
    """获取会话详情"""
    session = await db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此会话")
    return session


async def update_session(
    db: AsyncSession,
    session_id: int,
    body: ChatSessionCreate,
    current_user: User,
) -> ChatSession:
    """更新会话"""
    session = await get_session(db, session_id, current_user)
    if body.name:
        session.name = body.name
    if body.model is not None:
        session.model = body.model
    if body.knowledge_base_id is not None:
        session.knowledge_base_id = body.knowledge_base_id
    await db.flush()
    await db.commit()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session_id: int, current_user: User):
    """删除会话"""
    session = await get_session(db, session_id, current_user)
    await db.delete(session)
    await db.commit()


async def get_messages(db: AsyncSession, session_id: int, current_user: User) -> list[ChatMessage]:
    """获取会话消息列表"""
    from sqlalchemy.orm import joinedload

    await get_session(db, session_id, current_user)
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .options(joinedload(ChatMessage.files))
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def save_message_file(
    db: AsyncSession,
    file_content: bytes,
    filename: str,
) -> ChatMessageFile:
    """保存消息附件文件"""
    file_ext = Path(filename).suffix.lower()
    file_type = file_ext.lstrip(".")
    is_image = file_ext in IMAGE_EXTENSIONS

    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_name
    file_path.write_bytes(file_content)

    file_record = ChatMessageFile(
        file_path=str(file_path),
        file_name=filename,
        file_size=len(file_content),
        file_type=file_type,
        is_image=is_image,
    )
    db.add(file_record)
    await db.flush()
    await db.refresh(file_record)
    return file_record


async def create_message(
    db: AsyncSession,
    session_id: int,
    role: str,
    content: str,
    file_ids: list[int] = [],
) -> ChatMessage:
    """创建消息"""
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    await db.flush()
    await db.refresh(message)

    if file_ids:
        for file_id in file_ids:
            file_record = await db.get(ChatMessageFile, file_id)
            if file_record:
                file_record.message_id = message.id
                await db.flush()

    await db.commit()
    return message


async def update_message_rating(
    db: AsyncSession,
    message_id: int,
    rating: str | None,
    current_user: User,
) -> ChatMessage:
    """更新消息评分"""
    message = await db.get(ChatMessage, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="消息不存在")

    session = await db.get(ChatSession, message.session_id)
    if session is None or session.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此消息")

    message.rating = rating
    await db.flush()
    await db.commit()
    await db.refresh(message)
    return message


async def stream_chat_response(
    session_id: int,
    user_content: str,
    model_str: str,
    db: AsyncSession,
    current_user: User,
    knowledge_base_id: int | None = None,
) -> AsyncGenerator[tuple[str, Any], None]:
    """流式获取 AI 聊天室回复"""
    session = await get_session(db, session_id, current_user)

    model_to_use = model_str or session.model
    if not model_to_use:
        raise HTTPException(status_code=400, detail="未指定模型")

    parsed_model = model_to_use.split(":")[-1]

    from app.modules.aitest.services.ai_service import (
        AIClientFactory,
        AICompletionConfig,
        _resolve_api_key,
        _resolve_base_url,
    )
    from app.modules.config_center.models.ai_model_config import AIModelConfig

    stmt = (
        select(AIModelConfig)
        .where(AIModelConfig.model_name == parsed_model)
        .where(AIModelConfig.is_active.is_(True))
        .limit(1)
    )
    result = await db.execute(stmt)
    model_config = result.scalar_one_or_none()
    if model_config is None:
        raise HTTPException(status_code=400, detail=f"未找到启用的模型配置: {parsed_model}")

    history_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(20)
    )
    history_result = await db.execute(history_stmt)
    history = list(reversed(history_result.scalars().all()))

    llm_messages: list[dict] = []
    for msg in history:
        llm_messages.append({"role": msg.role, "content": msg.content})

    llm_messages.append({"role": "user", "content": user_content})

    import asyncio

    provider = AIClientFactory.get_provider(model_config.model_type)
    ai_config = AICompletionConfig(
        api_key=_resolve_api_key(model_config),
        base_url=_resolve_base_url(model_config),
        model_name=model_config.model_name,
        max_tokens=model_config.max_tokens or 4096,
        temperature=model_config.temperature or 0.7,
        top_p=model_config.top_p or 0.9,
    )

    chunk_queue: asyncio.Queue = asyncio.Queue()
    full_content_parts: list[str] = []
    ai_error: Exception | None = None

    async def _run_ai_stream():
        nonlocal ai_error
        try:
            def _on_chunk(text: str):
                full_content_parts.append(text)
                chunk_queue.put_nowait(text)

            await provider.chat_stream(llm_messages, ai_config, on_chunk=_on_chunk)
        except Exception as e:
            ai_error = e
        finally:
            chunk_queue.put_nowait(None)

    ai_task = asyncio.create_task(_run_ai_stream())

    try:
        while True:
            chunk = await chunk_queue.get()
            if chunk is None:
                break
            yield "token", chunk

        if ai_error:
            raise ai_error

        full_content = "".join(full_content_parts)
        yield "complete", full_content
    finally:
        if not ai_task.done():
            ai_task.cancel()