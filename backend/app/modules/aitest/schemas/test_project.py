"""
测试项目 Pydantic 模型

定义 TestProject 和 ProjectMember 相关的请求/响应模型。
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TestProjectCreate(BaseModel):
    """创建测试项目请求"""
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: str | None = Field(None, description="项目描述")
    leader: str | None = Field(None, max_length=50, description="负责人")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")


class TestProjectUpdate(BaseModel):
    """更新测试项目请求"""
    name: str | None = Field(None, min_length=1, max_length=200, description="项目名称")
    description: str | None = Field(None, description="项目描述")
    leader: str | None = Field(None, max_length=50, description="负责人")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
    status: str | None = Field(None, description="项目状态（active/completed/archived）")


class TestProjectResponse(BaseModel):
    """测试项目响应"""
    id: int
    name: str
    description: str | None = None
    leader: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "active"
    created_by: int
    member_count: int = 0
    version_count: int = 0
    case_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectStatsResponse(BaseModel):
    """项目统计响应"""
    total: int = 0
    active: int = 0
    completed: int = 0
    archived: int = 0


class MemberAdd(BaseModel):
    """添加成员请求"""
    user_id: int = Field(..., description="用户ID")
    role: str = Field(
        ..., description="角色（admin/tester/viewer）",
    )


class MemberUpdate(BaseModel):
    """更新成员角色请求"""
    role: str = Field(
        ..., description="角色（admin/tester/viewer）",
    )


class MemberResponse(BaseModel):
    """成员响应"""
    id: int
    user_id: int
    username: str | None = None
    email: str | None = None
    department: str | None = None
    position: str | None = None
    role: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
