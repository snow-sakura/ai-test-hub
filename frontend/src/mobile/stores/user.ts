/**
 * 移动端用户状态管理
 * 逻辑与桌面端一致，API 调用指向移动端独立 API 层
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import client from '../api/client'
import type { LoginRequest, RegisterRequest, UserInfo, UserUpdate } from '@/shared/types/user'

export const useUserStore = defineStore('mobile-user', () => {
  // ========== 状态 ==========
  const user = ref<UserInfo | null>(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const tokenExpiresAt = ref(parseInt(localStorage.getItem('token_expires_at') || '0'))
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  // ========== 计算属性 ==========
  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)
  const isTokenExpired = computed(() => {
    if (!tokenExpiresAt.value) return false
    return Date.now() > tokenExpiresAt.value
  })
  const isTokenExpiringSoon = computed(() => {
    if (!tokenExpiresAt.value) return false
    const timeLeft = tokenExpiresAt.value - Date.now()
    return timeLeft > 0 && timeLeft < 5 * 60 * 1000
  })
  const username = computed(() => user.value?.username || '')
  const avatar = computed(() => user.value?.username?.charAt(0).toUpperCase() || '?')

  // ========== 持久化 ==========
  function persistAuth(token: string, refresh: string, expiresAt: number): void {
    accessToken.value = token
    refreshToken.value = refresh
    tokenExpiresAt.value = expiresAt
    localStorage.setItem('access_token', token)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('token_expires_at', expiresAt.toString())
  }

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

  // ========== 自动刷新 ==========
  function startAutoRefresh(): void {
    stopAutoRefresh()
    refreshTimer = setInterval(async () => {
      if (refreshToken.value && isTokenExpiringSoon.value && !isTokenExpired.value) {
        try {
          await refreshAccessToken()
        } catch { /* 已在 refreshAccessToken 中处理 */ }
      }
    }, 2 * 60 * 1000)
  }

  function stopAutoRefresh(): void {
    if (refreshTimer !== null) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  // ========== 业务操作 ==========
  async function login(credentials: LoginRequest): Promise<void> {
    const res = await client.post<{ data: { access_token: string; refresh_token: string } }>(
      '/v1/auth/login', credentials,
    )
    const { access_token, refresh_token } = res.data.data
    const expiresAt = Date.now() + 30 * 60 * 1000
    persistAuth(access_token, refresh_token, expiresAt)
    await fetchUser()
    startAutoRefresh()
  }

  async function register(data: RegisterRequest): Promise<void> {
    await client.post('/v1/auth/register', data)
  }

  async function logout(): Promise<void> {
    stopAutoRefresh()
    try {
      await client.post('/v1/auth/logout')
    } catch { /* ignore */ } finally {
      clearAuth()
    }
  }

  async function refreshAccessToken(): Promise<string> {
    try {
      const res = await client.post<{ data: { access_token: string; refresh_token: string } }>(
        '/v1/auth/refresh',
        { refresh_token: refreshToken.value },
      )
      const { access_token, refresh_token } = res.data.data
      const expiresAt = Date.now() + 30 * 60 * 1000
      persistAuth(access_token, refresh_token, expiresAt)
      return access_token
    } catch (error) {
      await logout()
      throw error
    }
  }

  async function fetchUser(): Promise<void> {
    const res = await client.get<{ data: UserInfo }>('/v1/auth/me')
    user.value = res.data.data
    localStorage.setItem('user', JSON.stringify(res.data.data))
  }

  async function updateUser(data: UserUpdate): Promise<void> {
    const res = await client.patch<{ data: UserInfo }>('/v1/auth/me', data)
    user.value = res.data.data
    localStorage.setItem('user', JSON.stringify(res.data.data))
  }

  async function initAuth(): Promise<void> {
    if (!user.value) {
      const savedUser = localStorage.getItem('user')
      if (savedUser) {
        try { user.value = JSON.parse(savedUser) } catch { localStorage.removeItem('user') }
      }
    }
    if (accessToken.value) {
      if (isTokenExpired.value && refreshToken.value) {
        try { await refreshAccessToken() } catch { return }
      }
      if (!user.value) {
        try { await fetchUser() } catch { await logout(); return }
      }
      startAutoRefresh()
    }
  }

  return {
    user, accessToken, refreshToken, tokenExpiresAt,
    isLoggedIn, isTokenExpired, isTokenExpiringSoon, username, avatar,
    login, register, logout, refreshAccessToken, fetchUser, updateUser, initAuth,
    startAutoRefresh, stopAutoRefresh,
  }
})
