/**
 * SSE (Server-Sent Events) Composable
 *
 * 提供连接到 SSE 端点并接收流式事件的能力。
 * 支持动态 URL 切换、断线重连、生命周期的自动清理。
 */

import { onUnmounted, ref, type Ref } from 'vue'

/** SSE 连接选项 */
interface SSEOptions {
  /** 连接成功后自动开始接收事件 */
  autoConnect?: boolean
  /** 发生错误时是否自动重连 */
  autoReconnect?: boolean
  /** 重连延迟（毫秒） */
  reconnectDelay?: number
}

/** SSE 事件处理器 */
type SSEEventHandler = (data: unknown) => void

/**
 * SSE Composable
 *
 * @param url SSE 端点 URL（可以是字符串或 ref）
 * @param onMessage 收到消息时的回调
 * @param options 连接选项
 *
 * @example
 * ```ts
 * const { connect, close, isConnected, setUrl } = useSSE(
 *   '',
 *   (data) => {
 *     if (data.type === 'chunk') console.log(data.content)
 *   }
 * )
 * setUrl('/api/v1/ai/generate/task-xxx/stream')
 * connect()
 * ```
 */
export function useSSE(
  initialUrl: string | Ref<string> = '',
  onMessage: SSEEventHandler,
  options: SSEOptions = {},
) {
  const {
    autoConnect = false,
    autoReconnect = false,
    reconnectDelay = 3000,
  } = options

  /** 当前 EventSource 实例 */
  let eventSource: EventSource | null = null
  /** 当前 SSE URL */
  const url: Ref<string> = ref(
    typeof initialUrl === 'string' ? initialUrl : initialUrl.value,
  )
  /** 是否已连接 */
  const isConnected: Ref<boolean> = ref(false)
  /** 是否正在重连 */
  const isReconnecting: Ref<boolean> = ref(false)
  /** 是否被主动关闭 */
  let isManuallyClosed = false
  /** 重连计时器 */
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  /**
   * 动态更新 URL（下次 connect 时生效）
   */
  function setUrl(newUrl: string): void {
    url.value = newUrl
  }

  /**
   * 建立 SSE 连接
   */
  function connect(): void {
    // 关闭已有连接
    closeInternal()

    if (!url.value) {
      console.warn('[useSSE] URL 为空，跳过连接')
      return
    }

    isManuallyClosed = false
    isReconnecting.value = false

    try {
      eventSource = new EventSource(url.value)

      eventSource.onopen = () => {
        isConnected.value = true
      }

      eventSource.onmessage = (event: MessageEvent) => {
        try {
          const parsed = JSON.parse(event.data)
          onMessage(parsed)

          // 收到 done 或 error 事件时自动关闭
          if (parsed.type === 'done' || parsed.type === 'error') {
            closeInternal()
          }
        } catch {
          // 无法解析的 JSON 忽略
        }
      }

      eventSource.onerror = () => {
        isConnected.value = false

        if (!isManuallyClosed && autoReconnect) {
          isReconnecting.value = true
          if (reconnectTimer) clearTimeout(reconnectTimer)
          reconnectTimer = setTimeout(() => {
            connect()
          }, reconnectDelay)
        }
      }
    } catch {
      isConnected.value = false
    }
  }

  /**
   * 内部关闭（不重置手动关闭标记）
   */
  function closeInternal(): void {
    isConnected.value = false
    isReconnecting.value = false

    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  /**
   * 关闭 SSE 连接（主动调用）
   */
  function close(): void {
    isManuallyClosed = true
    closeInternal()
  }

  // 如果 initialUrl 是 ref，监听变化自动重连
  if (typeof initialUrl !== 'string') {
    // 简单的 watcher 替代方案：用户手动调用 connect
  }

  // 自动连接
  if (autoConnect && url.value) {
    connect()
  }

  // 组件销毁时自动清理
  onUnmounted(() => {
    close()
  })

  return {
    /** 当前 SSE URL */
    url,
    /** 是否已连接 */
    isConnected,
    /** 是否正在重连 */
    isReconnecting,
    /** 更新目标 URL */
    setUrl,
    /** 建立连接 */
    connect,
    /** 关闭连接 */
    close,
  }
}
