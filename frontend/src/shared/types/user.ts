/**
 * 用户相关类型定义
 */

/** 用户信息 */
export interface UserInfo {
  id: number
  username: string
  email: string
  phone?: string
  avatar?: string
  department?: string
  position?: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

/** 登录请求 */
export interface LoginRequest {
  username: string
  password: string
}

/** 注册请求 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
}

/** Token 响应 */
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

/** 用户信息更新请求 */
export interface UserUpdate {
  email?: string
  phone?: string
  avatar?: string
  department?: string
  position?: string
}
