"""add_test_case_execution_table

Revision ID: 7ae06c474002
Revises: cf1bf5641705
Create Date: 2026-06-17 18:26:17.070878
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ae06c474002'
down_revision: Union[str, None] = 'cf1bf5641705'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 test_case_execution 表"""
    op.create_table('test_case_execution',
        sa.Column('case_id', sa.Integer(), nullable=False, comment='关联用例ID'),
        sa.Column('status', sa.String(length=20), nullable=True,
                  comment='执行结果（pass/fail/blocked/skip）'),
        sa.Column('actual_result', sa.Text(), nullable=True, comment='实际结果描述'),
        sa.Column('executed_by', sa.Integer(), nullable=False, comment='执行人ID'),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['case_id'], ['test_case.id'], ),
        sa.ForeignKeyConstraint(['executed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """删除 test_case_execution 表"""
    op.drop_table('test_case_execution')
