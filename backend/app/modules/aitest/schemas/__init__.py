"""AI 测试 Pydantic 模式包"""

from app.modules.aitest.schemas.ai import (
    AIGenerationRequest,
    AIGenerationResponse,
    AIGenerationTaskSummary,
    AIModelConfigSummary,
    AIEvaluationRequest,
    AIEvaluationResponse,
    AIReportDetail,
    AIReportStats,
    AIReportSummary,
    AIReviewRequest,
    AIReviewResponse,
    AISettingsResponse,
    AISettingsUpdate,
    AITaskDetailResponse,
    FailedCaseItem,
    GeneratedTestCaseItem,
    ModuleStatItem,
    PromptConfigSummary,
)
from app.modules.aitest.schemas.attachment import AttachmentDownloadResponse, AttachmentResponse
from app.modules.aitest.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.modules.aitest.schemas.project import ProjectSummary
from app.modules.aitest.schemas.review import (
    ReviewAssignmentResponse,
    TestReviewApprove,
    TestReviewCreate,
    TestReviewDetail,
    TestReviewUpdate,
)
from app.modules.aitest.schemas.test_case import (
    ExcelImportResult,
    TestCaseBatchCreate,
    TestCaseCreate,
    TestCaseResponse,
    TestCaseStats,
    TestCaseUpdate,
)
from app.modules.aitest.schemas.dashboard import DashboardStatsResponse
from app.modules.aitest.schemas.generated_case import (
    BatchUpdateCasesRequest,
    GeneratedCaseItemResponse,
    SaveToLibraryRequest,
)
from app.modules.aitest.schemas.operation_log import OperationLogResponse
from app.modules.aitest.schemas.version import TestVersionCreate, TestVersionResponse, TestVersionUpdate

__all__ = [
    # AI
    "AIGenerationRequest",
    "AIGenerationResponse",
    "AIGenerationTaskSummary",
    "AIModelConfigSummary",
    "AIEvaluationRequest",
    "AIEvaluationResponse",
    "AIReportDetail",
    "AIReportStats",
    "AIReportSummary",
    "AIReviewRequest",
    "AIReviewResponse",
    "AISettingsResponse",
    "AISettingsUpdate",
    "AITaskDetailResponse",
    "FailedCaseItem",
    "GeneratedTestCaseItem",
    "ModuleStatItem",
    "PromptConfigSummary",
    # Attachment
    "AttachmentDownloadResponse",
    "AttachmentResponse",
    # Comment
    "CommentCreate",
    "CommentResponse",
    "CommentUpdate",
    # Project
    "ProjectSummary",
    # Review
    "ReviewAssignmentResponse",
    "ReviewCaseItem",
    "ReviewCaseUpdate",
    "ReviewStatsResponse",
    "TestReviewApprove",
    "TestReviewCreate",
    "TestReviewDetail",
    "TestReviewUpdate",
    # TestCase
    "ExcelImportResult",
    "TestCaseBatchCreate",
    "TestCaseCreate",
    "TestCaseResponse",
    "TestCaseStats",
    "TestCaseUpdate",
    # Dashboard
    "DashboardStatsResponse",
    # GeneratedCase
    "BatchUpdateCasesRequest",
    "GeneratedCaseItemResponse",
    "SaveToLibraryRequest",
    # OperationLog
    "OperationLogResponse",
    # Version
    "TestVersionCreate",
    "TestVersionResponse",
    "TestVersionUpdate",
]
