"""
Mock LLM 服务器（OpenAI 兼容 /v1/chat/completions）

用途：
- 本地开发 / CI / 浏览器端到端验证时，无需真实 AI API Key 即可跑通
  「分析 → 编写 → 评审 → 修订」完整生成链路。
- 根据 system prompt 内容自动识别阶段并返回对应格式的响应：
    需求分析 → 分析文本
    用例编写 → 7 列 Markdown 用例表格
    用例评审 → ```json {"score":..,"passed":..}```
    用例修订 → 修订后的 Markdown 用例表格
- 支持 SSE 流式（stream=true），块间延迟可用环境变量 MOCK_DELAY 控制，
  便于观察免费模型串行 / 付费模型并行的调度效果。

启动：
    python scripts/mock_llm_server.py            # 默认 8030 端口
    MOCK_DELAY=8 python scripts/mock_llm_server.py  # 每次调用总耗时约 8 秒

配套模型配置（配置中心 → AI 模型配置）：
    base_url = http://127.0.0.1:8030/v1
    model_name = mock-llm
    api_key    = mock-key（任意非空值）
"""

import asyncio
import json
import os
import time
import uuid

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI(title="Mock LLM Server")

MOCK_DELAY = float(os.environ.get("MOCK_DELAY", "2"))  # 每次调用总耗时（秒）
PORT = int(os.environ.get("MOCK_PORT", "8030"))

ANALYSIS_TEXT = (
    "## 需求分析结果\n\n"
    "### 核心功能模块\n"
    "1. 用户认证模块：登录、注册、验证码校验\n"
    "2. 安全策略模块：错误次数限制、账号锁定机制\n\n"
    "### 核心流程\n"
    "输入手机号 → 获取验证码 → 校验验证码 → 登录成功/失败处理\n\n"
    "### 边界条件与风险点\n"
    "- 验证码有效期边界（59s/60s/61s）\n"
    "- 连续错误次数边界（4次/5次/6次）\n"
    "- 锁定时间窗口（9分59秒/10分钟）\n"
    "- 手机号格式校验、重复获取频率限制\n\n"
    "### 测试优先级建议\n"
    "P0：验证码正确登录、错误码拒绝、锁定策略；P1：过期、频率限制；P2：格式校验\n"
)

CASES_TABLE = (
    "| 用例编号 | 模块 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |\n"
    "| --- | --- | --- | --- | --- | --- | --- |\n"
    "| TC-001 | 登录认证 | 正确验证码登录成功 | 用户已注册且未锁定 | 1.输入手机号 2.获取验证码 3.输入正确验证码 4.点击登录 | 登录成功跳转首页 | P0 |\n"
    "| TC-002 | 登录认证 | 错误验证码登录失败 | 用户已注册 | 1.输入手机号 2.获取验证码 3.输入错误验证码 4.点击登录 | 提示验证码错误，留在登录页 | P0 |\n"
    "| TC-003 | 安全策略 | 验证码60秒过期失效 | 用户已获取验证码 | 1.等待61秒 2.输入旧验证码登录 | 提示验证码已过期 | P1 |\n"
    "| TC-004 | 安全策略 | 连续5次错误锁定10分钟 | 用户已注册 | 1.连续输错验证码5次 | 提示账号锁定10分钟，期间无法登录 | P0 |\n"
    "| TC-005 | 安全策略 | 锁定10分钟后自动解锁 | 账号处于锁定状态 | 1.等待10分钟 2.用正确验证码登录 | 登录成功 | P1 |\n"
    "| TC-006 | 登录认证 | 非法手机号格式拦截 | 打开登录页 | 1.输入11位以下手机号 2.点击获取验证码 | 提示手机号格式不正确 | P2 |\n"
)

