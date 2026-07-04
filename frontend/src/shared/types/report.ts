/**
 * AI 测试报告类型定义
 *
 * 与后端 AI 测试报告 API 的数据结构对应，覆盖报告列表、统计、详情等场景。
 */

/** AI 测试报告列表项 */
export interface AIReportSummary {
  /** 任务数据库 ID */
  id: number
  /** 任务唯一标识 */
  task_id: string
  /** 报告标题 */
  title: string
  /** 关联项目名称 */
  project_name: string
  /** 任务状态 */
  status: string
  /** 总用例数 */
  total_cases: number
  /** 通过数 */
  passed: number
  /** 失败数 */
  failed: number
  /** 阻塞数 */
  blocked: number
  /** 通过率（百分比） */
  pass_rate: number
  /** 创建时间 */
  created_at: string
}

/** 失败用例详情项 */
export interface FailedCaseItem {
  /** 用例编号 */
  case_id: string
  /** 用例标题 */
  title: string
  /** 所属模块 */
  module: string
  /** 优先级 */
  priority: string
  /** 失败原因 */
  reason: string
  /** 用例状态 */
  status: string
}

/** 模块分布统计项 */
export interface ModuleStatItem {
  /** 模块名称 */
  module: string
  /** 该模块总用例数 */
  total: number
  /** 通过数 */
  passed: number
  /** 失败数 */
  failed: number
  /** 通过率（百分比） */
  pass_rate: number
}

/** AI 测试报告统计数据 */
export interface AIReportStats {
  /** 总用例数 */
  total_cases: number
  /** 通过数 */
  passed: number
  /** 失败数 */
  failed: number
  /** 阻塞数 */
  blocked: number
  /** 通过率（百分比） */
  pass_rate: number
  /** 模块分布统计 */
  module_stats: ModuleStatItem[]
  /** 失败用例列表 */
  failed_cases: FailedCaseItem[]
}

/** AI 测试报告详情 */
export interface AIReportDetail {
  /** 报告概要 */
  summary: AIReportSummary
  /** 统计数据 */
  stats: AIReportStats
  /** 全部用例明细 */
  cases: import('@/types/ai').GeneratedTestCase[]
}

/** API 报告列表响应（分页） */
export interface ReportListResponse {
  code: number
  message: string
  data: AIReportSummary[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}
