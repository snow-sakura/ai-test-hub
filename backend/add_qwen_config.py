"""
添加阿里云百炼千问模型配置到数据库
"""

import asyncio

from sqlalchemy import select

from app.database import async_session_factory
from app.modules.config_center.models.ai_model_config import AIModelConfig


async def add_qwen_config():
    """添加千问模型配置"""
    async with async_session_factory() as db:
        # 检查是否已存在
        result = await db.execute(
            select(AIModelConfig).where(AIModelConfig.model_type == "qwen")
        )
        existing = result.scalar_one_or_none()
        if existing:
            print("千问模型配置已存在，跳过")
            return

        # 添加千问编写模型
        writer_config = AIModelConfig(
            name="Qwen 编写模型",
            model_type="qwen",
            role="writer",
            api_key="",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name="qwen3.7-max",
            max_tokens=8192,
            temperature=0.7,
            top_p=0.9,
            is_active=True,
            created_by=1,
        )
        db.add(writer_config)

        # 添加千问评审模型
        reviewer_config = AIModelConfig(
            name="Qwen 评审模型",
            model_type="qwen",
            role="reviewer",
            api_key="",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name="qwen3.7-max",
            max_tokens=8192,
            temperature=0.3,
            top_p=0.9,
            is_active=True,
            created_by=1,
        )
        db.add(reviewer_config)

        await db.commit()
        print("已成功添加千问模型配置！")


if __name__ == "__main__":
    asyncio.run(add_qwen_config())