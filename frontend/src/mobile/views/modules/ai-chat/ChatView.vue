<template>
  <!--
    移动端 AI 聊天室 - 阶段 3
    - 文件上传支持（选择文件、预览、删除）
    - 知识库关联面板
    - 模型切换面板
    - 消息文件附件显示
  -->
  <div class="m-chat">
    <!-- 无会话时：欢迎屏 -->
    <div v-if="!store.currentSession" class="m-welcome">
      <div class="m-welcome-icon">
        <van-icon name="chat-o" size="64" color="#C67B5C" />
      </div>
      <h2 class="m-welcome-title">AI 聊天室</h2>
      <p class="m-welcome-desc">与智能助手对话，获取专业帮助</p>
      <div class="m-quick-prompts">
        <div class="m-prompt-chip" @click="fillPrompt('帮我设计一套登录功能的测试用例')">
          <van-icon name="edit" size="16" color="#C67B5C" />
          <span>设计测试用例</span>
        </div>
        <div class="m-prompt-chip" @click="fillPrompt('解释一下什么是RESTful API')">
          <van-icon name="info-o" size="16" color="#10b981" />
          <span>技术问答</span>
        </div>
        <div class="m-prompt-chip" @click="fillPrompt('帮我优化这段代码')">
          <van-icon name="setting-o" size="16" color="#3b82f6" />
          <span>代码优化</span>
        </div>
        <div class="m-prompt-chip" @click="fillPrompt('生成API接口文档')">
          <van-icon name="description" size="16" color="#f59e0b" />
          <span>文档生成</span>
        </div>
      </div>
    </div>

    <!-- 有会话时：聊天界面 -->
    <template v-else>
      <!-- 会话头部 -->
      <div class="m-chat-header">
        <van-icon name="chat-o" size="18" color="#C67B5C" />
        <span class="m-chat-title">{{ store.currentSession.name }}</span>
        <!-- 模型/知识库状态标签 -->
        <div class="m-header-tags">
          <span class="m-tag" @click="showModelPanel = true">
            <van-icon name="setting-o" size="12" />
            {{ currentModelLabel }}
          </span>
          <span v-if="store.selectedKnowledgeBaseId" class="m-tag m-tag-kb" @click="showKBPanel = true">
            <van-icon name="label-o" size="12" />
            {{ currentKBName }}
          </span>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="messageContainer" class="m-message-list">
        <div
          v-for="msg in store.messages"
          :key="msg.id"
          :class="['m-msg-block', msg.role === 'user' ? 'is-user' : 'is-ai']"
        >
          <!-- AI 消息：文档式 -->
          <template v-if="msg.role === 'assistant'">
            <div class="m-ai-msg">
              <div class="m-ai-label">
                <span class="m-ai-name">AI 助手</span>
                <span class="m-ai-time">{{ formatTime(msg.created_at) }}</span>
              </div>
              <div class="m-markdown" v-html="renderMarkdown(msg.content)"></div>
              <!-- 文件附件 -->
              <div v-if="msg.files && msg.files.length > 0" class="m-msg-files">
                <div v-for="file in msg.files" :key="file.id" class="m-file-tag">
                  <van-icon :name="file.is_image ? 'photo-o' : 'description'" size="14" />
                  <span>{{ file.file_name }}</span>
                </div>
              </div>
              <div class="m-ai-actions">
                <van-button
                  size="small"
                  :type="msg.rating === 'up' ? 'primary' : 'default'"
                  @click="handleRate(msg.id, 'up')"
                >
                  <van-icon name="good-job-o" size="14" />
                </van-button>
                <van-button
                  size="small"
                  :type="msg.rating === 'down' ? 'danger' : 'default'"
                  @click="handleRate(msg.id, 'down')"
                >
                  <van-icon name="good-job-o" size="14" style="transform: rotate(180deg)" />
                </van-button>
                <van-button size="small" @click="handleCopy(msg.content)">
                  <van-icon name="records-o" size="14" />
                </van-button>
              </div>
            </div>
          </template>

          <!-- 用户消息：气泡 -->
          <template v-else>
            <div class="m-bubble m-bubble-user">
              <!-- 文件附件 -->
              <div v-if="msg.files && msg.files.length > 0" class="m-bubble-files">
                <div v-for="file in msg.files" :key="file.id" class="m-file-tag m-file-tag-light">
                  <van-icon :name="file.is_image ? 'photo-o' : 'description'" size="12" />
                  <span>{{ file.file_name }}</span>
                </div>
              </div>
              <div class="m-bubble-content">{{ msg.content }}</div>
              <div class="m-bubble-time">{{ formatTime(msg.created_at) }}</div>
            </div>
          </template>
        </div>

        <!-- Typing indicator -->
        <div v-if="showTyping" class="m-msg-block is-ai">
          <div class="m-ai-msg">
            <div class="m-ai-label">
              <span class="m-ai-name">AI 助手</span>
              <span class="m-ai-time">正在回复...</span>
            </div>
            <div class="m-typing">
              <span class="m-dot"></span>
              <span class="m-dot"></span>
              <span class="m-dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 文件上传预览区 -->
      <div v-if="uploadedFiles.length > 0" class="m-upload-preview">
        <div v-for="(file, index) in uploadedFiles" :key="index" class="m-upload-item">
          <van-icon :name="isImageFile(file.name) ? 'photo-o' : 'description'" size="16" color="#C67B5C" />
          <span class="m-upload-name">{{ file.name }}</span>
          <van-icon name="cross" size="14" color="#999" @click="removeUploadedFile(index)" />
        </div>
      </div>

      <!-- 输入区 -->
      <div class="m-chat-footer">
        <div class="m-input-tools">
          <van-icon name="records-o" size="20" color="#8B7355" @click="triggerFileUpload" />
          <van-icon name="photo-o" size="20" color="#8B7355" @click="triggerImageUpload" />
          <input ref="fileInput" type="file" multiple class="m-hidden-input"
            accept=".docx,.doc,.xmind,.md,.xlsx,.xls,.csv,.txt,.htm,.html,.pdf,.xml"
            @change="handleFileSelect" />
          <input ref="imageInput" type="file" multiple class="m-hidden-input"
            accept="image/*"
            @change="handleImageSelect" />
        </div>
        <div class="m-input-row">
          <van-field
            v-model="inputText"
            placeholder="输入消息..."
            :disabled="store.isStreaming"
            @keydown.enter.exact.prevent="handleSend"
            class="m-input"
            autosize
            rows="1"
            type="textarea"
          />
          <van-button
            class="m-btn-send"
            type="primary"
            :loading="store.isStreaming"
            :disabled="!inputText.trim() && uploadedFiles.length === 0"
            @click="handleSend"
            round
            size="small"
          >
            <van-icon name="guide-o" size="18" />
          </van-button>
        </div>
      </div>
    </template>

    <!-- 会话列表侧滑抽屉 -->
    <van-popup
      v-model:show="showDrawer"
      position="left"
      :style="{ width: '75%', height: '100%' }"
      class="m-session-drawer"
    >
      <div class="m-drawer-content">
        <div class="m-drawer-header">
          <span class="m-drawer-title">会话列表</span>
          <van-button type="primary" size="small" round icon="plus" @click="handleNewSession">
            新对话
          </van-button>
        </div>
        <van-search v-model="searchKeyword" placeholder="搜索会话" shape="round" class="m-drawer-search" />
        <div class="m-session-list">
          <template v-for="group in sessionGroups" :key="group.label">
            <div class="m-date-label">{{ group.label }}</div>
            <div
              v-for="session in group.sessions"
              :key="session.id"
              :class="['m-session-item', { active: store.currentSession?.id === session.id }]"
              @click="handleSelectSession(session)"
            >
              <van-icon name="chat-o" size="18" color="#8B7355" />
              <div class="m-session-info">
                <span class="m-session-title">{{ store.getSessionTitle(session) }}</span>
                <span class="m-session-time">{{ formatTime(session.created_at) }}</span>
              </div>
              <van-icon name="delete-o" size="16" color="#ef4444" @click.stop="handleDeleteSession(session.id)" />
            </div>
          </template>
          <van-empty v-if="store.sessions.length === 0" description="暂无会话" image="search" />
        </div>
      </div>
    </van-popup>

    <!-- 模型切换面板 -->
    <van-popup v-model:show="showModelPanel" position="bottom" round :style="{ maxHeight: '50%' }">
      <div class="m-panel">
        <div class="m-panel-header">
          <span class="m-panel-title">选择模型</span>
          <van-icon name="cross" size="20" @click="showModelPanel = false" />
        </div>
        <div class="m-panel-body">
          <div
            v-for="opt in store.modelOptions"
            :key="opt.value"
            :class="['m-panel-item', { active: store.selectedModel === opt.value }]"
            @click="handleModelChange(opt.value)"
          >
            <span>{{ opt.label }}</span>
            <van-icon v-if="store.selectedModel === opt.value" name="success" size="18" color="#C67B5C" />
          </div>
        </div>
      </div>
    </van-popup>

    <!-- 知识库选择面板 -->
    <van-popup v-model:show="showKBPanel" position="bottom" round :style="{ maxHeight: '60%' }">
      <div class="m-panel">
        <div class="m-panel-header">
          <span class="m-panel-title">关联知识库</span>
          <van-icon name="cross" size="20" @click="showKBPanel = false" />
        </div>
        <div class="m-panel-body">
          <div
            v-if="store.selectedKnowledgeBaseId"
            class="m-panel-item m-kb-clear"
            @click="handleKBSelect(null)"
          >
            <van-icon name="close" size="16" color="#ef4444" />
            <span>取消关联知识库</span>
          </div>
          <div
            v-for="kb in store.knowledgeBases"
            :key="kb.id"
            :class="['m-panel-item', { active: store.selectedKnowledgeBaseId === kb.id }]"
            @click="handleKBSelect(kb.id)"
          >
            <div class="m-kb-info">
              <span class="m-kb-name">{{ kb.name }}</span>
              <span class="m-kb-count">{{ kb.document_count }} 文档</span>
            </div>
            <van-icon v-if="store.selectedKnowledgeBaseId === kb.id" name="success" size="18" color="#C67B5C" />
          </div>
          <van-empty v-if="store.knowledgeBases.length === 0" description="暂无知识库" image="search" />
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useChatStore } from '../../../stores/chat'
import { formatTime } from '@/utils'
import type { ChatSession } from '../../../../shared/types/ai_chat'

