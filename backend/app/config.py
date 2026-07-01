"""
应用配置模块

使用 pydantic-settings 从环境变量或 .env 文件读取配置。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """应用配置类，所有配置项从环境变量读取"""

    # ---------- 数据库 ----------
    DATABASE_URL: str = "mysql+aiomysql://snow:Wxh123456!@localhost:3306/ai_hub_test"

    # ---------- Redis ----------
    REDIS_URL: str = "redis://:redis123@localhost:6379/0"

    # ---------- JWT 认证 ----------
    SECRET_KEY: str = "ai-hub-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------- CORS ----------
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # ---------- 通用 ----------
    DEBUG: bool = True

    # ---------- AI 提供商 API ----------
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"

    # ---------- 文件上传 ----------
    UPLOAD_DIR: str = "uploads"

    # ---------- 服务端口 ----------
    APP_PORT: int = 8000

    # ---------- pydantic-settings 配置 ----------
    model_config = SettingsConfigDict(
        env_file=".env",          # 从 .env 文件读取
        env_file_encoding="utf-8",
        case_sensitive=True,      # 环境变量名区分大小写
    )


# 全局单例配置对象
settings = Settings()


def get_settings() -> Settings:
    """获取应用配置（工厂函数，保持与懒加载一致的接口）"""
    return settings
