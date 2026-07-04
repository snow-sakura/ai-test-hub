/**
 * API 接口测试相关类型定义
 *
 * 与后端 api_testing 模块的数据结构对应，覆盖项目、接口、测试套件等场景。
 */

// ==================== API 项目 ====================

/** API 项目 */
export interface ApiProject {
  id: number
  name: string
  description: string | null
  base_url: string | null
  swagger_url: string | null
  version: string | null
  status: 'active' | 'archived'
  created_by: number
  endpoint_count?: number
  created_at: string
  updated_at: string
}

/** 创建 API 项目请求 */
export interface ApiProjectCreate {
  name: string
  description?: string | null
  base_url?: string | null
  swagger_url?: string | null
  version?: string | null
}

/** 更新 API 项目请求 */
export interface ApiProjectUpdate {
  name?: string
  description?: string | null
  base_url?: string | null
  swagger_url?: string | null
  version?: string | null
  status?: 'active' | 'archived'
}

/** 项目概要用作下拉选项 */
export interface ApiProjectOption {
  id: number
  name: string
  description: string | null
  base_url: string | null
  endpoint_count: number
}

// ==================== API 端点 ====================

/** API 端点（接口） */
export interface ApiEndpoint {
  id: number
  project_id: number
  name: string
  path: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  tag: string | null
  description: string | null
  request_params: ApiParam[] | null
  request_headers: ApiParam[] | null
  request_body: Record<string, unknown> | null
  response_example: Record<string, unknown> | null
  status: 'active' | 'disabled'
  created_at: string
  updated_at: string
}

/** API 参数 */
export interface ApiParam {
  key: string
  value: string
  type?: string
  required?: boolean
  description?: string
}

/** 创建 API 端点请求 */
export interface ApiEndpointCreate {
  name: string
  path: string
  method: string
  tag?: string | null
  description?: string | null
  request_params?: ApiParam[] | null
  request_headers?: ApiParam[] | null
  request_body?: Record<string, unknown> | null
  response_example?: Record<string, unknown> | null
}

/** 更新 API 端点请求 */
export interface ApiEndpointUpdate {
  name?: string
  path?: string
  method?: string
  tag?: string | null
  description?: string | null
  request_params?: ApiParam[] | null
  request_headers?: ApiParam[] | null
  request_body?: Record<string, unknown> | null
  response_example?: Record<string, unknown> | null
  status?: 'active' | 'disabled'
}

/** Swagger 导入请求 */
export interface SwaggerImportRequest {
  url: string
  project_id: number
}

// ==================== 测试套件 ====================

/** 测试套件 */
export interface ApiTestSuite {
  id: number
  project_id: number
  name: string
  description: string | null
  endpoints_config: EndpointConfig[] | null
  assertions: AssertionRule | null
  status: 'draft' | 'ready' | 'running' | 'completed' | 'failed'
  created_by: number
  created_at: string
  updated_at: string
}

/** 创建测试套件请求 */
export interface ApiTestSuiteCreate {
  project_id: number
  name: string
  description?: string | null
  endpoints_config?: EndpointConfig[] | null
  assertions?: AssertionRule | null
}

/** 更新测试套件请求 */
export interface ApiTestSuiteUpdate {
  name?: string
  description?: string | null
  endpoints_config?: EndpointConfig[] | null
  assertions?: AssertionRule | null
  status?: 'draft' | 'ready' | 'running' | 'completed' | 'failed'
}

/** 端点执行配置 */
export interface EndpointConfig {
  endpoint_id: number
  path?: string
  method?: string
  name?: string
  variable_overrides?: Record<string, string>
  order?: number
}

/** 断言规则 */
export interface AssertionRule {
  logic?: 'and' | 'or'
  rules: AssertionItem[]
}

/** 断言项 */
export interface AssertionItem {
  type: 'status_code' | 'response_header' | 'json_path' | 'response_time'
  operator: 'eq' | 'ne' | 'lt' | 'lte' | 'gt' | 'gte' | 'contains' | 'exists'
  expected?: string | number
  header?: string
  jsonPath?: string
  maxMs?: number
}

// ==================== 执行结果 ====================

/** 单接口执行结果 */
export interface ApiExecutionResult {
  endpoint_id: number
  endpoint_name: string
  method: string
  path: string
  status_code: number | null
  response_body: Record<string, unknown> | null
  response_headers: Record<string, string> | null
  elapsed_ms: number
  assertions_passed: number
  assertions_failed: number
  assertion_details: AssertionDetail[]
  passed: boolean
  error: string | null
}

/** 断言详情 */
export interface AssertionDetail {
  passed: boolean
  detail: string
}

/** 执行报告 */
export interface ApiTestReport {
  execution_id: string
  suite_id: number
  suite_name: string
  status: string
  started_at: string
  finished_at: string | null
  total_endpoints: number
  passed: number
  failed: number
  results: ApiExecutionResult[]
}

/** 执行结果响应 */
export interface ExecuteResponse {
  execution_id: string
  status: string
  total_endpoints: number
  passed: number
  failed: number
}

// ==================== 常量 ====================

/** HTTP 方法颜色映射 */
export const METHOD_COLORS: Record<string, string> = {
  GET: '#52C41A',
  POST: '#4A90D9',
  PUT: '#FAAD14',
  DELETE: '#FF4D4F',
  PATCH: '#9254DE',
}

/** HTTP 方法选项 */
export const METHOD_OPTIONS = [
  { value: 'GET', label: 'GET' },
  { value: 'POST', label: 'POST' },
  { value: 'PUT', label: 'PUT' },
  { value: 'DELETE', label: 'DELETE' },
  { value: 'PATCH', label: 'PATCH' },
] as const

/** 套件状态颜色映射 */
export const SUITE_STATUS_COLORS: Record<string, string> = {
  draft: '#909399',
  ready: '#409EFF',
  running: '#E6A23C',
  completed: '#67C23A',
  failed: '#F56C6C',
}

/** 套件状态选项 */
export const SUITE_STATUS_OPTIONS = [
  { value: 'draft', label: '草稿', color: '#909399' },
  { value: 'ready', label: '就绪', color: '#409EFF' },
  { value: 'running', label: '执行中', color: '#E6A23C' },
  { value: 'completed', label: '已完成', color: '#67C23A' },
  { value: 'failed', label: '失败', color: '#F56C6C' },
] as const

/** 断言类型选项 */
export const ASSERTION_TYPE_OPTIONS = [
  { value: 'status_code', label: '状态码' },
  { value: 'response_header', label: '响应头' },
  { value: 'json_path', label: 'JSON Path' },
  { value: 'response_time', label: '响应时间' },
] as const

/** 断言操作符选项 */
export const ASSERTION_OPERATORS: Record<string, { value: string; label: string }[]> = {
  status_code: [
    { value: 'eq', label: '等于' },
    { value: 'ne', label: '不等于' },
  ],
  response_header: [
    { value: 'eq', label: '等于' },
    { value: 'contains', label: '包含' },
    { value: 'exists', label: '存在' },
  ],
  json_path: [
    { value: 'eq', label: '等于' },
    { value: 'ne', label: '不等于' },
    { value: 'contains', label: '包含' },
    { value: 'exists', label: '存在' },
  ],
  response_time: [
    { value: 'lte', label: '不超过(ms)' },
  ],
}