const store = useChatStore()

// ====== State ======
const inputText = ref('')
const messageContainer = ref<HTMLElement | null>(null)
const showDrawer = ref(false)
const searchKeyword = ref('')
const showModelPanel = ref(false)
const showKBPanel = ref(false)
const uploadedFiles = ref<File[]>([])
const uploadedFileIds = ref<number[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)

// ====== Computed ======
const showTyping = computed(() => {
  if (!store.isStreaming) return false
  const last = store.messages[store.messages.length - 1]
  return !last || last.role !== 'assistant'
})

const currentModelLabel = computed(() => {
  const opt = store.modelOptions.find((o) => o.value === store.selectedModel)
  return opt?.label?.split(' ')[0] || '模型'
})

const currentKBName = computed(() => {
  const kb = store.knowledgeBases.find((k) => k.id === store.selectedKnowledgeBaseId)
  return kb?.name || '知识库'
})

interface SessionGroup { label: string; sessions: ChatSession[] }
const sessionGroups = computed<SessionGroup[]>(() => {
  const list = searchKeyword.value
    ? store.sessions.filter((s: ChatSession) =>
        s.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
        (s.first_message && s.first_message.toLowerCase().includes(searchKeyword.value.toLowerCase()))
      )
    : store.sessions

  const groups: Record<string, ChatSession[]> = {}
  const now = new Date()
  const todayStr = now.toISOString().slice(0, 10)
  const yesterday = new Date(now.getTime() - 86400000).toISOString().slice(0, 10)

  for (const s of list) {
    const d = s.created_at ? new Date(s.created_at) : new Date()
    const ds = d.toISOString().slice(0, 10)
    let label = ''
    if (ds === todayStr) label = '今天'
    else if (ds === yesterday) label = '昨天'
    else label = `${d.getMonth() + 1}月${d.getDate()}日`
    if (!groups[label]) groups[label] = []
    groups[label].push(s)
  }

  const order = ['今天', '昨天']
  const result: SessionGroup[] = []
  for (const k of order) {
    if (groups[k]) result.push({ label: k, sessions: groups[k] })
  }
  for (const [k, v] of Object.entries(groups)) {
    if (!order.includes(k)) result.push({ label: k, sessions: v })
  }
  return result
})

