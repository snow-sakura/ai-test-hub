/**
 * 项目 CRUD API 封装
 *
 * 提供项目的增删改查接口调用。
 */

import type { ApiResponse } from '@/types/api'
import type {
  ProjectCreateRequest,
  ProjectResponse,
  ProjectSummary,
  ProjectUpdateRequest,
} from '@/types/project'
import client from './client'

/** 项目管理 API */
export const projectsApi = {
  /**
   * 获取项目列表
   */
  list(): Promise<ApiResponse<ProjectSummary[]>> {
    return client.get('/v1/projects').then((res) => res.data)
  },

  /**
   * 创建项目
   */
  create(data: ProjectCreateRequest): Promise<ApiResponse<ProjectResponse>> {
    return client.post('/v1/projects', data).then((res) => res.data)
  },

  /**
   * 更新项目
   */
  update(id: number, data: ProjectUpdateRequest): Promise<ApiResponse<ProjectResponse>> {
    return client.put(`/v1/projects/${id}`, data).then((res) => res.data)
  },

  /**
   * 删除项目
   */
  delete(id: number): Promise<ApiResponse> {
    return client.delete(`/v1/projects/${id}`).then((res) => res.data)
  },
}
