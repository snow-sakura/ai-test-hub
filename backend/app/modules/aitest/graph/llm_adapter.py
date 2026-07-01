"""
LLM 适配器

将数据库中的 AIModelConfig 转换为 LangChain ChatOpenAI 实例。
所有兼容 OpenAI API 的模型（DeepSeek、Qwen、SiliconFlow 等）均通过此适配器使用。
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.modules.config_center.models.ai_model_config import AIModelConfig


def build_chat_openai(model_config: AIModelConfig | None, fallback_api_key: str = "") -> ChatOpenAI:
    """
    根据 AIModelConfig 构建 LangChain ChatOpenAI 实例

    Args:
        model_config: 模型配置 ORM 对象（可能为 None）
        fallback_api_key: 当 model_config 无 api_key 时的兜底密钥

    Returns:
        配置好的 ChatOpenAI 实例
    """
    if model_config is None:
        # 使用兜底配置（默认千问模型）
        return ChatOpenAI(
            model="qwen3.7-max",
            openai_api_key=fallback_api_key,
            openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=0.7,
            max_tokens=8192,
            streaming=True,
        )

    api_key = (model_config.api_key or fallback_api_key).strip()
    base_url = (model_config.base_url or "").rstrip("/")
    # 确保 base_url 是指向 /v1 的路径（LangChain 会自动补全 /chat/completions）
    if not base_url.endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    return ChatOpenAI(
        model=model_config.model_name,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=model_config.temperature or 0.7,
        max_tokens=model_config.max_tokens or 4096,
        top_p=model_config.top_p or 0.9,
        streaming=True,
    )
