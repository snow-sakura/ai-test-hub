"""
数据库连接模块

创建异步 SQLAlchemy 引擎和会话工厂，提供数据库会话依赖注入。
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.common.models.base import Base

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,                    # 开发环境下打印 SQL 语句
    pool_size=10,                            # 连接池大小
    max_overflow=20,                         # 最大溢出连接数
    pool_pre_ping=True,                      # 连接前检查健康状态
)

# 异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,                  # 提交后不过期，避免懒加载问题
)


async def get_db() -> AsyncSession:
    """
    数据库会话依赖注入生成器

    用法:
        async def get_user(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
