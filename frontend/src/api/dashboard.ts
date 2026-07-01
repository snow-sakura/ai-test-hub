/**
 * 仪表盘相关 API 封装
 *
 * 提供统计数据获取、功能模块列表查询等接口调用。
 */

import type { ApiResponse } from '@/types/api'
import type { DashboardStats, ModuleInfo } from '@/types/dashboard'
import client from './client'

/** 仪表盘 API */
export const dashboardApi = {
  /**
   * 获取仪表盘统计数据
   *
   * 返回项目总数、用例总数、今日执行次数和通过率。
   */
  getStats(): Promise<ApiResponse<DashboardStats>> {
    return client.get('/v1/dashboard/stats').then((res) => res.data)
  },

  /**
   * 获取功能模块列表
   *
   * 返回 9 个功能模块的图标、名称、描述和路由信息。
   */
  getModules(): Promise<ApiResponse<ModuleInfo[]>> {
    return client.get('/v1/dashboard/modules').then((res) => res.data)
  },
}
