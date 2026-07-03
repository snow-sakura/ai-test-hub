import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatSession, KnowledgeBase } from '../../types/ai_chat'
import { aiChatApi, knowledgeBaseApi } from '../../api/ai_chat'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<ChatMessage[]>([])
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const selectedKnowledgeBaseId = ref<number | null>(null)
  const isStreaming = ref(false)
  const selectedModel = ref('qwen:qwen3.7-max')
  let currentAbort: (() => void) | null = null

  const modelOptions = computed(() => [
    { label: 'Qwen3.7-Max', value: 'qwen:qwen3.7-max' },
    { label: 'DeepSeek V4 Flash', value: 'deepseek:deepseek-v4-flash' },
    { label: 'GPT-4.1', value: 'openai:gpt-4.1' },
    { label: 'Claude Sonnet 4.6', value: 'anthropic:claude-sonnet-4-6' },
  ])

  async function loadSessions() {
    sessions.value = await aiChatApi.sessions.list()
  }

  async function loadKnowledgeBases() {
    knowledgeBases.value = await knowledgeBaseApi.list()
  }

  async function createSession(name?: string, knowledgeBaseId?: number) {
    const session = await aiChatApi.sessions.create({
      name: name || '新会话',
      model: selectedModel.value,
      knowledge_base_id: knowledgeBaseId,
    })
    sessions.value.unshift(session)
    currentSession.value = session
    messages.value = []
    return session
  }

  async function selectSession(session: ChatSession) {
    abortCurrentRequest()
    currentSession.value = session
    messages.value = await aiChatApi.messages.list(session.id)
    selectedModel.value = session.model || 'qwen:qwen3.7-max'
    selectedKnowledgeBaseId.value = session.knowledge_base_id || null
  }

  async function updateSession(id: number, data: Partial<ChatSession>) {
    const session = await aiChatApi.sessions.update(id, data)
    const index = sessions.value.findIndex((s) => s.id === id)
    if (index !== -1) {
      sessions.value[index] = { ...sessions.value[index], ...session }
    }
    if (currentSession.value?.id === id) {
      currentSession.value = { ...currentSession.value, ...session }
    }
  }

  async function deleteSession(id: number) {
    await aiChatApi.sessions.delete(id)
    sessions.value = sessions.value.filter((s) => s.id !== id)
    if (currentSession.value?.id === id) {
      currentSession.value = null
      messages.value = []
    }
  }

  function sendMessage(content: string, fileIds: number[] = [], onChunk: (data: string) => void, onError: (error: Error) => void): void {
    if (!currentSession.value) {
      throw new Error('No current session')
    }

    abortCurrentRequest()
    isStreaming.value = true
    const sessionId = currentSession.value!.id

    const { abort } = aiChatApi.messages.stream(sessionId, {
      content,
      model: selectedModel.value,
      file_ids: fileIds,
      knowledge_base_id: selectedKnowledgeBaseId.value,
    }, onChunk, onError)

    currentAbort = abort
  }

  function abortCurrentRequest() {
    if (currentAbort) {
      currentAbort()
      currentAbort = null
    }
    isStreaming.value = false
  }

  function addMessage(message: ChatMessage) {
    messages.value.push(message)
  }

  function updateMessageContent(messageId: number, content: string) {
    const message = messages.value.find((m) => m.id === messageId)
    if (message) {
      message.content = content
    }
  }

  async function rateMessage(messageId: number, rating: string | undefined) {
    await aiChatApi.messages.rate(messageId, rating ?? null)
    const message = messages.value.find((m) => m.id === messageId)
    if (message) {
      message.rating = rating ?? undefined
    }
  }

  async function uploadFile(file: File) {
    return aiChatApi.messages.uploadFile(file)
  }

  async function createKnowledgeBase(name: string, description?: string) {
    const kb = await knowledgeBaseApi.create({ name, description })
    knowledgeBases.value.unshift(kb)
    return kb
  }

  async function uploadToKnowledgeBase(kbId: number, files: File[]) {
    return knowledgeBaseApi.documents.upload(kbId, files)
  }

  function getSessionTitle(session: ChatSession): string {
    const firstMsg = session.first_message?.trim() || ''
    if (firstMsg.length > 0) {
      return firstMsg.length > 10 ? firstMsg.substring(0, 10) + '...' : firstMsg
    }
    return session.name
  }

  return {
    sessions,
    currentSession,
    messages,
    knowledgeBases,
    selectedKnowledgeBaseId,
    isStreaming,
    selectedModel,
    modelOptions,
    loadSessions,
    loadKnowledgeBases,
    createSession,
    selectSession,
    updateSession,
    deleteSession,
    sendMessage,
    abortCurrentRequest,
    addMessage,
    updateMessageContent,
    rateMessage,
    uploadFile,
    createKnowledgeBase,
    uploadToKnowledgeBase,
    getSessionTitle,
  }
})