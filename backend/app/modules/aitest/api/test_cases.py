"""
测试用例 CRUD API 路由

提供测试用例的增删改查及批量创建接口。
TestCase 是跨模块共享的核心实体，其他模块也可通过内部 Service 调用。
"""

import io
import logging

from fastapi import APIRouter, Depends, File as FastAPIFile, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.database import get_db
from app.deps import get_current_active_user
from app.modules.aitest.models.execution import TestCaseExecution
from app.modules.aitest.models.test_case import TestCase

logger = logging.getLogger(__name__)
from app.modules.aitest.schemas.test_case import (
    TestCaseBatchCreate,
    TestCaseCreate,
    TestCaseResponse,
    TestCaseStats,
    TestCaseUpdate,
)
from app.modules.aitest.services.test_case_service import (
    batch_create_test_cases,
    create_test_case,
    get_test_case,
    get_test_case_stats,
    list_test_cases,
)

router = APIRouter(prefix="/api/v1/test-cases", tags=["测试用例管理"])


@router.get("", response_model=ResponseModel[list[TestCaseResponse]])
async def list_test_cases_api(
    project_id: int | None = Query(None, description="按项目筛选"),
    version_id: int | None = Query(None, description="按版本筛选"),
    test_type: str | None = Query(None, description="测试类型（functional/api/ui/app）"),
    status: str | None = Query(None, description="用例状态（draft/active/deprecated）"),
    priority: str | None = Query(None, description="优先级（p0/p1/p2/p3）"),
    search: str | None = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取测试用例列表"""
    cases = await list_test_cases(
        db,
        project_id=project_id,
        version_id=version_id,
        test_type=test_type,
        status=status,
        priority=priority,
        search=search,
    )

    # 批量查询最新执行结果，避免 N+1
    exec_map: dict[int, str] = {}
    if cases:
        case_ids = [c.id for c in cases]
        exec_result = await db.execute(
            select(TestCaseExecution)
            .where(TestCaseExecution.case_id.in_(case_ids))
            .order_by(TestCaseExecution.case_id, TestCaseExecution.created_at.desc()),
        )
        for exec_record in exec_result.scalars().all():
            if exec_record.case_id not in exec_map:
                exec_map[exec_record.case_id] = exec_record.status

    data = []
    for c in cases:
        resp = TestCaseResponse.model_validate(c)
        resp.latest_execution_status = exec_map.get(c.id)
        data.append(resp)

    return ResponseModel(data=data)


@router.post("", response_model=ResponseModel[TestCaseResponse], status_code=status.HTTP_201_CREATED)
async def create_test_case_api(
    body: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建单个测试用例"""
    case = await create_test_case(db, body, created_by=current_user.id)
    return ResponseModel(data=TestCaseResponse.model_validate(case))


@router.post("/batch", response_model=ResponseModel[list[TestCaseResponse]], status_code=status.HTTP_201_CREATED)
async def batch_create(
    body: TestCaseBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量创建测试用例（供 AI 模块调用）"""
    cases = await batch_create_test_cases(db, body.cases, created_by=current_user.id)
    return ResponseModel(
        data=[TestCaseResponse.model_validate(c) for c in cases],
    )


@router.get("/stats", response_model=ResponseModel[TestCaseStats])
async def test_case_stats(
    project_id: int = Query(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取测试用例统计"""
    stats = await get_test_case_stats(db, project_id)
    return ResponseModel(data=TestCaseStats(**stats))


# ======================================================================
# 多格式导入导出（导出路由必须定义在 /{case_id} 之前，避免 "export" 被作为 case_id 匹配）
# ======================================================================

# 支持的文件扩展名 → 格式名称映射
EXPORT_FORMATS = {"xlsx", "csv", "md", "xmind"}
IMPORT_EXTENSIONS = {".xlsx", ".xls", ".csv", ".md", ".xmind", ".mm"}

# 格式 → MIME 类型映射
FORMAT_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "md": "text/markdown",
    "xmind": "application/x-xmind",
}

# 格式 → 文件扩展名
FORMAT_EXTENSIONS = {
    "xlsx": ".xlsx",
    "csv": ".csv",
    "md": ".md",
    "xmind": ".xmind",
}


@router.get("/export", response_model=None)
async def export_test_cases(
    format: str = Query("xlsx", description=f"导出格式：{'/'.join(EXPORT_FORMATS)}"),
    project_id: int | None = Query(None, description="按项目筛选"),
    version_id: int | None = Query(None, description="按版本筛选"),
    test_type: str | None = Query(None, description="测试类型"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    导出测试用例，支持多种格式：
    - xlsx: Excel 文件
    - csv: CSV 文件
    - md: Markdown 文件
    - xmind: XMind 思维导图
    """
    if format not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的导出格式：{format}，支持：{'/'.join(EXPORT_FORMATS)}",
        )

    from app.modules.aitest.services.test_case_service import list_test_cases
    cases = await list_test_cases(
        db, project_id=project_id, version_id=version_id, test_type=test_type,
    )

    ext = FORMAT_EXTENSIONS.get(format, ".xlsx")
    filename = f"test_cases_{project_id or 'all'}{ext}"
    media_type = FORMAT_MEDIA_TYPES.get(format, "application/octet-stream")

    if format == "csv":
        return _export_csv(cases, filename)
    elif format == "md":
        return _export_markdown(cases, filename)
    elif format == "xmind":
        return _export_xmind(cases, filename)
    else:
        # 默认 xlsx
        return _export_xlsx(cases, filename)


def _export_xlsx(cases: list, filename: str) -> StreamingResponse:
    """导出为 Excel .xlsx"""
    from app.modules.aitest.services.excel_handler import export_cases_to_xlsx
    excel_bytes = export_cases_to_xlsx(cases, project_name=filename.replace(".xlsx", ""))
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type=FORMAT_MEDIA_TYPES["xlsx"],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _export_csv(cases: list, filename: str) -> StreamingResponse:
    """导出为 CSV"""
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["用例标题", "模块", "优先级", "前置条件", "测试步骤", "预期结果", "测试类型", "状态"])
    for case in cases:
        writer.writerow([
            case.name, case.module or "", case.priority,
            case.precondition or "", case.test_steps or "",
            case.expected_result or "", case.test_type or "", case.status,
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=FORMAT_MEDIA_TYPES["csv"],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _export_markdown(cases: list, filename: str) -> StreamingResponse:
    """导出为 Markdown"""
    from app.modules.aitest.services.excel_handler import export_cases_to_markdown
    md_text = export_cases_to_markdown(cases)
    return StreamingResponse(
        iter([md_text]),
        media_type=FORMAT_MEDIA_TYPES["md"],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _export_xmind(cases: list, filename: str) -> StreamingResponse:
    """导出为 XMind"""
    from app.modules.aitest.services.excel_handler import export_cases_to_xmind
    xmind_bytes = export_cases_to_xmind(cases)
    return StreamingResponse(
        io.BytesIO(xmind_bytes),
        media_type=FORMAT_MEDIA_TYPES["xmind"],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{case_id}", response_model=ResponseModel[TestCaseResponse])
async def get_test_case_api(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用例详情"""
    case = await get_test_case(db, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用例不存在",
        )
    return ResponseModel(data=TestCaseResponse.model_validate(case))


@router.put("/{case_id}", response_model=ResponseModel[TestCaseResponse])
async def update_test_case(
    case_id: int,
    body: TestCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新测试用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id),
    )
    case = result.scalar_one_or_none()

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用例不存在",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    await db.flush()
    await db.refresh(case)
    return ResponseModel(data=TestCaseResponse.model_validate(case))


@router.delete("/{case_id}", response_model=ResponseModel)
async def delete_test_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除测试用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id),
    )
    case = result.scalar_one_or_none()

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用例不存在",
        )

    await db.delete(case)
    await db.flush()
    return ResponseModel(message="删除成功")