REVISED_TABLE = (
    "| 用例编号 | 模块 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |\n"
    "| --- | --- | --- | --- | --- | --- | --- |\n"
    "| TC-001 | 登录认证 | 正确验证码登录成功 | 用户已注册且未锁定 | 1.输入手机号 2.获取验证码 3.输入正确验证码 4.点击登录 | 登录成功并返回有效token | P0 |\n"
    "| TC-002 | 登录认证 | 错误验证码登录失败 | 用户已注册 | 1.输入手机号 2.获取验证码 3.输入错误验证码 4.点击登录 | 提示验证码错误，剩余次数-1 | P0 |\n"
    "| TC-003 | 安全策略 | 验证码60秒过期失效 | 用户已获取验证码 | 1.等待61秒 2.输入旧验证码登录 | 提示验证码已过期，可重新获取 | P1 |\n"
    "| TC-004 | 安全策略 | 连续5次错误锁定10分钟 | 用户已注册 | 1.连续输错验证码5次 | 提示账号锁定10分钟并记录审计日志 | P0 |\n"
    "| TC-005 | 安全策略 | 锁定10分钟后自动解锁 | 账号处于锁定状态 | 1.等待10分钟 2.用正确验证码登录 | 登录成功，错误计数清零 | P1 |\n"
    "| TC-006 | 登录认证 | 非法手机号格式拦截 | 打开登录页 | 1.输入11位以下手机号 2.点击获取验证码 | 前端拦截并提示格式不正确 | P2 |\n"
    "| TC-007 | 安全策略 | 验证码60秒内重复获取限制 | 刚获取过验证码 | 1.60秒内再次点击获取 | 提示获取过于频繁，按钮倒计时 | P2 |\n"
)

REVIEW_JSON = (
    "```json\n"
    "{\n"
    '  "score": 8.5,\n'
    '  "passed": true,\n'
    '  "summary": "用例覆盖核心流程与安全边界，整体质量良好",\n'
    '  "issues": ["建议补充验证码重复获取频率限制用例", "建议明确 token 返回断言"]\n'
    "}\n"
    "```"
)


def detect_stage(messages: list[dict]) -> str:
    """根据 system prompt 首行角色特征识别阶段（正文可能含跨阶段关键词）"""
    sysmsg = ""
    for m in messages:
        if m.get("role") == "system":
            sysmsg = m.get("content", "")[:200]
            break
    if "资深测试架构师" in sysmsg or "Senior Test Architect" in sysmsg:
        return "analyze"
    if "评审质量" in sysmsg or "评审专家" in sysmsg or "Auditor" in sysmsg:
        return "review"
    if "精准修订" in sysmsg or ("修订" in sysmsg and "评审反馈" in sysmsg):
        return "revise"
    if "测试工程师" in sysmsg or "QA Engineer" in sysmsg:
        return "write"
    return "write"


def build_reply(messages: list[dict]) -> str:
    stage = detect_stage(messages)
    if stage == "analyze":
        return ANALYSIS_TEXT
    if stage == "review":
        return REVIEW_JSON
    if stage == "revise":
        return REVISED_TABLE
    return CASES_TABLE


def openai_chunk(
    cid: str, model: str, created: int, delta: dict, finish: str | None = None
) -> str:
    payload = {
        "id": cid,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model", "mock-llm")
    stream = bool(body.get("stream"))

    content = build_reply(messages)
    cid = f"chatcmpl-mock-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    if not stream:
        return JSONResponse(
            {
                "id": cid,
                "object": "chat.completion",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": len(content) // 2,
                    "total_tokens": 100 + len(content) // 2,
                },
            }
        )

    async def gen():
        # 首块：角色
        yield openai_chunk(cid, model, created, {"role": "assistant", "content": ""})
        # 内容按小块切分流式输出，总耗时控制在 MOCK_DELAY 左右
        chunk_size = 24
        parts = [
            content[i : i + chunk_size] for i in range(0, len(content), chunk_size)
        ]
        per = max(0.01, MOCK_DELAY / max(1, len(parts)))
        for p in parts:
            await asyncio.sleep(per)
            yield openai_chunk(cid, model, created, {"content": p})
        yield openai_chunk(cid, model, created, {}, finish="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/v1/models")
async def models():
    return {
        "object": "list",
        "data": [{"id": "mock-llm", "object": "model", "owned_by": "mock"}],
    }


if __name__ == "__main__":
    print(f"Mock LLM 服务器启动: http://127.0.0.1:{PORT}  (MOCK_DELAY={MOCK_DELAY}s)")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
