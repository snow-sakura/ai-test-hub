"""
用例评论 API 路由

提供评论 CRUD 接口。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.database import get_db
from app.deps import get_current_active_user
from app.modules.aitest.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from app.modules.aitest.services.comment_service import (
    create_comment,
    delete_comment,
    get_comment,
    list_comments,
    update_comment,
)

router = APIRouter(prefix="/api/v1", tags=["用例评论管理"])


@router.get(
    "/cases/{case_id}/comments",
    response_model=ResponseModel[list[CommentResponse]],
)
async def list_case_comments(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用例的评论列表（按创建时间升序）"""
    comments = await list_comments(db, case_id)
    return ResponseModel(
        data=[_comment_to_response(c) for c in comments],
    )


@router.post(
    "/cases/{case_id}/comments",
    response_model=ResponseModel[CommentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_case_comment(
    case_id: int,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建用例评论"""
    comment = await create_comment(db, case_id, body.content, author_id=current_user.id)
    return ResponseModel(data=_comment_to_response(comment))


@router.put(
    "/comments/{comment_id}",
    response_model=ResponseModel[CommentResponse],
)
async def update_case_comment(
    comment_id: int,
    body: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新评论内容"""
    comment = await update_comment(db, comment_id, body.content)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在",
        )

    # 权限校验：仅评论作者可更新
    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改他人的评论",
        )

    return ResponseModel(data=_comment_to_response(comment))


@router.delete(
    "/comments/{comment_id}",
    response_model=ResponseModel,
)
async def delete_case_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除评论"""
    # 先查询评论以校验权限
    comment = await get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在",
        )

    # 权限校验：仅评论作者可删除
    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除他人的评论",
        )

    deleted = await delete_comment(db, comment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在",
        )
    return ResponseModel(message="删除成功")


def _comment_to_response(comment) -> CommentResponse:
    """将 CaseComment ORM 对象转换为 CommentResponse"""
    return CommentResponse(
        id=comment.id,
        case_id=comment.case_id,
        content=comment.content,
        author_id=comment.author_id,
        author_name=comment.author.username if comment.author else None,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )
