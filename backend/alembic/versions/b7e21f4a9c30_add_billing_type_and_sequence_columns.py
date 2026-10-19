"""add billing_type and generation sequence columns

Revision ID: b7e21f4a9c30
Revises: cf11e2ea706d
Create Date: 2026-10-18

新增：
- ai_model_config.billing_type     计费类型（free/paid）
- ai_generation_task.batch_id      生成序列批次ID
- ai_generation_task.queued_at     进入排队时间
- ai_generation_task.billing_type  执行时计费类型快照
"""

from alembic import op
import sqlalchemy as sa

revision = "b7e21f4a9c30"
down_revision = "cf11e2ea706d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_model_config",
        sa.Column(
            "billing_type",
            sa.String(10),
            nullable=False,
            server_default="free",
            comment="计费类型（free=免费模型，任务串行执行 / paid=付费模型，任务可并行执行）",
        ),
    )
    op.add_column(
        "ai_generation_task",
        sa.Column(
            "batch_id",
            sa.String(50),
            nullable=True,
            comment="生成序列批次ID（同一批提交的任务共享）",
        ),
    )
    op.add_column(
        "ai_generation_task",
        sa.Column(
            "queued_at", sa.DateTime(), nullable=True, comment="进入排队队列的时间"
        ),
    )
    op.add_column(
        "ai_generation_task",
        sa.Column(
            "billing_type",
            sa.String(10),
            nullable=True,
            comment="执行时编写模型的计费类型快照（free/paid）",
        ),
    )
    op.create_index(
        "ix_ai_generation_task_batch_id", "ai_generation_task", ["batch_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_ai_generation_task_batch_id", table_name="ai_generation_task")
    op.drop_column("ai_generation_task", "billing_type")
    op.drop_column("ai_generation_task", "queued_at")
    op.drop_column("ai_generation_task", "batch_id")
    op.drop_column("ai_model_config", "billing_type")
