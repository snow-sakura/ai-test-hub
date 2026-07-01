"""
用例评论服务

提供评论 CRUD 业务逻辑。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.aitest.models.case_comment import CaseComment


async def create_comment(
    db: AsyncSession,
    case_id: int,
    content: str,
    author_id: int,
) -> CaseComment:
    """创建评论"""
    comment = CaseComment(
        case_id=case_id,
        content=content,
        author_id=author_id,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)

    # 加载 author 关系以获取用户名
    stmt = (
        select(CaseComment)
        .options(joinedload(CaseComment.author))
        .where(CaseComment.id == comment.id)
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one()


async def list_comments(db: AsyncSession, case_id: int) -> list[CaseComment]:
    """获取用例的评论列表（按创建时间升序）"""
    stmt = (
        select(CaseComment)
        .options(joinedload(CaseComment.author))
        .where(CaseComment.case_id == case_id)
        .order_by(CaseComment.id.asc())
    )
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())


async def update_comment(
    db: AsyncSession,
    comment_id: int,
    content: str,
) -> CaseComment | None:
    """更新评论内容，评论不存在则返回 None"""
    stmt = (
        select(CaseComment)
        .options(joinedload(CaseComment.author))
        .where(CaseComment.id == comment_id)
    )
    result = await db.execute(stmt)
    comment = result.unique().scalar_one_or_none()
    if comment is None:
        return None

    comment.content = content
    await db.flush()
    await db.refresh(comment)
    return comment


async def get_comment(db: AsyncSession, comment_id: int) -> CaseComment | None:
    """获取单个评论"""
    stmt = select(CaseComment).where(CaseComment.id == comment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_comment(db: AsyncSession, comment_id: int) -> bool:
    """删除评论，评论不存在则返回 False"""
    stmt = select(CaseComment).where(CaseComment.id == comment_id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if comment is None:
        return False

    await db.delete(comment)
    await db.flush()
    return True
