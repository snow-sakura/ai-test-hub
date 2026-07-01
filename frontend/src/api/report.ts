/**
 * AI 测试报告 API 封装
 *
 * 提供报告列表、详情、统计等接口调用。
 */

import type { ApiResponse } from '@/types/api'
import type {
  AIReportDetail,
  AIReportStats,
  ReportListResponse,
  ModuleStatItem,
} from '@/types/report'
import client from './client'

/** 报告 API */
export const reportApi = {
  /**
   * 获取 AI 测试报告列表（分页）
   *
   * @param params 查询参数（项目筛选、时间范围、分页）
   */
  getReportList(params?: {
    project_id?: number
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }): Promise<ReportListResponse> {
    return client.get('/v1/ai/reports', { params }).then((res) => res.data)
  },

  /**
   * 获取报告详情（含全部用例明细）
   *
   * @param taskId 任务 ID
   */
  getReportDetail(taskId: string): Promise<ApiResponse<AIReportDetail>> {
    return client.get(`/v1/ai/reports/${taskId}`).then((res) => res.data)
  },

  /**
   * 获取报告统计数据（轻量，不含用例明细）
   *
   * @param taskId 任务 ID
   */
  getReportStats(taskId: string): Promise<ApiResponse<AIReportStats>> {
    return client.get(`/v1/ai/reports/${taskId}/stats`).then((res) => res.data)
  },

  /**
   * 获取报告模块分布统计
   *
   * @param taskId 任务 ID
   */
  getModuleStats(taskId: string): Promise<ApiResponse<ModuleStatItem[]>> {
    return client.get(`/v1/ai/reports/${taskId}/module-stats`).then((res) => res.data)
  },
}
