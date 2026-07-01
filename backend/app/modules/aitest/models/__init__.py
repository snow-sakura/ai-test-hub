"""AI智能测试（aitest）模块数据库模型"""

from app.modules.aitest.models.ai_task import AIGenerationTask, GeneratedTestCase
from app.modules.aitest.models.ai_settings import AISettings
from app.modules.aitest.models.ai_tester_message import AITesterMessage
from app.modules.aitest.models.ai_tester_session import AITesterSession
from app.modules.aitest.models.case_attachment import CaseAttachment
from app.modules.aitest.models.case_comment import CaseComment
from app.modules.aitest.models.generated_case_item import GeneratedCaseItem
from app.modules.aitest.models.generation_result import AIGenerationResult
from app.modules.aitest.models.operation_log import OperationLog
from app.modules.aitest.models.project import TestProject, ProjectMember
from app.modules.aitest.models.review import TestReview, ReviewAssignment
from app.modules.aitest.models.execution import TestCaseExecution
from app.modules.aitest.models.test_case import TestCase
from app.modules.aitest.models.version import TestVersion

__all__ = [
    "AIGenerationTask",
    "TestCaseExecution",
    "GeneratedTestCase",
    "AIGenerationResult",
    "AISettings",
    "AITesterSession",
    "AITesterMessage",
    "CaseAttachment",
    "CaseComment",
    "GeneratedCaseItem",
    "OperationLog",
    "TestProject",
    "ProjectMember",
    "TestReview",
    "ReviewAssignment",
    "TestCase",
    "TestVersion",
]
