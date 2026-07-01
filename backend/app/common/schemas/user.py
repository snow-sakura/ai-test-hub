"""
认证与系统管理 Pydantic 模型模块

定义用户注册、登录、信息更新、Token 响应以及系统管理相关（角色、设置、审计日志）的请求/响应模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """用户注册请求体"""

    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """用户登录请求体"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserRoleInfo(BaseModel):
    """角色简要信息（嵌入用户响应中）"""

    id: int
    name: str
    code: str

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """用户信息响应体"""

    id: int
    username: str
    email: str
    phone: str | None = None
    avatar: str | None = None
    department: str | None = None
    position: str | None = None
    is_active: bool
    is_superuser: bool
    roles: list[UserRoleInfo] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Token 响应体"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token 刷新请求体"""

    refresh_token: str


class UserUpdate(BaseModel):
    """用户信息更新请求体"""

    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    department: str | None = None
    position: str | None = None


# ====================================================================
# 系统管理：用户管理
# ====================================================================


class AdminUserCreate(BaseModel):
    """管理员创建用户请求体"""

    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    phone: str | None = Field(None, description="手机号")
    department: str | None = Field(None, description="部门")
    position: str | None = Field(None, description="职位")
    is_active: bool = Field(True, description="是否激活")
    is_superuser: bool = Field(False, description="是否超级管理员")
    role_ids: list[int] | None = Field(None, description="关联角色ID列表")


class AdminUserUpdate(BaseModel):
    """管理员修改用户请求体"""

    email: str | None = None
    phone: str | None = None
    department: str | None = None
    position: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    role_ids: list[int] | None = Field(None, description="关联角色ID列表")


class ResetPasswordRequest(BaseModel):
    """重置密码请求体"""

    password: str = Field(..., min_length=6, max_length=100, description="新密码")


# ====================================================================
# 系统管理：角色权限
# ====================================================================


class RoleCreate(BaseModel):
    """创建角色请求体"""

    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色编码")
    description: str | None = Field(None, description="角色描述")
    permissions: dict | list | None = Field(None, description="权限配置")


class RoleUpdate(BaseModel):
    """更新角色请求体"""

    name: str | None = Field(None, max_length=50, description="角色名称")
    description: str | None = None
    permissions: dict | list | None = None


class RoleResponse(BaseModel):
    """角色信息响应体"""

    id: int
    name: str
    code: str
    description: str | None = None
    permissions: dict | list | None = None
    is_system: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ====================================================================
# 系统管理：系统设置
# ====================================================================


class SystemSettingsResponse(BaseModel):
    """系统设置响应体"""

    site_name: str = Field(default="AI-HUB", description="站点名称")
    site_description: str = Field(default="基于AI技术的一站式智能软件测试平台", description="站点描述")
    logo_url: str | None = Field(default=None, description="Logo URL")
    icp_beian: str | None = Field(default=None, description="备案号")

    # 安全设置
    password_min_length: int = Field(default=6, description="密码最小长度")
    password_complexity: str = Field(default="letter_digit", description="密码复杂度要求")
    max_login_attempts: int = Field(default=5, description="最大登录尝试次数")
    login_lock_minutes: int = Field(default=30, description="登录锁定时间(分钟)")
    session_timeout_minutes: int = Field(default=60, description="会话超时时间(分钟)")
    password_expire_days: int = Field(default=90, description="密码过期天数")

    # 存储设置
    upload_max_size_mb: int = Field(default=100, description="最大上传大小(MB)")
    allowed_file_types: str = Field(default="pdf,doc,docx,md", description="允许的文件类型")

    model_config = {"from_attributes": True}


class SystemSettingsUpdate(BaseModel):
    """更新系统设置请求体"""

    site_name: str | None = None
    site_description: str | None = None
    logo_url: str | None = None
    icp_beian: str | None = None
    password_min_length: int | None = None
    password_complexity: str | None = None
    max_login_attempts: int | None = None
    login_lock_minutes: int | None = None
    session_timeout_minutes: int | None = None
    password_expire_days: int | None = None
    upload_max_size_mb: int | None = None
    allowed_file_types: str | None = None


# ====================================================================
# 系统管理：审计日志
# ====================================================================


class AuditLogResponse(BaseModel):
    """审计日志响应体"""

    id: int
    user_id: int
    username: str
    action: str
    module: str
    target_type: str | None = None
    target_id: int | None = None
    detail: str | None = None
    ip_address: str | None = None
    status: str = "success"
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
