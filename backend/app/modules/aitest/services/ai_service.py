"""
AI 业务服务层

移植自 testhub 的 AIModelService，适配 FastAPI + SQLAlchemy async 环境。
提供测试用例生成、评审、改进、排序等完整业务能力。
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, AsyncGenerator, Callable

from fastapi import HTTPException, status
from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.config_center.models.ai_model_config import AIModelConfig
from app.modules.aitest.models.ai_task import AIGenerationTask
from app.modules.config_center.models.prompt_config import PromptConfig
from app.common.utils.ai_client import (
    AIClientFactory,
    AICompletionConfig,
    Message,
)
from app.modules.aitest.models.ai_tester_session import AITesterSession
from app.modules.aitest.models.ai_tester_message import AITesterMessage
from app.common.models.user import User

logger = logging.getLogger(__name__)

# 测试用例表格正则（用于排序/修复等操作）
# Markdown 表格行格式：| 编号 | 模块 | 标题 | ...
_CASE_LINE_RE = re.compile(r"^\s*\|\s*(TC[-：:]\d+|P\d+[三四四]?)\s*\|")
_CASE_ID_RE = re.compile(r"TC[-：:](\d+)")
_COLUMN_SEPARATOR_RE = re.compile(r"\\\|")  # 转义的管道符
_PIPE_SPLIT_RE = re.compile(r"(?<!\\)\|")


# ---------------------------------------------------------------------------
# 辅助工具方法
# ---------------------------------------------------------------------------


def _build_user_message_for_generation(
    requirement_text: str,
) -> str:
    """
    构建编写测试用例的用户消息。

    仅包含需求文本和关键的格式约束提示，不再重复系统提示词内容。
    系统提示词已在 messages 中单独设置。
    """
    return (
        f"请根据系统提示词的规范要求，为以下需求生成测试用例。\n\n"
        f"**核心格式约束**：\n"
        f"   - **编号必须连续**，从 TC-001 开始，中间不能有遗漏\n"
        f"   - **所有用例必须一次性完整输出**，不能中断\n"
        f"6. **⚠️ 特殊字符处理（关键）**：\n"
        f"   - **如果在表格内容（如操作步骤、预期结果）中出现管道符 '|'，必须转义为 '\\|'**。\n"
        f"   - **否则会导致表格列错位，无法解析**。\n"
        f"   - 示例：应输入 'a\\|b' 而不是 'a|b'。\n\n"
        f"【需求文档内容】\n{requirement_text}"
    )


async def _get_model_config(db: Any, config_id: int | None) -> AIModelConfig | None:
    """获取模型配置（带 joinedload）"""
    if config_id is None:
        return None
    stmt = select(AIModelConfig).where(AIModelConfig.id == config_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_prompt_config(db: Any, config_id: int | None) -> PromptConfig | None:
    """获取提示词配置"""
    if config_id is None:
        return None
    stmt = select(PromptConfig).where(PromptConfig.id == config_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _resolve_api_key(model_config: AIModelConfig) -> str:
    """解析 API Key：优先数据库配置，回退到环境变量

    当数据库中的 Key 为空或包含脱敏标记（****）时，
    自动回退到环境变量中对应 provider 的 API Key。
    """
    api_key = model_config.api_key or ""
    if api_key and "****" not in api_key:
        return api_key

    # 回退到环境变量
    from app.config import settings

    env_key_map = {
        "deepseek": settings.DEEPSEEK_API_KEY,
        "openai": settings.OPENAI_API_KEY,
        "qwen": settings.QWEN_API_KEY,
        "siliconflow": settings.SILICONFLOW_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
    }
    fallback = env_key_map.get(model_config.model_type, "")
    if fallback:
        logger.info("使用环境变量 API Key (provider=%s)", model_config.model_type)
        return fallback

    return api_key


def _resolve_base_url(model_config: AIModelConfig) -> str:
    """解析 Base URL：优先数据库配置，回退到环境变量默认值"""
    base_url = model_config.base_url or ""
    if base_url:
        return base_url

    from app.config import settings

    env_url_map = {
        "deepseek": settings.DEEPSEEK_BASE_URL,
        "openai": settings.OPENAI_BASE_URL,
        "qwen": settings.QWEN_BASE_URL,
        "siliconflow": settings.SILICONFLOW_BASE_URL,
        "anthropic": settings.ANTHROPIC_BASE_URL,
    }
    return env_url_map.get(model_config.model_type, "")


def _model_config_to_ai_config(model_config: AIModelConfig) -> AICompletionConfig:
    """将 ORM 模型配置转为 AICompletionConfig 数据类"""
    return AICompletionConfig(
        api_key=_resolve_api_key(model_config),
        base_url=_resolve_base_url(model_config),
        model_name=model_config.model_name,
        max_tokens=model_config.max_tokens or 4096,
        temperature=model_config.temperature or 0.7,
        top_p=model_config.top_p or 0.9,
    )


# ---------------------------------------------------------------------------
# AIService
# ---------------------------------------------------------------------------

class AIService:
    """AI 服务类"""

    # ==================================================================
    # 生成测试用例（非流式）
    # ==================================================================

    @staticmethod
    async def generate_test_cases(task: AIGenerationTask, db: Any) -> str:
        """
        生成测试用例。

        移植自 testhub 的 TestCaseGenerationTask.generate_test_cases。
        构造 writer prompt + 需求文本 -> 调用 AI -> 返回完整用例文本。
        """
        # 获取配置（支持从 task 的 relationship 或独立查询）
        writer_model = task.writer_model_config
        writer_prompt = task.writer_prompt_config

        if writer_model is None or writer_prompt is None:
            raise ValueError("未配置编写模型或编写提示词")

        prompt_content = writer_prompt.content
        user_message = _build_user_message_for_generation(task.requirement_text)

        messages: list[Message] = [
            {"role": "system", "content": prompt_content},
            {"role": "user", "content": user_message},
        ]

        provider = AIClientFactory.get_provider(writer_model.model_type)
        config = _model_config_to_ai_config(writer_model)
        result = await provider.chat_complete(messages, config)

        return result.content

    # ==================================================================
    # 评审测试用例（非流式）
    # ==================================================================

    @staticmethod
    async def review_test_cases(task: AIGenerationTask, test_cases: str, db: Any) -> str:
        """
        评审测试用例。

        移植自 testhub 的 review_test_cases。
        使用 reviewer prompt 对已生成的用例进行评审。
        """
        reviewer_model = task.reviewer_model_config
        reviewer_prompt = task.reviewer_prompt_config

        if reviewer_model is None or reviewer_prompt is None:
            raise ValueError("未配置评审模型或评审提示词")

        user_message = f"请评审以下测试用例：\n\n{test_cases}"

        messages: list[Message] = [
            {"role": "system", "content": reviewer_prompt.content},
            {"role": "user", "content": user_message},
        ]

        provider = AIClientFactory.get_provider(reviewer_model.model_type)
        config = _model_config_to_ai_config(reviewer_model)
        result = await provider.chat_complete(messages, config)

        return result.content

    # ==================================================================
    # 生成测试用例（流式）
    # ==================================================================

    @staticmethod
    async def generate_test_cases_stream(
        task: AIGenerationTask,
        db: Any,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """
        流式生成测试用例。

        on_chunk 每收到一个文本块被调用，用于 SSE 推送。
        """
        writer_model = task.writer_model_config
        writer_prompt = task.writer_prompt_config

        if writer_model is None or writer_prompt is None:
            raise ValueError("未配置编写模型或编写提示词")

        prompt_content = writer_prompt.content
        user_message = _build_user_message_for_generation(task.requirement_text)

        messages: list[Message] = [
            {"role": "system", "content": prompt_content},
            {"role": "user", "content": user_message},
        ]

        provider = AIClientFactory.get_provider(writer_model.model_type)
        config = _model_config_to_ai_config(writer_model)
        result = await provider.chat_stream(messages, config, on_chunk=on_chunk)

        return result.content

    # ==================================================================
    # 需求分析（流式）
    # ==================================================================

    @staticmethod
    async def analyze_requirement(
        task: AIGenerationTask,
        db: Any,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """
        分析需求文档，返回结构化分析结果。

        使用编写模型的配置，搭配分析提示词进行需求分析。
        分析结果用于前端需求分析卡片展示。
        """
        model = task.writer_model_config
        if model is None:
            raise ValueError("未配置编写模型")

        from app.modules.aitest.graph.prompts import ANALYZE_PROMPT
        # 优先使用数据库中 analyzer 提示词配置，无则用默认分析提示词
        analyze_content = task.analyzer_prompt_config.content if task.analyzer_prompt_config else ANALYZE_PROMPT

        user_message = (
            f"请分析以下需求文档，提取功能模块、核心流程、边界条件和测试要点：\n\n"
            f"{task.requirement_text}"
        )

        messages: list[Message] = [
            {"role": "system", "content": analyze_content},
            {"role": "user", "content": user_message},
        ]

        provider = AIClientFactory.get_provider(model.model_type)
        config = _model_config_to_ai_config(model)
        result = await provider.chat_stream(messages, config, on_chunk=on_chunk)

        return result.content

    # ==================================================================
    # 评审测试用例（流式）
    # ==================================================================

    @staticmethod
    async def review_test_cases_stream(
        task: AIGenerationTask,
        test_cases: str,
        db: Any,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """
        流式评审测试用例。
        """
        reviewer_model = task.reviewer_model_config
        reviewer_prompt = task.reviewer_prompt_config

        if reviewer_model is None or reviewer_prompt is None:
            raise ValueError("未配置评审模型或评审提示词")

        user_message = f"请评审以下测试用例：\n\n{test_cases}"

        messages: list[Message] = [
            {"role": "system", "content": reviewer_prompt.content},
            {"role": "user", "content": user_message},
        ]

        provider = AIClientFactory.get_provider(reviewer_model.model_type)
        config = _model_config_to_ai_config(reviewer_model)
        result = await provider.chat_stream(messages, config, on_chunk=on_chunk)

        return result.content

    # ==================================================================
    # 根据评审意见改进测试用例
    # ==================================================================

    @staticmethod
    async def revise_test_cases_based_on_review(
        task: AIGenerationTask,
        original: str,
        review_feedback: str,
        db: Any,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """
        根据评审意见改进测试用例。

        将原始用例 + 评审反馈一起发给编写模型，要求其修改。
        """
        writer_model = task.writer_model_config

        if writer_model is None:
            raise ValueError("未配置编写模型")

        from app.modules.aitest.graph.prompts import REVISE_PROMPT
        # 优先使用数据库中 improver 提示词配置，无则用默认修订提示词
        system_prompt = task.improver_prompt_config.content if task.improver_prompt_config else REVISE_PROMPT

        user_message = (
            f"【原始测试用例】\n{original}\n\n"
            f"【评审反馈意见】\n{review_feedback}\n\n"
            f"请根据评审意见修改上述测试用例，输出完整的、修改后的测试用例。"
        )

        messages: list[Message] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        provider = AIClientFactory.get_provider(writer_model.model_type)
        config = _model_config_to_ai_config(writer_model)
        result = await provider.chat_stream(messages, config, on_chunk=on_chunk)

        return result.content

    # ==================================================================
    # 测试用例后处理工具
    # ==================================================================

    @staticmethod
    def sort_test_cases_by_id(content: str) -> str:
        """
        按照用例编号对 Markdown 表格中的测试用例排序。

        识别以 | TC-xxx | 开头的表格行，按编号数字排序，
        非用例行（标题行、分隔行、空行等）保持原顺序。
        """
        lines = content.split("\n")
        # 将行分类：用例行 / 非用例行
        case_lines: list[tuple[int, str]] = []
        other_lines: list[str] = []

        for line in lines:
            m = _CASE_LINE_RE.search(line.strip())
            if m:
                case_id_str = m.group(1)
                id_match = _CASE_ID_RE.search(case_id_str)
                if id_match:
                    case_num = int(id_match.group(1))
                    case_lines.append((case_num, line))
                    continue
            other_lines.append(line)

        # 对用例行按编号排序
        case_lines.sort(key=lambda x: x[0])

        # 重建：保留非用例行，在对应位置插入排序后的用例行
        # 简单做法：用排序后的用例行替换原用例行
        sorted_lines: list[str] = []
        case_iter = iter(cl[1] for cl in case_lines)

        for line in lines:
            m = _CASE_LINE_RE.search(line.strip())
            if m and _CASE_ID_RE.search(m.group(1)):
                try:
                    sorted_lines.append(next(case_iter))
                except StopIteration:
                    sorted_lines.append(line)
            else:
                sorted_lines.append(line)

        return "\n".join(sorted_lines)

    @staticmethod
    def fix_incomplete_last_case(content: str) -> str:
        """
        修复不完整的最后一条测试用例。

        检测逻辑：如果一个表格行（在非分隔行区域）包含的列数少于预期（< 7 列），
        且这是最后一行内容，将前一行与其合并或删除残缺行。
        """
        lines = content.split("\n")

        # 找到最后一个非空行
        last_content_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                last_content_idx = i
                break

        if last_content_idx < 0:
            return content

        last_line = lines[last_content_idx].strip()

        # 判断是否为不完整的用例行（以 | 开头但列数 < 7）
        if last_line.startswith("|"):
            # 去除转义后的列数统计
            processed = _COLUMN_SEPARATOR_RE.sub("|", last_line)
            columns = [c.strip() for c in _PIPE_SPLIT_RE.split(processed) if c.strip()]
            if 2 <= len(columns) < 7:
                logger.info(
                    "检测到不完整的最后用例行 (列数=%s)，移除: %s",
                    len(columns), last_line[:80],
                )
                lines.pop(last_content_idx)

        return "\n".join(lines)

    @staticmethod
    def renumber_test_cases(content: str, start: int = 1) -> str:
        """
        重新编号测试用例。

        规则：将表格行中的 TC-xxx 或 TC：xxx 重新编号为连续的 TC-{start}, TC-{start+1}, ...
        """
        counter = start
        new_lines: list[str] = []

        for line in content.split("\n"):
            stripped = line.strip()
            m = _CASE_LINE_RE.search(stripped)
            if m:
                old_id = m.group(1)
                # 保留原始格式（横线或冒号）
                separator = "：" if "：" in old_id else "-"
                new_id = f"TC{separator}{counter:03d}"
                # 替换当前行的编号部分
                new_line = line.replace(old_id, new_id, 1)
                new_lines.append(new_line)
                counter += 1
            else:
                new_lines.append(line)

        return "\n".join(new_lines)

    # ==================================================================
    # AI 评测测试用例（新增：评测师功能）
    # ==================================================================

    @staticmethod
    async def evaluate_test_cases(
        test_cases: list[str],
        model_config: AIModelConfig,
        prompt_config: PromptConfig,
    ) -> dict:
        """
        AI 评测测试用例。

        参数:
            test_cases: 测试用例列表（文本形式）
            model_config: 评测模型配置
            prompt_config: 评测提示词配置

        返回:
            {
                "overall_score": float,        # 综合评分（0-100）
                "issues": [str],               # 问题列表
                "improvements": [str],         # 改进建议
                "detail": str,                 # AI 原始评测文本
            }
        """
        cases_text = "\n\n".join(
            f"用例 {i + 1}:\n{case}" for i, case in enumerate(test_cases)
        )

        user_message = (
            f"请对以下测试用例进行综合评测：\n\n{cases_text}\n\n"
            f"请从以下维度评分（满分 100）：\n"
            f"1. 完整性（30 分）：覆盖了所有主要场景和边界条件\n"
            f"2. 准确性（25 分）：用例描述准确，预期结果明确\n"
            f"3. 可执行性（20 分）：步骤清晰，可操作性强\n"
            f"4. 一致性（15 分）：格式统一，风格一致\n"
            f"5. 效率（10 分）：无冗余用例，设计合理\n\n"
            f"请输出 JSON 格式结果（严格按以下结构）：\n"
            f"{{\n"
            f'  "overall_score": <综合评分0-100>,\n'
            f'  "issues": [\n'
            f'    {{\n'
            f'      "severity": "high/mid/low",\n'
            f'      "title": "问题标题",\n'
            f'      "description": "问题详细描述",\n'
            f'      "fix_suggestion": "修复建议",\n'
            f'      "related_cases": "相关用例编号"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "improvements": ["改进建议1", "改进建议2", ...],\n'
            f'  "detail": "详细评测意见..."\n'
            f"}}"
        )

        messages: list[Message] = [
            {"role": "system", "content": prompt_config.content},
            {"role": "user", "content": user_message},
        ]

        provider = AIClientFactory.get_provider(model_config.model_type)
        config = _model_config_to_ai_config(model_config)
        result = await provider.chat_complete(messages, config)

        # 尝试解析 JSON
        try:
            # 查找 JSON 块
            json_match = re.search(r"\{.*\}", result.content, re.DOTALL)
            if json_match:
                import json as json_mod
                return json_mod.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            logger.warning("评测结果不是有效 JSON，返回原始文本")

        return {
            "overall_score": 0,
            "issues": [],
            "improvements": [],
            "detail": result.content,
        }

    # ==================================================================
    # AI 评测师流式回复
    # ==================================================================

    @staticmethod
    async def stream_ai_tester_response(
        session_id: int,
        user_message: str,
        model_str: str,
        db: AsyncSession,
        current_user: User,
    ) -> AsyncGenerator[tuple[str, Any], None]:
        """
        流式获取 AI 评测师回复，自动保存消息到数据库。

        功能：
        1. 验证会话归属权
        2. 确定使用的模型，查找对应模型配置
        3. 保存用户消息到数据库
        4. 构建对话上下文（最近 20 条消息）
        5. 流式调用 AI 接口并逐 token 产出
        6. 保存完整 AI 回复到数据库
        7. 更新会话的消息计数

        Yields:
            tuple[str, Any]: (event_type, data)
            - ("chunk", str)           — AI 回复文本块
            - ("complete", dict)       — 完成事件，包含 user_message_id / assistant_message_id
            - ("error", str)           — 错误信息

        Raises:
            HTTPException: 会话不存在 / 无权访问 / 模型未配置
        """
        # ---- 1. 验证会话 ----
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

        # ---- 2. 确定模型 ----
        model_to_use = model_str or session.model
        if not model_to_use:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未指定模型，请在会话或消息中指定",
            )

        # ---- 3. 查找模型配置 ----
        stmt = (
            select(AIModelConfig)
            .where(AIModelConfig.model_name == model_to_use)
            .where(AIModelConfig.is_active.is_(True))
            .limit(1)
        )
        result = await db.execute(stmt)
        model_config = result.scalar_one_or_none()
        if model_config is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到启用的模型配置: {model_to_use}",
            )

        # ---- 4. 保存用户消息 ----
        user_msg_obj = AITesterMessage(
            session_id=session_id,
            role="user",
            content=user_message,
        )
        db.add(user_msg_obj)
        await db.flush()
        await db.refresh(user_msg_obj)

        # ---- 5. 构建对话上下文（取最近 20 条消息） ----
        history_stmt = (
            select(AITesterMessage)
            .where(AITesterMessage.session_id == session_id)
            .order_by(AITesterMessage.id.desc())
            .limit(20)
        )
        history_result = await db.execute(history_stmt)
        history = list(reversed(history_result.scalars().all()))

        llm_messages: list[Message] = []
        for msg in history:
            llm_messages.append({"role": msg.role, "content": msg.content})

        # ---- 6. 流式调用 AI ----
        # 用 Queue 桥接同步 on_chunk 回调和异步生成器
        chunk_queue: asyncio.Queue = asyncio.Queue()
        full_content_parts: list[str] = []
        ai_error: Exception | None = None

        async def _run_ai_stream():
            """后台执行 AI 流式调用，通过队列推送文本块。"""
            nonlocal ai_error
            try:
                provider = AIClientFactory.get_provider(model_config.model_type)
                ai_config = AICompletionConfig(
                    api_key=_resolve_api_key(model_config),
                    base_url=_resolve_base_url(model_config),
                    model_name=model_config.model_name,
                    max_tokens=model_config.max_tokens or 4096,
                    temperature=model_config.temperature or 0.7,
                    top_p=model_config.top_p or 0.9,
                )

                def _on_chunk(text: str):
                    """同步回调：收集文本块并推入队列"""
                    full_content_parts.append(text)
                    chunk_queue.put_nowait(text)

                await provider.chat_stream(llm_messages, ai_config, on_chunk=_on_chunk)

            except Exception as e:
                logger.error("AI 流式调用异常: %s", repr(e))
                ai_error = e
            finally:
                chunk_queue.put_nowait(None)  # 结束信号

        # 启动后台任务
        asyncio.create_task(_run_ai_stream())

        # 从队列中 yield 文本块
        while True:
            chunk = await chunk_queue.get()
            if chunk is None:
                break
            yield ("chunk", chunk)

        # ---- 7. 处理 AI 错误 ----
        if ai_error:
            yield ("error", str(ai_error))
            return

        # ---- 8. 保存 AI 回复 ----
        full_content = "".join(full_content_parts)
        if not full_content.strip():
            yield ("error", "AI 返回内容为空")
            return

        assistant_msg = AITesterMessage(
            session_id=session_id,
            role="assistant",
            content=full_content,
        )
        db.add(assistant_msg)
        await db.flush()
        await db.refresh(assistant_msg)

        # ---- 9. 更新会话消息计数 ----
        count_stmt = select(sql_func.count()).select_from(AITesterMessage.__table__).where(
            AITesterMessage.session_id == session_id,
        )
        count_result = await db.execute(count_stmt)
        session.message_count = count_result.scalar() or 0
        await db.flush()

        # ---- 10. 产出完成事件 ----
        yield ("complete", {
            "user_message_id": user_msg_obj.id,
            "assistant_message_id": assistant_msg.id,
        })
