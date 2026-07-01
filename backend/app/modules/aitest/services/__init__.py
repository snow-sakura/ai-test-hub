"""AI智能测试（aitest）业务服务包"""

from app.modules.aitest.services.ai_service import AIService
from app.modules.aitest.services.attachment_service import (
    create_attachment,
    delete_attachment,
    get_attachment,
    list_attachments,
)
from app.modules.aitest.services.comment_service import (
    create_comment,
    delete_comment,
    get_comment,
    list_comments,
    update_comment,
)
from app.modules.aitest.services.project_service import (
    get_project_stats,
    get_project_with_counts,
    list_projects_with_counts,
    get_members_with_user,
)
from app.modules.aitest.services.review_service import (
    create_review_assignments,
    get_review_with_assignments,
    list_reviews,
)
from app.modules.aitest.services.test_case_service import (
    batch_create_test_cases,
    create_test_case,
    get_test_case,
    get_test_case_stats,
    list_test_cases,
)
from app.modules.aitest.services.version_service import (
    get_version,
    list_versions,
)

__all__ = [
    "AIService",
    # Project
    "get_project_stats",
    "get_project_with_counts",
    "list_projects_with_counts",
    "get_members_with_user",
    # Review
    "create_review_assignments",
    "get_review_with_assignments",
    "list_reviews",
    # TestCase
    "batch_create_test_cases",
    "create_test_case",
    "get_test_case",
    "get_test_case_stats",
    "list_test_cases",
    # Version
    "get_version",
    "list_versions",
    # Attachment
    "create_attachment",
    "list_attachments",
    "get_attachment",
    "delete_attachment",
    # Comment
    "create_comment",
    "list_comments",
    "get_comment",
    "update_comment",
    "delete_comment",
]
