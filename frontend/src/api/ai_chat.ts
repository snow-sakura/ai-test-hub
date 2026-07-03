import client from './client'
import type { ChatMessageBody, ChatSession } from '../types/ai_chat'
import type { KnowledgeBase, KBDocument, KBSearchResult } from '../types/ai_chat'

const BASE_URL = '/v1'

export const aiChatApi = {
  sessions: {
    list(): Promise<ChatSession[]> {
      return client.get(`${BASE_URL}/ai-chat/sessions`).then((res) => res.data)
    },
    create(data: Partial<ChatSession>): Promise<ChatSession> {
      return client.post(`${BASE_URL}/ai-chat/sessions`, data).then((res) => res.data)
    },
    get(id: number): Promise<ChatSession> {
      return client.get(`${BASE_URL}/ai-chat/sessions/${id}`).then((res) => res.data)
    },
    update(id: number, data: Partial<ChatSession>): Promise<ChatSession> {
      return client.put(`${BASE_URL}/ai-chat/sessions/${id}`, data).then((res) => res.data)
    },
    delete(id: number): Promise<void> {
      return client.delete(`${BASE_URL}/ai-chat/sessions/${id}`)
    },
  },
  messages: {
    list(sessionId: number) {
      return client.get(`${BASE_URL}/ai-chat/sessions/${sessionId}/messages`).then((res) => res.data)
    },
    stream(sessionId: number, body: ChatMessageBody, onChunk: (data: string) => void, onError: (error: Error) => void, onComplete?: () => void): { abort: () => void } {
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
                errorMessage = json.detail
              }
            } catch {}
            throw new Error(errorMessage)
          }

          const reader = response.body!.getReader()
          const decoder = new TextDecoder('utf-8')
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            onChunk(decoder.decode(value))
          }
        } catch (error: any) {
          if (!controller.signal.aborted) {
            onError(error as Error)
          }
        } finally {
          if (!controller.signal.aborted) {
            onComplete?.()
          }
        }
      }

      run().catch(() => {})

      return {
        abort: () => controller.abort(),
      }
    },
    uploadFile(file: File): Promise<{ id: number; file_name: string; file_size: number; file_type: string; is_image: boolean }> {
      const formData = new FormData()
      formData.append('file', file)
      return client.post(`${BASE_URL}/ai-chat/messages/files`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then((res) => res.data)
    },
    rate(messageId: number, rating: string | null): Promise<void> {
      return client.put(`${BASE_URL}/ai-chat/messages/${messageId}/rating`, { rating })
    },
  },
}

export const knowledgeBaseApi = {
  list(): Promise<KnowledgeBase[]> {
    return client.get(`${BASE_URL}/knowledge-base`).then((res) => res.data)
  },
  create(data: { name: string; description?: string; embedding_model?: string }): Promise<KnowledgeBase> {
    return client.post(`${BASE_URL}/knowledge-base`, data).then((res) => res.data)
  },
  get(id: number): Promise<KnowledgeBase> {
    return client.get(`${BASE_URL}/knowledge-base/${id}`).then((res) => res.data)
  },
  update(id: number, data: Partial<KnowledgeBase>): Promise<KnowledgeBase> {
    return client.put(`${BASE_URL}/knowledge-base/${id}`, data).then((res) => res.data)
  },
  delete(id: number): Promise<void> {
    return client.delete(`${BASE_URL}/knowledge-base/${id}`)
  },
  documents: {
    list(kbId: number): Promise<KBDocument[]> {
      return client.get(`${BASE_URL}/knowledge-base/${kbId}/documents`).then((res) => res.data)
    },
    upload(kbId: number, files: File[]): Promise<KBDocument[]> {
      const formData = new FormData()
      files.forEach((file) => formData.append('files', file))
      return client.post(`${BASE_URL}/knowledge-base/${kbId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then((res) => res.data)
    },
    delete(kbId: number, docId: number): Promise<void> {
      return client.delete(`${BASE_URL}/knowledge-base/${kbId}/documents/${docId}`)
    },
  },
  search(kbId: number, query: string, topK: number = 5): Promise<KBSearchResult[]> {
    return client.post(`${BASE_URL}/knowledge-base/${kbId}/search`, { query, top_k: topK }).then((res) => res.data)
  },
  reindex(kbId: number): Promise<KnowledgeBase> {
    return client.post(`${BASE_URL}/knowledge-base/${kbId}/reindex`).then((res) => res.data)
  },
}