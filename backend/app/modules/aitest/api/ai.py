"""
AI 测试接口模块

提供 AI 用例生成（含 SSE 流式输出）、评测、评审等功能的 RESTful 接口。
（模型配置和提示词配置 CRUD 已移至 config_center 模块）
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.deps import get_current_active_user
from app.modules.config_center.models.ai_model_config import AIModelConfig
from app.modules.aitest.models.ai_settings import AISettings
from app.modules.aitest.models.ai_task import AIGenerationTask, GeneratedTestCase
from app.modules.aitest.models.generated_case_item import GeneratedCaseItem
from app.modules.config_center.models.prompt_config import PromptConfig
from app.common.models.user import User
from app.modules.aitest.schemas.ai import (
    AIGenerationRequest,
    AIReviseRequest,
    AIGenerationResponse,
    AIGenerationTaskSummary,
    AIModelConfigSummary,
    AIEvaluationRequest,
    AIEvaluationResponse,
    AIReportDetail,
    AIReportStats,
    AIReportSummary,
    AIReviewRequest,
    AIReviewResponse,
    AISettingsResponse,
    AISettingsUpdate,
    AITaskDetailResponse,
    FailedCaseItem,
    GeneratedTestCaseItem,
    ModuleStatItem,
    PromptConfigSummary,
)
from app.common.schemas.common import ResponseModel, PaginatedResponse, PaginationMeta
from app.modules.aitest.schemas.project import ProjectSummary
from app.common.models.project import Project
from sqlalchemy import func as sql_func

from pydantic import BaseModel, Field

from app.modules.aitest.services.ai_service import AIService
from app.modules.aitest.utils import (
    compute_pass_rate,
    compute_case_stats,
    compute_module_stats,
    compute_failed_cases,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI智能测试"])

# 用于 SSE 流式输出的队列存储：{task_id: asyncio.Queue}
_stream_queues: dict[str, asyncio.Queue] = {}


# ======================================================================
# 辅助函数
# ======================================================================

async def _get_task_or_404(
    task_id: str,
    db: AsyncSession,
) -> AIGenerationTask:
    """获取任务，不存在则 404"""
    stmt = (
        select(AIGenerationTask)
        .where(AIGenerationTask.task_id == task_id)
        .options(
            joinedload(AIGenerationTask.generated_test_cases),
        )
    )
    result = await db.execute(stmt)
    task = result.scalars().first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    return task


# 优先级中文映射
_PRIORITY_MAP = {
    "高": "P1", "中": "P2", "低": "P3",
    "p0": "P0", "p1": "P1", "p2": "P2", "p3": "P3",
    "P0": "P0", "P1": "P1", "P2": "P2", "P3": "P3",
}
_HEADER_ALIASES = {
    "编号": "case_id", "id": "case_id", "序号": "case_id",
    "模块": "module",
    "标题": "title", "名称": "title", "用例标题": "title",
    "前置条件": "precondition", "前置": "precondition",
    "测试步骤": "test_steps", "步骤": "test_steps",
    "预期结果": "expected_result", "预期": "expected_result",
    "优先级": "priority", "优先": "priority", "等级": "priority",
}


def _normalize_priority(val: str) -> str:
    """将中文或其他格式的优先级映射为标准 P0-P3"""
    val = val.strip()
    if val in _PRIORITY_MAP:
        return _PRIORITY_MAP[val]
    # 尝试提取数字（如 "P0级" → "P0", "2（中）" → "P2"）
    import re as _re
    m = _re.search(r"(P[0-3])", val, _re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = _re.search(r"([0-3])", val)
    if m:
        return f"P{m.group(1)}"
    return "P2"


def _detect_column_order(header_cols: list[str]) -> dict[str, int]:
    """通过表头识别列顺序"""
    order: dict[str, int] = {}
    for i, h in enumerate(header_cols):
        h_clean = h.strip().lower()
        for alias, field in _HEADER_ALIASES.items():
            if alias.lower() in h_clean or h_clean in alias.lower():
                if field not in order:
                    order[field] = i
                    break
    return order


async def _parse_test_cases_from_text(text: str) -> list[dict[str, str]]:
    """
    从 AI 返回的 Markdown 表格文本中解析测试用例。

    支持通过表头自动识别列顺序，避免因列顺序不同导致解析错位。
    返回列表，每个元素为 {case_id, module, title, precondition, test_steps, expected_result, priority}
    """
    cases: list[dict[str, str]] = []
    lines = text.strip().split("\n")

    # 默认列顺序（7列标准顺序）
    default_cols = ["case_id", "module", "title", "precondition", "test_steps", "expected_result", "priority"]
    col_order: dict[str, int] = {}
    started_data = False

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        if line.count("|") < 3:
            continue

        cols = [c.strip() for c in line.split("|")]
        if cols and cols[0] == "":
            cols = cols[1:]
        if cols and cols[-1] == "":
            cols = cols[:-1]

        if len(cols) < 4:
            continue

        # 跳过分隔行
        if any("—" in c or "-" * 3 in c for c in cols if len(c) > 0):
            continue

        # 尝试从表头检测列顺序
        if not started_data:
            detected = _detect_column_order(cols)
            if detected and len(detected) >= 4:
                col_order = detected
                started_data = True
                continue
            # 如果第一行没有表头特征，使用默认顺序
            started_data = True

        # 恢复被转义的管道符
        cols = [c.replace("\\|", "|") for c in cols]

        def _get(field: str, idx: int) -> str:
            i = col_order.get(field, idx)
            return cols[i] if i < len(cols) else ""

        case: dict[str, str] = {
            "case_id": _get("case_id", 0),
            "module": _get("module", 1),
            "title": _get("title", 2),
            "precondition": _get("precondition", 3),
            "test_steps": _get("test_steps", 4),
            "expected_result": _get("expected_result", 5),
            "priority": _normalize_priority(_get("priority", 6)),
        }

        if case["case_id"] and any(c.isdigit() for c in case["case_id"]):
            cases.append(case)

    return cases


async def _save_test_cases_to_db(
    task: AIGenerationTask,
    text: str,
    db: AsyncSession,
) -> list[GeneratedTestCase]:
    """将解析出的用例保存到数据库"""
    cases_data = await _parse_test_cases_from_text(text)
    saved_cases: list[GeneratedTestCase] = []

    for case_data in cases_data:
        # 确保 priority 不超过数据库列长度（VARCHAR(5)）
        priority = case_data.get("priority", "P2") or "P2"
        if len(priority) > 5:
            priority = _normalize_priority(priority) if len(priority) > 5 else priority[:5]

        test_case = GeneratedTestCase(
            task_id=task.id,
            case_id=case_data["case_id"],
            title=case_data["title"],
            module=case_data["module"],
            priority=priority,
            precondition=case_data["precondition"],
            test_steps=case_data["test_steps"],
            expected_result=case_data["expected_result"],
        )
        db.add(test_case)
        saved_cases.append(test_case)

    await db.flush()
    return saved_cases


# ======================================================================
# 生成任务
# ======================================================================

@router.post("/generate", response_model=ResponseModel[AIGenerationResponse])
async def create_generation_task(
    body: AIGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建 AI 用例生成任务

    返回 task_id 并立即开始异步生成。通过 SSE 接口获取流式输出内容。
    """
    # 生成唯一任务 ID
    task_id = f"AI-{uuid.uuid4().hex[:8].upper()}"

    # 简化标题：取需求前 30 个字符
    title = body.requirement_text.strip()[:30]
    if len(body.requirement_text.strip()) > 30:
        title += "..."

    # 如果未指定模型/提示词，使用默认配置
    writer_model_config_id = body.writer_model_config_id
    writer_prompt_config_id = body.writer_prompt_config_id
    reviewer_model_config_id = body.reviewer_model_config_id
    reviewer_prompt_config_id = body.reviewer_prompt_config_id

    if writer_model_config_id is None:
        # 查找默认的 writer 模型
        stmt = (
            select(AIModelConfig)
            .where(AIModelConfig.role == "writer")
            .where(AIModelConfig.is_active.is_(True))
            .limit(1)
        )
        result = await db.execute(stmt)
        default_model = result.scalar_one_or_none()
        if default_model:
            writer_model_config_id = default_model.id

    if writer_prompt_config_id is None:
        # 查找默认的 writer 提示词
        stmt = (
            select(PromptConfig)
            .where(PromptConfig.prompt_type == "writer")
            .where(PromptConfig.is_active.is_(True))
            .limit(1)
        )
        result = await db.execute(stmt)
        default_prompt = result.scalar_one_or_none()
        if default_prompt:
            writer_prompt_config_id = default_prompt.id

    if body.enable_auto_review and reviewer_model_config_id is None:
        # 如果没有指定评审模型，使用编写模型作为默认（保持整个流程使用同一个模型）
        if writer_model_config_id:
            reviewer_model_config_id = writer_model_config_id
        else:
            # 查找默认的 reviewer 模型
            stmt = (
                select(AIModelConfig)
                .where(AIModelConfig.role == "reviewer")
                .where(AIModelConfig.is_active.is_(True))
                .limit(1)
            )
            result = await db.execute(stmt)
            default_model = result.scalar_one_or_none()
            if default_model:
                reviewer_model_config_id = default_model.id

    if body.enable_auto_review and reviewer_prompt_config_id is None:
        stmt = (
            select(PromptConfig)
            .where(PromptConfig.prompt_type == "reviewer")
            .where(PromptConfig.is_active.is_(True))
            .limit(1)
        )
        result = await db.execute(stmt)
        default_prompt = result.scalar_one_or_none()
        if default_prompt:
            reviewer_prompt_config_id = default_prompt.id

    # 自动检测 analyzer 提示词
    analyzer_prompt_config_id = body.analyzer_prompt_config_id
    if analyzer_prompt_config_id is None:
        stmt = (
            select(PromptConfig)
            .where(PromptConfig.prompt_type == "analyzer")
            .where(PromptConfig.is_active.is_(True))
            .limit(1)
        )
        result = await db.execute(stmt)
        default_prompt = result.scalar_one_or_none()
        if default_prompt:
            analyzer_prompt_config_id = default_prompt.id

    # 自动检测 improver 提示词（仅在启用自动评审时有效）
    improver_prompt_config_id = body.improver_prompt_config_id
    if body.enable_auto_review and improver_prompt_config_id is None:
        stmt = (
            select(PromptConfig)
            .where(PromptConfig.prompt_type == "improver")
            .where(PromptConfig.is_active.is_(True))
            .limit(1)
        )
        result = await db.execute(stmt)
        default_prompt = result.scalar_one_or_none()
        if default_prompt:
            improver_prompt_config_id = default_prompt.id

    # 创建数据库记录
    task = AIGenerationTask(
        task_id=task_id,
        title=title,
        requirement_text=body.requirement_text,
        status="pending",
        progress=0,
        pipeline_type=body.pipeline_type,
        output_mode=body.output_mode,
        project_id=body.project_id,
        writer_model_config_id=writer_model_config_id,
        writer_prompt_config_id=writer_prompt_config_id,
        reviewer_model_config_id=reviewer_model_config_id,
        reviewer_prompt_config_id=reviewer_prompt_config_id,
        analyzer_prompt_config_id=analyzer_prompt_config_id,
        improver_prompt_config_id=improver_prompt_config_id,
        created_by=current_user.id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    # 创建 SSE 队列
    queue: asyncio.Queue = asyncio.Queue()
    _stream_queues[task_id] = queue

    # 提交事务，确保后台管线能查询到该任务
    await db.commit()

    # 读取兜底 API Key：优先 DB 设置，回退到环境变量（LangGraph 和 AutoGen 管线需要）
    fallback_key = ""
    if body.pipeline_type in ("langgraph", "autogen"):
        try:
            settings_stmt = select(AISettings).limit(1)
            settings_result = await db.execute(settings_stmt)
            settings = settings_result.scalar_one_or_none()
            if settings and settings.api_key:
                fallback_key = settings.api_key
        except Exception:
            pass

        if not fallback_key and writer_model_config_id:
            mt_stmt = select(AIModelConfig.model_type).where(AIModelConfig.id == writer_model_config_id)
            mt_result = await db.execute(mt_stmt)
            model_type = mt_result.scalar_one_or_none()
            if model_type:
                from app.config import settings as app_settings
                env_key_map = {
                    "deepseek": app_settings.DEEPSEEK_API_KEY,
                    "openai": app_settings.OPENAI_API_KEY,
                    "qwen": app_settings.QWEN_API_KEY,
                    "siliconflow": app_settings.SILICONFLOW_API_KEY,
                    "anthropic": app_settings.ANTHROPIC_API_KEY,
                }
                fallback_key = env_key_map.get(model_type, "")

    # 获取继续生成的阶段
    continue_from_stage = body.continue_from_stage or "analyze"
    
    # 启动后台生成任务（使用独立 session，不传请求作用域 db）
    if body.pipeline_type == "autogen":
        from app.modules.aitest.graph.autogen_pipeline import run_autogen_pipeline
        asyncio.create_task(
            run_autogen_pipeline(
                task.id, body.enable_auto_review, queue,
                fallback_api_key=fallback_key,
                continue_from_stage=continue_from_stage,
            )
        )
    elif body.pipeline_type == "langgraph":
        from app.modules.aitest.graph.sse_stream import run_langgraph_pipeline
        asyncio.create_task(
            run_langgraph_pipeline(
                task.id, body.enable_auto_review, queue,
                fallback_api_key=fallback_key,
                continue_from_stage=continue_from_stage,
            )
        )
    else:
        asyncio.create_task(
            _run_generation_pipeline(task.id, body.enable_auto_review, queue, continue_from_stage)
        )

    return ResponseModel(
        data=AIGenerationResponse(task_id=task_id, status="pending"),
    )


async def _run_generation_pipeline(
    task_db_id: int,
    enable_auto_review: bool,
    queue: asyncio.Queue,
    continue_from_stage: str = "analyze",
):
    """
    后台执行生成 -> 解析 -> 评审 -> 改进 完整管线。
    使用独立数据库 session，不受 HTTP 请求生命周期影响。
    
    :param continue_from_stage: 从哪个阶段开始继续（analyze/writing/review/revise）
    """
    from app.database import async_session_factory

    async def _log(level: str, message: str):
        """推送日志事件到 SSE"""
        await queue.put({"type": "log", "message": message, "level": level})

    async with async_session_factory() as db:
        try:
            # ---- 在独立 session 中重新查询任务 ----
            stmt = (
                select(AIGenerationTask)
                .where(AIGenerationTask.id == task_db_id)
                .options(
                    joinedload(AIGenerationTask.writer_model_config),
                    joinedload(AIGenerationTask.writer_prompt_config),
                    joinedload(AIGenerationTask.reviewer_model_config),
                    joinedload(AIGenerationTask.reviewer_prompt_config),
                    joinedload(AIGenerationTask.analyzer_prompt_config),
                    joinedload(AIGenerationTask.improver_prompt_config),
                )
            )
            result = await db.execute(stmt)
            task = result.scalars().first()
            if task is None:
                raise RuntimeError("任务不存在")

            await _log("info", "📋 任务已创建，准备开始生成...")

            stages_to_skip = []
            if continue_from_stage == "writing":
                stages_to_skip = ["analyze"]
                await _log("info", "⏭️ 跳过需求分析阶段")
            elif continue_from_stage == "review":
                stages_to_skip = ["analyze", "writing"]
                await _log("info", "⏭️ 跳过需求分析和用例编写阶段")
            elif continue_from_stage == "revise":
                stages_to_skip = ["analyze", "writing", "review"]
                await _log("info", "⏭️ 跳过需求分析、用例编写和评审阶段")

            # ---- 阶段 1：需求分析 ----
            if "analyze" not in stages_to_skip:
                task.status = "analyzing"
                await db.flush()
                await queue.put({"type": "status", "status": "analyzing", "progress": 5})
                await _log("info", "🔍 AI 正在分析需求...")

                analysis_parts: list[str] = []

                def on_analysis_chunk(chunk_text: str):
                    analysis_parts.append(chunk_text)
                    asyncio.ensure_future(queue.put({
                        "type": "chunk",
                        "stage": "analyze",
                        "content": chunk_text,
                    }))

                await AIService.analyze_requirement(task, db, on_chunk=on_analysis_chunk)
                await _log("success", "✅ 需求分析完成")
            else:
                await _log("info", "✅ 需求分析已跳过")

            # ---- 阶段 2：用例编写 ----
            if "writing" not in stages_to_skip:
                task.status = "generating"
                task.progress = 25
                await db.flush()
                await queue.put({"type": "status", "status": "generating", "progress": 25})
                await _log("info", "✏️ AI 正在编写测试用例...")

            # 收集生成内容
            content_parts: list[str] = []
            generated_text = ""
            last_chunk_log = 0

            # 流式生成回调
            def on_chunk(chunk_text: str):
                nonlocal last_chunk_log
                content_parts.append(chunk_text)
                asyncio.ensure_future(queue.put({
                    "type": "chunk",
                    "content": chunk_text,
                }))

            # 执行生成
            generated_text = await AIService.generate_test_cases_stream(
                task, db, on_chunk=on_chunk,
            )
            full_content = generated_text

            # 保存完整生成内容
            task.generated_content = {"text": full_content}

            # ---- 解析并保存用例 ----
            saved_cases = await _save_test_cases_to_db(task, full_content, db)
            task.progress = 50
            await db.flush()
            await _log("success", f"📊 已解析 {len(saved_cases)} 条测试用例")

            # ---- 创建 GeneratedCaseItem 记录（供「保存到用例库」使用） ----
            for tc in saved_cases:
                case_item = GeneratedCaseItem(
                    task_id=task.id,
                    title=tc.title,
                    priority=tc.priority,
                    module=tc.module,
                    precondition=tc.precondition,
                    test_steps=tc.test_steps,
                    expected_result=tc.expected_result,
                    status="adopted",
                    sort_order=0,
                )
                db.add(case_item)
            await db.flush()

            # 推送解析完成事件
            cases_for_sse = [
                {
                    "case_id": c.case_id,
                    "module": c.module or "",
                    "title": c.title,
                    "precondition": c.precondition or "",
                    "test_steps": c.test_steps or "",
                    "expected_result": c.expected_result or "",
                    "priority": c.priority,
                    "status": c.status,
                }
                for c in saved_cases
            ]
            await queue.put({
                "type": "cases",
                "cases": cases_for_sse,
                "progress": 50,
            })

            # ---- 自动评审（可选） ----
            if enable_auto_review and "review" not in stages_to_skip:
                # 如果没有评审模型，使用编写模型
                reviewer_model = task.reviewer_model_config or task.writer_model_config
                if reviewer_model:
                    task.reviewer_model_config = reviewer_model
                    task.status = "reviewing"
                    task.progress = 60
                    await db.flush()
                    await queue.put({"type": "status", "status": "reviewing", "progress": 60})
                    await _log("info", "📋 AI 正在进行评审...")

                    review_parts: list[str] = []

                    def on_review_chunk(chunk_text: str):
                        review_parts.append(chunk_text)
                        asyncio.ensure_future(queue.put({
                            "type": "review_chunk",
                            "content": chunk_text,
                        }))

                    review_feedback = await AIService.review_test_cases_stream(
                        task, full_content, db, on_chunk=on_review_chunk,
                    )
                    task.review_feedback = review_feedback
                    task.progress = 80
                    await db.flush()
                    await _log("success", "✅ AI 评审完成")

                    await queue.put({
                        "type": "review_complete",
                        "feedback": review_feedback,
                        "progress": 80,
                    })
            elif "review" in stages_to_skip:
                await _log("info", "✅ 评审阶段已跳过")

            # ---- 根据评审意见改进（可选） ----
            if "revise" not in stages_to_skip:
                if enable_auto_review and task.review_feedback and task.review_feedback.strip():
                    task.status = "revising"
                    task.progress = 85
                    await db.flush()
                    await queue.put({"type": "status", "status": "revising", "progress": 85})
                    await _log("info", "🔄 AI 正在根据评审意见改进...")

                    revise_parts: list[str] = []

                    def on_revise_chunk(chunk_text: str):
                        revise_parts.append(chunk_text)
                        asyncio.ensure_future(queue.put({
                            "type": "revise_chunk",
                            "content": chunk_text,
                        }))

                    revised_text = await AIService.revise_test_cases_based_on_review(
                        task, full_content, task.review_feedback, db,
                        on_chunk=on_revise_chunk,
                    )
                    task.final_content = {"text": revised_text}
                    task.progress = 95
                    await db.flush()
                    await _log("success", "✅ AI 改进完成")

                    await queue.put({
                        "type": "revise_complete",
                        "content": revised_text,
                        "progress": 95,
                    })

                    # 解析修订后的用例并推送 cases 事件
                    try:
                        revised_cases = await _parse_test_cases_from_text(revised_text)
                        if revised_cases:
                            await queue.put({
                                "type": "cases",
                                "cases": revised_cases,
                                "progress": 95,
                            })
                            await _log("success", f"📊 修订完成，共 {len(revised_cases)} 条用例")
                    except Exception:
                        await _log("warning", "解析修订后的用例失败")
            else:
                await _log("info", "✅ 改进阶段已跳过")

            # ---- 完成 ----
            task.status = "completed"
            task.progress = 100
            from datetime import datetime, timezone
            task.completed_at = datetime.now(timezone.utc)
            await db.flush()
            await _log("success", "🎉 用例生成完成")

            await queue.put({
                "type": "complete",
                "status": "completed",
                "progress": 100,
            })

            await db.commit()

        except Exception as e:
            logger.error("生成任务异常: %s", repr(e))
            try:
                task.status = "failed"
                task.error_message = str(e)
                await db.flush()
            except Exception:
                pass

            await queue.put({
                "type": "error",
                "message": str(e),
            })
            await queue.put({
                "type": "log",
                "message": f"❌ 生成失败: {str(e)}",
                "level": "error",
            })
            try:
                await db.rollback()
            except Exception:
                pass
        finally:
            # 标记队列已结束
            await queue.put(None)


@router.get("/generate/{task_id}/stream")
async def stream_generation(task_id: str):
    """
    SSE 流式获取生成内容

    通过 Server-Sent Events 实时推送：
    - type: log          — 实时日志消息
    - type: chunk        — 普通文本块
    - type: cases        — 解析完成的用例列表
    - type: status       — 状态更新
    - type: review_chunk — 评审文本块
    - type: review_complete — 评审完成
    - type: revise_chunk — 改进文本块
    - type: revise_complete — 改进完成
    - type: complete     — 全部完成
    - type: error        — 异常
    """

    if task_id not in _stream_queues:
        # 如果队列不存在，可能有延迟，等待 3 秒
        for _ in range(6):
            await asyncio.sleep(0.5)
            if task_id in _stream_queues:
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务流式队列不存在",
            )

    queue = _stream_queues[task_id]

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                if event is None:
                    # 结束信号
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            logger.info("SSE 连接被客户端断开: task_id=%s", task_id)
        except Exception as e:
            logger.error("SSE 异常: %s", repr(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # 清理队列
            _stream_queues.pop(task_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ======================================================================
# 任务列表与详情
# ======================================================================

@router.get("/tasks", response_model=ResponseModel[list[AIGenerationTaskSummary]])
async def list_generation_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取生成任务列表

    按创建时间倒序返回当前用户的所有生成任务。
    """
    stmt = (
        select(AIGenerationTask)
        .where(AIGenerationTask.created_by == current_user.id)
        .order_by(AIGenerationTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return ResponseModel(
        data=[AIGenerationTaskSummary.model_validate(t) for t in tasks],
    )


@router.get("/tasks/{task_id}", response_model=ResponseModel[AITaskDetailResponse])
async def get_task_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取任务详情

    包含生成的完整用例列表。
    """
    task = await _get_task_or_404(task_id, db)

    return ResponseModel(
        data=AITaskDetailResponse(
            id=task.id,
            task_id=task.task_id,
            title=task.title,
            status=task.status,
            progress=task.progress,
            requirement_text=task.requirement_text,
            output_mode=task.output_mode,
            project_id=task.project_id,
            writer_model_config_id=task.writer_model_config_id,
            reviewer_model_config_id=task.reviewer_model_config_id,
            writer_prompt_config_id=task.writer_prompt_config_id,
            reviewer_prompt_config_id=task.reviewer_prompt_config_id,
            analyzer_prompt_config_id=task.analyzer_prompt_config_id,
            improver_prompt_config_id=task.improver_prompt_config_id,
            created_by=task.created_by,
            generated_content=task.generated_content,
            review_feedback=task.review_feedback,
            final_content=task.final_content,
            error_message=task.error_message,
            saved_to_library=task.saved_to_library or False,
            created_at=task.created_at,
            completed_at=task.completed_at,
            test_cases=[
                GeneratedTestCaseItem.model_validate(tc)
                for tc in task.generated_test_cases
            ],
        ),
    )


# ======================================================================
# AI 评测
# ======================================================================

@router.post("/evaluate", response_model=ResponseModel[AIEvaluationResponse])
async def evaluate_test_cases(
    body: AIEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    AI 评测测试用例

    根据选定的模型和提示词对用例列表进行综合评分。
    """
    # 获取模型配置
    stmt = select(AIModelConfig).where(AIModelConfig.id == body.model_config_id)
    result = await db.execute(stmt)
    model_config = result.scalar_one_or_none()
    if model_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型配置不存在",
        )

    # 获取提示词配置
    stmt = select(PromptConfig).where(PromptConfig.id == body.prompt_config_id)
    result = await db.execute(stmt)
    prompt_config = result.scalar_one_or_none()
    if prompt_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词配置不存在",
        )

    evaluation = await AIService.evaluate_test_cases(
        body.test_cases, model_config, prompt_config,
    )

    return ResponseModel(
        data=AIEvaluationResponse(
            overall_score=evaluation.get("overall_score", 0),
            issues=evaluation.get("issues", []),
            improvements=evaluation.get("improvements", []),
            detail=evaluation.get("detail", ""),
        ),
    )


# ======================================================================
# AI 评审
# ======================================================================

@router.post("/review", response_model=ResponseModel[AIReviewResponse])
async def review_test_cases(
    body: AIReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    AI 评审测试用例

    对已生成的用例进行评审，返回评审反馈。
    """
    task = await _get_task_or_404(body.task_id, db)

    # 重新加载含关系的 task
    stmt = (
        select(AIGenerationTask)
        .where(AIGenerationTask.id == task.id)
        .options(
            joinedload(AIGenerationTask.reviewer_model_config),
            joinedload(AIGenerationTask.reviewer_prompt_config),
        )
    )
    result = await db.execute(stmt)
    full_task = result.scalars().first()

    if full_task is None or full_task.reviewer_model_config is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未配置评审模型",
        )

    feedback = await AIService.review_test_cases(
        full_task, body.test_cases, db,
    )

    # 保存评审反馈
    task.review_feedback = feedback
    await db.flush()

    return ResponseModel(
        data=AIReviewResponse(
            task_id=body.task_id,
            feedback=feedback,
            status="completed",
        ),
    )


# ======================================================================
# 获取配置列表（用于前端下拉选择）
# ======================================================================

@router.get("/models", response_model=ResponseModel[list[AIModelConfigSummary]])
async def list_ai_models(
    role: str | None = Query(None, description="按角色筛选（writer/reviewer）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取 AI 模型配置列表

    可选按角色（writer/reviewer）筛选，仅返回启用的模型。
    """
    stmt = select(AIModelConfig).where(AIModelConfig.is_active.is_(True))
    if role:
        stmt = stmt.where(AIModelConfig.role == role)
    stmt = stmt.order_by(AIModelConfig.id.asc())

    result = await db.execute(stmt)
    models = result.scalars().all()

    return ResponseModel(
        data=[AIModelConfigSummary.model_validate(m) for m in models],
    )


@router.get("/prompts", response_model=ResponseModel[list[PromptConfigSummary]])
async def list_prompt_configs(
    prompt_type: str | None = Query(None, description="按类型筛选（writer/reviewer）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取提示词配置列表

    可选按类型（writer/reviewer）筛选，仅返回启用的提示词。
    """
    stmt = select(PromptConfig).where(PromptConfig.is_active.is_(True))
    if prompt_type:
        stmt = stmt.where(PromptConfig.prompt_type == prompt_type)
    stmt = stmt.order_by(PromptConfig.id.asc())

    result = await db.execute(stmt)
    prompts = result.scalars().all()

    return ResponseModel(
        data=[PromptConfigSummary.model_validate(p) for p in prompts],
    )


@router.get("/projects", response_model=ResponseModel[list[ProjectSummary]])
async def list_projects_for_ai(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取项目列表（用于 AI 生成页面的下拉选择）

    按创建时间倒序返回。
    """
    stmt = select(Project).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()

    return ResponseModel(
        data=[ProjectSummary.model_validate(p) for p in projects],
    )


# ======================================================================
# AI 测试报告
# ======================================================================
# 报告相关（使用 utils 模块中的工具函数）
# ======================================================================


@router.get("/reports", response_model=PaginatedResponse)
async def list_ai_reports(
    project_id: int | None = Query(None, description='项目ID筛选'),
    start_date: str | None = Query(None, description='开始日期（YYYY-MM-DD）'),
    end_date: str | None = Query(None, description='结束日期（YYYY-MM-DD）'),
    page: int = Query(1, ge=1, description='页码'),
    page_size: int = Query(20, ge=1, le=100, description='每页条数'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    AI 测试报告列表

    查询已完成（含失败/取消）的 AI 生成任务，聚合用例统计数据。
    支持按项目和时间范围筛选。
    """
    # 基础查询：只查询已完成的任务
    stmt = (
        select(AIGenerationTask)
        .options(
            joinedload(AIGenerationTask.generated_test_cases),
        )
    )

    # 按项目筛选
    if project_id is not None:
        stmt = stmt.where(AIGenerationTask.project_id == project_id)

    # 按时间范围筛选
    if start_date:
        stmt = stmt.where(AIGenerationTask.created_at >= start_date)
    if end_date:
        stmt = stmt.where(AIGenerationTask.created_at <= end_date + " 23:59:59")

    # 统计总数
    count_stmt = select(sql_func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # 排序并分页
    stmt = stmt.order_by(AIGenerationTask.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    tasks = result.unique().scalars().all()

    # 聚合报告数据
    reports: list[AIReportSummary] = []
    for task in tasks:
        cases = task.generated_test_cases
        stats = compute_case_stats(cases)

        # 获取项目名称
        project_name = ''
        if task.project_id:
            proj_stmt = select(Project).where(Project.id == task.project_id)
            proj_result = await db.execute(proj_stmt)
            proj = proj_result.scalar_one_or_none()
            if proj:
                project_name = proj.name

        reports.append(AIReportSummary(
            id=task.id,
            task_id=task.task_id,
            title=task.title,
            project_name=project_name,
            status=task.status,
            total_cases=stats['total'],
            passed=stats['passed'],
            failed=stats['failed'],
            blocked=stats['blocked'],
            pass_rate=stats['pass_rate'],
            created_at=str(task.created_at) if task.created_at else '',
        ))

    return PaginatedResponse(
        data=[r.model_dump() for r in reports],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, (total + page_size - 1) // page_size),
        ),
    )


@router.get("/reports/{task_id}", response_model=ResponseModel[AIReportDetail])
async def get_report_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    AI 测试报告详情

    包含任务概要、统计数据和全部用例明细。
    """
    task = await _get_task_or_404(task_id, db)
    cases = task.generated_test_cases

    # 使用工具函数计算统计
    stats = compute_case_stats(cases)

    # 获取项目名称
    project_name = ''
    if task.project_id:
        proj_stmt = select(Project).where(Project.id == task.project_id)
        proj_result = await db.execute(proj_stmt)
        proj = proj_result.scalar_one_or_none()
        if proj:
            project_name = proj.name

    # 模块分布统计
    module_stats = [
        ModuleStatItem(**item) for item in compute_module_stats(cases)
    ]

    # 失败用例
    failed_cases = [
        FailedCaseItem(
            case_id=c.case_id,
            title=c.title,
            module=c.module or '',
            priority=c.priority,
            reason=f"状态为「{c.status}」",
            status=c.status,
        )
        for c in cases if c.status != 'approved'
    ]

    # 概要
    summary = AIReportSummary(
        id=task.id,
        task_id=task.task_id,
        title=task.title,
        project_name=project_name,
        status=task.status,
        total_cases=stats['total'],
        passed=stats['passed'],
        failed=stats['failed'],
        blocked=stats['blocked'],
        pass_rate=stats['pass_rate'],
        created_at=str(task.created_at) if task.created_at else '',
    )

    # 统计数据
    report_stats = AIReportStats(
        total_cases=stats['total'],
        passed=stats['passed'],
        failed=stats['failed'],
        blocked=stats['blocked'],
        pass_rate=stats['pass_rate'],
        module_stats=module_stats,
        failed_cases=failed_cases,
    )

    # 全部用例明细
    case_items = [
        GeneratedTestCaseItem.model_validate(c) for c in cases
    ]

    return ResponseModel(
        data=AIReportDetail(
            summary=summary,
            stats=report_stats,
            cases=case_items,
        ),
    )


@router.get("/reports/{task_id}/stats", response_model=ResponseModel[AIReportStats])
async def get_report_stats(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    AI 测试报告统计数据

    仅返回统计信息（不含用例明细），用于弹窗等轻量展示。
    """
    task = await _get_task_or_404(task_id, db)
    cases = task.generated_test_cases

    # 使用工具函数计算统计
    stats = compute_case_stats(cases)
    module_stats = [ModuleStatItem(**item) for item in compute_module_stats(cases)]
    failed_cases = [
        FailedCaseItem(
            case_id=c.case_id,
            title=c.title,
            module=c.module or '',
            priority=c.priority,
            reason=f"状态为「{c.status}」",
            status=c.status,
        )
        for c in cases if c.status != 'approved'
    ]

    return ResponseModel(
        data=AIReportStats(
            total_cases=stats['total'],
            passed=stats['passed'],
            failed=stats['failed'],
            blocked=stats['blocked'],
            pass_rate=stats['pass_rate'],
            module_stats=module_stats,
            failed_cases=failed_cases,
        ),
    )


@router.get("/reports/{task_id}/module-stats", response_model=ResponseModel[list[ModuleStatItem]])
async def get_report_module_stats(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    报告模块分布统计

    按 module 字段分组统计用例通过/失败情况。
    """
    task = await _get_task_or_404(task_id, db)
    cases = task.generated_test_cases

    module_stats = [ModuleStatItem(**item) for item in compute_module_stats(cases)]

    return ResponseModel(data=module_stats)


# ======================================================================
# AI 智能模式配置
# ======================================================================


@router.get("/settings", response_model=ResponseModel[AISettingsResponse])
async def get_ai_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取 AI 智能模式配置

    返回当前生效的配置，记录不存在时返回默认值。
    """
    stmt = select(AISettings).limit(1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    if settings is None:
        # 没有配置时返回默认值
        return ResponseModel(
            data=AISettingsResponse(
                ai_mode_enabled=True,
                auto_trigger_on_requirement_change=False,
                auto_generate_report=False,
                auto_retest_on_failure=False,
                notification_config=None,
                provider='',
                api_key='',
                model_name='',
                temperature=0.7,
                context_window=128000,
                max_input_tokens=128000,
                max_output_tokens=4096,
                retry_count=3,
                timeout_seconds=120,
                concurrency=1,
                rate_limit_rpm=60,
                custom_prompt_template=None,
                id=0,
                created_by=current_user.id,
                created_at='',
                updated_at='',
            ),
        )

    # API Key 脱敏
    api_key = settings.api_key or ''
    if api_key and len(api_key) > 8:
        api_key = api_key[:4] + '****' + api_key[-4:]
    elif api_key:
        api_key = '****'

    return ResponseModel(
        data=AISettingsResponse(
            ai_mode_enabled=settings.ai_mode_enabled,
            auto_trigger_on_requirement_change=settings.auto_trigger_on_requirement_change,
            auto_generate_report=settings.auto_generate_report,
            auto_retest_on_failure=settings.auto_retest_on_failure,
            notification_config=settings.notification_config,
            provider=settings.provider or '',
            api_key=api_key,
            model_name=settings.model_name or '',
            temperature=settings.temperature or 0.7,
            context_window=settings.context_window or 128000,
            max_input_tokens=settings.max_input_tokens or 128000,
            max_output_tokens=settings.max_output_tokens or 4096,
            retry_count=settings.retry_count or 3,
            timeout_seconds=settings.timeout_seconds or 120,
            concurrency=settings.concurrency or 1,
            rate_limit_rpm=settings.rate_limit_rpm or 60,
            custom_prompt_template=settings.custom_prompt_template,
            id=settings.id,
            created_by=settings.created_by,
            created_at=str(settings.created_at) if settings.created_at else '',
            updated_at=str(settings.updated_at) if settings.updated_at else '',
        ),
    )


@router.put("/settings", response_model=ResponseModel[AISettingsResponse])
async def update_ai_settings(
    body: AISettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新 AI 智能模式配置

    仅更新提供的字段。如果当前没有配置记录，会自动创建一条新记录再更新。
    """
    stmt = select(AISettings).limit(1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    if settings is None:
        # 创建默认配置
        settings = AISettings(
            ai_mode_enabled=True,
            created_by=current_user.id,
        )
        db.add(settings)
        await db.flush()

    # 更新提供的字段
    update_data = body.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    await db.flush()
    await db.refresh(settings)

    # API Key 脱敏
    api_key = settings.api_key or ''
    if api_key and len(api_key) > 8:
        api_key = api_key[:4] + '****' + api_key[-4:]
    elif api_key:
        api_key = '****'

    return ResponseModel(
        data=AISettingsResponse(
            ai_mode_enabled=settings.ai_mode_enabled,
            auto_trigger_on_requirement_change=settings.auto_trigger_on_requirement_change,
            auto_generate_report=settings.auto_generate_report,
            auto_retest_on_failure=settings.auto_retest_on_failure,
            notification_config=settings.notification_config,
            provider=settings.provider or '',
            api_key=api_key,
            model_name=settings.model_name or '',
            temperature=settings.temperature or 0.7,
            context_window=settings.context_window or 128000,
            max_input_tokens=settings.max_input_tokens or 128000,
            max_output_tokens=settings.max_output_tokens or 4096,
            retry_count=settings.retry_count or 3,
            timeout_seconds=settings.timeout_seconds or 120,
            concurrency=settings.concurrency or 1,
            rate_limit_rpm=settings.rate_limit_rpm or 60,
            custom_prompt_template=settings.custom_prompt_template,
            id=settings.id,
            created_by=settings.created_by,
            created_at=str(settings.created_at) if settings.created_at else '',
            updated_at=str(settings.updated_at) if settings.updated_at else '',
        ),
    )


# ======================================================================
# 配置检查与连接测试
# ======================================================================


class _TestConnectionRequest(BaseModel):
    """测试 AI 连接请求"""
    provider: str = Field(..., description="模型类型（deepseek/qwen/siliconflow/openai/anthropic/other）")
    api_key: str = Field("", description="API Key（留空则使用环境变量）")
    base_url: str = Field("", description="API Base URL（留空则使用环境变量默认值）")
    model_name: str = Field(..., description="模型名称")
    max_tokens: int = Field(256, description="最大Token数")
    temperature: float = Field(0.7, description="温度参数")
    top_p: float = Field(0.9, description="Top P参数")
    test_message: str = Field("你好，请回复'好的'", description="测试消息内容")


@router.get("/config/check", response_model=ResponseModel)
async def check_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    检查 AI 模型配置和提示词配置是否存在且有效。

    返回各配置的启用状态和数量，用于前端判断是否可进行 AI 操作。
    """
    # 统计活跃的模型配置
    model_stmt = select(sql_func.count()).select_from(AIModelConfig).where(
        AIModelConfig.is_active.is_(True),
    )
    model_result = await db.execute(model_stmt)
    model_count = model_result.scalar() or 0

    # 统计活跃的提示词配置
    prompt_stmt = select(sql_func.count()).select_from(PromptConfig).where(
        PromptConfig.is_active.is_(True),
    )
    prompt_result = await db.execute(prompt_stmt)
    prompt_count = prompt_result.scalar() or 0

    return ResponseModel(
        data={
            "models_configured": model_count > 0,
            "prompts_configured": prompt_count > 0,
            "model_count": model_count,
            "prompt_count": prompt_count,
            "status": "ok" if model_count > 0 else "missing_models",
        },
    )


@router.post("/config/test-connection", response_model=ResponseModel)
async def test_ai_connection(
    body: _TestConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    测试 AI 模型连接的可用性。

    使用提供的模型参数发送简短的测试消息，验证 API 密钥和端点是否正确。
    返回连接状态和 AI 响应内容。
    """
    from app.common.utils.ai_client import AIClientFactory, AICompletionConfig
    from app.config import settings

    # 如果请求中未提供 API Key，从环境变量回退
    api_key = body.api_key
    if not api_key:
        env_key_map = {
            "deepseek": settings.DEEPSEEK_API_KEY,
            "openai": settings.OPENAI_API_KEY,
            "qwen": settings.QWEN_API_KEY,
            "siliconflow": settings.SILICONFLOW_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
        }
        fallback = env_key_map.get(body.provider, "")
        if fallback:
            logger.info("测试连接使用环境变量 API Key (provider=%s)", body.provider)
            api_key = fallback

    base_url = body.base_url
    if not base_url:
        env_url_map = {
            "deepseek": settings.DEEPSEEK_BASE_URL,
            "openai": settings.OPENAI_BASE_URL,
            "qwen": settings.QWEN_BASE_URL,
            "siliconflow": settings.SILICONFLOW_BASE_URL,
            "anthropic": settings.ANTHROPIC_BASE_URL,
        }
        base_url = env_url_map.get(body.provider, "")

    test_config = AICompletionConfig(
        api_key=api_key,
        base_url=base_url,
        model_name=body.model_name,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        top_p=body.top_p,
        max_retries=1,
        read_timeout=30,
    )

    test_messages: list[dict] = [
        {"role": "user", "content": body.test_message},
    ]

    try:
        provider = AIClientFactory.get_provider(body.provider)
        result = await provider.chat_complete(test_messages, test_config)

        return ResponseModel(
            data={
                "success": True,
                "message": "连接成功",
                "response": result.content[:200] if result.content else "",
                "model": result.model or body.model_name,
            },
        )
    except Exception as e:
        logger.warning("AI 连接测试失败: %s", repr(e))
        return ResponseModel(
            data={
                "success": False,
                "message": f"连接失败: {str(e)}",
                "response": None,
                "model": body.model_name,
            },
        )


# ======================================================================
# 文档上传（AI 生成输入）
# ======================================================================

from fastapi import UploadFile, File as FastAPIFile


def _decode_text(data: bytes) -> str:
    """自动检测编码并解码，优先 UTF-8，其次中文编码，最后逐字节回退"""
    for enc in ("utf-8", "gb18030", "gbk", "gb2312", "shift_jis", "big5", "utf-16"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


async def _extract_doc_text(content_bytes: bytes) -> str:
    """从旧版 .doc 二进制格式中提取文本

    按优先级尝试：
    1. antiword（跨平台，推荐）
    2. textutil（macOS 内置）
    3. olefile 原始数据回退
    """
    import subprocess

    # 策略 1：antiword（Linux/macOS，可靠）
    for cmd in ("antiword",):
        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                [cmd, "-m", "UTF-8.txt", "-"],  # 从 stdin 读取
                input=content_bytes,
                capture_output=True,
                timeout=30,
            )
            if proc.returncode == 0:
                text = proc.stdout.decode("utf-8", errors="replace").strip()
                if text:
                    return text
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        except Exception:
            continue

    # 策略 2：textutil（macOS 内置）
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            ["textutil", "-convert", "txt", "-stdin", "-stdout"],
            input=content_bytes,
            capture_output=True,
            timeout=30,
        )
        if proc.returncode == 0:
            text = proc.stdout.decode("utf-8", errors="replace").strip()
            if text:
                return text
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except Exception:
        pass

    # 策略 3：olefile 回退（提取 WordDocument 流中的原始文本）
    try:
        import olefile
        ole = olefile.OleFileIO(content_bytes)
        text_parts = []
        if ole.exists('WordDocument'):
            data = ole.openstream('WordDocument').read()
            # 尝试解码整个流
            raw = _decode_text(data)
            # 过滤掉明显的二进制垃圾，只保留可读文本行
            import re
            for line in raw.split('\n'):
                cleaned = re.sub(r'[^一-鿿　-〿＀-￯ -~ -ÿ]', '', line)
                cleaned = cleaned.strip()
                if len(cleaned) > 4:  # 忽略过短的垃圾片段
                    text_parts.append(cleaned)
        ole.close()
        if text_parts:
            return '\n'.join(text_parts)
    except Exception:
        pass

    return ""


@router.post("/generate/upload-doc", response_model=ResponseModel)
async def upload_generation_doc(
    file: UploadFile = FastAPIFile(..., description="上传的文档文件（PDF/Word/TXT）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    上传文档作为 AI 生成的输入。

    支持格式：.txt, .md, .pdf, .doc, .docx
    文件大小限制：10MB
    返回解析后的文本内容和文件名。
    """
    # 文件类型白名单
    ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".doc", ".docx"}
    import os

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型：{ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 大小限制 10MB
    MAX_SIZE = 10 * 1024 * 1024
    content_bytes = await file.read()
    if len(content_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小超过限制（最大 10MB）",
        )

    # 解析文本内容
    text_content = ""
    try:
        if ext in (".txt", ".md"):
            text_content = _decode_text(content_bytes)
        elif ext == ".pdf":
            try:
                import io
                from PyPDF2 import PdfReader
                pdf_file = io.BytesIO(content_bytes)
                reader = PdfReader(pdf_file)
                text_content = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
            except Exception:
                text_content = _decode_text(content_bytes)
        elif ext == ".docx":
            try:
                import io
                from docx import Document
                docx_file = io.BytesIO(content_bytes)
                doc = Document(docx_file)
                text_content = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                text_content = _decode_text(content_bytes)
        elif ext == ".doc":
            # 旧版 .doc 二进制格式，python-docx 不支持
            # 使用外部工具提取文本：antiword（跨平台）> textutil（macOS）> olefile 回退
            text_content = await _extract_doc_text(content_bytes)
            if not text_content.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法解析旧版 .doc 文件，请转换为 .docx 格式后重试",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("文档解析失败: %s", repr(e))
        # 只有 txt/md 文件才用二进制解码回退，其他格式抛出错误
        if ext in (".txt", ".md"):
            text_content = _decode_text(content_bytes)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法解析文件内容，请确保文件有效或转换为 .txt/.md 格式后重试",
            )

    return ResponseModel(
        data={
            "filename": file.filename,
            "content": text_content[:50000],  # 限制最大 50000 字符
            "size": len(content_bytes),
            "parsed": bool(text_content.strip()),
        },
    )


# ======================================================================
# 生成任务控制（取消/修订）
# ======================================================================


# ======================================================================
# 生成任务控制（取消/修订/删除/状态更新）
# ======================================================================


class TaskStatusUpdate(BaseModel):
    """任务状态更新请求"""
    status: str = Field(..., description="新状态")


@router.get("/generate/stats", response_model=ResponseModel)
async def get_generation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取 AI 生成统计

    返回总任务数、已完成数、总生成用例数等统计信息，用于仪表盘展示。
    """
    # 总任务数
    total_stmt = select(sql_func.count()).select_from(AIGenerationTask).where(
        AIGenerationTask.created_by == current_user.id,
    )
    total_result = await db.execute(total_stmt)
    total_tasks = total_result.scalar() or 0

    # 已完成任务数
    completed_stmt = select(sql_func.count()).select_from(AIGenerationTask).where(
        AIGenerationTask.created_by == current_user.id,
        AIGenerationTask.status == "completed",
    )
    completed_result = await db.execute(completed_stmt)
    completed_tasks = completed_result.scalar() or 0

    # 总生成用例数
    cases_stmt = (
        select(sql_func.count())
        .select_from(GeneratedTestCase)
        .join(AIGenerationTask, GeneratedTestCase.task_id == AIGenerationTask.id)
        .where(AIGenerationTask.created_by == current_user.id)
    )
    cases_result = await db.execute(cases_stmt)
    total_cases = cases_result.scalar() or 0

    return ResponseModel(data={
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "total_cases": total_cases,
    })


@router.get("/generate/tasks/{task_id}/results", response_model=ResponseModel)
async def get_generation_results(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取生成任务各阶段结果

    返回生成过程中各阶段的结果数据（生成内容、评审反馈、最终内容等）。
    """
    task = await _get_task_or_404(task_id, db)
    return ResponseModel(data={
        "generated_content": task.generated_content,
        "review_feedback": task.review_feedback,
        "final_content": task.final_content,
        "test_cases": [
            GeneratedTestCaseItem.model_validate(tc)
            for tc in task.generated_test_cases
        ],
    })


@router.delete("/generate/tasks/{task_id}", response_model=ResponseModel)
async def delete_generation_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除生成任务及其关联的用例

    物理删除任务记录及其生成的测试用例。
    """
    task = await _get_task_or_404(task_id, db)
    # 删除关联用例
    if task.generated_test_cases:
        for tc in task.generated_test_cases:
            await db.delete(tc)
    await db.delete(task)
    await db.flush()
    return ResponseModel(message="任务已删除")


class _BatchDeleteIds(BaseModel):
    """批量删除 ID 列表"""
    ids: list[int]


@router.post("/generate/tasks/batch-delete", response_model=ResponseModel)
async def batch_delete_generation_tasks(
    body: _BatchDeleteIds,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量删除生成任务（按主键 ID）"""
    stmt = (
        select(AIGenerationTask)
        .where(AIGenerationTask.id.in_(body.ids))
        .options(joinedload(AIGenerationTask.generated_test_cases))
    )
    result = await db.execute(stmt)
    tasks = result.unique().scalars().all()

    for task in tasks:
        if task.generated_test_cases:
            for tc in task.generated_test_cases:
                await db.delete(tc)
        await db.delete(task)

    await db.flush()
    return ResponseModel(message=f"已删除 {len(tasks)} 个任务")


@router.put("/generate/tasks/{task_id}/status", response_model=ResponseModel)
async def update_task_status(
    task_id: str,
    body: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新任务状态

    用于手动调整任务状态（如恢复失败的任务）。
    """
    task = await _get_task_or_404(task_id, db)
    task.status = body.status
    await db.flush()
    return ResponseModel(
        data={"task_id": task.task_id, "status": task.status},
        message="状态已更新",
    )


@router.post("/generate/{task_id}/cancel", response_model=ResponseModel)
async def cancel_generation_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    取消进行中的 AI 生成任务。

    仅允许对 pending/generating/reviewing/revising 状态的任务进行取消操作。
    """
    task = await _get_task_or_404(task_id, db)

    if task.status in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务已处于「{task.status}」状态，无法取消",
        )

    task.status = "cancelled"
    task.progress = 0
    await db.flush()

    return ResponseModel(message="任务已取消")


@router.post("/generate/{task_id}/revise", response_model=ResponseModel)
async def revise_generation_task(
    task_id: str,
    body: AIReviseRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    重新生成 AI 任务（复用已有需求重新生成）。

    允许对失败、已完成或待处理的任务进行重新生成，
    重置状态后自动启动生成管线。
    """
    # 使用 joinedload 预先加载 writer_model_config，避免懒加载错误
    stmt = (
        select(AIGenerationTask)
        .where(AIGenerationTask.task_id == task_id)
        .options(
            joinedload(AIGenerationTask.writer_model_config),
            joinedload(AIGenerationTask.generated_test_cases),
        )
    )
    result = await db.execute(stmt)
    task = result.scalars().first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    if task.status == "generating":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务正在生成中，请等待当前生成完成",
        )

    # 重置状态和进度
    task.status = "pending"
    task.progress = 0
    task.review_feedback = None
    task.final_content = None
    task.error_message = None
    task.completed_at = None
    
    # 更新管线类型为用户当前选择的类型
    if body.pipeline_type:
        task.pipeline_type = body.pipeline_type

    # 清除已生成的用例
    if task.generated_test_cases:
        for tc in task.generated_test_cases:
            await db.delete(tc)

    # 保存当前任务数据用于启动后台任务
    task_db_id = task.id
    task_pipeline_type = task.pipeline_type
    task_enable_auto_review = task.enable_auto_review
    fallback_key = ""
    if task.writer_model_config:
        from app.config import settings as app_settings
        env_key_map = {
            "deepseek": app_settings.DEEPSEEK_API_KEY,
            "openai": app_settings.OPENAI_API_KEY,
            "qwen": app_settings.QWEN_API_KEY,
            "siliconflow": app_settings.SILICONFLOW_API_KEY,
            "anthropic": app_settings.ANTHROPIC_API_KEY,
        }
        fallback_key = env_key_map.get(task.writer_model_config.model_type, "")

    await db.commit()

    # 创建 SSE 队列（在事务提交后）
    queue: asyncio.Queue = asyncio.Queue()
    _stream_queues[task.task_id] = queue

    # 启动后台生成任务（在事务提交后，避免锁冲突）
    if task_pipeline_type == "autogen":
        from app.modules.aitest.graph.autogen_pipeline import run_autogen_pipeline
        asyncio.create_task(
            run_autogen_pipeline(
                task_db_id, task_enable_auto_review, queue,
                fallback_api_key=fallback_key,
            )
        )
    elif task_pipeline_type == "langgraph":
        from app.modules.aitest.graph.sse_stream import run_langgraph_pipeline
        asyncio.create_task(
            run_langgraph_pipeline(
                task_db_id, task_enable_auto_review, queue,
                fallback_api_key=fallback_key,
            )
        )
    else:
        asyncio.create_task(
            _run_generation_pipeline(task_db_id, task_enable_auto_review, queue)
        )

    return ResponseModel(
        data={"task_id": task.task_id, "status": "generating"},
        message="任务已重新开始生成",
    )
