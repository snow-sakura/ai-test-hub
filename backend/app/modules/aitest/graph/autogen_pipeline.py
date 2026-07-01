"""
AutoGen 多智能体 SSE 流式协调器

使用 Microsoft AutoGen (autogen-agentchat) 的模型客户端和 Agent 模式
实现 analyze → write → review → revise 四阶段测试用例生成管线。
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.modules.aitest.graph.prompts import (
    ANALYZE_PROMPT,
    REVISE_PROMPT,
    REVIEW_PROMPT,
    WRITE_PROMPT,
)
from app.modules.aitest.models.ai_task import AIGenerationTask
from app.modules.config_center.models.ai_model_config import AIModelConfig

logger = logging.getLogger(__name__)


async def _load_prompt_content(prompt_config, default: str) -> str:
    """加载提示词内容，优先使用数据库配置"""
    if prompt_config and hasattr(prompt_config, 'content') and prompt_config.content:
        return prompt_config.content
    return default


async def run_autogen_pipeline(
    task_db_id: int,
    enable_auto_review: bool,
    queue: asyncio.Queue,
    fallback_api_key: str = "",
    continue_from_stage: str = "analyze",
) -> None:
    """
    使用 AutoGen 模型客户端实现多智能体用例生成，并通过 SSE 推送事件。

    四个阶段依次执行：analyze → write → review(可选) → revise(可选)
    事件格式兼容 LangGraph 管线的 SSE 规范，前端 useGenerationStream 无需改动。
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

            await _log("info", "🤖 使用 AutoGen 多智能体管线...")
            await _sse("status", status="generating", progress=5)

            # ---- 加载提示词 ----
            analyze_prompt = await _load_prompt_content(task.analyzer_prompt_config, ANALYZE_PROMPT)
            write_prompt = await _load_prompt_content(task.writer_prompt_config, WRITE_PROMPT)
            review_prompt = await _load_prompt_content(task.reviewer_prompt_config, REVIEW_PROMPT)
            revise_prompt = await _load_prompt_content(task.improver_prompt_config, REVISE_PROMPT)

            # ---- 构建 AutoGen 模型客户端 ----
            from autogen_ext.models.openai import OpenAIChatCompletionClient

            def _build_client(model_cfg: AIModelConfig | None, fallback_key: str) -> OpenAIChatCompletionClient:
                """从 AIModelConfig 构建 AutoGen OpenAI 兼容客户端"""
                if model_cfg is None:
                    return OpenAIChatCompletionClient(
                        model="qwen3.7-max",
                        api_key=fallback_key,
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                        temperature=0.7,
                        max_tokens=8192,
                    )
                api_key = (model_cfg.api_key or fallback_key).strip()
                base_url = (model_cfg.base_url or "").rstrip("/")
                if not base_url.endswith("/v1"):
                    base_url += "/v1"
                return OpenAIChatCompletionClient(
                    model=model_cfg.model_name,
                    api_key=api_key,
                    base_url=base_url,
                    temperature=model_cfg.temperature or 0.7,
                    max_tokens=model_cfg.max_tokens or 4096,
                    top_p=model_cfg.top_p or 0.9,
                )

            analyzer_client = _build_client(task.writer_model_config, fallback_api_key)
            writer_client = _build_client(task.writer_model_config, fallback_api_key)
            reviewer_client = None
            if enable_auto_review:
                # 使用评审模型，如果没有则使用编写模型
                reviewer_model = task.reviewer_model_config or task.writer_model_config
                if reviewer_model:
                    reviewer_client = _build_client(reviewer_model, fallback_api_key)
            improver_client = _build_client(task.writer_model_config, fallback_api_key)

            # ---- 辅助函数：流式调用模型 ----
            async def _stream_chat(
                client: OpenAIChatCompletionClient,
                system_prompt: str,
                user_message: str,
                stage: str,
            ) -> str:
                """
                使用 AutoGen 模型客户端流式生成，推送 token 到 SSE 队列。

                返回完整生成的文本内容。
                """
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ]
                full_text = ""
                try:
                    async for chunk in client.create_stream(messages=messages):
                        if chunk and chunk.content:
                            full_text += chunk.content
                            await queue.put({
                                "type": "chunk",
                                "content": chunk.content,
                                "stage": stage,
                            })
                except Exception as e:
                    logger.warning("AutoGen 流式生成异常(stage=%s): %s", stage, e)
                    # 如果流式失败，回退到非流式调用
                    result = await client.create(messages=messages)
                    if result and result.content:
                        full_text = result.content
                        await queue.put({
                            "type": "chunk",
                            "content": full_text,
                            "stage": stage,
                        })
                return full_text

            # ---- 阶段 1：需求分析 ----
            await _log("info", "🔍 AI 正在分析需求...")
            await _sse("testing_stage", stage="analyze", label="需求分析")

            analysis = await _stream_chat(
                analyzer_client, analyze_prompt,
                task.requirement_text or "",
                "analyze",
            )
            task.progress = 15
            await db.flush()

            await _log("success", "✅ 需求分析完成")
            await _log("info", "✍️ AI 正在编写测试用例...")
            await _sse("testing_stage", stage="writing", label="用例编写")
            await _sse("status", status="generating", progress=15)

            # ---- 阶段 2：用例编写 ----
            # 将分析结果作为上下文传递给编写阶段
            write_context = f"需求分析结果：\n\n{analysis}\n\n请根据以上需求分析编写测试用例。"
            generated_text = await _stream_chat(
                writer_client, write_prompt,
                write_context,
                "writing",
            )
            task.progress = 40
            task.generated_content = {"text": generated_text}
            task.status = "reviewing"
            await db.flush()

            await _log("success", "📊 测试用例编写完成")

            # 保存 write 阶段生成的用例到候选用例表
            write_cases_cache: list[dict] = []
            try:
                from app.modules.aitest.api.ai import _parse_test_cases_from_text as _parse_cases
                from app.modules.aitest.models.generated_case_item import GeneratedCaseItem
                parsed = await _parse_cases(generated_text)
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

            # ---- 阶段 3：AI 评审（可选） ----
            has_reviewed = False
            overall_score = 10.0
            review_passed = True
            review_feedback_text = ""

            if reviewer_client:
                await _log("info", "📋 AI 正在进行评审...")
                await _sse("testing_stage", stage="review", label="AI 评审")
                task.status = "reviewing"
                task.progress = 55
                await db.flush()
                await _sse("status", status="reviewing", progress=55)

                review_context = (
                    f"用户需求：\n\n{task.requirement_text}\n\n"
                    f"生成的测试用例：\n\n{generated_text}\n\n"
                    f"请对以上测试用例进行全面评审。"
                )
                review_feedback_text = await _stream_chat(
                    reviewer_client, review_prompt,
                    review_context,
                    "review",
                )
                has_reviewed = True
                task.review_feedback = review_feedback_text
                task.progress = 70
                await db.flush()

                # 从评审反馈中解析评分和结论
                try:
                    import re
                    score_match = re.search(r'(?:评分|得分|score)[：:\s]*(\d+(?:\.\d+)?)', review_feedback_text)
                    if score_match:
                        overall_score = float(score_match.group(1))
                    pass_match = re.search(r'(?:通过|passed|approved|pass)[：:\s]*(yes|true|是|通过|✓)', review_feedback_text, re.IGNORECASE)
                    if pass_match:
                        review_passed = True
                    reject_match = re.search(r'(?:驳回|拒绝|reject|fail)[：:\s]*(yes|true|是|拒绝|驳回)', review_feedback_text, re.IGNORECASE)
                    if reject_match:
                        review_passed = False
                except Exception:
                    pass

                await _log("success", f"✅ AI 评审完成（评分：{overall_score}/10）")

                await _sse("testing_review",
                    overall_score=overall_score,
                    passed=review_passed,
                    raw=review_feedback_text[:500] if review_feedback_text else "",
                )

                # 始终进入修订阶段
                task.status = "revising"
                task.progress = 80
                await db.flush()
                await _log("info", "🔄 AI 正在根据评审意见修订...")
                await _sse("testing_stage", stage="revise", label="修订完善")
                await _sse("status", status="revising", progress=80)
            else:
                await _log("info", "📋 未配置评审模型，跳过 AI 评审")
                # 无评审时也进入修订（完善格式）
                await _sse("testing_stage", stage="revise", label="修订完善")
                await _sse("status", status="revising", progress=80)

            # ---- 阶段 4：修订完善 ----
            if review_feedback_text:
                revise_context = (
                    f"用户需求：\n\n{task.requirement_text}\n\n"
                    f"原始用例：\n\n{generated_text}\n\n"
                    f"评审意见：\n\n{review_feedback_text}\n\n"
                    f"请根据评审意见修订测试用例。"
                )
            else:
                revise_context = (
                    f"用户需求：\n\n{task.requirement_text}\n\n"
                    f"生成的测试用例：\n\n{generated_text}\n\n"
                    f"请优化和完善以上测试用例的格式。"
                )

            revised_text = await _stream_chat(
                improver_client, revise_prompt,
                revise_context,
                "revise",
            )
            task.final_content = {"text": revised_text}
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now(timezone.utc)
            await db.flush()

            # 合并 write + revise 用例并推送 cases 事件
            try:
                from app.modules.aitest.api.ai import _parse_test_cases_from_text as _parse_cases
                from app.modules.aitest.models.generated_case_item import GeneratedCaseItem
                revise_cases = await _parse_cases(revised_text)
                seen_titles = {c.get("title", "") for c in write_cases_cache if c.get("title")}
                all_cases = list(write_cases_cache)
                for c in revise_cases:
                    title = c.get("title", "")
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        all_cases.append(c)
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
                review_passed=review_passed,
                overall_score=overall_score,
            )

            await db.commit()

        except Exception as e:
            logger.error("AutoGen 生成异常: %s", repr(e))
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
                "message": f"❌ AutoGen 生成失败: {str(e)}",
                "level": "error",
            })
            try:
                await db.rollback()
            except Exception:
                pass
        finally:
            await queue.put(None)
