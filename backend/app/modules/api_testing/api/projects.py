"""
API 项目管理 + 接口管理 CRUD 接口

提供 API 项目和接口的增删改查，以及 Swagger 导入功能。
"""

import json

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.common.models.user import User
from app.common.schemas.common import ResponseModel
from app.modules.api_testing.models.project import ApiProject
from app.modules.api_testing.models.endpoint import ApiEndpoint
from app.modules.api_testing.schemas.project import (
    ApiProjectCreate,
    ApiProjectResponse,
    ApiProjectSummary,
    ApiProjectUpdate,
)
from app.modules.api_testing.schemas.endpoint import (
    ApiEndpointCreate,
    ApiEndpointResponse,
    ApiEndpointSummary,
    ApiEndpointUpdate,
)

router = APIRouter(prefix="/api/v1/api-projects", tags=["API项目管理"])

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}


# ==================== 项目管理 ====================


@router.get("", response_model=ResponseModel[list[ApiProjectSummary]])
async def list_projects(
    search: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取 API 项目列表，支持按名称搜索和状态筛选"""
    stmt = select(ApiProject)

    if search:
        stmt = stmt.where(ApiProject.name.like(f"%{search}%"))
    if status_filter:
        stmt = stmt.where(ApiProject.status == status_filter)

    stmt = stmt.order_by(ApiProject.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()

    # 统计每个项目的接口数量
    data = []
    for p in projects:
        count_stmt = select(ApiEndpoint).where(ApiEndpoint.project_id == p.id)
        count_result = await db.execute(count_stmt)
        endpoint_count = len(count_result.scalars().all())

        summary = ApiProjectSummary(
            id=p.id,
            name=p.name,
            description=p.description,
            base_url=p.base_url,
            version=p.version,
            status=p.status,
            endpoint_count=endpoint_count,
        )
        data.append(summary)

    return ResponseModel(data=data)


@router.post("", response_model=ResponseModel[ApiProjectResponse], status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ApiProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建 API 项目"""
    project = ApiProject(
        name=body.name,
        description=body.description,
        base_url=body.base_url,
        swagger_url=body.swagger_url,
        version=body.version,
        created_by=current_user.id,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    return ResponseModel(data=ApiProjectResponse.model_validate(project))


@router.put("/{project_id}", response_model=ResponseModel[ApiProjectResponse])
async def update_project(
    project_id: int,
    body: ApiProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新 API 项目"""
    stmt = select(ApiProject).where(ApiProject.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.flush()
    await db.refresh(project)

    return ResponseModel(data=ApiProjectResponse.model_validate(project))


@router.delete("/{project_id}", response_model=ResponseModel)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除 API 项目"""
    stmt = select(ApiProject).where(ApiProject.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    await db.delete(project)
    await db.flush()

    return ResponseModel(message="删除成功")


# ==================== 接口管理 ====================


@router.get("/{project_id}/endpoints", response_model=ResponseModel[list[ApiEndpointResponse]])
async def list_endpoints(
    project_id: int,
    method: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目下的接口列表，支持按方法和标签筛选"""
    # 验证项目存在
    project_stmt = select(ApiProject).where(ApiProject.id == project_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    stmt = select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)

    if method:
        stmt = stmt.where(ApiEndpoint.method == method.upper())
    if tag:
        stmt = stmt.where(ApiEndpoint.tag == tag)

    stmt = stmt.order_by(ApiEndpoint.tag, ApiEndpoint.name)
    result = await db.execute(stmt)
    endpoints = result.scalars().all()

    return ResponseModel(
        data=[ApiEndpointResponse.model_validate(ep) for ep in endpoints],
    )


@router.post(
    "/{project_id}/endpoints",
    response_model=ResponseModel[ApiEndpointResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_endpoint(
    project_id: int,
    body: ApiEndpointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """在项目下创建接口"""
    # 验证项目存在
    project_stmt = select(ApiProject).where(ApiProject.id == project_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    method_upper = body.method.upper()
    if method_upper not in HTTP_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的 HTTP 方法: {body.method}",
        )

    endpoint = ApiEndpoint(
        project_id=project_id,
        name=body.name,
        path=body.path,
        method=method_upper,
        tag=body.tag,
        description=body.description,
        request_params=body.request_params,
        request_headers=body.request_headers,
        request_body=body.request_body,
        response_example=body.response_example,
    )
    db.add(endpoint)
    await db.flush()
    await db.refresh(endpoint)

    return ResponseModel(data=ApiEndpointResponse.model_validate(endpoint))


@router.put(
    "/{project_id}/endpoints/{endpoint_id}",
    response_model=ResponseModel[ApiEndpointResponse],
)
async def update_endpoint(
    project_id: int,
    endpoint_id: int,
    body: ApiEndpointUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新接口信息"""
    stmt = select(ApiEndpoint).where(
        ApiEndpoint.id == endpoint_id,
        ApiEndpoint.project_id == project_id,
    )
    result = await db.execute(stmt)
    endpoint = result.scalar_one_or_none()

    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在",
        )

    update_data = body.model_dump(exclude_unset=True)
    if "method" in update_data:
        method_upper = update_data["method"].upper()
        if method_upper not in HTTP_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的 HTTP 方法: {update_data['method']}",
            )
        update_data["method"] = method_upper

    for field, value in update_data.items():
        setattr(endpoint, field, value)

    await db.flush()
    await db.refresh(endpoint)

    return ResponseModel(data=ApiEndpointResponse.model_validate(endpoint))


@router.delete(
    "/{project_id}/endpoints/{endpoint_id}",
    response_model=ResponseModel,
)
async def delete_endpoint(
    project_id: int,
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除接口"""
    stmt = select(ApiEndpoint).where(
        ApiEndpoint.id == endpoint_id,
        ApiEndpoint.project_id == project_id,
    )
    result = await db.execute(stmt)
    endpoint = result.scalar_one_or_none()

    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在",
        )

    await db.delete(endpoint)
    await db.flush()

    return ResponseModel(message="删除成功")


# ==================== Swagger 导入 ====================


async def _parse_swagger_json(swagger_data: dict, project_id: int) -> list[ApiEndpoint]:
    """解析 Swagger/OpenAPI JSON 数据，生成 ApiEndpoint 列表"""
    endpoints = []
    paths = swagger_data.get("paths", {})

    # 获取全局的 tags/分组信息
    tags_map = {}
    for tag_item in swagger_data.get("tags", []):
        tags_map[tag_item.get("name", "")] = tag_item.get("description", "")

    for path, methods in paths.items():
        for method, detail in methods.items():
            method_upper = method.upper()
            if method_upper not in HTTP_METHODS:
                continue

            summary = detail.get("summary", "") or detail.get("operationId", "")
            tag = ""
            tags = detail.get("tags", [])
            if tags:
                tag = tags[0]

            # 解析参数
            params = []
            headers = []
            for param in detail.get("parameters", []):
                param_in = param.get("in", "")
                param_item = {
                    "key": param.get("name", ""),
                    "value": "",
                    "type": param.get("schema", {}).get("type", "string"),
                    "required": param.get("required", False),
                    "description": param.get("description", ""),
                }
                if param_in == "header":
                    headers.append(param_item)
                else:
                    params.append(param_item)

            # 解析请求体
            request_body = None
            if "requestBody" in detail:
                content = detail["requestBody"].get("content", {})
                for content_type, content_detail in content.items():
                    schema = content_detail.get("schema", {})
                    request_body = schema
                    break

            endpoint = ApiEndpoint(
                project_id=project_id,
                name=summary or f"{method_upper} {path}",
                path=path,
                method=method_upper,
                tag=tag or None,
                description=detail.get("description", ""),
                request_params=params if params else None,
                request_headers=headers if headers else None,
                request_body=request_body,
            )
            endpoints.append(endpoint)

    return endpoints


async def _parse_swagger_yaml_text(yaml_text: str, project_id: int) -> list[ApiEndpoint]:
    """尝试解析 YAML 格式的 Swagger 文档"""
    try:
        import yaml
        swagger_data = yaml.safe_load(yaml_text)
        if not isinstance(swagger_data, dict) or "paths" not in swagger_data:
            raise ValueError("无效的 Swagger 文档：缺少 paths")
        return await _parse_swagger_json(swagger_data, project_id)
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PyYAML 未安装，无法解析 YAML 格式的 Swagger 文档",
        )


class SwaggerImportRequest(BaseModel):
    """Swagger 导入请求体"""
    url: str = Field(..., description="Swagger JSON/YAML URL")
    project_id: int = Field(..., description="目标项目 ID")


@router.post("/import-swagger", response_model=ResponseModel)
async def import_swagger(
    body: SwaggerImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    从 Swagger URL 导入接口定义

    支持 JSON 和 YAML 格式的 Swagger 2.0 / OpenAPI 3.0 文档。
    """
    # 验证项目存在
    project_stmt = select(ApiProject).where(ApiProject.id == body.project_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    # 下载 Swagger 文档
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(body.url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            raw_text = resp.text
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="下载 Swagger 文档超时",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"下载 Swagger 文档失败: HTTP {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"下载 Swagger 文档失败: {str(e)}",
        )

    # 尝试解析 JSON 或 YAML
    endpoints = []
    # 先尝试 JSON 解析
    try:
        swagger_data = json.loads(raw_text)
        if isinstance(swagger_data, dict) and "paths" in swagger_data:
            endpoints = await _parse_swagger_json(swagger_data, body.project_id)
    except json.JSONDecodeError:
        pass

    # JSON 解析失败，尝试 YAML
    if not endpoints:
        try:
            endpoints = await _parse_swagger_yaml_text(raw_text, body.project_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法解析 Swagger 文档，请确认 URL 指向有效的 JSON 或 YAML 格式文档",
            )

    if not endpoints:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Swagger 文档中未找到有效的 API 路径",
        )

    # 批量创建接口
    for ep in endpoints:
        db.add(ep)
    await db.flush()

    return ResponseModel(
        message=f"成功导入 {len(endpoints)} 个接口",
        data={"count": len(endpoints)},
    )
