/**
 * 系统管理 API 封装
 *
 * 提供用户管理、角色权限、系统设置、审计日志等接口调用。
 */

import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type {
  AdminUserCreate,
  AdminUserInfo,
  AdminUserUpdate,
  AuditLog,
  AuditLogQuery,
  ResetPasswordRequest,
  RoleCreate,
  RoleInfo,
  RoleUpdate,
  SystemSettings,
  SystemSettingsUpdate,
} from '@/types/admin'
import client from './client'

/** 系统管理 API */
export const adminApi = {
  // ====================================================================
  // 用户管理
  // ====================================================================

  /**
   * 获取用户列表（分页）
   */
  getUsers(params: {
    page?: number
    page_size?: number
    keyword?: string
    is_active?: boolean
  }): Promise<PaginatedResponse<AdminUserInfo>> {
    return client.get('/v1/admin/users', { params }).then((res) => res.data)
  },

  /**
   * 创建用户
   */
  createUser(data: AdminUserCreate): Promise<ApiResponse<AdminUserInfo>> {
    return client.post('/v1/admin/users', data).then((res) => res.data)
  },

  /**
   * 修改用户
   */
  updateUser(id: number, data: AdminUserUpdate): Promise<ApiResponse<AdminUserInfo>> {
    return client.put(`/v1/admin/users/${id}`, data).then((res) => res.data)
  },

  /**
   * 删除用户
   */
  deleteUser(id: number): Promise<ApiResponse> {
    return client.delete(`/v1/admin/users/${id}`).then((res) => res.data)
  },

  /**
   * 重置密码
   */
  resetPassword(id: number, data: ResetPasswordRequest): Promise<ApiResponse> {
    return client.put(`/v1/admin/users/${id}/reset-password`, data).then((res) => res.data)
  },

  // ====================================================================
  // 角色权限
  // ====================================================================

  /**
   * 获取角色列表
   */
  getRoles(): Promise<ApiResponse<RoleInfo[]>> {
    return client.get('/v1/admin/roles').then((res) => res.data)
  },

  /**
   * 创建角色
   */
  createRole(data: RoleCreate): Promise<ApiResponse<RoleInfo>> {
    return client.post('/v1/admin/roles', data).then((res) => res.data)
  },

  /**
   * 更新角色
   */
  updateRole(id: number, data: RoleUpdate): Promise<ApiResponse<RoleInfo>> {
    return client.put(`/v1/admin/roles/${id}`, data).then((res) => res.data)
  },

  /**
   * 删除角色
   */
  deleteRole(id: number): Promise<ApiResponse> {
    return client.delete(`/v1/admin/roles/${id}`).then((res) => res.data)
  },

  // ====================================================================
  // 系统设置
  // ====================================================================

  /**
   * 获取系统设置
   */
  getSettings(): Promise<ApiResponse<SystemSettings>> {
    return client.get('/v1/admin/settings').then((res) => res.data)
  },

  /**
   * 更新系统设置
   */
  updateSettings(data: SystemSettingsUpdate): Promise<ApiResponse<SystemSettings>> {
    return client.put('/v1/admin/settings', data).then((res) => res.data)
  },

  // ====================================================================
  // 审计日志
  // ====================================================================

  /**
   * 获取审计日志列表（分页）
   */
  getAuditLogs(params: AuditLogQuery): Promise<PaginatedResponse<AuditLog>> {
    return client.get('/v1/admin/audit-logs', { params }).then((res) => res.data)
  },
}
