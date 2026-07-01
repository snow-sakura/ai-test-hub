"""
LangGraph 生成流程状态定义

GenerationState 是图中各节点共享的状态数据。
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict


class GenerationState(TypedDict):
    """AI 用例生成流程状态"""
    requirement_text: str              # 原始需求文本
    analyze_prompt: str                # 分析阶段提示词
    write_prompt: str                  # 编写阶段提示词
    review_prompt: str                 # 评审阶段提示词
    revise_prompt: str                 # 修订阶段提示词

    analysis: str                      # 需求分析结果
    generated_text: str                # 生成的测试用例文本
    review_feedback: str               # 评审反馈
    review_passed: bool                # 评审是否通过
    overall_score: float               # 评审总分
    revised_text: str                  # 修订后的用例文本
    error: Optional[str]               # 错误信息

    # 运行时注入（非序列化）
    _analyzer_llm: Optional[Any]         # 需求分析 LLM（使用 writer 模型配置）
    _writer_llm: Optional[Any]           # 用例编写 LLM
    _reviewer_llm: Optional[Any]         # 评审 LLM
    _improver_llm: Optional[Any]         # 修订完善 LLM（使用 writer 模型配置）
