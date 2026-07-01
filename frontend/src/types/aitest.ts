/**
 * AI智能测试（aitest）统一类型定义
 *
 * 合并原 ai-testing 和 test-management 的类型定义，覆盖12个子功能模块。
 * 与后端 aitest 模块的数据结构对应。
 */

// ==================== AI 用例生成 ====================

/** AI 用例生成请求 */
export interface AIGenerationRequest {
  requirement_text: string
  project_id?: number
  writer_model_config_id?: number
  writer_prompt_config_id?: number
  reviewer_model_config_id?: number
  reviewer_prompt_config_id?: number
  output_mode?: 'stream' | 'complete'
  enable_auto_review?: boolean
  /** 生成管线类型 */
  pipeline_type?: 'traditional' | 'langgraph' | 'autogen'
  /** 从指定阶段继续生成（断点续传） */
  continue_from_stage?: string
  /** 继续的任务 ID（断点续传） */
  continue_task_id?: string
  /** @deprecated 已废弃，请使用 pipeline_type */
  use_langgraph?: boolean
}

/** AI 生成任务 */
export interface AIGenerationTask {
  id: number
  task_id: string
  title: string
  status: 'pending' | 'generating' | 'reviewing' | 'revising' | 'completed' | 'failed' | 'cancelled'
  progress: number
  requirement_text: string
  output_mode: string
  project_id: number | null
  created_by: number
  generated_content: Record<string, unknown> | null
  review_feedback: string | null
  final_content: Record<string, unknown> | null
  error_message: string | null
  saved_to_library?: boolean
  pipeline_type?: string
  created_at: string
  completed_at: string | null
  test_cases?: GeneratedTestCase[]
}

/** 生成的测试用例 */
export interface GeneratedTestCase {
  id?: number
  case_id: string
  title: string
  module: string
  priority: string
  precondition: string
  test_steps: string
  expected_result: string
  status: string
  created_at?: string
}

/** AI 模型配置概要（下拉选择用） */
export interface AIModelConfigSummary {
  id: number
  name: string
  model_type: string
  role: string
  model_name: string
  is_active: boolean
}

/** 提示词配置概要（下拉选择用） */
export interface PromptConfigSummary {
  id: number
  name: string
  prompt_type: string
  is_active: boolean
}

/** 评测问题项 */
export interface EvaluationIssue {
  severity: 'high' | 'mid' | 'low'
  title: string
  description: string
  fix_suggestion: string
  related_cases?: string
}

/** AI 评测请求 */
export interface AIEvaluationRequest {
  test_cases: string[]
  model_config_id: number
  prompt_config_id: number
}

/** AI 评测响应 */
export interface AIEvaluationResponse {
  overall_score: number
  issues: EvaluationIssue[]
  improvements: string[]
  detail: string
}

/** AI 评审请求 */
export interface AIReviewRequest {
  task_id: string
  test_cases: string
}

/** AI 评审响应 */
export interface AIReviewResponse {
  task_id: string
  feedback: string
  status: string
}

/** 生成表单数据（用于 InputPanel） */
export interface GenerationFormData {
  requirement_text: string
  project_id?: number
  writer_model_config_id?: number
  reviewer_model_config_id?: number
  writer_prompt_config_id?: number
  reviewer_prompt_config_id?: number
  output_mode: 'stream' | 'complete'
  enable_auto_review: boolean
  /** 生成管线类型 */
  pipeline_type?: 'traditional' | 'langgraph' | 'autogen'
  /** @deprecated 已废弃，请使用 pipeline_type */
  use_langgraph?: boolean
}

/** SSE 事件类型 */
export interface SSEEvent {
  type: 'log' | 'chunk' | 'cases' | 'status' | 'review_chunk' | 'review_complete'
    | 'revise_chunk' | 'revise_complete' | 'complete' | 'error' | 'done'
    | 'testing_stage' | 'testing_token' | 'testing_review' | 'testing_done'
  content?: string
  cases?: GeneratedTestCase[]
  status?: string
  progress?: number
  feedback?: string
  message?: string
  /** log 事件专用 */
  level?: 'info' | 'success' | 'warning' | 'error'
  /** LangGraph/AutoGen 阶段事件字段 */
  stage?: string
  label?: string
  overall_score?: number
  raw?: string
}

// ==================== 测试项目管理 ====================

export interface TestProject {
  id: number
  name: string
  description: string | null
  leader: string | null
  start_date: string | null
  end_date: string | null
  status: 'active' | 'completed' | 'archived'
  created_by: number
  member_count: number
  version_count: number
  case_count: number
  created_at: string
  updated_at: string
}

