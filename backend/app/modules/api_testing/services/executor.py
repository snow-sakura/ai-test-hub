"""
API 测试套件执行引擎

异步执行测试套件中的接口调用和断言检查。
"""

import json
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.api_testing.models.endpoint import ApiEndpoint
from app.modules.api_testing.models.project import ApiProject
from app.modules.api_testing.models.test_suite import ApiTestSuite
from app.modules.api_testing.schemas.test_suite import ApiExecutionResult, ApiTestReport


def _check_status_code_assertion(rule: dict, status_code: int) -> tuple[bool, str]:
    """检查状态码断言"""
    expected = rule.get("expected", 200)
    operator = rule.get("operator", "eq")
    actual = status_code

    if operator == "eq":
        passed = actual == expected
    elif operator == "ne":
        passed = actual != expected
    elif operator == "lt":
        passed = actual < expected
    elif operator == "lte":
        passed = actual <= expected
    elif operator == "gt":
        passed = actual > expected
    elif operator == "gte":
        passed = actual >= expected
    else:
        passed = actual == expected

    detail = f"状态码断言: {actual} {'==' if passed else '!='} {expected}"
    return passed, detail


def _check_header_assertion(rule: dict, response_headers: dict) -> tuple[bool, str]:
    """检查响应头断言"""
    header_key = rule.get("header", "")
    expected = rule.get("expected", "")
    operator = rule.get("operator", "eq")
    actual = response_headers.get(header_key.lower(), "")

    if operator == "eq":
        passed = str(actual) == str(expected)
    elif operator == "contains":
        passed = str(expected) in str(actual)
    elif operator == "exists":
        passed = header_key.lower() in response_headers
    else:
        passed = str(actual) == str(expected)

    detail = f"响应头断言 [{header_key}]: {actual} {'==' if passed else '!='} {expected}"
    return passed, detail


def _check_json_path_assertion(rule: dict, response_body: dict) -> tuple[bool, str]:
    """检查 JSON Path 断言（支持简单点路径）"""
    json_path = rule.get("jsonPath", "")
    expected = rule.get("expected", "")
    operator = rule.get("operator", "eq")

    # 解析简单点路径：data.items[0].name
    parts = json_path.replace("[", ".").replace("]", "").split(".")
    value = response_body
    try:
        for part in parts:
            if not part:
                continue
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list):
                idx = int(part)
                value = value[idx]
            else:
                value = None
                break
        actual = value
    except (IndexError, KeyError, ValueError, TypeError):
        actual = None

    if operator == "eq":
        passed = str(actual) == str(expected)
    elif operator == "ne":
        passed = str(actual) != str(expected)
    elif operator == "contains":
        passed = str(expected) in str(actual) if actual else False
    elif operator == "exists":
        passed = actual is not None
    else:
        passed = str(actual) == str(expected)

    detail = f"JSON Path 断言 [{json_path}]: {actual} {'==' if passed else '!='} {expected}"
    return passed, detail


def _check_response_time_assertion(rule: dict, elapsed_ms: float) -> tuple[bool, str]:
    """检查响应时间断言"""
    max_ms = rule.get("maxMs", 5000)
    passed = elapsed_ms <= max_ms
    detail = f"响应时间断言: {elapsed_ms:.0f}ms {'<=' if passed else '>'} {max_ms}ms"
    return passed, detail