// ====== Actions ======
function scrollToBottom() {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

function renderMarkdown(content: string): string {
  const html = marked.parse(content) as string
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre', 'blockquote',
      'ul', 'ol', 'li', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'div', 'span'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'title', 'class', 'id'],
  })
}

function isImageFile(name: string): boolean {
  return /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(name)
}

async function fillPrompt(text: string) {
  if (!store.currentSession) {
    await store.createSession()
    inputText.value = text
    await nextTick()
    handleSend()
    return
  }
  inputText.value = text
}

async function handleNewSession() {
  await store.createSession()
  showDrawer.value = false
}

async function handleSelectSession(session: ChatSession) {
  await store.selectSession(session)
  showDrawer.value = false
  await nextTick()
  scrollToBottom()
}

async function handleDeleteSession(id: number) {
  try {
    await showConfirmDialog({ title: '确认删除', message: '此操作不可恢复' })
    await store.deleteSession(id)
    showToast({ message: '已删除', type: 'success' })
  } catch {
    // 用户取消
  }
}

// ====== 文件上传 ======
function triggerFileUpload() {
  fileInput.value?.click()
}

function triggerImageUpload() {
  imageInput.value?.click()
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  for (const file of files) {
    uploadedFiles.value.push(file)
    try {
      const result = await store.uploadFile(file)
      uploadedFileIds.value.push(result.id)
    } catch {
      showToast({ message: `上传 ${file.name} 失败`, type: 'fail' })
    }
  }
  target.value = ''
}

