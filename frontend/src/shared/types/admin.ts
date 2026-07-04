/**
 * 系统管理相关类型定义
 *
 * 涵盖用户管理、角色权限、系统设置、审计日志等模块。
 */

// ====================================================================
// 用户管理
// ====================================================================

/** 角色简要信息（嵌入用户响应中） */
export interface UserRoleBrief {
  id: number
  name: string
  code: string
}

/** 用户详情（管理端） */
export interface AdminUserInfo {
  id: number
  username: string
  email: string
  phone?: string
  avatar?: string
  department?: string
  position?: string
  is_active: boolean
  is_superuser: boolean
  roles: UserRoleBrief[]
  created_at: string
  updated_at?: string
  last_login?: string
}

/** 管理员创建用户请求 */
export interface AdminUserCreate {
  username: string
  email: string
  password: string
  phone?: string
  department?: string
  position?: string
  is_active?: boolean
  is_superuser?: boolean
  role_ids?: number[]
}

/** 管理员修改用户请求 */
export interface AdminUserUpdate {
  email?: string
  phone?: string
  department?: string
  position?: string
  is_active?: boolean
  is_superuser?: boolean
  role_ids?: number[]
}

/** 重置密码请求 */
export interface ResetPasswordRequest {
  password: string
}

// ====================================================================
// 角色权限
// ====================================================================

/** 角色信息 */
export interface RoleInfo {
  id: number
  name: string
  code: string
  description?: string
  permissions?: Record<string, any>
  is_system: boolean
  created_at: string
  updated_at?: string
}

/** 创建角色请求 */
export interface RoleCreate {
  name: string
  code: string
  description?: string
  permissions?: Record<string, any>
}

/** 更新角色请求 */
export interface RoleUpdate {
  name?: string
  description?: string
  permissions?: Record<string, any>
}

// ====================================================================
// 系统设置
// ====================================================================

/** 系统设置 */
export interface SystemSettings {
  site_name: string
  site_description: string
  logo_url?: string
  icp_beian?: string
  password_min_length: number
  password_complexity: string
  max_login_attempts: number
  login_lock_minutes: number
  session_timeout_minutes: number
  password_expire_days: number
  upload_max_size_mb: number
  allowed_file_types: string
}

/** 更新系统设置请求 */
export interface SystemSettingsUpdate {
  site_name?: string
  site_description?: string
  logo_url?: string
  icp_beian?: string
  password_min_length?: number
  password_complexity?: string
  max_login_attempts?: number
  login_lock_minutes?: number
  session_timeout_minutes?: number
  password_expire_days?: number
  upload_max_size_mb?: number
  allowed_file_types?: string
}

// ====================================================================
// 审计日志
// ====================================================================

/** 审计日志条目 */
export interface AuditLog {
  id: number
  user_id: number
  username: string
  action: string
  module: string
  target_type?: string
  target_id?: number
  detail?: string
  ip_address?: string
  status: string
  created_at: string
}

/** 审计日志查询参数 */
export interface AuditLogQuery {
  page?: number
  page_size?: number
  action?: string
  module?: string
  username?: string
  keyword?: string
  start_date?: string
  end_date?: string
}
