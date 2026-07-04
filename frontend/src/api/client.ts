import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

/** 扩展 Axios 请求配置，携带重试标记 */
interface CustomAxiosConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

/** 存储待刷新 token 期间挂起的请求 */
let isRefreshing = false
let pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

/** 处理挂起的请求队列 */
function processQueue(error: unknown, token: string | null = null): void {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token!)
    }
  })
  pendingQueue = []
}

/** 判断 token 是否即将过期（5 分钟内） */
function isTokenExpiringSoon(): boolean {
  const expiresAt = localStorage.getItem('token_expires_at')
  if (!expiresAt) return false
  const timeLeft = parseInt(expiresAt) - Date.now()
  return timeLeft > 0 && timeLeft < 5 * 60 * 1000
}

/** 判断 token 是否已过期 */
function isTokenExpired(): boolean {
  const expiresAt = localStorage.getItem('token_expires_at')
  if (!expiresAt) return false
  return Date.now() > parseInt(expiresAt)
}

// 创建 Axios 实例
const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 请求拦截器 —— 自动注入 token，并在 token 即将过期时主动刷新
 */
client.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')

    // 跳过刷新 token 的请求自身（避免死循环）
    if (config.url === '/v1/auth/refresh') {
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    }

    if (token && config.headers) {
      // token 即将过期且未在刷新中，主动触发刷新
      if (isTokenExpiringSoon() && !isTokenExpired() && !isRefreshing) {
        isRefreshing = true
        try {
          const newToken = await doRefreshToken()
          processQueue(null, newToken)
          config.headers.Authorization = `Bearer ${newToken}`
        } catch (err) {
          processQueue(err, null)
          return Promise.reject(err)
        } finally {
          isRefreshing = false
        }
      } else if (isRefreshing) {
        // 有正在进行的刷新，将当前请求挂起等待
        return new Promise<string>((resolve, reject) => {
          pendingQueue.push({ resolve, reject })
        }).then((newToken) => {
          config.headers!.Authorization = `Bearer ${newToken}`
          return config
        }).catch((err) => {
          return Promise.reject(err)
        })
      } else {
        config.headers.Authorization = `Bearer ${token}`
      }
    }

    return config
  },
  (error: AxiosError) => Promise.reject(error),
)

/**
 * 执行 token 刷新的核心逻辑
 */
async function doRefreshToken(): Promise<string> {
  const refreshTokenVal = localStorage.getItem('refresh_token')
  const response = await client.post<{ data: { access_token: string; refresh_token: string } }>(
    '/v1/auth/refresh',
    { refresh_token: refreshTokenVal },
  )
  const { access_token, refresh_token } = response.data.data
  localStorage.setItem('access_token', access_token)
  localStorage.setItem('refresh_token', refresh_token)
  // 更新过期时间（当前时间 + 30 分钟）
  localStorage.setItem('token_expires_at', (Date.now() + 30 * 60 * 1000).toString())
  return access_token
}

/**
 * 响应拦截器 —— 统一错误处理，401 时触发 token 刷新队列
 */
client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as CustomAxiosConfig | undefined
    const status = error.response?.status

    // 网络连接失败（无 response）
    if (!error.response) {
      console.error('[API] 网络请求失败:', error.message, error.config?.url)
      ElMessage.error('网络连接失败，请检查后端服务是否启动')
      return Promise.reject(error)
    }

    // 非 401 错误直接拒绝
    if (!originalRequest || status !== 401) {
      const errData = error.response?.data as { detail?: string; message?: string } | undefined
      const errMsg = errData?.detail || errData?.message || ''
      // 服务器错误提示
      if (status && status >= 500) {
        const detail = errMsg || '服务器错误，请稍后重试'
        console.error(`API Error [${status}]:`, error.response?.data)
        ElMessage.error(detail)
      } else if (status) {
        const detail = errMsg || `请求失败 [${status}]`
        console.error(`API Error [${status}]:`, error.response?.data)
        ElMessage.error(detail)
      }
      return Promise.reject(error)
    }

    // 如果已经是重试请求，说明刷新也失败了，直接拒绝
    if (originalRequest._retry) {
      return Promise.reject(error)
    }

    // 登出或刷新请求的 401 不重试（防止死循环）
    const noRetryPaths = ['/v1/auth/logout', '/v1/auth/refresh']
    if (noRetryPaths.some((p) => originalRequest.url?.includes(p))) {
      clearAuthState()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // Token 刷新队列模式：
    // 如果已经在刷新中，将当前请求挂起等待刷新完成
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        pendingQueue.push({ resolve, reject })
      }).then((newToken) => {
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return client(originalRequest)
      })
    }

    // 有 refresh token 则尝试刷新
    if (localStorage.getItem('refresh_token')) {
      isRefreshing = true
      originalRequest._retry = true

      try {
        const newToken = await doRefreshToken()
        processQueue(null, newToken)

        // 重试当前请求
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return client(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearAuthState()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 没有 refresh token，直接跳转登录
    clearAuthState()
    window.location.href = '/login'
    return Promise.reject(error)
  },
)

/** 清除本地认证状态 */
function clearAuthState(): void {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('token_expires_at')
  localStorage.removeItem('user')
}

export default client
