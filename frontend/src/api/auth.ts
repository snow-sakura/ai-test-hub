/**
 * 认证相关 API 封装
 *
 * 提供登录、注册、Token 刷新、用户信息管理等接口调用。
 */

import type { ApiResponse } from '@/types/api'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserInfo,
  UserUpdate,
} from '@/types/user'
import client from './client'

/** 认证 API */
export const authApi = {
  /**
   * 用户登录
   */
  login(data: LoginRequest): Promise<ApiResponse<TokenResponse>> {
    return client.post('/v1/auth/login', data).then((res) => res.data)
  },

  /**
   * 用户注册
   */
  register(data: RegisterRequest): Promise<ApiResponse<UserInfo>> {
    return client.post('/v1/auth/register', data).then((res) => res.data)
  },

  /**
   * 刷新 Token
   */
  refreshToken(refreshToken: string): Promise<ApiResponse<TokenResponse>> {
    return client
      .post('/v1/auth/refresh', { refresh_token: refreshToken })
      .then((res) => res.data)
  },

  /**
   * 用户登出
   */
  logout(): Promise<ApiResponse> {
    return client.post('/v1/auth/logout').then((res) => res.data)
  },

  /**
   * 获取当前用户信息
   */
  getMe(): Promise<ApiResponse<UserInfo>> {
    return client.get('/v1/auth/me').then((res) => res.data)
  },

  /**
   * 更新当前用户信息
   */
  updateMe(data: UserUpdate): Promise<ApiResponse<UserInfo>> {
    return client.put('/v1/auth/me', data).then((res) => res.data)
  },
}
