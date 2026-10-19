"""
数据库初始化脚本（一次性建库建表）

用途：全新环境从零构建 ai_hub_test 数据库。
背景：项目历史迁移链不包含早期核心表的 create_table（历史上由 create_all 建立），
     因此全新库请使用本脚本，而不是 `alembic upgrade head`。

流程：
1. 连接 MySQL 服务器，CREATE DATABASE IF NOT EXISTS
2. Base.metadata.create_all 创建全部当前模型表
3. 将 alembic 版本标记（stamp）到最新 head，之后可正常使用 alembic 增量迁移

用法（在 backend 目录）：
    source .venv/bin/activate
    python scripts/init_db.py
"""

import asyncio
import re
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.common.models.base import Base  # noqa: E402
from app.config import settings  # noqa: E402

# 与 alembic/env.py 保持一致：导入所有模型模块以注册元数据
import app.common.models  # noqa: E402,F401
import app.modules.aitest.models  # noqa: E402,F401
import app.modules.config_center.models  # noqa: E402,F401
import app.modules.system_management.models  # noqa: E402,F401
import app.modules.api_testing.models  # noqa: E402,F401


def _split_db_url(url: str) -> tuple[str, str]:
    """从 DATABASE_URL 中拆出（不含库名的服务器URL，库名）"""
    m = re.match(r"^(.*?://[^/]*)/([^?]+)(\?.*)?$", url)
    if not m:
        raise ValueError(f"无法解析 DATABASE_URL: {url}")
    return m.group(1) + (m.group(3) or ""), m.group(2)


async def init() -> None:
    server_url, db_name = _split_db_url(settings.DATABASE_URL)

    # 1. 建库
    server_engine = create_async_engine(server_url, isolation_level="AUTOCOMMIT")
    async with server_engine.connect() as conn:
        await conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    await server_engine.dispose()
    print(f"✅ 数据库 `{db_name}` 就绪")

    # 2. 建表
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print(f"✅ 已创建 {len(Base.metadata.tables)} 张表")

    # 3. stamp 到最新版本（与 alembic/versions 中 head 一致）
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "stamp", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"⚠️ alembic stamp 失败：\n{result.stderr or result.stdout}")
        sys.exit(1)
    print("✅ alembic 版本已标记为 head")


if __name__ == "__main__":
    asyncio.run(init())
