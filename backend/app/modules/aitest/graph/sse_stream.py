"""
SSE 流式协调器

包装 LangGraph 执行过程，将各阶段事件转换为 SSE 格式推送至队列。
与 ai.py 中的 _stream_queues 配合使用，兼容现有前端 SSE 消费逻辑。
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.modules.aitest.graph.graph import build_generation_graph
from app.modules.aitest.graph.llm_adapter import build_chat_openai
from app.modules.aitest.graph.prompts import (
    ANALYZE_PROMPT,
    REVISE_PROMPT,
    REVIEW_PROMPT,
    WRITE_PROMPT,
)
from app.modules.aitest.graph.state import GenerationState
from app.modules.aitest.models.ai_task import AIGenerationTask
from app.modules.config_center.models.ai_model_config import AIModelConfig
from app.modules.config_center.models.prompt_config import PromptConfig

logger = logging.getLogger(__name__)


class SSECallbackHandler(AsyncCallbackHandler):
    """将 LLM token 流实时推送至 SSE 队列"""

    def __init__(self, queue: asyncio.Queue, stage: str):
        self.queue = queue
        self.stage = stage

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        await self.queue.put({
            "type": "chunk",
            "content": token,
            "stage": self.stage,
        })


async def _load_prompt_content(prompt_config: PromptConfig | None, default: str) -> str:
    """加载提示词内容，优先使用数据库配置"""
    if prompt_config and prompt_config.content:
        return prompt_config.content
    return default


async def run_langgraph_pipeline(
    task_db_id: int,
    enable_auto_review: bool,
    queue: asyncio.Queue,
    fallback_api_key: str = "",
    continue_from_stage: str = "analyze",
) -> None:
    """
    使用 LangGraph DAG 执行 AI 用例生成，并通过 SSE 推送事件。

    该函数作为后台 asyncio task 运行，不受 HTTP 请求生命周期影响。
    事件格式兼容前端 useGenerationStream composable 的双模式 SSE 解析。
    """
    from app.database import async_session_factory

    async def _log(level: str, message: str):
        await queue.put({"type": "log", "message": message, "level": level})

    async def _sse(event_type: str, **data: Any):
        await queue.put({"type": event_type, **data})

    async with async_session_factory() as db:
        try:
            # ---- 加载任务及配置 ----
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

            await _log("info", "🚀 创建生成任务...")
            task.status = "generating"
            await db.flush()

            await _log("info", "📋 任务已创建，准备开始生成...")
            await _sse("status", status="generating", progress=5)

            # ---- 加载提示词 ----
            analyze_prompt = await _load_prompt_content(task.analyzer_prompt_config, ANALYZE_PROMPT)
            write_prompt = await _load_prompt_content(task.writer_prompt_config, WRITE_PROMPT)
            review_prompt = await _load_prompt_content(task.reviewer_prompt_config, REVIEW_PROMPT)
            revise_prompt = await _load_prompt_content(task.improver_prompt_config, REVISE_PROMPT)

            # ---- 构建 LLM 实例（各阶段独立回调，确保前端 2×2 卡片正确展示） ----
            analyzer_llm = build_chat_openai(task.writer_model_config, fallback_api_key)
            analyzer_llm = analyzer_llm.with_config({
                "callbacks": [SSECallbackHandler(queue, "analyze")],
            })

            writer_llm = build_chat_openai(task.writer_model_config, fallback_api_key)
            writer_llm = writer_llm.with_config({
                "callbacks": [SSECallbackHandler(queue, "writing")],
            })

            reviewer_llm = None
            if enable_auto_review:
                # 使用评审模型，如果没有则使用编写模型
                reviewer_model = task.reviewer_model_config or task.writer_model_config
                if reviewer_model:
                    reviewer_llm = build_chat_openai(reviewer_model, fallback_api_key)
                    reviewer_llm = reviewer_llm.with_config({
                        "callbacks": [SSECallbackHandler(queue, "review")],
                    })

            improver_llm = build_chat_openai(task.writer_model_config, fallback_api_key)
            improver_llm = improver_llm.with_config({
                "callbacks": [SSECallbackHandler(queue, "revise")],
            })

            # ---- 构建 LangGraph 并执行 ----
            graph = build_generation_graph()

            initial_state: GenerationState = {
                "requirement_text": task.requirement_text or "",
                "analyze_prompt": analyze_prompt,
                "write_prompt": write_prompt,
                "review_prompt": review_prompt,
                "revise_prompt": revise_prompt,
                "analysis": "",
                "generated_text": "",
                "review_feedback": "",
                "review_passed": True,
                "overall_score": 10.0,
                "revised_text": "",
                "error": None,
                "_analyzer_llm": analyzer_llm,
                "_writer_llm": writer_llm,
                "_reviewer_llm": reviewer_llm,
                "_improver_llm": improver_llm,
            }

            await _log("info", "🔍 AI 正在分析需求...")
            await _sse("testing_stage", stage="analyze", label="需求分析")

            final_state: GenerationState | None = None
            has_reviewed = False
            has_revised = False
            # 缓存 write 阶段解析的用例列表，供 revise 阶段合并时使用
            write_cases_cache: list[dict] = []

            async for step in graph.astream(initial_state):
                for node_name, node_state in step.items():
                    final_state = node_state

                    if node_name == "analyze":
                        # 分析完成，进入编写阶段
                        task.progress = 15
                        await db.flush()

                        await _log("info", "✅ 需求分析完成")
                        await _log("info", "✍️ AI 正在编写测试用例...")
                        await _sse("testing_stage", stage="writing", label="用例编写")
                        await _sse("status", status="generating", progress=15)

                    elif node_name == "write":
                        # 编写完成，进入评审阶段
                        generated = node_state.get("generated_text", "")
                        task.progress = 40
                        task.generated_content = {"text": generated}
                        await db.flush()

                        await _log("success", "📊 测试用例编写完成")
                        await _sse("testing_stage", stage="review", label="AI 评审")
                        task.status = "reviewing"
                        task.progress = 55
                        await db.flush()
                        await _log("info", "📋 AI 正在进行评审...")
                        await _sse("status", status="reviewing", progress=55)

                        # 保存 write 阶段生成的用例到候选用例表（供后续保存到用例库）
                        try:
                            from app.modules.aitest.api.ai import _parse_test_cases_from_text as _parse_cases
                            from app.modules.aitest.models.generated_case_item import GeneratedCaseItem
                            parsed = await _parse_cases(generated)
                            write_cases_cache = list(parsed)
                            for c in write_cases_cache:
                                db.add(GeneratedCaseItem(
                                    task_id=task.id,
                                    title=c["title"],
                                    priority=c.get("priority", "P2"),
                                    module=c.get("module", ""),
                                    precondition=c.get("precondition", ""),
                                    test_steps=c.get("test_steps", ""),
                                    expected_result=c.get("expected_result", ""),
                                    status="adopted",
                                    sort_order=0,
                                ))
                            await db.flush()
                            await _log("info", f"📊 编写完成，已解析 {len(write_cases_cache)} 条用例")
                        except Exception as e:
                            logger.warning("保存 write 用例失败: %s", e)

                    elif node_name == "review":
                        has_reviewed = True
                        feedback = node_state.get("review_feedback", "")
                        passed = node_state.get("review_passed", True)
                        score = node_state.get("overall_score", 10.0)

                        task.review_feedback = feedback
                        task.progress = 70
                        await db.flush()

                        await _log("success", f"✅ AI 评审完成（评分：{score}/10）")

                        # 无评审模型时补充默认展示内容，避免前端卡片空白
                        if not feedback and not reviewer_llm:
                            await _sse("chunk", stage="review",
                                content="（无评审模型，默认通过）\n\n评分：10.0/10\n\n状态：通过")

                        await _sse("testing_review",
                            overall_score=score,
                            passed=passed,
                            raw=feedback[:500] if feedback else "",
                        )

                        # 始终进入修订阶段，确保前端四阶段卡片完整展示
                        has_revised = True
                        task.status = "revising"
                        task.progress = 80
                        await db.flush()
                        await _log("info", "🔄 AI 正在根据评审意见修订...")
                        await _sse("testing_stage", stage="revise", label="修订完善")
                        await _sse("status", status="revising", progress=80)

                    elif node_name == "revise":
                        has_revised = True
                        revised = node_state.get("revised_text", "")
                        task.final_content = {"text": revised}
                        task.status = "completed"
                        task.progress = 100
                        task.completed_at = datetime.now(timezone.utc)
                        await db.flush()

                        # 合并 write + revise 用例并推送 cases 事件
                        try:
                            from app.modules.aitest.api.ai import _parse_test_cases_from_text as _parse_cases
                            from app.modules.aitest.models.generated_case_item import GeneratedCaseItem
                            revise_cases = await _parse_cases(revised)
                            # 按 title 去重：write 用例优先，revise 新增的追加
                            seen_titles = {c.get("title", "") for c in write_cases_cache if c.get("title")}
                            all_cases = list(write_cases_cache)
                            for c in revise_cases:
                                title = c.get("title", "")
                                if title and title not in seen_titles:
                                    seen_titles.add(title)
                                    all_cases.append(c)
                                    # 保存新增的 revise 用例
                                    db.add(GeneratedCaseItem(
                                        task_id=task.id,
                                        title=c["title"],
                                        priority=c.get("priority", "P2"),
                                        module=c.get("module", ""),
                                        precondition=c.get("precondition", ""),
                                        test_steps=c.get("test_steps", ""),
                                        expected_result=c.get("expected_result", ""),
                                        status="adopted",
                                        sort_order=0,
                                    ))
                            await db.flush()
                            if all_cases:
                                await _sse("cases", cases=all_cases, progress=95)
                                added = len(all_cases) - len(write_cases_cache)
                                await _log("success", f"📊 共 {len(all_cases)} 条用例（编写 {len(write_cases_cache)} 条"
                                    f"{f' + 修订新增 {added} 条' if added > 0 else '，无新增'}）")
                        except Exception as e:
                            logger.warning("解析/保存修订用例失败: %s", e)

                        await _log("success", "🎉 用例修订完成，用例生成结束")
                        await _sse("testing_done",
                            task_id=task.task_id,
                            generated_count=0,
                            review_passed=False,
                            overall_score=node_state.get("overall_score", 0),
                        )

            # 确保任务状态已更新
            if not has_reviewed and final_state:
                # 无评审模式单独处理
                pass

            await db.commit()

        except Exception as e:
            logger.error("LangGraph 生成异常: %s", repr(e))
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
                "message": f"❌ LangGraph 生成失败: {str(e)}",
                "level": "error",
            })
            try:
                await db.rollback()
            except Exception:
                pass
        finally:
            # 结束信号
            await queue.put(None)
