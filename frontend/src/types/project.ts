/**
 * 项目相关类型定义
 *
 * 与后端 Project CRUD API 的数据结构对应。
 */

/** 项目概要（下拉选择用） */
export interface ProjectSummary {
  id: number
  name: string
  description?: string
}

/** 创建项目请求 */
export interface ProjectCreateRequest {
  name: string
  description?: string
}

/** 更新项目请求 */
export interface ProjectUpdateRequest {
  name?: string
  description?: string
}

/** 项目详细响应 */
export interface ProjectResponse {
  id: number
  name: string
  description?: string
  created_by: number
  created_at: string
  updated_at: string
}
