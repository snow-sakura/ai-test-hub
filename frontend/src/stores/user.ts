/**
 * 用户状态管理（Pinia Store）
 *
 * 管理登录状态、Token 生命周期、用户信息，
 * 支持 Token 自动刷新和登录状态持久化。
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '@/api/auth'
import type { LoginRequest, RegisterRequest, UserInfo, UserUpdate } from '@/types/user'

export const useUserStore = defineStore('user', () => {
  // ========== 状态 ==========

  /** 用户信息 */
  const user = ref<UserInfo | null>(null)
  /** Access Token */
  const accessToken = ref(localStorage.getItem('access_token') || '')
  /** Refresh Token */
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  /** Token 过期时间戳（毫秒） */
  const tokenExpiresAt = ref(parseInt(localStorage.getItem('token_expires_at') || '0'))

  /** Token 自动刷新定时器 ID */
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  // ========== 计算属性 ==========

  /** 是否已登录（同时有 token 和用户信息） */
  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)

  /** Token 是否已过期 */
  const isTokenExpired = computed(() => {
    if (!tokenExpiresAt.value) return false
    return Date.now() > tokenExpiresAt.value
  })

  /** Token 是否即将过期（5 分钟内） */
  const isTokenExpiringSoon = computed(() => {
    if (!tokenExpiresAt.value) return false
    const timeLeft = tokenExpiresAt.value - Date.now()
    return timeLeft > 0 && timeLeft < 5 * 60 * 1000
  })

  /** 用户名（方便组件使用） */
  const username = computed(() => user.value?.username || '')
  /** 用户头像首字母 */
  const avatar = computed(() => {
    return user.value?.username?.charAt(0).toUpperCase() || '?'
  })

  // ========== 持久化辅助 ==========

  /** 保存认证状态到 localStorage */
  function persistAuth(
    token: string,
    refresh: string,
    expiresAt: number,
  ): void {
    accessToken.value = token
    refreshToken.value = refresh
    tokenExpiresAt.value = expiresAt
    localStorage.setItem('access_token', token)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('token_expires_at', expiresAt.toString())
  }

  /** 清除所有认证状态 */
  function clearAuth(): void {
    accessToken.value = ''
    refreshToken.value = ''
    tokenExpiresAt.value = 0
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')
    localStorage.removeItem('user')
  }

  // ========== Token 自动刷新 ==========

  /** 启动定时器，每 2 分钟检查一次 token 是否需要刷新 */
  function startAutoRefresh(): void {
    stopAutoRefresh()
    refreshTimer = setInterval(async () => {
      if (refreshToken.value && isTokenExpiringSoon.value && !isTokenExpired.value) {
        try {
          await refreshAccessToken()
        } catch {
          // refreshAccessToken 失败时已自动 logout
        }
      }
    }, 2 * 60 * 1000)
  }

  /** 停止自动刷新定时器 */
  function stopAutoRefresh(): void {
    if (refreshTimer !== null) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  // ========== 业务操作 ==========

  /**
   * 登录
   */
  async function login(credentials: LoginRequest): Promise<void> {
    const res = await authApi.login(credentials)
    const { access_token, refresh_token } = res.data
    const expiresAt = Date.now() + 30 * 60 * 1000
    persistAuth(access_token, refresh_token, expiresAt)
    await fetchUser()
    startAutoRefresh()
  }

  /**
   * 注册
   */
  async function register(data: RegisterRequest): Promise<void> {
    await authApi.register(data)
    // 注册成功后不自动登录，交由用户手动登录
  }

  /**
   * 登出
   */
  async function logout(): Promise<void> {
    stopAutoRefresh()
    try {
      await authApi.logout()
    } catch {
      // logout API 失败不影响本地清除
    } finally {
      clearAuth()
    }
  }

  /**
   * 刷新 Access Token
   */
  async function refreshAccessToken(): Promise<string> {
    try {
      const res = await authApi.refreshToken(refreshToken.value)
      const { access_token, refresh_token } = res.data
      const expiresAt = Date.now() + 30 * 60 * 1000
      persistAuth(access_token, refresh_token, expiresAt)
      return access_token
    } catch (error) {
      await logout()
      throw error
    }
  }

  /**
   * 获取当前用户信息
   */
  async function fetchUser(): Promise<void> {
    const res = await authApi.getMe()
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  }

  /**
   * 更新用户信息
   */
  async function updateUser(data: UserUpdate): Promise<void> {
    const res = await authApi.updateMe(data)
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  }

  /**
   * 应用启动时初始化认证状态
   * 从 localStorage 恢复用户信息，检查并刷新过期 token
   */
  async function initAuth(): Promise<void> {
    // 从 localStorage 恢复用户信息
    if (!user.value) {
      const savedUser = localStorage.getItem('user')
      if (savedUser) {
        try {
          user.value = JSON.parse(savedUser)
        } catch {
          localStorage.removeItem('user')
        }
      }
    }

    if (accessToken.value) {
      // token 已过期但有 refresh token，尝试刷新
      if (isTokenExpired.value && refreshToken.value) {
        try {
          await refreshAccessToken()
        } catch {
          return
        }
      }

      // 没有用户信息则获取
      if (!user.value) {
        try {
          await fetchUser()
        } catch {
          await logout()
          return
        }
      }

      startAutoRefresh()
    }
  }

  return {
    // 状态
    user,
    accessToken,
    refreshToken,
    tokenExpiresAt,
    // 计算属性
    isLoggedIn,
    isTokenExpired,
    isTokenExpiringSoon,
    username,
    avatar,
    // 操作
    login,
    register,
    logout,
    refreshAccessToken,
    fetchUser,
    updateUser,
    initAuth,
    startAutoRefresh,
    stopAutoRefresh,
  }
})
