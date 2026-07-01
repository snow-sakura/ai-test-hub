/**
 * AI智能测试（aitest）统一 API 封装
 *
 * 合并原 ai-testing 和 test-management 的所有接口调用。
 * 覆盖12个子功能模块：项目管理、版本管理、项目成员、用例列表、用例评审、
 * AI用例生成、AI生成记录、AI评测师、AI模型配置、AI提示词配置、生成行为配置、智能模式配置。
 */

import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type {
  AIGenerationRequest,
  AIGenerationTask,
  AIEvaluationRequest,
  AIEvaluationResponse,
  AIReviewRequest,
  AIReviewResponse,
  AIModelConfigSummary,
  AISettings,
  AISettingsUpdate,
  PromptConfigSummary,
  TestProject,
  TestProjectCreate,
  TestProjectUpdate,
  ProjectStats,
  ProjectMember,
  MemberAdd,
  TestVersion,
  TestVersionCreate,
  TestVersionUpdate,
  TestReview,
  TestReviewCreate,
  TestReviewUpdate,
  TestReviewApprove,
  TestCase,
  TestCaseCreate,
  TestCaseStats,
  TestCaseExecution,
  TestCaseExecuteRequest,
  CaseReviewSummary,
  AITesterSession,
  AITesterSessionCreate,
  AITesterSessionUpdate,
  AITesterMessage,
  AITesterChatRequest,
  AITesterMessageRating,
  CaseAttachment,
  CaseComment,
  CaseCommentCreate,
  CaseCommentUpdate,
  GeneratedCaseItem,
  BatchUpdateCasesRequest,
  SaveToLibraryRequest,
  DashboardStats,
  OperationLog,
  ConfigCheckResult,
  TestConnectionRequest,
  TestConnectionResult,
} from '@/types/aitest'
import type { ProjectSummary } from '@/types/project'
import type { AdminUserInfo } from '@/types/admin'
import client from './client'

