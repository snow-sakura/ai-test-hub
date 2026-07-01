"""
测试用例编写节点

基于需求分析和编写提示词，生成完整的测试用例集。
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.modules.aitest.graph.state import GenerationState


async def write_node(state: GenerationState) -> dict:
    """
    编写测试用例

    输出到 state.generated_text
    """
    llm = state.get("_writer_llm")
    if not llm:
        raise RuntimeError("write_node: writer LLM 未初始化")

    prompt = state.get("write_prompt") or ""
    requirement = state.get("requirement_text") or ""

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=requirement[:8000]),
    ]

    response = await llm.ainvoke(messages)

    return {"generated_text": response.content}