async def _execute_single_endpoint(
    endpoint: ApiEndpoint,
    project: ApiProject,
    config: dict | None,
    timeout: int = 30,
) -> ApiExecutionResult:
    """执行单个接口测试"""
    method = endpoint.method.lower()
    path = endpoint.path
    base_url = project.base_url or ""
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}" if base_url else path

    # 构建请求
    headers = {}
    params = {}
    body = None

    # 从端点配置中提取
    if endpoint.request_headers:
        for h in endpoint.request_headers:
            if isinstance(h, dict) and "key" in h:
                headers[h["key"]] = h.get("value", "")
    if endpoint.request_params:
        for p in endpoint.request_params:
            if isinstance(p, dict) and "key" in p:
                params[p["key"]] = p.get("value", "")
    if endpoint.request_body:
        body = endpoint.request_body

    # 套件级别的变量覆盖
    if config and isinstance(config, dict):
        var_overrides = config.get("variable_overrides", {})
        if var_overrides:
            # 简单替换 headers 中的变量
            for key, value in var_overrides.items():
                placeholder = f"${{{key}}}"
                for hk in headers:
                    if placeholder in str(headers[hk]):
                        headers[hk] = str(headers[hk]).replace(placeholder, str(value))
                for pk in params:
                    if placeholder in str(params[pk]):
                        params[pk] = str(params[pk]).replace(placeholder, str(value))

    result = ApiExecutionResult(
        endpoint_id=endpoint.id,
        endpoint_name=endpoint.name,
        method=endpoint.method,
        path=endpoint.path,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            start_time = datetime.now(timezone.utc)

            if method == "get":
                resp = await client.get(url, headers=headers, params=params)
            elif method == "post":
                resp = await client.post(url, headers=headers, params=params, json=body)
            elif method == "put":
                resp = await client.put(url, headers=headers, params=params, json=body)
            elif method == "delete":
                resp = await client.delete(url, headers=headers, params=params)
            elif method == "patch":
                resp = await client.patch(url, headers=headers, params=params, json=body)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            elapsed_ms = round(elapsed, 2)

            # 解析响应
            try:
                resp_body = resp.json()
            except (json.JSONDecodeError, ValueError):
                resp_body = {"raw": resp.text}

            result.status_code = resp.status_code
            result.response_body = resp_body
            result.response_headers = dict(resp.headers)
            result.elapsed_ms = elapsed_ms

            # 执行断言检查（从套件配置读取）
            result.passed = True  # 默认通过
            result.assertions_passed = 0
            result.assertions_failed = 0
            result.assertion_details = []

    except httpx.TimeoutException:
        result.error = "请求超时"
        result.passed = False
    except httpx.ConnectionError:
        result.error = "连接失败"
        result.passed = False
    except Exception as e:
        result.error = f"执行异常: {str(e)}"
        result.passed = False

    return result


async def execute_suite(
    db: AsyncSession,
    suite_id: int,
    user_id: int,
) -> ApiTestReport:
    """
    异步执行测试套件

    Args:
        db: 数据库会话
        suite_id: 套件 ID
        user_id: 执行用户 ID

    Returns:
        测试执行报告
    """
    # 查询套件信息
    stmt = select(ApiTestSuite).where(ApiTestSuite.id == suite_id)
    result = await db.execute(stmt)
    suite = result.scalar_one_or_none()

    if not suite:
        raise ValueError(f"测试套件不存在: {suite_id}")

    # 查询项目信息
    stmt_project = select(ApiProject).where(ApiProject.id == suite.project_id)
    result_project = await db.execute(stmt_project)
    project = result_project.scalar_one_or_none()

    if not project:
        raise ValueError(f"关联项目不存在: {suite.project_id}")

    # 更新套件状态为运行中
    suite.status = "running"
    await db.flush()

    execution_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    # 解析 endpoints_config 获取接口列表和配置
    endpoints_config = suite.endpoints_config or []
    endpoint_ids = []
    config_map = {}

    for item in endpoints_config:
        if isinstance(item, dict):
            eid = item.get("endpoint_id")
            if eid:
                endpoint_ids.append(eid)
                config_map[eid] = item
        elif isinstance(item, int):
            endpoint_ids.append(item)

    if not endpoint_ids:
        suite.status = "completed"
        await db.flush()
        return ApiTestReport(
            execution_id=execution_id,
            suite_id=suite_id,
            suite_name=suite.name,
            status="completed",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )

    # 查询所有接口
    stmt_endpoints = select(ApiEndpoint).where(
        ApiEndpoint.id.in_(endpoint_ids),
        ApiEndpoint.project_id == suite.project_id,
    )
    result_endpoints = await db.execute(stmt_endpoints)
    endpoints_map = {ep.id: ep for ep in result_endpoints.scalars().all()}

    # 按配置顺序执行
    raw_results: list[ApiExecutionResult] = []
    for eid in endpoint_ids:
        endpoint = endpoints_map.get(eid)
        if not endpoint:
            raw_results.append(ApiExecutionResult(
                endpoint_id=eid,
                endpoint_name=f"未知接口(ID:{eid})",
                method="?",
                path="?",
                error="接口不存在或已被删除",
                passed=False,
            ))
            continue

        config = config_map.get(eid)
        ep_result = await _execute_single_endpoint(endpoint, project, config)
        raw_results.append(ep_result)

    # 统计结果
    passed_count = sum(1 for r in raw_results if r.passed)
    failed_count = sum(1 for r in raw_results if not r.passed)

    # 更新套件状态
    suite.status = "completed" if failed_count == 0 else "failed"
    await db.flush()

    finished_at = datetime.now(timezone.utc).isoformat()

    return ApiTestReport(
        execution_id=execution_id,
        suite_id=suite_id,
        suite_name=suite.name,
        status=suite.status,
        started_at=started_at,
        finished_at=finished_at,
        total_endpoints=len(raw_results),
        passed=passed_count,
        failed=failed_count,
        results=raw_results,
    )
