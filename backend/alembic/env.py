"""
Alembic 环境配置模块

配置 Alembic 迁移引擎，连接到项目中的 ORM 模型和数据库配置。
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# 将后端项目根目录加入 sys.path，确保能导入 app 包
sys.path.insert(0, str(Path(__file__).parent.parent))

# Alembic Config 对象，读取 alembic.ini
config = context.config

# 配置日志（如果 alembic.ini 中配置了日志）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ========== 导入 ORM 模型（非常重要！Alembic 通过它检测模型变更） ==========
from app.config import settings
from app.common.models.base import Base

# 导出所有模型以确保 Base.metadata 包含所有表
from app.common.models import *         # 公共模型
from app.modules.aitest.models import *         # AI智能测试模型（合并）
from app.modules.config_center.models import * # 配置中心模型
from app.modules.system_management.models import *  # 系统管理模型
from app.modules.api_testing.models import *      # API 测试模型（P1）

# 设置 Alembic 的 target_metadata（用于自动生成迁移）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式执行迁移（不连接数据库，仅生成 SQL 脚本）

    适用于生成 SQL 文件审查后再执行。
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """在线模式执行迁移的辅助函数"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    异步执行迁移（连接数据库执行）

    使用异步引擎创建连接并执行迁移。
    """
    # 使用异步引擎
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在线模式执行迁移（默认方式）

    连接到数据库并执行迁移。
    """
    asyncio.run(run_async_migrations())


# 根据 Alembic 运行上下文选择执行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
