"""
统一 AI 客户端抽象层

提供 AI 提供者的抽象基类和多种实现（httpx 原生、Anthropic SDK 等），
支持流式和非流式调用，以及自动续写、错误重试等高级功能。
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable

import httpx

logger = logging.getLogger(__name__)

# ---------- 类型别名 ----------
Message = dict[str, str]  # {"role": "...", "content": "..."}


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------


@dataclass
class AICompletionConfig:
    """AI 模型调用配置"""
    api_key: str
    base_url: str
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    # 超时配置（秒）
    connect_timeout: int = 60
    read_timeout: int = 900
    write_timeout: int = 60
    pool_timeout: int = 60
    # 重试/续写配置
    max_retries: int = 3
    retry_base_delay: float = 2.0
    max_continuations: int = 5  # 流式续写最大次数


@dataclass
class CompletionResult:
    """AI 完成结果"""
    content: str
    finish_reason: str | None = None
    usage: dict | None = None
    model: str | None = None


# ---------------------------------------------------------------------------
# 基础 URL 智能补全
# ---------------------------------------------------------------------------


def _normalize_base_url(url: str) -> str:
    """
    对 base_url 进行智能补全，确保最终 URL 指向 /v1/chat/completions。

    规则：
      1. 去掉末尾的 /
      2. 如果已以 /chat/completions 结尾 -> 直接返回
      3. 如果以 /v1 结尾 -> 补全 /chat/completions
      4. 否则 -> 补全 /v1/chat/completions
    """
    url = url.rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    return f"{url}/v1/chat/completions"


# ---------------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------------


class BaseAIProvider(ABC):
    """AI 提供者抽象基类"""

    @abstractmethod
    async def chat_complete(
        self,
        messages: list[Message],
        config: AICompletionConfig,
    ) -> CompletionResult:
        """非流式完整调用，返回完整结果"""

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        config: AICompletionConfig,
        on_chunk: Callable[[str], None] | None = None,
    ) -> CompletionResult:
        """
        流式调用。

        参数:
            on_chunk: 每收到一个文本 chunk 时的回调（chunk 参数为纯文本片段）。
                      可用于 SSE 推送。
        返回:
            合并后的 CompletionResult。
        """


# ---------------------------------------------------------------------------
# httpx 实现的 OpenAI 兼容提供者
# ---------------------------------------------------------------------------


class HttpxOpenAIProvider(BaseAIProvider):
    """
    基于 httpx.AsyncClient 的 OpenAI 兼容提供者。

    兼容：OpenAI / DeepSeek / 通义千问 / SiliconFlow / 任何 OpenAI 格式的 API。
    """

    # SSE 行前缀
    _DATA_PREFIX = b"data: "
    _DONE_MARKER = b"[DONE]"

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _build_headers(config: AICompletionConfig) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _build_body(
        messages: list[Message],
        config: AICompletionConfig,
        stream: bool = False,
    ) -> dict[str, Any]:
        return {
            "model": config.model_name,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": stream,
        }

    @staticmethod
    def _create_client(config: AICompletionConfig) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=config.connect_timeout,
                read=config.read_timeout,
                write=config.write_timeout,
                pool=config.pool_timeout,
            ),
        )

    @staticmethod
    def _parse_non_stream_response(body: dict) -> CompletionResult:
        """解析非流式响应 JSON"""
        choice = body["choices"][0]
        return CompletionResult(
            content=choice["message"]["content"],
            finish_reason=choice.get("finish_reason"),
            usage=body.get("usage"),
            model=body.get("model"),
        )

    @staticmethod
    def _parse_sse_line(line: bytes) -> dict | None:
        """解析单条 SSE 行，返回 delta 数据或 None。"""
        if not line.startswith(HttpxOpenAIProvider._DATA_PREFIX):
            return None
        payload = line[len(HttpxOpenAIProvider._DATA_PREFIX):].strip()
        if not payload or payload == HttpxOpenAIProvider._DONE_MARKER:
            return None
        return json.loads(payload)

    # ------------------------------------------------------------------
    # 流式续写核心逻辑（移植自 testhub）
    # ------------------------------------------------------------------

    async def _stream_with_continuation(
        self,
        messages: list[Message],
        config: AICompletionConfig,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """
        流式调用，并自动处理 finish_reason='length' 的续写。

        续写机制（移植自 testhub 的流式逻辑）：
          1. 检测 finish_reason='length'
          2. 将已生成内容作为 assistant 消息追加到 messages
          3. 追加 "请继续输出" 的 user 指令
          4. 最多续写 max_continuations 次
        """
        all_content_parts: list[str] = []
        continuation_count = 0

        while True:
            current_messages = messages[:]  # 复制，不修改原始列表
            # 如果已有累积内容，将其作为 assistant 消息并追加续写指令
            if all_content_parts:
                continuation_count += 1
                if continuation_count > config.max_continuations:
                    logger.warning("达到最大续写次数 %s，停止续写", config.max_continuations)
                    break
                logger.info("触发续写第 %s/%s 次", continuation_count, config.max_continuations)
                current_messages.append({
                    "role": "assistant",
                    "content": "".join(all_content_parts),
                })
                current_messages.append({
                    "role": "user",
                    "content": "请继续输出",
                })

            url = _normalize_base_url(config.base_url)
            headers = self._build_headers(config)
            body = self._build_body(current_messages, config, stream=True)

            stream_finished = False
            async with self._create_client(config) as client:
                try:
                    async with client.stream("POST", url, headers=headers, json=body) as resp:
                        if resp.status_code != 200:
                            error_text = await resp.aread()
                            logger.error(
                                "API 流式返回错误: status=%s, body=%s",
                                resp.status_code, error_text,
                            )
                        resp.raise_for_status()

                        async for line in resp.aiter_lines():
                            # 将字符串行转 bytes 以复用 _parse_sse_line
                            parsed = self._parse_sse_line(line.encode("utf-8"))
                            if parsed is None:
                                continue
                            choices = parsed.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                all_content_parts.append(content)
                                if on_chunk:
                                    on_chunk(content)

                            finish_reason = choices[0].get("finish_reason")
                            if finish_reason == "stop":
                                stream_finished = True
                            elif finish_reason == "length":
                                # 后续会进入续写逻辑
                                pass

                except httpx.HTTPStatusError as e:
                    logger.error("API HTTP 错误: %s", repr(e))
                    raise
                except httpx.TimeoutException as e:
                    logger.error("API 超时: %s", repr(e))
                    raise
                except Exception as e:
                    logger.error("API 流式调用异常: %s", repr(e))
                    raise

            if stream_finished:
                break

        return "".join(all_content_parts)

    # ------------------------------------------------------------------
    # 接口实现
    # ------------------------------------------------------------------

    async def chat_complete(
        self,
        messages: list[Message],
        config: AICompletionConfig,
    ) -> CompletionResult:
        url = _normalize_base_url(config.base_url)
        headers = self._build_headers(config)
        body = self._build_body(messages, config, stream=False)

        last_exception: Exception | None = None
        for attempt in range(config.max_retries):
            try:
                async with self._create_client(config) as client:
                    response = await client.post(url, headers=headers, json=body)
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(
                            "API 返回错误: status=%s, body=%s",
                            response.status_code, error_text,
                        )
                    response.raise_for_status()
                    return self._parse_non_stream_response(response.json())

            except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
                last_exception = e
                logger.warning(
                    "API 调用失败 (attempt %s/%s): %s",
                    attempt + 1, config.max_retries, repr(e),
                )
                if attempt < config.max_retries - 1:
                    delay = config.retry_base_delay * (2 ** attempt)  # 指数退避
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                logger.error("API 调用异常 (非重试): %s", repr(e))
                raise

        # 所有重试均失败
        raise last_exception  # type: ignore[misc]

    async def chat_stream(
        self,
        messages: list[Message],
        config: AICompletionConfig,
        on_chunk: Callable[[str], None] | None = None,
    ) -> CompletionResult:
        full_content = await self._stream_with_continuation(messages, config, on_chunk)
        return CompletionResult(content=full_content)


# ---------------------------------------------------------------------------
# Anthropic 提供者（预留，需安装 anthropic SDK）
# ---------------------------------------------------------------------------


class AnthropicProvider(BaseAIProvider):
    """
    Anthropic Claude 提供者。

    使用 anthropic.AsyncAnthropic SDK。如果 SDK 未安装，会给出友好的错误提示。
    """

    def __init__(self) -> None:
        self._client: Any = None  # anthropic.AsyncAnthropic

    def _ensure_client(self, config: AICompletionConfig) -> Any:
        """延迟初始化 SDK 客户端"""
        if self._client is not None:
            return self._client
        try:
            from anthropic import AsyncAnthropic  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "使用 Anthropic 提供者需要安装 anthropic SDK: "
                "pip install anthropic"
            )
        self._client = AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=httpx.Timeout(
                connect=config.connect_timeout,
                read=config.read_timeout,
                write=config.write_timeout,
                pool=config.pool_timeout,
            ),
        )
        return self._client

    async def chat_complete(
        self,
        messages: list[Message],
        config: AICompletionConfig,
    ) -> CompletionResult:
        client = self._ensure_client(config)
        # 将 OpenAI 格式消息转为 Anthropic 格式
        system_msg = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] in ("user", "assistant"):
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        kwargs: dict[str, Any] = {
            "model": config.model_name,
            "messages": anthropic_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        if system_msg:
            kwargs["system"] = system_msg

        last_exception: Exception | None = None
        for attempt in range(config.max_retries):
            try:
                response = await client.messages.create(**kwargs)
                return CompletionResult(
                    content=response.content[0].text,
                    finish_reason=response.stop_reason,
                    usage={
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    model=response.model,
                )
            except Exception as e:
                last_exception = e
                logger.warning(
                    "Anthropic API 调用失败 (attempt %s/%s): %s",
                    attempt + 1, config.max_retries, repr(e),
                )
                if attempt < config.max_retries - 1:
                    delay = config.retry_base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise
        raise last_exception  # type: ignore[misc]

    async def chat_stream(
        self,
        messages: list[Message],
        config: AICompletionConfig,
        on_chunk: Callable[[str], None] | None = None,
    ) -> CompletionResult:
        client = self._ensure_client(config)
        system_msg = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] in ("user", "assistant"):
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        kwargs: dict[str, Any] = {
            "model": config.model_name,
            "messages": anthropic_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": True,
        }
        if system_msg:
            kwargs["system"] = system_msg

        parts: list[str] = []
        async with client.messages.create(**kwargs) as stream:  # type: ignore[arg-type]
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.text:
                    parts.append(event.delta.text)
                    if on_chunk:
                        on_chunk(event.delta.text)

        return CompletionResult(content="".join(parts))


# ---------------------------------------------------------------------------
# 工厂
# ---------------------------------------------------------------------------


class AIClientFactory:
    """AI 客户端工厂"""

    _providers: dict[str, type[BaseAIProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: type[BaseAIProvider]) -> None:
        """注册自定义提供者"""
        cls._providers[name] = provider_cls

    @staticmethod
    def get_provider(model_type: str) -> BaseAIProvider:
        """
        根据模型类型返回对应的 AI 提供者实例。

        目前支持:
          - deepseek, qwen, siliconflow, openai, other -> HttpxOpenAIProvider
          - anthropic                                    -> AnthropicProvider
        """
        model_type = model_type.lower().strip()

        # Anthropic 使用独立 SDK
        if model_type == "anthropic":
            return AnthropicProvider()

        # 所有 OpenAI 兼容格式统一使用 httpx 提供者
        return HttpxOpenAIProvider()


# 默认注册
AIClientFactory.register("openai", HttpxOpenAIProvider)
AIClientFactory.register("deepseek", HttpxOpenAIProvider)
AIClientFactory.register("qwen", HttpxOpenAIProvider)
AIClientFactory.register("siliconflow", HttpxOpenAIProvider)
AIClientFactory.register("anthropic", AnthropicProvider)
AIClientFactory.register("other", HttpxOpenAIProvider)
