"""create case_comment table

迁移 ID: a1b2c3d4e5f6
父级迁移: 30bf9ef33b4b
创建时间: 2026-06-16

只创建 case_comment 表，不包含其他变更。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "30bf9ef33b4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_comment",
        sa.Column("case_id", sa.Integer(), nullable=False, comment="关联用例ID"),
        sa.Column("content", sa.Text(), nullable=False, comment="评论内容"),
        sa.Column("author_id", sa.Integer(), nullable=False, comment="作者ID"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["test_case.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="用例评论",
    )
    op.create_index(
        op.f("ix_case_comment_case_id"), "case_comment", ["case_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_case_comment_case_id"), table_name="case_comment")
    op.drop_table("case_comment")
