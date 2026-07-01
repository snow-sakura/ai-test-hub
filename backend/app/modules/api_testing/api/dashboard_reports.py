"""
API 测试看板、报告、请求历史与通知路由模块

包含看板数据聚合、报告列表/详情、请求历史 CRUD、通知列表等端点。
注意：P1-2 的执行记录模型尚未定义，以下端点当前返回模拟/空数据结构。
"""

import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.common.models.user import User
from app.common.schemas.common import ResponseModel

router = APIRouter(prefix="/api/v1/api-testing", tags=["API测试看板"])


# ======================================================================
# 看板
# ======================================================================

@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取看板聚合统计

    返回项目数、接口数、套件数、执行统计和趋势数据。
    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    # 生成最近 7 天趋势模拟数据
    trend_data = []
    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        executions = random.randint(10, 50)
        passed = random.randint(max(0, executions - 20), executions)
        failed = executions - passed
        trend_data.append({
            "date": day.strftime("%Y-%m-%d"),
            "executions": executions,
            "passed": passed,
            "failed": failed,
        })

    return ResponseModel(data={
        "total_projects": 0,
        "total_endpoints": 0,
        "total_suites": 0,
        "total_executions": 0,
        "today_executions": 0,
        "pass_rate": 0.0,
        "trend_data": trend_data,
        "method_distribution": {
            "GET": 0,
            "POST": 0,
            "PUT": 0,
            "DELETE": 0,
            "PATCH": 0,
        },
        "recent_reports": [],
    })


# ======================================================================
# 报告
# ======================================================================

@router.get("/reports")
async def list_reports(
    project_id: int | None = Query(None, description="项目ID"),
    suite_name: str | None = Query(None, description="套件名称关键词"),
    status: str | None = Query(None, description="状态"),
    start_date: str | None = Query(None, description="开始日期"),
    end_date: str | None = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取测试报告列表（分页）

    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    return ResponseModel(data={
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 20,
    })


@router.get("/reports/{report_id}")
async def get_report_detail(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取报告详情

    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    # 暂时返回空结构
    return ResponseModel(data={
        "id": report_id,
        "name": "",
        "project": {},
        "suite": {},
        "total": 0,
        "passed": 0,
        "failed": 0,
        "pass_rate": 0.0,
        "duration": 0,
        "details": [],
        "created_at": "",
    })


# ======================================================================
# 请求历史
# ======================================================================

@router.get("/history")
async def list_request_history(
    project_id: int | None = Query(None, description="项目ID"),
    methods: str | None = Query(None, description="HTTP方法（逗号分隔）"),
    status_code_min: int | None = Query(None, description="状态码下限"),
    status_code_max: int | None = Query(None, description="状态码上限"),
    start_date: str | None = Query(None, description="开始日期"),
    end_date: str | None = Query(None, description="结束日期"),
    path_keyword: str | None = Query(None, description="路径关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取请求历史列表（分页+筛选）

    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    return ResponseModel(data={
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    })


@router.get("/history/{history_id}")
async def get_request_detail(
    history_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取请求历史详情（含请求报文和响应报文）

    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    # 暂时返回空结构
    return ResponseModel(data={
        "id": history_id,
        "method": "",
        "path": "",
        "status_code": 0,
        "duration": 0,
        "request": {
            "headers": {},
            "body": None,
        },
        "response": {
            "headers": {},
            "body": None,
        },
        "created_at": "",
    })


@router.delete("/history/{history_id}")
async def delete_request_history(
    history_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除请求历史记录

    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    # 暂时返回成功（实际数据未实现时总是成功）
    return ResponseModel(message="请求历史已删除")


@router.delete("/history")
async def bulk_delete_history(
    ids: list[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量删除请求历史记录

    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    return ResponseModel(message=f"已删除 {len(ids)} 条记录")


@router.delete("/history/clear")
async def clear_all_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    清空所有请求历史记录

    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    return ResponseModel(message="已清空所有请求历史记录")


# ======================================================================
# 通知
# ======================================================================

@router.get("/notifications")
async def list_notifications(
    status: str | None = Query(None, description="状态（all/unread/read）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取通知列表（分页+筛选）

    TODO: P1-2 执行记录模型就绪后连接真实数据。
    """
    return ResponseModel(data={
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    })


@router.put("/notifications/read")
async def mark_notifications_read(
    ids: list[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量标记通知为已读

    TODO: P1-2 通知模型就绪后连接真实数据。
    """
    return ResponseModel(message=f"已标记 {len(ids)} 条通知为已读")
