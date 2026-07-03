"""添加 AI 聊天室和知识库表

Revision ID: 000000000001
Revises: 710c36bc7de3
Create Date: 2026-07-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '000000000001'
down_revision: Union[str, None] = '710c36bc7de3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 知识库表
    op.create_table(
        'knowledge_base',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, comment='知识库名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('status', sa.String(20), default='active', comment='状态（active/disabled）'),
        sa.Column('embedding_model', sa.String(100), default='', comment='嵌入模型'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建者ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 知识库文档表
    op.create_table(
        'kb_document',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='知识库ID'),
        sa.Column('filename', sa.String(255), nullable=False, comment='文件名'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='文件路径'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='文件大小'),
        sa.Column('status', sa.String(20), default='pending', comment='状态（pending/processing/completed/failed）'),
        sa.Column('chunk_count', sa.Integer(), default=0, comment='分块数量'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_base.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # AI 聊天室会话表
    op.create_table(
        'ai_chat_session',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), default='新会话', comment='会话名称'),
        sa.Column('model', sa.String(100), default='', comment='使用的模型'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=True, comment='关联知识库ID'),
        sa.Column('message_count', sa.Integer(), default=0, comment='消息数'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建者ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_base.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # AI 聊天室消息表
    op.create_table(
        'ai_chat_message',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False, comment='会话ID'),
        sa.Column('role', sa.String(10), nullable=False, comment='角色（user/assistant/system）'),
        sa.Column('content', sa.Text(), nullable=False, comment='消息内容'),
        sa.Column('rating', sa.String(10), nullable=True, comment='评分（up/down）'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['ai_chat_session.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # AI 聊天室消息文件表
    op.create_table(
        'ai_chat_message_file',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False, comment='消息ID'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='文件存储路径'),
        sa.Column('file_name', sa.String(255), nullable=False, comment='原始文件名'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='文件大小'),
        sa.Column('file_type', sa.String(50), nullable=False, comment='文件类型'),
        sa.Column('is_image', sa.Boolean(), default=False, comment='是否图片'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['ai_chat_message.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ai_chat_message_file')
    op.drop_table('ai_chat_message')
    op.drop_table('ai_chat_session')
    op.drop_table('kb_document')
    op.drop_table('knowledge_base')