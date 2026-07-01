"""
AI 评测师 API 接口模块

提供 AI 评测师聊天会话管理、消息发送（含 SSE 流式输出）、消息评分等功能的 RESTful 接口。
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update, delete, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.common.models.user import User
from app.common.schemas.common import ResponseModel

from app.modules.aitest.models.ai_tester_session import AITesterSession
from app.modules.aitest.models.ai_tester_message import AITesterMessage
from app.modules.aitest.schemas.ai_tester import (
    AITesterSessionCreate,
    AITesterSessionUpdate,
    AITesterSessionResponse,
    AITesterMessageBody,
    AITesterMessageResponse,
    AITesterMessageRatingUpdate,
    BatchDeleteSessionsRequest,
)
from app.modules.aitest.services.ai_service import AIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI 评测师"])


# ======================================================================
# 会话 CRUD
# ======================================================================


@router.get("/sessions", response_model=ResponseModel[list[AITesterSessionResponse]])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户的 AI 评测师会话列表。

    按更新时间倒序返回所有会话。
    """
    stmt = (
        select(AITesterSession)
        .where(AITesterSession.created_by == current_user.id)
        .order_by(AITesterSession.updated_at.desc())
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    session_responses = []
    for session in sessions:
        first_msg_stmt = (
            select(AITesterMessage.content)
            .where(AITesterMessage.session_id == session.id)
            .order_by(AITesterMessage.id.asc())
            .limit(1)
        )
        msg_result = await db.execute(first_msg_stmt)
        first_message = msg_result.scalar_one_or_none()

        response_data = AITesterSessionResponse.model_validate(session)
        response_data.first_message = first_message
        session_responses.append(response_data)

    return ResponseModel(
        data=session_responses,
    )


@router.post("/sessions", response_model=ResponseModel[AITesterSessionResponse])
async def create_session(
    body: AITesterSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建新的 AI 评测师会话。

    可指定会话名称和初始模型。创建后消息数为 0。
    """
    session = AITesterSession(
        name=body.name or "新会话",
        model=body.model or "",
        message_count=0,
        created_by=current_user.id,
    )
    db.add(session)
    await db.flush()
    await db.commit()
    await db.refresh(session)

    return ResponseModel(
        data=AITesterSessionResponse.model_validate(session),
    )


@router.put("/sessions/{session_id}", response_model=ResponseModel[AITesterSessionResponse])
async def rename_session(
    session_id: int,
    body: AITesterSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    重命名 AI 评测师会话。

    仅允许会话创建者操作。
    """
    session = await db.get(AITesterSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    if session.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此会话",
        )

    session.name = body.name
    await db.flush()
    await db.refresh(session)

    return ResponseModel(
        data=AITesterSessionResponse.model_validate(session),
    )


@router.delete("/sessions/{session_id}", response_model=ResponseModel)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除 AI 评测师会话（含所有消息）。

    仅允许会话创建者操作。级联删除关联的所有消息。
    """
    session = await db.get(AITesterSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    if session.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此会话",
        )

    await db.delete(session)
    await db.flush()

    return ResponseModel()


@router.post("/sessions/batch-delete", response_model=ResponseModel)
async def batch_delete_sessions(
    body: BatchDeleteSessionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量删除 AI 评测师会话（含所有消息）。

    仅删除当前用户拥有的会话。级联删除关联的所有消息。
    """
    if not body.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供要删除的会话 ID 列表",
        )

    result = await db.execute(
        select(AITesterSession).where(
            AITesterSession.id.in_(body.ids),
            AITesterSession.created_by == current_user.id,
        ),
    )
    sessions = result.scalars().all()

    for session in sessions:
        await db.delete(session)
    await db.flush()

    return ResponseModel(
        message=f"成功删除 {len(sessions)} 个会话",
        data={"deleted_count": len(sessions)},
    )


# ======================================================================
# 会话消息
# ======================================================================


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ResponseModel[list[AITesterMessageResponse]],
)
async def list_messages(
    session_id: int,
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(50, ge=1, le=200, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取会话的消息列表。

    按创建时间正序返回，支持分页（offset/limit）。
    """
    # 验证会话归属
    session = await db.get(AITesterSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    if session.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    stmt = (
        select(AITesterMessage)
        .where(AITesterMessage.session_id == session_id)
        .order_by(AITesterMessage.id.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return ResponseModel(
        data=[AITesterMessageResponse.model_validate(m) for m in messages],
    )


@router.post("/sessions/{session_id}/messages", response_model=ResponseModel)
async def send_message(
    session_id: int,
    body: AITesterMessageBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    发送消息（非流式）。

    流程：
    1. 保存用户消息到数据库
    2. 构建对话上下文（最近 20 条消息）
    3. 调用 AI 获取完整回复
    4. 保存 AI 回复到数据库
    5. 更新会话的消息计数
    """
    # ---- 1. 验证会话 ----
    session = await db.get(AITesterSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此会话")

    # ---- 2. 确定模型 ----
    model_to_use = body.model or session.model
    if not model_to_use:
        raise HTTPException(status_code=400, detail="未指定模型，请在会话或消息中指定")

    # ---- 3. 解析模型名（支持 provider:model_name 格式）----
    # 前端传递的格式可能是 "provider:model_name"，需要提取纯模型名
    parsed_model_name = model_to_use.split(':')[-1]

    # ---- 4. 查找模型配置 ----
    from app.modules.config_center.models.ai_model_config import AIModelConfig

    stmt = (
        select(AIModelConfig)
        .where(AIModelConfig.model_name == parsed_model_name)
        .where(AIModelConfig.is_active.is_(True))
        .limit(1)
    )
    result = await db.execute(stmt)
    model_config = result.scalar_one_or_none()
    if model_config is None:
        raise HTTPException(status_code=400, detail=f"未找到启用的模型配置: {parsed_model_name}")

    # ---- 4. 保存用户消息 ----
    user_msg = AITesterMessage(
        session_id=session_id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()
    await db.refresh(user_msg)

    # ---- 5. 构建对话上下文 ----
    history_stmt = (
        select(AITesterMessage)
        .where(AITesterMessage.session_id == session_id)
        .order_by(AITesterMessage.id.desc())
        .limit(20)
    )
    history_result = await db.execute(history_stmt)
    history = list(reversed(history_result.scalars().all()))

    messages: list[dict] = []
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    # ---- 6. 调用 AI（非流式） ----
    from app.common.utils.ai_client import AIClientFactory, AICompletionConfig

    provider = AIClientFactory.get_provider(model_config.model_type)
    config = AICompletionConfig(
        api_key=model_config.api_key or "",
        base_url=model_config.base_url,
        model_name=model_config.model_name,
        max_tokens=model_config.max_tokens or 4096,
        temperature=model_config.temperature or 0.7,
        top_p=model_config.top_p or 0.9,
    )

    try:
        result = await provider.chat_complete(messages, config)
        full_content = result.content
    except Exception as e:
        logger.error("AI 调用异常: %s", repr(e))
        raise HTTPException(status_code=502, detail=f"AI 调用失败: {str(e)}")

    # ---- 7. 保存 AI 回复 ----
    assistant_msg = AITesterMessage(
        session_id=session_id,
        role="assistant",
        content=full_content,
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    # ---- 8. 更新会话消息计数 ----
    count_stmt = select(sql_func.count()).select_from(AITesterMessage.__table__).where(
        AITesterMessage.session_id == session_id,
    )
    count_result = await db.execute(count_stmt)
    session.message_count = count_result.scalar() or 0
    await db.flush()

    return ResponseModel(
        data={
            "user_message": AITesterMessageResponse.model_validate(user_msg).model_dump(mode="json"),
            "assistant_message": AITesterMessageResponse.model_validate(assistant_msg).model_dump(mode="json"),
        },
    )


@router.post("/sessions/{session_id}/messages/stream")
async def send_message_stream(
    session_id: int,
    body: AITesterMessageBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    发送消息（SSE 流式）。

    通过 Server-Sent Events 实时推送 AI 回复文本块，支持流式展示。
    消息数据会自动保存到数据库。

    推送事件类型：
    - type: chunk        — AI 回复文本块
    - type: complete     — 全部完成，包含消息 ID
    - type: error        — 异常
    - type: done         — 流结束信号
    """
    # 验证会话
    session = await db.get(AITesterSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此会话")

    # 解析模型名（支持 provider:model_name 格式）
    parsed_model = body.model.split(':')[-1] if body.model else None

    # 创建事件队列
    queue: asyncio.Queue = asyncio.Queue()

    # 启动后台流式生成任务
    asyncio.create_task(
        _run_ai_tester_stream(
            session_id=session_id,
            user_content=body.content,
            model_str=parsed_model,
            db=db,
            current_user=current_user,
            queue=queue,
        ),
    )

    async def _event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connected', 'message': '连接成功'})}\n\n"
            
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=300)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'error', 'message': '请求超时'})}\n\n"
                    break
                    
                if event is None:
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            logger.info("SSE 连接被客户端断开: session_id=%s", session_id)
        except Exception as e:
            logger.error("SSE 异常: %s", repr(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _run_ai_tester_stream(
    session_id: int,
    user_content: str,
    model_str: str,
    db: AsyncSession,
    current_user: User,
    queue: asyncio.Queue,
):
    """后台执行 AI 评测师流式回复，通过队列推送 SSE 事件。"""
    try:
        # 通过服务层流式生成器获取 AI 回复
        async for event_type, data in AIService.stream_ai_tester_response(
            session_id=session_id,
            user_message=user_content,
            model_str=model_str,
            db=db,
            current_user=current_user,
        ):
            if event_type == "chunk":
                await queue.put({"type": "chunk", "content": data})
            elif event_type == "complete":
                await queue.put({
                    "type": "complete",
                    "user_message_id": data["user_message_id"],
                    "assistant_message_id": data["assistant_message_id"],
                })
            elif event_type == "error":
                await queue.put({"type": "error", "message": data})
    except Exception as e:
        logger.error("AI 评测师流式异常: %s", repr(e))
        await queue.put({"type": "error", "message": str(e)})
    finally:
        await queue.put(None)


# ======================================================================
# 消息评分
# ======================================================================


@router.put("/messages/{message_id}/rating", response_model=ResponseModel)
async def update_message_rating(
    message_id: int,
    body: AITesterMessageRatingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新消息评分（up / down / null 清除）。

    仅允许消息所属会话的创建者操作。
    """
    # 获取消息
    message = await db.get(AITesterMessage, message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在",
        )

    # 验证会话归属
    session = await db.get(AITesterSession, message.session_id)
    if session is None or session.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此消息",
        )

    # 验证评分值
    if body.rating is not None and body.rating not in ("up", "down"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="评分值无效，仅支持: up, down, null",
        )

    message.rating = body.rating
    await db.flush()

    return ResponseModel()
