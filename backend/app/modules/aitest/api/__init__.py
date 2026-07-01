"""AI智能测试（aitest）API 路由包"""

from app.modules.aitest.api.ai import router as ai_router
from app.modules.aitest.api.attachments import router as attachments_router
from app.modules.aitest.api.comments import router as comments_router
from app.modules.aitest.api.test_projects import router as test_projects_router
from app.modules.aitest.api.versions import router as test_versions_router
from app.modules.aitest.api.reviews import router as test_reviews_router
from app.modules.aitest.api.test_cases import router as test_cases_router
from app.modules.aitest.api.generated_cases import router as generated_cases_router
from app.modules.aitest.api.operation_logs import router as operation_logs_router
from app.modules.aitest.api.dashboard import router as dashboard_router
from app.modules.aitest.api.ai_tester import router as ai_tester_router
from app.modules.aitest.api.executions import router as executions_router
from app.modules.aitest.api.case_reviews import router as case_reviews_router

__all__ = [
    "ai_router",
    "attachments_router",
    "comments_router",
    "test_projects_router",
    "test_versions_router",
    "test_reviews_router",
    "test_cases_router",
    "generated_cases_router",
    "operation_logs_router",
    "dashboard_router",
    "ai_tester_router",
    "executions_router",
    "case_reviews_router",
]
