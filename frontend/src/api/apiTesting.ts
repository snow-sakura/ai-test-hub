/**
 * API 接口测试 API 封装
 *
 * 提供 API 项目管理、接口管理、测试套件管理等接口调用。
 */

import type { ApiResponse } from '@/types/api'
import type {
  ApiProject,
  ApiProjectCreate,
  ApiProjectUpdate,
  ApiEndpoint,
  ApiEndpointCreate,
  ApiEndpointUpdate,
  ApiTestSuite,
  ApiTestSuiteCreate,
  ApiTestSuiteUpdate,
  SwaggerImportRequest,
  ExecuteResponse,
  ApiTestReport,
} from '@/types/api-testing'
import client from './client'

/** API 接口测试 API */
export const apiTestingApi = {
  // ==================== 项目管理 ====================

  /**
   * 获取 API 项目列表
   */
  listProjects(search?: string, status?: string): Promise<ApiResponse<ApiProject[]>> {
    return client.get('/v1/api-projects', { params: { search, status_filter: status } }).then((res) => res.data)
  },

  /**
   * 创建 API 项目
   */
  createProject(data: ApiProjectCreate): Promise<ApiResponse<ApiProject>> {
    return client.post('/v1/api-projects', data).then((res) => res.data)
  },

  /**
   * 更新 API 项目
   */
  updateProject(id: number, data: ApiProjectUpdate): Promise<ApiResponse<ApiProject>> {
    return client.put(`/v1/api-projects/${id}`, data).then((res) => res.data)
  },

  /**
   * 删除 API 项目
   */
  deleteProject(id: number): Promise<ApiResponse> {
    return client.delete(`/v1/api-projects/${id}`).then((res) => res.data)
  },

  /**
   * 从 Swagger URL 导入接口
   */
  importSwagger(data: SwaggerImportRequest): Promise<ApiResponse<{ count: number }>> {
    return client.post('/v1/api-projects/import-swagger', data).then((res) => res.data)
  },

  // ==================== 接口管理 ====================

  /**
   * 获取项目下的接口列表
   */
  listEndpoints(projectId: number, method?: string, tag?: string): Promise<ApiResponse<ApiEndpoint[]>> {
    return client.get(`/v1/api-projects/${projectId}/endpoints`, { params: { method, tag } }).then((res) => res.data)
  },

  /**
   * 创建接口
   */
  createEndpoint(projectId: number, data: ApiEndpointCreate): Promise<ApiResponse<ApiEndpoint>> {
    return client.post(`/v1/api-projects/${projectId}/endpoints`, data).then((res) => res.data)
  },

  /**
   * 更新接口
   */
  updateEndpoint(projectId: number, endpointId: number, data: ApiEndpointUpdate): Promise<ApiResponse<ApiEndpoint>> {
    return client.put(`/v1/api-projects/${projectId}/endpoints/${endpointId}`, data).then((res) => res.data)
  },

  /**
   * 删除接口
   */
  deleteEndpoint(projectId: number, endpointId: number): Promise<ApiResponse> {
    return client.delete(`/v1/api-projects/${projectId}/endpoints/${endpointId}`).then((res) => res.data)
  },

  // ==================== 测试套件 ====================

  /**
   * 获取测试套件列表
   */
  listTestSuites(projectId?: number): Promise<ApiResponse<ApiTestSuite[]>> {
    return client.get('/v1/api-test-suites', { params: { project_id: projectId } }).then((res) => res.data)
  },

  /**
   * 创建测试套件
   */
  createTestSuite(data: ApiTestSuiteCreate): Promise<ApiResponse<ApiTestSuite>> {
    return client.post('/v1/api-test-suites', data).then((res) => res.data)
  },

  /**
   * 更新测试套件
   */
  updateTestSuite(id: number, data: ApiTestSuiteUpdate): Promise<ApiResponse<ApiTestSuite>> {
    return client.put(`/v1/api-test-suites/${id}`, data).then((res) => res.data)
  },

  /**
   * 删除测试套件
   */
  deleteTestSuite(id: number): Promise<ApiResponse> {
    return client.delete(`/v1/api-test-suites/${id}`).then((res) => res.data)
  },

  /**
   * 执行测试套件
   */
  executeTestSuite(id: number): Promise<ApiResponse<ExecuteResponse>> {
    return client.post(`/v1/api-test-suites/${id}/execute`).then((res) => res.data)
  },

  /**
   * 获取执行报告列表
   */
  getTestReports(suiteId: number): Promise<ApiResponse<ApiTestReport[]>> {
    return client.get(`/v1/api-test-suites/${suiteId}/reports`).then((res) => res.data)
  },
}