// ==================== 项目统计 ====================

export interface ProjectStats {
  total: number
  active: number
  completed: number
  archived: number
}

export interface TestProjectCreate {
  name: string
  description?: string | null
  leader?: string | null
  start_date?: string | null
  end_date?: string | null
}

export interface TestProjectUpdate {
  name?: string
  description?: string | null
  leader?: string | null
  start_date?: string | null
  end_date?: string | null
  status?: 'active' | 'completed' | 'archived'
}

// ==================== 项目成员 ====================

export interface ProjectMember {
  id: number
  user_id: number
  username: string | null
  email: string | null
  department?: string | null
  position?: string | null
  role: 'admin' | 'tester' | 'viewer'
  created_at: string
}

export interface MemberAdd {
  user_id: number
  role: 'admin' | 'tester' | 'viewer'
}

// ==================== 测试版本 ====================

export interface TestVersion {
  id: number
  project_id: number
  name: string
  description: string | null
  changelog: string | null
  status: 'released' | 'in_progress' | 'obsolete'
  project_name: string | null
  created_by: number
  created_at: string
  updated_at: string
}

export interface TestVersionCreate {
  project_id: number
  name: string
  description?: string | null
  changelog?: string | null
}

export interface TestVersionUpdate {
  name?: string
  description?: string | null
  changelog?: string | null
  status?: 'released' | 'in_progress' | 'obsolete'
}

// ==================== 用例评审 ====================

export interface TestReview {
  id: number
  project_id: number
  project_name: string | null
  name: string
  status: 'pending' | 'passed' | 'rejected'
  cases: any[] | null
  conclusion: string | null
  created_by: number
  creator_name: string | null
  assignments: ReviewAssignment[] | null
  created_at: string
  updated_at: string
}

export interface ReviewAssignment {
  id: number
  review_id: number
  user_id: number
  username: string | null
  status: 'pending' | 'approved' | 'rejected'
  comment: string | null
  created_at: string | null
}

export interface TestReviewCreate {
  project_id: number
  name: string
  cases?: any[] | null
  reviewer_ids?: number[] | null
}

export interface TestReviewUpdate {
  name?: string
  cases?: any[] | null
}

export interface TestReviewApprove {
  action: 'pass' | 'reject'
  conclusion?: string | null
}

// ==================== 测试用例 ====================

export interface TestCase {
  id: number
  project_id: number | null
  version_id: number | null
  module: string | null
  name: string
  description: string | null
  priority: 'p0' | 'p1' | 'p2' | 'p3'
  precondition: string | null
  test_steps: string | null
  expected_result: string | null
  status: 'draft' | 'active' | 'deprecated'
  test_type: 'functional' | 'api' | 'ui' | 'app'
  source: 'ai_generated' | 'manual' | 'imported'
  tags: string[] | null
  created_by: number
  created_at: string | null
  updated_at: string | null
}

export interface TestCaseCreate {
  project_id?: number | null
  version_id?: number | null
  module?: string | null
  name: string
  description?: string | null
  priority?: string
  precondition?: string | null
  test_steps?: string | null
  expected_result?: string | null
  status?: string
  test_type?: string
  source?: string
  tags?: string[] | null
}

export interface TestCaseStats {
  total: number
  by_type: Record<string, number>
  by_priority: Record<string, number>
  by_status: Record<string, number>
}

// ==================== 测试用例执行 ====================

export interface TestCaseExecution {
  id: number
  case_id: number
  status: 'pass' | 'fail' | 'blocked' | 'skip'
  actual_result: string | null
  executed_by: number
  executor_name?: string
  created_at: string | null
}

export interface TestCaseExecuteRequest {
  status: 'pass' | 'fail' | 'blocked' | 'skip'
  actual_result?: string
}

/** 用例关联的评审摘要 */
export interface CaseReviewSummary {
  id: number
  name: string
  status: string
  conclusion: string | null
  creator_name: string | null
  created_at: string | null
}

// ==================== AI 智能模式配置 ====================

export interface AISettings {
  ai_mode_enabled: boolean
  auto_trigger_on_requirement_change: boolean
  auto_generate_report: boolean
  auto_retest_on_failure: boolean
  notification_config: Record<string, unknown> | null
  provider: string
  api_key: string
  model_name: string
  temperature: number
  context_window: number
  max_input_tokens: number
  max_output_tokens: number
  retry_count: number
  timeout_seconds: number
  concurrency: number
  rate_limit_rpm: number
  custom_prompt_template: string | null
  id: number
  created_by: number
  created_at: string
  updated_at: string
}

