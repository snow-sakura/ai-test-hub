"""
演示数据种子脚本（幂等，可重复执行）

写入内容（不含任何密钥硬编码）：
- admin 用户 / admin 角色
- ai_settings   全局 AI 配置（api_key 从环境变量 AGNES_API_KEY 读取）
- ai_model_config × 2：同一模型分别标记 paid / free，用于验证「免费串行 / 付费并行」调度
- prompt_config × 4：writer / reviewer / analyzer / improver

API Key 提供方式（脚本不落盘，缺失时该配置以空 Key 写入、可随时在页面补填）：
    export AGNES_API_KEY=sk-xxx

用法（在 backend 目录）：
    source .venv/bin/activate
    python scripts/seed_demo.py
"""

import asyncio
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.common.models.base import Base  # noqa: E402
from app.common.models.user import User  # noqa: E402
from app.common.models.role import Role  # noqa: E402
from app.common.services.auth_service import hash_password  # noqa: E402
from app.database import async_session_factory, engine  # noqa: E402
from app.modules.aitest.models.ai_settings import AISettings  # noqa: E402
from app.modules.config_center.models.ai_model_config import AIModelConfig  # noqa: E402
from app.modules.config_center.models.prompt_config import PromptConfig  # noqa: E402

# ---- 演示模型网关（OpenAI 兼容）----
GATEWAY_BASE_URL = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
GATEWAY_MODEL = os.getenv("AGNES_MODEL", "agnes-3.0-flash")


def _resolve_api_key() -> str:
    """API Key 仅从环境变量读取，脚本与数据库均不写入真实密钥"""
    return os.getenv("AGNES_API_KEY", "").strip()


WRITER_PROMPT = """你是一名资深软件测试专家，擅长根据需求编写高覆盖率的测试用例。

输出要求（必须严格遵守）：
1. 只输出一个 Markdown 表格，不要输出任何其他解释文字。
2. 表头固定为：| 编号 | 模块 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
3. 编号从 TC-001 开始连续递增。
4. 优先级只能是 P0/P1/P2/P3 之一。
5. 测试步骤写在同一单元格内，用 1. 2. 3. 编号分步。
6. 覆盖正常路径、边界条件与异常场景，用例数量不少于 8 条。"""

REVIEWER_PROMPT = """你是测试评审专家。对收到的测试用例进行严格评审，输出：
1. 总体评价（一句话）
2. 覆盖缺口：指出遗漏的功能点/边界/异常场景
3. 质量问题：步骤不可执行、预期不明确、优先级不当的具体用例编号
4. 改进建议：按编号列出应补充或修改的用例
保持简洁，使用中文。"""

ANALYZER_PROMPT = """你是需求分析专家。对需求文档进行分析，用中文简洁输出：
## 功能模块清单
## 核心业务流程
## 边界条件与约束
## 测试要点（按优先级排序）
不要输出测试用例本身，控制在 400 字以内。"""

IMPROVER_PROMPT = """你是测试用例改进专家。根据评审意见修改测试用例。
输出要求：只输出修改后的完整 Markdown 用例表格，表头固定为：
| 编号 | 模块 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
保留原有用例中合理的部分，补充评审指出的缺口，编号连续。"""


async def seed() -> None:
    api_key = _resolve_api_key()
    if api_key:
        print(f"🔑 使用 API Key: {api_key[:6]}***")
    else:
        print("⚠️ 未提供 API Key（AGNES_API_KEY），模型配置将留空，需之后在界面填写")

    async with async_session_factory() as db:
        # ---- 角色 & 用户 ----
        role = (
            (
                await db.execute(
                    select(Role).where(Role.code.in_(("admin", "super_admin")))
                )
            )
            .scalars()
            .first()
        )
        if role is None:
            role = Role(
                name="超级管理员",
                code="admin",
                description="系统内置角色",
                is_system=True,
            )
            db.add(role)
            await db.flush()

        user = (
            await db.execute(select(User).where(User.username == "admin"))
        ).scalar_one_or_none()
        if user is None:
            user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password(
                    os.getenv("SEED_ADMIN_PASSWORD", "admin123")
                ),
                is_active=True,
                is_superuser=True,
                department="QA",
                position="测试负责人",
            )
            user.roles = [role]
            db.add(user)
            await db.flush()
            print("👤 已创建用户 admin（密码见 SEED_ADMIN_PASSWORD，默认 admin123）")
        else:
            print("👤 用户 admin 已存在，跳过")

        # ---- 全局 AI 设置 ----
        settings_row = (
            await db.execute(select(AISettings).limit(1))
        ).scalar_one_or_none()
        if settings_row is None:
            db.add(
                AISettings(
                    api_key=api_key, model_name=GATEWAY_MODEL, created_by=user.id
                )
            )
            print("⚙️ 已创建 ai_settings")

        # ---- 模型配置：paid + free ----
        for billing, name, active in (
            ("paid", "Agnes Flash（付费·并行）", True),
            ("free", "Agnes Flash（免费·串行）", True),
        ):
            exists = (
                await db.execute(
                    select(AIModelConfig).where(AIModelConfig.name == name)
                )
            ).scalar_one_or_none()
            if exists is None:
                db.add(
                    AIModelConfig(
                        name=name,
                        model_type="openai",
                        role="writer",
                        api_key=api_key,
                        base_url=GATEWAY_BASE_URL,
                        model_name=GATEWAY_MODEL,
                        billing_type=billing,
                        max_tokens=4096,
                        temperature=0.5,
                        is_active=active,
                        created_by=user.id,
                    )
                )
                print(f"🧠 已创建模型配置：{name}")

        # ---- Mock 模型配置（离线体验：scripts/mock_llm_server.py）----
        for billing, name in (
            ("free", "Mock 免费模型"),
            ("paid", "Mock 付费模型"),
        ):
            exists = (
                await db.execute(
                    select(AIModelConfig).where(AIModelConfig.name == name)
                )
            ).scalar_one_or_none()
            if exists is None:
                db.add(
                    AIModelConfig(
                        name=name,
                        model_type="openai",
                        role="writer",
                        api_key="mock-key",
                        base_url="http://127.0.0.1:8030/v1",
                        model_name="mock-llm",
                        billing_type=billing,
                        max_tokens=8192,
                        temperature=0.7,
                        top_p=0.9,
                        is_active=True,
                        created_by=user.id,
                    )
                )
                print(f"🧪 已创建 Mock 模型配置：{name}")

        # ---- 提示词配置（按类型幂等）----
        for ptype, name, content in (
            ("writer", "默认用例编写提示词", None),
            ("reviewer", "默认用例评审提示词", None),
            ("analyzer", "默认需求分析提示词", None),
            ("improver", "默认用例改进提示词", None),
        ):
            exists = (
                (
                    await db.execute(
                        select(PromptConfig).where(PromptConfig.prompt_type == ptype)
                    )
                )
                .scalars()
                .first()
            )
            if exists is not None:
                print(f"📝 提示词已存在（{ptype}），跳过")
                continue
            real_content = {
                "writer": WRITER_PROMPT,
                "reviewer": REVIEWER_PROMPT,
                "analyzer": ANALYZER_PROMPT,
                "improver": IMPROVER_PROMPT,
            }[ptype]
            db.add(
                PromptConfig(
                    name=name,
                    prompt_type=ptype,
                    content=real_content,
                    is_active=True,
                    created_by=user.id,
                )
            )
            print(f"📝 已创建提示词：{name}")

        await db.commit()
    print("✅ 种子数据完成")


if __name__ == "__main__":
    asyncio.run(seed())
