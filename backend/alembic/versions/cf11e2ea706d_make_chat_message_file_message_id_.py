"""make chat message file message_id nullable

Revision ID: cf11e2ea706d
Revises: 000000000001
Create Date: 2026-07-04 12:57:11.697227
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cf11e2ea706d'
down_revision: Union[str, None] = '000000000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'ai_chat_message_file', 'message_id',
        existing_type=sa.Integer,
        nullable=True,
        comment='消息ID（先上传后关联）',
    )


def downgrade() -> None:
    op.alter_column(
        'ai_chat_message_file', 'message_id',
        existing_type=sa.Integer,
        nullable=False,
        comment='消息ID',
    )