/** AI智能测试 API */
export const aitestApi = {
  // ======================================================================
  // AI 用例生成
  // ======================================================================

  createGenerationTask(data: AIGenerationRequest): Promise<ApiResponse<AIGenerationTask>> {
    return client.post('/v1/ai/generate', data).then((res) => res.data)
  },

  getStreamUrl(taskId: string): string {
    return `${client.defaults.baseURL}/v1/ai/generate/${taskId}/stream`
  },

  getTaskList(page = 1, pageSize = 20): Promise<ApiResponse<AIGenerationTask[]>> {
    return client.get('/v1/ai/tasks', { params: { page, page_size: pageSize } }).then((res) => res.data)
  },

  getTaskDetail(taskId: string): Promise<ApiResponse<AIGenerationTask>> {
    return client.get(`/v1/ai/tasks/${taskId}`).then((res) => res.data)
  },

  // ======================================================================
  // AI 评测
  // ======================================================================

  evaluateTestCases(data: AIEvaluationRequest): Promise<ApiResponse<AIEvaluationResponse>> {
    return client.post('/v1/ai/evaluate', data).then((res) => res.data)
  },

  // ======================================================================
  // AI 评审
  // ======================================================================

  reviewTestCases(data: AIReviewRequest): Promise<ApiResponse<AIReviewResponse>> {
    return client.post('/v1/ai/review', data).then((res) => res.data)
  },

  // ======================================================================
  // AI 模型/提示词配置（下拉选择）
  // ======================================================================

  getModelList(role?: string): Promise<ApiResponse<AIModelConfigSummary[]>> {
    return client.get('/v1/ai/models', { params: { role } }).then((res) => res.data)
  },

  getPromptList(promptType?: string): Promise<ApiResponse<PromptConfigSummary[]>> {
    return client.get('/v1/ai/prompts', { params: { prompt_type: promptType } }).then((res) => res.data)
  },

  getProjectSummaryList(): Promise<ApiResponse<ProjectSummary[]>> {
    return client.get('/v1/ai/projects').then((res) => res.data)
  },

  // ======================================================================
  // AI 智能模式配置
  // ======================================================================

  getSettings(): Promise<ApiResponse<AISettings>> {
    return client.get('/v1/ai/settings').then((res) => res.data)
  },

  updateSettings(data: AISettingsUpdate): Promise<ApiResponse<AISettings>> {
    return client.put('/v1/ai/settings', data).then((res) => res.data)
  },

  // ======================================================================
  // 项目管理
  // ======================================================================

  listProjects(params?: { search?: string; status?: string; page?: number; page_size?: number }): Promise<PaginatedResponse<TestProject>> {
    return client.get('/v1/test-projects', { params }).then((res) => res.data)
  },

  createProject(data: TestProjectCreate): Promise<ApiResponse<TestProject>> {
    return client.post('/v1/test-projects', data).then((res) => res.data)
  },

  getProject(id: number): Promise<ApiResponse<TestProject>> {
    return client.get(`/v1/test-projects/${id}`).then((res) => res.data)
  },

  updateProject(id: number, data: TestProjectUpdate): Promise<ApiResponse<TestProject>> {
    return client.put(`/v1/test-projects/${id}`, data).then((res) => res.data)
  },

  deleteProject(id: number): Promise<ApiResponse<null>> {
    return client.delete(`/v1/test-projects/${id}`).then((res) => res.data)
  },

  /** 批量删除项目 */
  batchDeleteTestProjects(ids: number[]): Promise<ApiResponse<null>> {
    return client.post('/v1/test-projects/batch-delete', { ids }).then((res) => res.data)
  },

  /** 获取项目统计 */
  getProjectStats(): Promise<ApiResponse<ProjectStats>> {
    return client.get('/v1/test-projects/stats').then((res) => res.data)
  },

  /** 批量更新项目 */
  batchUpdateProjects(ids: number[], data: TestProjectUpdate): Promise<ApiResponse<null>> {
    return client.post('/v1/test-projects/batch-update', { ids, data }).then((res) => res.data)
  },

  // ======================================================================
  // 成员管理
  // ======================================================================

  listMembers(projectId: number): Promise<ApiResponse<ProjectMember[]>> {
    return client.get(`/v1/test-projects/${projectId}/members`).then((res) => res.data)
  },

  addMember(projectId: number, data: MemberAdd): Promise<ApiResponse<ProjectMember>> {
    return client.post(`/v1/test-projects/${projectId}/members`, data).then((res) => res.data)
  },

  removeMember(projectId: number, userId: number): Promise<ApiResponse<null>> {
    return client.delete(`/v1/test-projects/${projectId}/members/${userId}`).then((res) => res.data)
  },

  /** 批量移除成员 */
  batchRemoveMembers(projectId: number, ids: number[]): Promise<ApiResponse<null>> {
    return client.post(`/v1/test-projects/${projectId}/batch-remove-members`, { ids }).then((res) => res.data)
  },

  updateMemberRole(projectId: number, userId: number, role: string): Promise<ApiResponse<ProjectMember>> {
    return client.put(`/v1/test-projects/${projectId}/members/${userId}`, { role }).then((res) => res.data)
  },

  // ======================================================================
  // 版本管理
  // ======================================================================

  listVersions(params?: { project_id?: number; search?: string; status?: string; page?: number; page_size?: number }): Promise<PaginatedResponse<TestVersion>> {
    return client.get('/v1/test-versions', { params }).then((res) => res.data)
  },

  createVersion(data: TestVersionCreate): Promise<ApiResponse<TestVersion>> {
    return client.post('/v1/test-versions', data).then((res) => res.data)
  },

  updateVersion(id: number, data: TestVersionUpdate): Promise<ApiResponse<TestVersion>> {
    return client.put(`/v1/test-versions/${id}`, data).then((res) => res.data)
  },

  deleteVersion(id: number): Promise<ApiResponse<null>> {
    return client.delete(`/v1/test-versions/${id}`).then((res) => res.data)
  },

  /** 批量删除版本 */
  batchDeleteVersions(ids: number[]): Promise<ApiResponse<null>> {
    return client.post('/v1/test-versions/batch-delete', { ids }).then((res) => res.data)
  },

  // ======================================================================
  // 评审管理
  // ======================================================================

  listReviews(params?: { project_id?: number; search?: string }): Promise<ApiResponse<TestReview[]>> {
    return client.get('/v1/test-reviews', { params }).then((res) => res.data)
  },

  createReview(data: TestReviewCreate): Promise<ApiResponse<TestReview>> {
    return client.post('/v1/test-reviews', data).then((res) => res.data)
  },

  getReview(id: number): Promise<ApiResponse<TestReview>> {
    return client.get(`/v1/test-reviews/${id}`).then((res) => res.data)
  },

  updateReview(id: number, data: TestReviewUpdate): Promise<ApiResponse<TestReview>> {
    return client.put(`/v1/test-reviews/${id}`, data).then((res) => res.data)
  },

  deleteReview(id: number): Promise<ApiResponse<null>> {
    return client.delete(`/v1/test-reviews/${id}`).then((res) => res.data)
  },

  /** 批量删除评审 */
  batchDeleteReviews(ids: number[]): Promise<ApiResponse<null>> {
    return client.post('/v1/test-reviews/batch-delete', { ids }).then((res) => res.data)
  },

  submitReview(id: number): Promise<ApiResponse<TestReview>> {
    return client.post(`/v1/test-reviews/${id}/submit`).then((res) => res.data)
  },

  /** 获取评审统计 */
  getReviewStats(): Promise<ApiResponse<{ total: number; pending: number; passed: number; rejected: number }>> {
    return client.get('/v1/test-reviews/stats').then((res) => res.data)
  },

  /** 获取评审用例列表 */
  listReviewCases(reviewId: number): Promise<ApiResponse<any[]>> {
    return client.get(`/v1/test-reviews/${reviewId}/cases`).then((res) => res.data)
  },

  /** 更新评审用例状态（逐用例审批） */
  updateReviewCase(reviewId: number, caseId: number, data: { status: string; comment?: string }): Promise<ApiResponse<any>> {
    return client.put(`/v1/test-reviews/${reviewId}/cases/${caseId}`, data).then((res) => res.data)
  },

  approveReview(id: number, data: TestReviewApprove): Promise<ApiResponse<TestReview>> {
    return client.post(`/v1/test-reviews/${id}/approve`, data).then((res) => res.data)
  },

  /** 获取用户列表（评审人选择用） */
  listUsers(params?: { page_size?: number; keyword?: string }): Promise<PaginatedResponse<AdminUserInfo>> {
    return client.get('/v1/admin/users', { params: { page_size: 100, ...params } }).then((res) => res.data)
  },

  // ======================================================================
  // 测试用例管理
  // ======================================================================

  listTestCases(params?: {
    project_id?: number
    version_id?: number
    test_type?: string
    status?: string
    priority?: string
    search?: string
  }): Promise<ApiResponse<TestCase[]>> {
    return client.get('/v1/test-cases', { params }).then((res) => res.data)
  },

  createTestCase(data: TestCaseCreate): Promise<ApiResponse<TestCase>> {
    return client.post('/v1/test-cases', data).then((res) => res.data)
  },

  getTestCase(id: number): Promise<ApiResponse<TestCase>> {
    return client.get(`/v1/test-cases/${id}`).then((res) => res.data)
  },

  updateTestCase(id: number, data: Partial<TestCaseCreate>): Promise<ApiResponse<TestCase>> {
    return client.put(`/v1/test-cases/${id}`, data).then((res) => res.data)
  },

  deleteTestCase(id: number): Promise<ApiResponse<null>> {
    return client.delete(`/v1/test-cases/${id}`).then((res) => res.data)
  },

  /** 批量删除测试用例 */
  batchDeleteTestCases(ids: number[]): Promise<ApiResponse<null>> {
    return client.post('/v1/test-cases/batch-delete', { ids }).then((res) => res.data)
  },

  getTestCaseStats(projectId: number): Promise<ApiResponse<TestCaseStats>> {
    return client.get('/v1/test-cases/stats', { params: { project_id: projectId } }).then((res) => res.data)
  },

  // ======================================================================
  // AI 评测师会话管理
  // ======================================================================

  /** 获取会话列表 */
  listTesterSessions(): Promise<ApiResponse<AITesterSession[]>> {
    return client.get('/v1/ai/sessions').then((res) => res.data)
  },

  /** 创建会话 */
  createTesterSession(data: AITesterSessionCreate): Promise<ApiResponse<AITesterSession>> {
    return client.post('/v1/ai/sessions', data).then((res) => res.data)
  },

  /** 更新会话名称 */
  updateTesterSession(id: number, data: AITesterSessionUpdate): Promise<ApiResponse<AITesterSession>> {
    return client.put(`/v1/ai/sessions/${id}`, data).then((res) => res.data)
  },

  /** 批量删除会话 */
  batchDeleteTesterSessions(ids: number[]): Promise<ApiResponse<{ deleted_count: number }>> {
    return client.post('/v1/ai/sessions/batch-delete', { ids }).then((res) => res.data)
  },

  /** 删除会话 */
  deleteTesterSession(id: number): Promise<ApiResponse<null>> {
    return client.delete(`/v1/ai/sessions/${id}`).then((res) => res.data)
  },

  /** 获取会话消息列表 */
  listTesterMessages(sessionId: number, offset = 0, limit = 50): Promise<ApiResponse<AITesterMessage[]>> {
    return client.get(`/v1/ai/sessions/${sessionId}/messages`, { params: { offset, limit } }).then((res) => res.data)
  },

  /** 发送消息（非流式） */
  sendTesterMessage(sessionId: number, data: AITesterChatRequest): Promise<ApiResponse<AITesterMessage>> {
    return client.post(`/v1/ai/sessions/${sessionId}/messages`, data).then((res) => res.data)
  },

  /** 获取 SSE 流式聊天 URL */
  getTesterStreamUrl(sessionId: number): string {
    return `${client.defaults.baseURL}/v1/ai/sessions/${sessionId}/messages/stream`
  },

  /** 消息评分 */
  rateTesterMessage(messageId: number, data: AITesterMessageRating): Promise<ApiResponse<null>> {
    return client.put(`/v1/ai/messages/${messageId}/rating`, data).then((res) => res.data)
  },

  // ======================================================================
  // 用例附件
  // ======================================================================

  /** 上传附件 */
  uploadAttachment(caseId: number, file: File): Promise<ApiResponse<CaseAttachment>> {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/v1/cases/${caseId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((res) => res.data)
  },

  /** 获取附件列表 */
  listAttachments(caseId: number): Promise<ApiResponse<CaseAttachment[]>> {
    return client.get(`/v1/cases/${caseId}/attachments`).then((res) => res.data)
  },

  /** 下载附件 */
  getAttachmentDownloadUrl(attachmentId: number): string {
    return `${client.defaults.baseURL}/v1/attachments/${attachmentId}/download`
  },

  /** 删除附件 */
  deleteAttachment(attachmentId: number): Promise<ApiResponse<null>> {
    return client.delete(`/v1/attachments/${attachmentId}`).then((res) => res.data)
  },

  // ======================================================================
  // 用例评论
  // ======================================================================

  /** 获取评论列表 */
  listComments(caseId: number): Promise<ApiResponse<CaseComment[]>> {
    return client.get(`/v1/cases/${caseId}/comments`).then((res) => res.data)
  },

  /** 创建评论 */
  createComment(caseId: number, data: CaseCommentCreate): Promise<ApiResponse<CaseComment>> {
    return client.post(`/v1/cases/${caseId}/comments`, data).then((res) => res.data)
  },

  /** 更新评论 */
  updateComment(commentId: number, data: CaseCommentUpdate): Promise<ApiResponse<CaseComment>> {
    return client.put(`/v1/comments/${commentId}`, data).then((res) => res.data)
  },

  /** 删除评论 */
  deleteComment(commentId: number): Promise<ApiResponse<null>> {
    return client.delete(`/v1/comments/${commentId}`).then((res) => res.data)
  },

  // ======================================================================
  // AI 生成候选用例
  // ======================================================================

  /** 获取候选用例列表 */
  listGeneratedCaseItems(taskId: string, params?: { page?: number; page_size?: number; status?: string }): Promise<PaginatedResponse<GeneratedCaseItem>> {
    return client.get(`/v1/ai/generate/tasks/${taskId}/generated-cases`, { params }).then((res) => res.data)
  },

  /** 批量更新候选用例状态 */
  batchUpdateCaseItems(taskId: string, data: BatchUpdateCasesRequest): Promise<ApiResponse<null>> {
    return client.post(`/v1/ai/generate/tasks/${taskId}/batch-update-cases`, data).then((res) => res.data)
  },

  /** 保存候选用例到用例库 */
  saveCaseItemsToLibrary(taskId: string, data: SaveToLibraryRequest): Promise<ApiResponse<TestCase[]>> {
    return client.post(`/v1/ai/generate/tasks/${taskId}/save-to-library`, data).then((res) => res.data)
  },

  // ======================================================================
  // 仪表盘统计
  // ======================================================================

  /** 获取仪表盘统计数据 */
  getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    return client.get('/v1/ai/dashboard/stats').then((res) => res.data)
  },

  // ======================================================================
  // 操作日志
  // ======================================================================

  /** 获取用例操作日志 */
  listCaseLogs(caseId: number, params?: { page?: number; page_size?: number }): Promise<ApiResponse<OperationLog[]>> {
    return client.get(`/v1/cases/${caseId}/logs`, { params }).then((res) => res.data)
  },

  /** 获取项目操作日志 */
  listProjectLogs(projectId: number, params?: { page?: number; page_size?: number }): Promise<ApiResponse<OperationLog[]>> {
    return client.get(`/v1/projects/${projectId}/logs`, { params }).then((res) => res.data)
  },

  // ======================================================================
  // 配置检查 & 连接测试
  // ======================================================================

  /** 检查 AI 配置状态 */
  checkAIConfig(): Promise<ApiResponse<ConfigCheckResult>> {
    return client.get('/v1/ai/config/check').then((res) => res.data)
  },

  /** 测试 AI 连接 */
  testAIConnection(data: TestConnectionRequest): Promise<ApiResponse<TestConnectionResult>> {
    return client.post('/v1/ai/config/test-connection', data).then((res) => res.data)
  },

  // ======================================================================
  // 文档上传
  // ======================================================================

  /** 上传文档供 AI 生成使用 */
  uploadGenerationDoc(file: File): Promise<ApiResponse<{ filename: string; content: string; size: number; parsed: boolean }>> {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/v1/ai/generate/upload-doc', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((res) => res.data)
  },

  // ======================================================================
  // 任务控制（取消/修订）
  // ======================================================================

  /** 删除生成任务 */
  deleteGenerationTask(taskId: string): Promise<ApiResponse<null>> {
    return client.delete(`/v1/ai/generate/tasks/${taskId}`).then((res) => res.data)
  },

  /** 取消生成任务 */
  cancelGenerationTask(taskId: string): Promise<ApiResponse<null>> {
    return client.post(`/v1/ai/generate/${taskId}/cancel`).then((res) => res.data)
  },

  /** 修订生成任务 */
  reviseGenerationTask(taskId: string, pipelineType?: string): Promise<ApiResponse<{ task_id: string; status: string }>> {
    return client.post(`/v1/ai/generate/${taskId}/revise`, { pipeline_type: pipelineType || 'traditional' }).then((res) => res.data)
  },

  /** 批量删除生成任务（按主键 ID） */
  batchDeleteGenerationTasks(ids: number[]): Promise<ApiResponse<null>> {
    return client.post('/v1/ai/generate/tasks/batch-delete', { ids }).then((res) => res.data)
  },

  // ======================================================================
  // Excel 导入导出
  // ======================================================================

  /** 导出用例为 Excel */
  /** 导出测试用例（支持 xlsx/csv/md/xmind）—— 直接下载 */
  exportTestCasesDownload(params?: {
    format?: string
    project_id?: number
    version_id?: number
    test_type?: string
  }): Promise<Blob> {
    return client.get('/v1/test-cases/export', { params, responseType: 'blob' }).then((res) => res.data)
  },

  /** 从文件导入用例（支持 .xlsx/.xls/.csv/.md/.xmind/.mm） */
  importTestCasesExcel(file: File, projectId: number): Promise<ApiResponse<{ imported: number; errors: string[] }>> {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/v1/test-cases/import?project_id=${projectId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((res) => res.data)
  },

  // ======================================================================
  // 测试用例执行
  // ======================================================================

  /** 执行测试用例（仅 active 状态允许） */
  executeTestCase(caseId: number, data: TestCaseExecuteRequest): Promise<ApiResponse<TestCaseExecution>> {
    return client.post(`/v1/test-cases/${caseId}/executions`, data).then((res) => res.data)
  },

  /** 获取用例执行历史 */
  listTestCaseExecutions(caseId: number): Promise<ApiResponse<TestCaseExecution[]>> {
    return client.get(`/v1/test-cases/${caseId}/executions`).then((res) => res.data)
  },

  /** 获取用例最新执行结果 */
  getLatestExecution(caseId: number): Promise<ApiResponse<TestCaseExecution | null>> {
    return client.get(`/v1/test-cases/${caseId}/executions/latest`).then((res) => res.data)
  },

  /** 获取用例关联的评审历史 */
  getCaseReviews(caseId: number): Promise<ApiResponse<CaseReviewSummary[]>> {
    return client.get(`/v1/test-cases/${caseId}/reviews`).then((res) => res.data)
  },
}
