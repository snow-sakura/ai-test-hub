"""
仪表盘接口模块

提供首页仪表盘所需的统计数据、功能模块列表等 RESTful 接口。
"""

from fastapi import APIRouter

from app.common.schemas.common import ResponseModel
from app.common.schemas.dashboard import DashboardStats, ModuleInfo

router = APIRouter(prefix="/api/v1/dashboard", tags=["仪表盘"])

# 功能模块预定义列表（按优先级排序）
MODULES: list[ModuleInfo] = [
    ModuleInfo(
        key="aitest",
        name="AI智能测试",
        description="项目、版本、用例、评审、AI生成、评测全流程管理",
        icon="MagicStick",
        color="#C67B5C",
        path="/modules/aitest/dashboard",
        meta="12个子模块",
    ),
    ModuleInfo(
        key="api-testing",
        name="API接口测试",
        description="HTTP/WebSocket接口测试与自动化",
        icon="Connection",
        color="#D4A574",
        path="/modules/api-testing/dashboard",
        meta="4个子模块",
    ),
    ModuleInfo(
        key="ui-automation",
        name="UI自动化测试",
        description="Web端UI自动化测试脚本录制与执行",
        icon="Monitor",
        color="#C67B5C",
        path="/modules/ui-automation",
        meta="5个子模块",
    ),
    ModuleInfo(
        key="app-automation",
        name="APP自动化测试",
        description="移动端APP自动化测试",
        icon="Iphone",
        color="#D4A574",
        path="/modules/app-automation",
        meta="4个子模块",
    ),
    ModuleInfo(
        key="configuration",
        name="配置中心",
        description="AI模型、提示词、环境统一配置",
        icon="Setting",
        color="#D4A574",
        path="/modules/configuration/ai-models",
        meta="3个子模块",
    ),
    ModuleInfo(
        key="ai-chat",
        name="AI聊天室",
        description="AI智能对话助手，随时获取测试建议",
        icon="ChatDotSquare",
        color="#C67B5C",
        path="/modules/ai-chat",
    ),
    ModuleInfo(
        key="knowledge-base",
        name="知识库",
        description="测试知识沉淀与共享",
        icon="Notebook",
        color="#D4A574",
        path="/modules/knowledge-base",
        meta="4个子模块",
    ),
    ModuleInfo(
        key="system-admin",
        name="系统管理",
        description="用户、角色、权限、审计管理",
        icon="Tools",
        color="#C67B5C",
        path="/modules/system-admin/users",
        meta="4个子模块",
    ),
]


@router.get("/stats", response_model=ResponseModel[DashboardStats])
async def get_dashboard_stats():
    """
    获取仪表盘统计数据

    返回项目总数、测试用例总数、今日执行次数和通过率。
    当前返回硬编码 0 值，后续任务完善时将填充真实数据。
    """
    return ResponseModel(data=DashboardStats())


@router.get("/modules", response_model=ResponseModel[list[ModuleInfo]])
async def get_dashboard_modules():
    """
    获取功能模块列表

    返回首页仪表盘展示的 9 个功能模块信息，
    包括图标、名称、描述、路由路径等。
    """
    return ResponseModel(data=MODULES)