@router.post("/import", response_model=ResponseModel)
async def import_test_cases(
    file: UploadFile = FastAPIFile(..., description=f"导入文件，支持扩展名：{'/'.join(IMPORT_EXTENSIONS)}"),
    project_id: int = Query(..., description="目标项目ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    从文件导入测试用例，支持多种格式：
    - .xlsx / .xls: Excel 文件
    - .csv: CSV 文件
    - .md: Markdown 文件
    - .xmind / .mm: XMind / FreeMind 思维导图
    """
    # 校验项目存在
    from app.modules.aitest.models.project import TestProject
    proj_result = await db.execute(
        select(TestProject).where(TestProject.id == project_id),
    )
    project = proj_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    import os
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in IMPORT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型：{ext}，支持：{'/'.join(IMPORT_EXTENSIONS)}",
        )

    content_bytes = await file.read()
    from app.modules.aitest.services import excel_handler

    try:
        if ext in (".xlsx", ".xls"):
            parsed = excel_handler.parse_xlsx_cases(content_bytes)
        elif ext == ".csv":
            parsed = excel_handler.parse_csv_cases(content_bytes)
        elif ext == ".md":
            text = content_bytes.decode("utf-8-sig")
            parsed = excel_handler.parse_markdown_cases(text)
        elif ext in (".xmind", ".mm"):
            parsed = excel_handler.parse_mindmap_cases(content_bytes)
        else:
            parsed = []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件解析失败：{str(e)}",
        )

    imported_count = 0
    errors: list[str] = []
    for row_idx, item in enumerate(parsed, 2):
        try:
            case = TestCase(
                project_id=project_id,
                name=item["name"],
                module=item.get("module"),
                priority=item.get("priority", "p2"),
                precondition=item.get("precondition"),
                test_steps=item.get("test_steps"),
                expected_result=item.get("expected_result"),
                test_type=item.get("test_type", "functional"),
                status=item.get("status", "active"),
                tags=item.get("tags"),
                source="imported",
                created_by=current_user.id,
                version_id=None,
            )
            db.add(case)
            imported_count += 1
        except Exception as e:
            errors.append(f"第 {row_idx} 行导入失败: {str(e)}")

    await db.flush()

    return ResponseModel(
        data={"imported": imported_count, "errors": errors},
        message=f"成功导入 {imported_count} 个用例" + (f"，{len(errors)} 个错误" if errors else ""),
    )


# ======================================================================
# 批量操作
# ======================================================================


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: list[int] = Field(..., description="用例 ID 列表")


@router.post("/batch-delete", response_model=ResponseModel)
async def batch_delete_test_cases(
    body: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量删除测试用例"""
    if not body.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供要删除的用例 ID 列表",
        )
    result = await db.execute(
        select(TestCase).where(TestCase.id.in_(body.ids)),
    )
    cases = result.scalars().all()
    for case in cases:
        await db.delete(case)
    await db.flush()
    return ResponseModel(message=f"成功删除 {len(cases)} 个用例")