async function handleImageSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  for (const file of files) {
    uploadedFiles.value.push(file)
    try {
      const result = await store.uploadFile(file)
      uploadedFileIds.value.push(result.id)
    } catch {
      showToast({ message: `上传 ${file.name} 失败`, type: 'fail' })
    }
  }
  target.value = ''
}

function removeUploadedFile(index: number) {
  uploadedFiles.value.splice(index, 1)
  uploadedFileIds.value.splice(index, 1)
}

// ====== 模型/知识库 ======
async function handleModelChange(model: string) {
  store.selectedModel = model
  if (store.currentSession) {
    await store.updateSession(store.currentSession.id, { model })
  }
  showModelPanel.value = false
}

async function handleKBSelect(kbId: number | null) {
  await store.selectKnowledgeBase(kbId)
  showKBPanel.value = false
}

// ====== 发送消息 ======
async function handleSend() {
  if (!inputText.value.trim() && uploadedFiles.value.length === 0) {
    showToast({ message: '请输入消息或选择文件', type: 'fail' })
    return
  }

  const content = inputText.value.trim() || '请分析我上传的文件'
  const sendFileIds = [...uploadedFileIds.value]
  const userMessage = {
    id: Date.now(),
    session_id: store.currentSession!.id,
    role: 'user' as const,
    content,
    files: sendFileIds.map((id) => ({ id, file_name: '', file_size: 0, file_type: '', is_image: false })),
    created_at: new Date().toISOString(),
  }
  store.addMessage(userMessage)
  inputText.value = ''
  uploadedFiles.value = []
  uploadedFileIds.value = []
  await nextTick()
  scrollToBottom()

  let buffer = ''
  let assistantContent = ''
  let assistantMessageId = 0

  const onChunk = async (data: string) => {
    buffer += data
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const jsonStr = line.substring(6)
          if (jsonStr === '[DONE]') {
            store.isStreaming = false
            await nextTick()
            scrollToBottom()
            continue
          }
          const json = JSON.parse(jsonStr)
          if (json.type === 'token') {
            assistantContent += json.content
            if (assistantMessageId === 0) {
              const newMsg = {
                id: Date.now(),
                session_id: store.currentSession!.id,
                role: 'assistant' as const,
                content: assistantContent,
                files: [],
                created_at: new Date().toISOString(),
              }
              store.addMessage(newMsg)
              assistantMessageId = newMsg.id
            } else {
              store.updateMessageContent(assistantMessageId, assistantContent)
            }
            await nextTick()
            scrollToBottom()
          } else if (json.type === 'complete') {
            if (json.message_id && assistantMessageId !== 0) {
              store.replaceMessageId(assistantMessageId, json.message_id)
              assistantMessageId = json.message_id
            }
            if (assistantMessageId !== 0) {
              store.updateMessageContent(assistantMessageId, json.content)
            }
            store.isStreaming = false
            store.loadSessions()
            await nextTick()
            scrollToBottom()
          } else if (json.type === 'error') {
            showToast({ message: json.message, type: 'fail' })
            store.isStreaming = false
          }
        } catch {
          continue
        }
      }
    }
  }

  const onError = (error: Error) => {
    if (error.message !== 'net::ERR_ABORTED') {
      showToast({ message: '发送失败: ' + error.message, type: 'fail' })
    }
    store.isStreaming = false
  }

  store.sendMessage(content, sendFileIds, onChunk, onError)
}