export interface AISettingsUpdate {
  ai_mode_enabled?: boolean
  auto_trigger_on_requirement_change?: boolean
  auto_generate_report?: boolean
  auto_retest_on_failure?: boolean
  notification_config?: Record<string, unknown> | null
  provider?: string
  api_key?: string
  model_name?: string
  temperature?: number
  context_window?: number
  max_input_tokens?: number
  max_output_tokens?: number
  retry_count?: number
  timeout_seconds?: number
  concurrency?: number
  rate_limit_rpm?: number
  custom_prompt_template?: string | null
}

// ==================== 常量 ====================

export const PROJECT_STATUS_OPTIONS = [
  { value: 'active', label: '进行中', color: '#409EFF' },
  { value: 'completed', label: '已完成', color: '#67C23A' },
  { value: 'archived', label: '已归档', color: '#909399' },
] as const

export const ROLE_OPTIONS = [
  { value: 'admin', label: '管理员', color: '#C67B5C' },
  { value: 'tester', label: '测试工程师', color: '#409EFF' },
  { value: 'viewer', label: '访客', color: '#909399' },
] as const

export const ROLE_COLORS: Record<string, string> = {
  admin: '#C67B5C',
  tester: '#409EFF',
  viewer: '#909399',
}

export const VERSION_STATUS_OPTIONS = [
  { value: 'released', label: '已发布', color: '#67C23A' },
  { value: 'in_progress', label: '进行中', color: '#409EFF' },
  { value: 'obsolete', label: '已废弃', color: '#909399' },
] as const

export const REVIEW_STATUS_OPTIONS = [
  { value: 'pending', label: '待评审', color: '#909399' },
  { value: 'passed', label: '通过', color: '#67C23A' },
  { value: 'rejected', label: '驳回', color: '#F56C6C' },
] as const

// ==================== AI 评测师 ====================

export interface AITesterSession {
  id: number
  name: string
  model: string
  message_count: number
  created_by: number
  created_at: string | null
  updated_at: string | null
  first_message?: string | null
}

export interface AITesterSessionCreate {
  name: string
  model?: string
}

export interface AITesterSessionUpdate {
  name: string
}

export interface AITesterMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  rating: string | null
  created_at: string | null
}

export interface AITesterChatRequest {
  message: string
  model?: string
}

export interface AITesterMessageRating {
  rating: 'up' | 'down' | null
}

// ==================== 用例附件 ====================

export interface CaseAttachment {
  id: number
  case_id: number
  file_name: string
  file_size: number
  file_type: string
  uploaded_by: number | null
  created_at: string | null
}

// ==================== 用例评论 ====================

export interface CaseComment {
  id: number
  case_id: number
  content: string
  author_id: number
  author_name: string
  created_at: string | null
  updated_at: string | null
}

export interface CaseCommentCreate {
  content: string
}

export interface CaseCommentUpdate {
  content: string
}

// ==================== AI 生成候选用例 ====================

export interface GeneratedCaseItem {
  id: number
  task_id: number
  title: string
  priority: string
  module: string | null
  precondition: string | null
  test_steps: string | null
  expected_result: string | null
  tags: string | null
  status: 'pending' | 'adopted' | 'discarded'
  sort_order: number
  created_at: string | null
}

export interface BatchUpdateCasesRequest {
  case_ids: number[]
  status: 'adopted' | 'discarded' | 'pending'
}

export interface SaveToLibraryRequest {
  project_id?: number
  case_ids?: number[]
}

// ==================== 仪表盘统计 ====================

export interface DashboardStats {
  project_count: number
  case_count: number
  version_count: number
  review_count: number
  task_count: number
  completed_task_count: number
  member_count: number
  case_by_priority: Record<string, number>
  case_by_type: Record<string, number>
  case_by_status: Record<string, number>
  recent_activities: OperationLog[]
}

// ==================== 操作日志 ====================

export interface OperationLog {
  id: number
  entity_type: string
  entity_id: number
  action: string
  operator_id: number | null
  detail: Record<string, unknown> | null
  created_at: string | null
}

// ==================== 配置检查 ====================

export interface ConfigCheckResult {
  models_configured: boolean
  prompts_configured: boolean
  model_count: number
  prompt_count: number
  status: string
}

export interface TestConnectionRequest {
  provider: string
  api_key: string
  base_url: string
  model_name: string
  max_tokens?: number
  temperature?: number
  top_p?: number
}

export interface TestConnectionResult {
  success: boolean
  message: string
  response: string | null
  model: string
}
