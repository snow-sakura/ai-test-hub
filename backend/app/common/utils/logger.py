"""
日志工具模块

提供统一的日志配置和工具函数。
"""

import logging


def setup_logger(name: str = "ai_hub") -> logging.Logger:
    """
    配置并返回指定名称的日志器。

    默认输出到控制台，格式为: [时间] 级别 模块名 - 消息
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    return logger