async function handleRate(messageId: number, rating: string) {
  const msg = store.messages.find((m: { id: number }) => m.id === messageId)
  const newRating = msg?.rating === rating ? undefined : rating
  await store.rateMessage(messageId, newRating)
}

async function handleCopy(content: string) {
  const cleanText = content
    .replace(/```[\s\S]*?```/g, (m) => m.replace(/```\w*\n?/g, '').replace(/```/g, ''))
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .trim()

  try {
    await navigator.clipboard.writeText(cleanText)
    showToast({ message: '已复制', type: 'success' })
  } catch {
    showToast({ message: '复制失败', type: 'fail' })
  }
}

// ====== Lifecycle ======
onMounted(async () => {
  try {
    await Promise.all([
      store.loadSessions(),
      store.loadKnowledgeBases(),
    ])
  } catch {
    showToast({ message: '加载数据失败', type: 'fail' })
  }
})

onUnmounted(() => {
  store.abortCurrentRequest()
})
</script>

<style scoped lang="scss">
.m-chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 46px - 50px);
  background: var(--van-background);
}

/* ====== 欢迎屏 ====== */
.m-welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
}

.m-welcome-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(198, 123, 92, 0.1), rgba(212, 165, 116, 0.06));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.m-welcome-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--van-text-color);
  margin: 0 0 8px;
}

.m-welcome-desc {
  font-size: 14px;
  color: var(--van-text-color-3);
  margin: 0 0 28px;
}

.m-quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.m-prompt-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--van-background-2);
  border: 1px solid var(--van-border-color);
  border-radius: 20px;
  font-size: 13px;
  color: var(--van-text-color-2);
  cursor: pointer;
  transition: all 0.2s;

  &:active {
    background: rgba(198, 123, 92, 0.08);
    transform: scale(0.97);
  }
}

/* ====== 会话头部 ====== */
.m-chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
  flex-wrap: wrap;
}

.m-chat-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--van-text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.m-header-tags {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.m-tag {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  background: rgba(198, 123, 92, 0.1);
  color: #C67B5C;
  cursor: pointer;
}

.m-tag-kb {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

/* ====== 消息列表 ====== */
.m-message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  -webkit-overflow-scrolling: touch;
}

.m-msg-block {
  margin-bottom: 16px;
  animation: m-fade-in 0.3s ease;

  &.is-user {
    display: flex;
    justify-content: flex-end;
  }

  &.is-ai {
    max-width: 100%;
  }
}

@keyframes m-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ====== AI 消息 ====== */
.m-ai-msg {
  width: 100%;
}

.m-ai-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.m-ai-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--van-text-color);
}

.m-ai-time {
  font-size: 11px;
  color: var(--van-text-color-3);
}

.m-ai-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--van-border-color);
}

/* ====== 文件附件标签 ====== */
.m-msg-files {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.m-file-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(198, 123, 92, 0.06);
  border-radius: 6px;
  font-size: 12px;
  color: var(--van-text-color-2);
}

.m-file-tag-light {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
}

/* ====== 用户气泡 ====== */
.m-bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 14px;
}

.m-bubble-user {
  background: linear-gradient(135deg, #C67B5C, #D49472);
  color: #fff;
  border-radius: 14px 14px 4px 14px;
  box-shadow: 0 2px 12px rgba(198, 123, 92, 0.25);
}

.m-bubble-files {
  margin-bottom: 6px;
}

.m-bubble-content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.m-bubble-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 4px;
  text-align: right;
}

