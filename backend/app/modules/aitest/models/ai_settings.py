"""
AI 智能模式设置模型 + 系统设置

存储 AI 智能模式的全局配置以及系统级参数（站点信息、安全设置等）。
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON

from app.common.models.base import BaseModel, TimestampMixin


class AISettings(BaseModel, TimestampMixin):
    """AI 智能模式设置 + 系统设置"""
    __tablename__ = 'ai_settings'

    # ====================================================================
    # 系统设置（站点信息）
    # ====================================================================
    site_name = Column(String(100), default='AI-HUB', comment='站点名称')
    site_description = Column(String(300), default='', comment='站点描述')
    logo_url = Column(String(500), nullable=True, comment='Logo URL')
    icp_beian = Column(String(100), nullable=True, comment='备案号')

    # ====================================================================
    # 系统设置（安全策略）
    # ====================================================================
    password_min_length = Column(Integer, default=6, comment='密码最小长度')
    password_complexity = Column(String(50), default='letter_digit', comment='密码复杂度要求')
    max_login_attempts = Column(Integer, default=5, comment='最大登录尝试次数')
    login_lock_minutes = Column(Integer, default=30, comment='登录锁定时间(分钟)')
    session_timeout_minutes = Column(Integer, default=60, comment='会话超时时间(分钟)')
    password_expire_days = Column(Integer, default=90, comment='密码过期天数')

    # ====================================================================
    # 系统设置（存储）
    # ====================================================================
    upload_max_size_mb = Column(Integer, default=100, comment='最大上传大小(MB)')
    allowed_file_types = Column(String(300), default='pdf,doc,docx,md', comment='允许的文件类型')

    # ====================================================================
    # AI 模式配置
    # ====================================================================
    ai_mode_enabled = Column(Boolean, default=True, comment='启用AI模式')
    auto_trigger_on_requirement_change = Column(Boolean, default=False, comment='需求变更自动触发')
    auto_generate_report = Column(Boolean, default=False, comment='自动生成报告')
    auto_retest_on_failure = Column(Boolean, default=False, comment='失败自动重测')

    # 通知配置（JSON存储）
    notification_config = Column(JSON, nullable=True, comment='通知配置')

    # 模型配置
    provider = Column(String(50), default='', comment='AI提供商')
    api_key = Column(String(500), default='', comment='API Key')
    model_name = Column(String(100), default='', comment='模型名称')
    temperature = Column(Float, default=0.7, comment='温度参数')
    context_window = Column(Integer, default=128000, comment='上下文窗口大小')

    # 高级配置
    max_input_tokens = Column(Integer, default=128000, comment='最大输入Token')
    max_output_tokens = Column(Integer, default=4096, comment='最大输出Token')
    retry_count = Column(Integer, default=3, comment='重试次数')
    timeout_seconds = Column(Integer, default=120, comment='超时时间(秒)')
    concurrency = Column(Integer, default=1, comment='并发数')
    rate_limit_rpm = Column(Integer, default=60, comment='速率限制(RPM)')
    custom_prompt_template = Column(Text, nullable=True, comment='自定义Prompt模板')

    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建者ID')

    def __repr__(self) -> str:
        return f"<AISettings(id={self.id}, site_name='{self.site_name}')>"
