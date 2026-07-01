"""
AI 评审节点

对生成的测试用例进行 9 维度评分，判断是否通过评审。
"""
from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.modules.aitest.graph.state import GenerationState


async def review_node(state: GenerationState) -> dict:
    """
    评审测试用例集

    输出到 state.review_feedback, state.review_passed, state.overall_score
    从 AI 输出中解析 JSON 结果获取评分和通过状态。
    """
    llm = state.get("_reviewer_llm")
    if not llm:
        # 没有评审模型，默认通过
        return {
            "review_feedback": "",
            "review_passed": True,
            "overall_score": 10.0,
        }

    prompt = state.get("review_prompt") or ""
    generated_text = state.get("generated_text") or ""

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=generated_text[:12000]),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content

    # 从响应中解析 JSON
    score = 5.0
    passed = False
    try:
        # 尝试从 ```json ... ``` 块中提取
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            data = json.loads(raw)

        score = float(data.get("score", 5.0))
        passed = data.get("passed", score >= 7.0)
    except (json.JSONDecodeError, ValueError, TypeError):
        # 解析失败时，使用默认值
        passed = True
        score = 7.0

    return {
        "review_feedback": raw,
        "review_passed": passed,
        "overall_score": score,
    }
