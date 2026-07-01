/**
 * API 通用响应类型定义
 */

/** 通用 API 响应结构 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 分页元信息 */
export interface PaginationMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

/** 分页响应结构 */
export interface PaginatedResponse<T = unknown> extends ApiResponse<T[]> {
  data: T[]
  pagination: PaginationMeta
}
