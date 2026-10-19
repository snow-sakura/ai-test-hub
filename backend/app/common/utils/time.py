"""
项目统一时间工具。

约定：数据库业务时间（created_at / updated_at / completed_at 等）统一使用
「本地时区的 naive datetime」，与 MySQL 列默认值 CURRENT_TIMESTAMP（会话时区）
保持一致，避免 naive UTC 与 naive local 混用导致前端展示相差 8 小时。

如需时长计算，直接用 datetime.now() 相减即可。
"""
from datetime import datetime


def local_now() -> datetime:
    """返回本地时区的 naive datetime（与 MySQL CURRENT_TIMESTAMP 口径一致）"""
    return datetime.now()
