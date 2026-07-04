/**
 * 移动端 API 客户端
 * 逻辑与桌面端一致，将 ElMessage 替换为 Vant showToast
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { showToast } from 'vant'

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
 * 请求拦截器 —— 自动注入 token
 */
client.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')

    // 跳过刷新 token 的请求自身
    if (config.url === '/v1/auth/refresh') {
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    }

    if (token && config.headers) {
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
 * 执行 token 刷新
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
  localStorage.setItem('token_expires_at', (Date.now() + 30 * 60 * 1000).toString())
  return access_token
}

/**
 * 响应拦截器 —— 统一错误处理
 */
client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as CustomAxiosConfig | undefined
    const status = error.response?.status

    // 网络连接失败
    if (!error.response) {
      showToast({ message: '网络连接失败，请检查网络', type: 'fail' })
      return Promise.reject(error)
    }

    // 非 401 错误
    if (!originalRequest || status !== 401) {
      const errData = error.response?.data as { detail?: string; message?: string } | undefined
      const errMsg = errData?.detail || errData?.message || ''
      if (status && status >= 500) {
        showToast({ message: errMsg || '服务器错误，请稍后重试', type: 'fail' })
      } else if (status && errMsg) {
        showToast({ message: errMsg, type: 'fail' })
      }
      return Promise.reject(error)
    }

    // 重试请求也失败
    if (originalRequest._retry) {
      return Promise.reject(error)
    }

    // 登出或刷新请求不重试
    const noRetryPaths = ['/v1/auth/logout', '/v1/auth/refresh']
    if (noRetryPaths.some((p) => originalRequest.url?.includes(p))) {
      clearAuthState()
      window.location.href = '/m/login'
      return Promise.reject(error)
    }

    // Token 刷新队列
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

    // 尝试刷新
    if (localStorage.getItem('refresh_token')) {
      isRefreshing = true
      originalRequest._retry = true

      try {
        const newToken = await doRefreshToken()
        processQueue(null, newToken)
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return client(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearAuthState()
        window.location.href = '/m/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    clearAuthState()
    window.location.href = '/m/login'
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
