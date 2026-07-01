"""
LangGraph StateGraph 定义

构建 analyze → write → review → revise 四阶段完整管线。
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.modules.aitest.graph.nodes.analyze import analyze_node
from app.modules.aitest.graph.nodes.review import review_node
from app.modules.aitest.graph.nodes.revise import revise_node
from app.modules.aitest.graph.nodes.write import write_node
from app.modules.aitest.graph.state import GenerationState


def build_generation_graph() -> StateGraph:
    """
    构建 AI 用例生成 StateGraph

    完整的四阶段固定管线：analyze → write → review → revise → END
    每个阶段依次执行，不跳过任何步骤。
    """
    builder = StateGraph(GenerationState)

    # 注册节点
    builder.add_node("analyze", analyze_node)
    builder.add_node("write", write_node)
    builder.add_node("review", review_node)
    builder.add_node("revise", revise_node)

    # 固定顺序边，始终执行完整四阶段
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "write")
    builder.add_edge("write", "review")
    builder.add_edge("review", "revise")
    builder.add_edge("revise", END)

    return builder.compile()
