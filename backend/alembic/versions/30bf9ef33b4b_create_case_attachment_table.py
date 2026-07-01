"""create_case_attachment_table

Revision ID: 30bf9ef33b4b
Revises: 0221dd3017e1
Create Date: 2026-06-16 19:26:04.488528
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30bf9ef33b4b'
down_revision: Union[str, None] = '0221dd3017e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 case_attachment 表"""
    op.create_table('case_attachment',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('case_id', sa.Integer(), nullable=False, comment='关联用例ID'),
        sa.Column('file_name', sa.String(length=255), nullable=False, comment='原始文件名'),
        sa.Column('file_path', sa.String(length=500), nullable=False, comment='存储路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        sa.Column('file_type', sa.String(length=100), nullable=True, comment='MIME类型'),
        sa.Column('uploaded_by', sa.Integer(), nullable=True, comment='上传者ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['case_id'], ['test_case.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """删除 case_attachment 表"""
    op.drop_table('case_attachment')
