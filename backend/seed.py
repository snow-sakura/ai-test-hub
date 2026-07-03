"""
AI-HUB 数据库初始化脚本

创建默认管理员账号、角色和 AI 模型配置。

用法：
    python seed.py
"""

import asyncio

from sqlalchemy import select, func

from app.database import async_session_factory
from app.common.models.role import Role, UserRole
from app.common.models.user import User
from app.common.services.auth_service import hash_password
from app.modules.config_center.models.ai_model_config import AIModelConfig


async def seed_model_configs():
    """创建默认 AI 模型配置（仅当表中无数据时）"""
    async with async_session_factory() as db:
        result = await db.execute(select(func.count()).select_from(AIModelConfig))
        if result.scalar() > 0:
            print("AI 模型配置已存在，跳过")
            return

        defaults = [
            AIModelConfig(
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
            ),
            AIModelConfig(
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
            ),
            AIModelConfig(
                name="DeepSeek 编写模型",
                model_type="deepseek",
                role="writer",
                api_key="",
                base_url="https://api.deepseek.com/v1",
                model_name="deepseek-v4-flash",
                max_tokens=8192,
                temperature=0.7,
                top_p=0.9,
                is_active=True,
                created_by=1,
            ),
            AIModelConfig(
                name="DeepSeek 评审模型",
                model_type="deepseek",
                role="reviewer",
                api_key="",
                base_url="https://api.deepseek.com/v1",
                model_name="deepseek-v4-flash",
                max_tokens=8192,
                temperature=0.3,
                top_p=0.9,
                is_active=True,
                created_by=1,
            ),
        ]
        for config in defaults:
            db.add(config)
        await db.commit()
        print("已创建默认 AI 模型配置：DeepSeek V4 Flash 编写模型 + 评审模型")
        print("   模型：deepseek-v4-flash | API Key 留空，由环境变量 DEEPSEEK_API_KEY 兜底")
        print("   注意：请确保已设置环境变量 DEEPSEEK_API_KEY，否则模型将无法工作")


async def init_data():
    """初始化默认数据"""
    async with async_session_factory() as db:
        # 检查是否已有管理员
        result = await db.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()
        if existing:
            print("管理员账号已存在，跳过初始化")
        else:
            # 创建管理员角色
            admin_role = Role(
                name="超级管理员",
                code="super_admin",
                description="系统超级管理员，拥有所有权限",
                permissions=[
                    "user:*", "role:*", "system:*", "audit:*",
                    "project:*", "ai:*", "config:*",
                ],
                is_system=True,
            )
            db.add(admin_role)

            # 创建普通用户角色
            user_role = Role(
                name="普通用户",
                code="normal_user",
                description="普通用户，拥有基础功能权限",
                permissions=[
                    "project:read", "project:write",
                    "ai:generate", "ai:review", "ai:evaluate",
                ],
                is_system=True,
            )
            db.add(user_role)
            await db.flush()  # 获取角色ID

            # 创建超级管理员账号
            admin_user = User(
                username="admin",
                email="admin@aihub.com",
                hashed_password=hash_password("admin123"),
                phone="13800000000",
                department="技术部",
                position="系统管理员",
                is_active=True,
                is_superuser=True,
            )
            db.add(admin_user)
            await db.flush()  # 获取用户ID

            # 分配管理员角色
            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))

            await db.commit()
            print("初始化完成！")
            print(f"   管理员账号: admin / admin123")
            print(f"   邮箱: admin@aihub.com")

    # 始终尝试创建默认 AI 模型配置（独立于管理员初始化）
    await seed_model_configs()


if __name__ == "__main__":
    asyncio.run(init_data())
