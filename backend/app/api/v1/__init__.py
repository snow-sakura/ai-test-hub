# API v1 路由包

from fastapi import APIRouter

from app.common.api.health import router as health_router
from app.common.api.auth import router as auth_router
from app.common.api.dashboard import router as dashboard_router
from app.modules.aitest.api.ai import router as aitest_ai_router
from app.modules.aitest.api.attachments import router as aitest_attachments_router
from app.modules.aitest.api.comments import router as aitest_comments_router
from app.modules.aitest.api.projects import router as aitest_common_projects_router
from app.modules.aitest.api.test_projects import router as aitest_projects_router
from app.modules.aitest.api.versions import router as aitest_versions_router
from app.modules.aitest.api.reviews import router as aitest_reviews_router
from app.modules.aitest.api.test_cases import router as aitest_cases_router
from app.modules.aitest.api.ai_tester import router as aitest_tester_router
from app.modules.aitest.api.generated_cases import router as aitest_generated_cases_router
from app.modules.aitest.api.dashboard import router as aitest_dashboard_router
from app.modules.aitest.api.executions import router as aitest_executions_router
from app.modules.aitest.api.case_reviews import router as aitest_case_reviews_router
from app.modules.aitest.api.operation_logs import router as aitest_operation_logs_router
from app.modules.api_testing.api.environments import router as api_environments_router
from app.modules.api_testing.api.schedules import router as api_schedules_router
from app.modules.api_testing.api.dashboard_reports import router as api_dashboard_router
from app.modules.api_testing.api.projects import router as api_projects_router
from app.modules.api_testing.api.testing import router as api_testing_router
from app.modules.system_management.api.admin import router as admin_router
from app.modules.config_center.api.configs import router as configs_router
from app.modules.ai_chat.api.chat import router as ai_chat_router
from app.modules.knowledge_base.api.kb import router as kb_router

# v1 版本路由汇总
api_v1_router = APIRouter()

# 注册子路由
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(dashboard_router)
# AI 智能测试（合并）
api_v1_router.include_router(aitest_ai_router)
api_v1_router.include_router(aitest_attachments_router)
api_v1_router.include_router(aitest_comments_router)
api_v1_router.include_router(aitest_common_projects_router)
api_v1_router.include_router(aitest_projects_router)
api_v1_router.include_router(aitest_versions_router)
api_v1_router.include_router(aitest_reviews_router)
api_v1_router.include_router(aitest_cases_router)
api_v1_router.include_router(aitest_tester_router)
api_v1_router.include_router(aitest_generated_cases_router)
api_v1_router.include_router(aitest_dashboard_router)
api_v1_router.include_router(aitest_executions_router)
api_v1_router.include_router(aitest_case_reviews_router)
api_v1_router.include_router(aitest_operation_logs_router)
# 其他模块
api_v1_router.include_router(api_environments_router)
api_v1_router.include_router(api_schedules_router)
api_v1_router.include_router(api_dashboard_router)
api_v1_router.include_router(api_projects_router)
api_v1_router.include_router(api_testing_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(configs_router)
api_v1_router.include_router(ai_chat_router)
api_v1_router.include_router(kb_router)
