/**
 * 仪表盘相关类型定义
 *
 * 与后端 dashboard API 返回的数据结构对应。
 */

/** 仪表盘统计数据 */
export interface DashboardStats {
  /** 项目总数 */
  total_projects: number
  /** 测试用例总数 */
  total_test_cases: number
  /** 今日执行次数 */
  today_executions: number
  /** 通过率（百分比） */
  pass_rate: number
}

/** 功能模块信息 */
export interface ModuleInfo {
  /** 模块唯一标识 */
  key: string
  /** 模块显示名称 */
  name: string
  /** 模块功能描述 */
  description: string
  /** Element Plus 图标名称 */
  icon: string
  /** 模块卡片主题色 */
  color: string
  /** 前端路由路径 */
  path: string
  /** 额外信息（如 API 数量等） */
  meta?: string
}
