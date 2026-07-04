/**
 * 移动端 AI 聊天状态管理
 * 与桌面端 chat store 逻辑一致，使用独立 API 模块
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatSession, ChatMessage, KnowledgeBase } from '../../shared/types/ai_chat'
import { sessionApi, messageApi } from '../api/chat'
import { knowledgeBaseApi } from '../api/knowledge'

export const useChatStore = defineStore('mobile-chat', () => {
  // ====== State ======
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const selectedModel = ref('opencode:mimo-v2.5-free')
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const selectedKnowledgeBaseId = ref<number | null>(null)
  let currentAbort: (() => void) | null = null

  // ====== Computed ======
  const modelOptions = computed(() => [
    { label: 'OpenCode MiMo V2.5 Free', value: 'opencode:mimo-v2.5-free' },
    { label: 'Qwen3.7-Max', value: 'qwen:qwen3.7-max' },
    { label: 'DeepSeek V4 Flash', value: 'deepseek:deepseek-v4-flash' },
  ])

  // ====== Session Actions ======

  /** 加载会话列表 */
  async function loadSessions() {
    sessions.value = await sessionApi.list()
  }

  /** 创建新会话 */
  async function createSession(name?: string) {
    const session = await sessionApi.create({
      name: name || '新会话',
      model: selectedModel.value,
      knowledge_base_id: selectedKnowledgeBaseId.value ?? undefined,
    })
    sessions.value.unshift(session)
    currentSession.value = session
    messages.value = []
    return session
  }

  /** 选中会话 */
  async function selectSession(session: ChatSession) {
    abortCurrentRequest()
    currentSession.value = session
    messages.value = await messageApi.list(session.id)
    selectedModel.value = session.model || 'opencode:mimo-v2.5-free'
    selectedKnowledgeBaseId.value = session.knowledge_base_id || null
  }

  /** 删除会话 */
  async function deleteSession(id: number) {
    await sessionApi.delete(id)
    sessions.value = sessions.value.filter((s) => s.id !== id)
    if (currentSession.value?.id === id) {
      currentSession.value = null
      messages.value = []
    }
  }

  /** 更新会话设置 */
  async function updateSession(id: number, data: Partial<ChatSession>) {
    const session = await sessionApi.update(id, data)
    const index = sessions.value.findIndex((s) => s.id === id)
    if (index !== -1) {
      sessions.value[index] = { ...sessions.value[index], ...session }
    }
    if (currentSession.value?.id === id) {
      currentSession.value = { ...currentSession.value, ...session }
    }
  }

  // ====== Message Actions ======

  /** 流式发送消息 */
  function sendMessage(
    content: string,
    fileIds: number[],
    onChunk: (data: string) => void | Promise<void>,
    onError: (error: Error) => void,
  ) {
    if (!currentSession.value) return

    abortCurrentRequest()
    isStreaming.value = true

    const { abort } = messageApi.stream(
      currentSession.value.id,
      {
        content,
        model: selectedModel.value,
        file_ids: fileIds,
        knowledge_base_id: selectedKnowledgeBaseId.value,
      },
      onChunk,
      onError,
    )
    currentAbort = abort
  }

  /** 中止当前请求 */
  function abortCurrentRequest() {
    if (currentAbort) {
      currentAbort()
      currentAbort = null
    }
    isStreaming.value = false
  }

  /** 添加消息 */
  function addMessage(message: ChatMessage) {
    messages.value.push(message)
  }

  /** 更新消息内容（流式追加） */
  function updateMessageContent(messageId: number, content: string) {
    const msg = messages.value.find((m) => m.id === messageId)
    if (msg) msg.content = content
  }

  /** 替换消息 ID（后端返回真实 ID 后） */
  function replaceMessageId(oldId: number, newId: number) {
    const msg = messages.value.find((m) => m.id === oldId)
    if (msg) msg.id = newId
  }

  /** 评分 */
  async function rateMessage(messageId: number, rating: string | undefined) {
    await messageApi.rate(messageId, rating ?? null)
    const msg = messages.value.find((m) => m.id === messageId)
    if (msg) msg.rating = rating ?? undefined
  }

  /** 上传文件 */
  async function uploadFile(file: File) {
    return messageApi.uploadFile(file)
  }

  // ====== Knowledge Base Actions ======

  /** 加载知识库列表 */
  async function loadKnowledgeBases() {
    knowledgeBases.value = await knowledgeBaseApi.list()
  }

  /** 选择知识库 */
  async function selectKnowledgeBase(kbId: number | null) {
    selectedKnowledgeBaseId.value = kbId
    if (currentSession.value) {
      await updateSession(currentSession.value.id, { knowledge_base_id: kbId ?? undefined })
    }
  }

  /** 获取会话标题（截取首条消息前 10 字） */
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
    isStreaming,
    selectedModel,
    knowledgeBases,
    selectedKnowledgeBaseId,
    modelOptions,
    loadSessions,
    createSession,
    selectSession,
    deleteSession,
    updateSession,
    sendMessage,
    abortCurrentRequest,
    addMessage,
    updateMessageContent,
    replaceMessageId,
    rateMessage,
    uploadFile,
    loadKnowledgeBases,
    selectKnowledgeBase,
    getSessionTitle,
  }
})
