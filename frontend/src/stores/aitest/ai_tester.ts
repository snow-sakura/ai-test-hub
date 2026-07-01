/**
 * AI 评测师 Pinia Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AITesterSession, AITesterSessionCreate, AITesterMessage } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export const useAITesterStore = defineStore('aitest-ai-tester', () => {
  const sessions = ref<AITesterSession[]>([])
  const currentSessionId = ref<number | null>(null)
  const messages = ref<AITesterMessage[]>([])
  const totalMessages = ref(0)
  const loadedCount = ref(0)
  const isLoading = ref(false)
  const isSending = ref(false)

  async function fetchSessions() {
    isLoading.value = true
    try {
      const res = await aitestApi.listTesterSessions()
      sessions.value = res.data || []
    } catch (e) {
      console.error('获取会话列表失败:', e)
      sessions.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function createSession(data: AITesterSessionCreate) {
    try {
      const res = await aitestApi.createTesterSession(data)
      if (res.data) {
        sessions.value.unshift(res.data)
        currentSessionId.value = res.data.id
        messages.value = []
        totalMessages.value = 0
        loadedCount.value = 0
      }
      return res.data
    } catch (e) {
      console.error('创建会话失败:', e)
      throw e
    }
  }

  async function deleteSession(sessionId: number) {
    const res = await aitestApi.deleteTesterSession(sessionId)
    if (res.data) {
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      if (currentSessionId.value === sessionId) {
        currentSessionId.value = null
        messages.value = []
        totalMessages.value = 0
        loadedCount.value = 0
      }
    }
    return res.data
  }

  async function selectSession(sessionId: number) {
    currentSessionId.value = sessionId
    isLoading.value = true
    try {
      const res = await aitestApi.listTesterMessages(sessionId, 0, 50)
      const dataList = res.data || []
      messages.value = Array.isArray(dataList) ? dataList : []
      totalMessages.value = messages.value.length
      loadedCount.value = messages.value.length
    } catch (e) {
      console.error('获取消息列表失败:', e)
      messages.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function sendMessage(content: string, model?: string) {
    if (!currentSessionId.value) return
    isSending.value = true
    try {
      await aitestApi.sendTesterMessage(
        currentSessionId.value,
        { message: content, model: model || 'deepseek:deepseek-v4-flash' },
      )
      await selectSession(currentSessionId.value!)
      await fetchSessions()
    } catch (e) {
      console.error('发送消息失败:', e)
    } finally {
      isSending.value = false
    }
  }

  async function updateSession(sessionId: number, data: { name: string }) {
    const res = await aitestApi.updateTesterSession(sessionId, data)
    if (res.data) {
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) session.name = data.name
    }
    return res.data
  }

  async function batchDeleteSessions(ids: number[]) {
    try {
      await aitestApi.batchDeleteTesterSessions(ids)
      sessions.value = sessions.value.filter(s => !ids.includes(s.id))
      if (currentSessionId.value && ids.includes(currentSessionId.value)) {
        currentSessionId.value = null
        messages.value = []
        totalMessages.value = 0
        loadedCount.value = 0
      }
    } catch (e) {
      console.error('批量删除会话失败:', e)
    }
  }

  return {
    sessions, currentSessionId, messages, totalMessages, loadedCount, isLoading, isSending,
    fetchSessions, createSession, deleteSession, updateSession,
    batchDeleteSessions, selectSession, sendMessage,
  }
})
