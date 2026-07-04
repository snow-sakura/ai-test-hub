/**
 * 移动端 AI 聊天 API 层
 * 复用桌面端 API 接口，使用移动端独立 axios 客户端
 */
import client from './client'
import type { ChatSession, ChatMessage, ChatMessageBody } from '../../shared/types/ai_chat'

const BASE_URL = '/v1'

/** 会话相关 API */
export const sessionApi = {
  /** 获取会话列表 */
  list(): Promise<ChatSession[]> {
    return client.get(`${BASE_URL}/ai-chat/sessions`).then((res) => res.data)
  },
  /** 创建新会话 */
  create(data: Partial<ChatSession>): Promise<ChatSession> {
    return client.post(`${BASE_URL}/ai-chat/sessions`, data).then((res) => res.data)
  },
  /** 更新会话 */
  update(id: number, data: Partial<ChatSession>): Promise<ChatSession> {
    return client.put(`${BASE_URL}/ai-chat/sessions/${id}`, data).then((res) => res.data)
  },
  /** 删除会话 */
  delete(id: number): Promise<void> {
    return client.delete(`${BASE_URL}/ai-chat/sessions/${id}`)
  },
}

/** 消息相关 API */
export const messageApi = {
  /** 获取会话消息列表 */
  list(sessionId: number): Promise<ChatMessage[]> {
    return client.get(`${BASE_URL}/ai-chat/sessions/${sessionId}/messages`).then((res) => res.data)
  },
  /** 流式发送消息 */
  stream(
    sessionId: number,
    body: ChatMessageBody,
    onChunk: (data: string) => void | Promise<void>,
    onError: (error: Error) => void,
  ): { abort: () => void } {
    const token = localStorage.getItem('access_token')
    const controller = new AbortController()

    const run = async () => {
      try {
        const response = await fetch(`/api${BASE_URL}/ai-chat/sessions/${sessionId}/messages/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        })

        if (!response.ok) {
          let errorMessage = `HTTP error! status: ${response.status}`
          try {
            const json = await response.json()
            if (json.detail) {
              errorMessage = typeof json.detail === 'string'
                ? json.detail
                : JSON.stringify(json.detail)
            }
          } catch {}
          throw new Error(errorMessage)
        }

        const reader = response.body!.getReader()
        const decoder = new TextDecoder('utf-8')
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          await onChunk(decoder.decode(value))
        }
        await onChunk('')
      } catch (error: any) {
        if (!controller.signal.aborted) {
          onError(error as Error)
        }
      }
    }

    run().catch(() => {})

    return {
      abort: () => controller.abort(),
    }
  },
  /** 上传文件 */
  uploadFile(file: File): Promise<{ id: number; file_name: string; file_size: number; file_type: string; is_image: boolean }> {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`${BASE_URL}/ai-chat/messages/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((res) => res.data)
  },
  /** 消息评分 */
  rate(messageId: number, rating: string | null): Promise<void> {
    return client.put(`${BASE_URL}/ai-chat/messages/${messageId}/rating`, { rating })
  },
}
