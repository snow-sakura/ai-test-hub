"""
需求分析节点

分析需求文本，提取功能模块、核心流程、边界条件等关键信息。
"""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.modules.aitest.graph.state import GenerationState


async def analyze_node(state: GenerationState) -> dict:
    """
    分析需求文本并提取结构化信息

    输出到 state.analysis
    """
    llm = state.get("_analyzer_llm") or state.get("_writer_llm")
    if not llm:
        raise RuntimeError("analyze_node: writer LLM 未初始化")

    prompt = state.get("analyze_prompt") or ""
    requirement = state.get("requirement_text") or ""

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=requirement[:8000]),
    ]

    response = await llm.ainvoke(messages)

    return {"analysis": response.content}