/* ====== Markdown 样式 ====== */
.m-markdown {
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;

  :deep(pre) {
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
  }

  :deep(code) {
    background: rgba(198, 123, 92, 0.1);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 13px;
    color: #C67B5C;
  }

  :deep(pre code) {
    background: none;
    padding: 0;
    color: inherit;
  }

  :deep(blockquote) {
    border-left: 3px solid #C67B5C;
    margin: 8px 0;
    padding: 6px 12px;
    background: rgba(198, 123, 92, 0.04);
    border-radius: 0 6px 6px 0;
    color: var(--van-text-color-2);
  }

  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    overflow-x: auto;
    display: block;
  }

  :deep(th),
  :deep(td) {
    border: 1px solid var(--van-border-color);
    padding: 6px 8px;
    text-align: left;
  }

  :deep(th) {
    background: rgba(198, 123, 92, 0.06);
    font-weight: 600;
  }

  :deep(a) {
    color: #C67B5C;
    text-decoration: underline;
  }

  :deep(img) {
    max-width: 100%;
    border-radius: 6px;
  }
}

/* ====== Typing indicator ====== */
.m-typing {
  display: flex;
  gap: 4px;
  padding: 6px 0;
}

.m-dot {
  width: 6px;
  height: 6px;
  background: #C67B5C;
  border-radius: 50%;
  animation: m-typing-dot 1.4s infinite ease-in-out both;

  &:nth-child(1) { animation-delay: -0.32s; }
  &:nth-child(2) { animation-delay: -0.16s; }
}

@keyframes m-typing-dot {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

/* ====== 文件上传预览 ====== */
.m-upload-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  background: var(--van-background-2);
  border-top: 1px solid var(--van-border-color);
}

.m-upload-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(198, 123, 92, 0.06);
  border-radius: 8px;
  font-size: 12px;
}

.m-upload-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--van-text-color-2);
}

/* ====== 输入区 ====== */
.m-chat-footer {
  padding: 8px 12px;
  background: var(--van-background-2);
  border-top: 1px solid var(--van-border-color);
}

.m-input-tools {
  display: flex;
  gap: 16px;
  padding: 4px 0 8px;
}

.m-hidden-input {
  display: none;
}

.m-input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.m-input {
  flex: 1;
  :deep(.van-field__control) {
    background: var(--van-background);
    border: 1px solid var(--van-border-color);
    border-radius: 20px;
    padding: 8px 14px;
    font-size: 14px;
    resize: none;
  }
}

.m-btn-send {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  :deep(.van-button__text) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

/* ====== 会话抽屉 ====== */
.m-session-drawer {
  .m-drawer-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--van-background);
  }

  .m-drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid var(--van-border-color);
  }

  .m-drawer-title {
    font-size: 17px;
    font-weight: 700;
    color: var(--van-text-color);
  }

  .m-drawer-search {
    padding: 8px 12px;
  }

  .m-session-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 8px 16px;
  }

  .m-date-label {
    font-size: 12px;
    color: var(--van-text-color-3);
    padding: 10px 12px 4px;
    font-weight: 500;
  }

  .m-session-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 4px;
    cursor: pointer;
    transition: background 0.2s;

    &:active,
    &.active {
      background: rgba(198, 123, 92, 0.1);
    }
  }

  .m-session-info {
    flex: 1;
    overflow: hidden;
    min-width: 0;
  }

  .m-session-title {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: var(--van-text-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .m-session-time {
    display: block;
    font-size: 11px;
    color: var(--van-text-color-3);
    margin-top: 2px;
  }
}

/* ====== 底部弹出面板 ====== */
.m-panel {
  background: var(--van-background);
}

.m-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--van-border-color);
}

.m-panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--van-text-color);
}

.m-panel-body {
  padding: 8px 0;
  max-height: 40vh;
  overflow-y: auto;
}

.m-panel-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;

  &:active {
    background: rgba(198, 123, 92, 0.06);
  }

  &.active {
    background: rgba(198, 123, 92, 0.1);
  }
}

.m-kb-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.m-kb-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--van-text-color);
}

.m-kb-count {
  font-size: 12px;
  color: var(--van-text-color-3);
}

.m-kb-clear {
  color: #ef4444;
  gap: 8px;
}
</style>
