"""
测试用例修订节点

根据评审反馈意见，对测试用例进行修订完善。
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.modules.aitest.graph.state import GenerationState


async def revise_node(state: GenerationState) -> dict:
    """
    根据评审反馈修订测试用例

    输出到 state.revised_text
    """
    llm = state.get("_improver_llm") or state.get("_writer_llm")
    if not llm:
        raise RuntimeError("revise_node: writer LLM 未初始化")

    prompt = state.get("revise_prompt") or ""
    generated_text = state.get("generated_text") or ""
    review_feedback = state.get("review_feedback") or ""

    user_message = (
        f"【原始测试用例】\n{generated_text[:6000]}\n\n"
        f"【评审反馈】\n{review_feedback[:4000]}\n\n"
        f"请根据上述评审反馈修订测试用例。"
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)

    return {"revised_text": response.content}
