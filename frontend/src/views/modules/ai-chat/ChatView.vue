<template>
  <div class="chat-app">
    <!-- 移动端汉堡菜单按钮 -->
    <button v-if="isMobile" class="mobile-menu-btn" @click="showMobileSidebar = true">
      <el-icon :size="20"><ChatDotRound /></el-icon>
    </button>

    <!-- 移动端侧边栏抽屉 -->
    <el-drawer
      v-model="showMobileSidebar"
      direction="ltr"
      :size="280"
      :with-header="false"
      class="mobile-sidebar-drawer"
    >
      <div class="mobile-sidebar-content">
        <div class="sidebar-header">
          <div class="logo-area">
            <div class="logo-icon">
              <el-icon :size="18" color="#fff"><ChatDotRound /></el-icon>
            </div>
            <span class="logo-title">AI 聊天室</span>
          </div>
          <el-button type="primary" size="small" @click="handleNewSession; showMobileSidebar = false" class="btn-new-chat">
            <el-icon :size="14"><Plus /></el-icon>
            <span>新对话</span>
          </el-button>
        </div>

        <div class="search-wrapper">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索会话..."
            size="small"
            prefix-icon="Search"
            class="search-input"
            clearable
          />
        </div>

        <nav class="session-nav">
          <div
            v-for="session in filteredSessions"
            :key="session.id"
            :class="['session-item', { active: store.currentSession?.id === session.id }]"
            @click="handleSelectSession(session); showMobileSidebar = false"
          >
            <div class="session-icon">
              <el-icon :size="14" :color="store.currentSession?.id === session.id ? '#C67B5C' : '#8B7355'"><ChatDotRound /></el-icon>
            </div>
            <div class="session-info">
              <span class="session-title">{{ store.getSessionTitle(session) }}</span>
              <span class="session-time">{{ formatTime(session.created_at) }}</span>
            </div>
            <div class="session-delete" @click.stop>
              <el-button text size="small" type="danger" @click="handleDeleteSession(session.id)" circle>
                <el-icon :size="12"><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <div v-if="store.sessions.length === 0" class="empty-state">
            <div class="empty-icon">
              <el-icon :size="40" color="#D4A574"><ChatDotRound /></el-icon>
            </div>
            <p class="empty-title">暂无对话</p>
            <p class="empty-desc">点击右上角开始新对话</p>
          </div>
        </nav>
      </div>
    </el-drawer>

    <div class="chat-container">
      <aside v-if="!isMobile" class="chat-sidebar">
        <div class="sidebar-header">
          <div class="logo-area">
            <div class="logo-icon">
              <el-icon :size="18" color="#fff"><ChatDotRound /></el-icon>
            </div>
            <span class="logo-title">AI 聊天室</span>
          </div>
          <el-button type="primary" size="small" @click="handleNewSession" class="btn-new-chat">
            <el-icon :size="14"><Plus /></el-icon>
            <span>新对话</span>
          </el-button>
        </div>

        <div class="search-wrapper">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索会话..."
            size="small"
            prefix-icon="Search"
            class="search-input"
            clearable
          />
        </div>

        <nav class="session-nav">
          <div
            v-for="session in filteredSessions"
            :key="session.id"
            :class="['session-item', { active: store.currentSession?.id === session.id }]"
            @click="handleSelectSession(session)"
          >
            <div class="session-icon">
              <el-icon :size="14" :color="store.currentSession?.id === session.id ? '#C67B5C' : '#8B7355'"><ChatDotRound /></el-icon>
            </div>
            <div class="session-info">
              <span class="session-title">{{ store.getSessionTitle(session) }}</span>
              <span class="session-time">{{ formatTime(session.created_at) }}</span>
            </div>
            <div class="session-delete" @click.stop>
              <el-button text size="small" type="danger" @click="handleDeleteSession(session.id)" circle>
                <el-icon :size="12"><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <div v-if="store.sessions.length === 0" class="empty-state">
            <div class="empty-icon">
              <el-icon :size="40" color="#D4A574"><ChatDotRound /></el-icon>
            </div>
            <p class="empty-title">暂无对话</p>
            <p class="empty-desc">点击右上角开始新对话</p>
          </div>
        </nav>
      </aside>

      <main class="chat-main">
        <div v-if="!store.currentSession" class="welcome-screen">
          <div class="welcome-content">
            <div class="welcome-illustration">
              <div class="illustration-circle">
                <el-icon :size="64" color="#C67B5C"><ChatDotRound /></el-icon>
              </div>
              <div class="ring ring-1"></div>
              <div class="ring ring-2"></div>
            </div>
            <h2 class="welcome-title">欢迎使用 AI 聊天室</h2>
            <p class="welcome-desc">与智能助手对话，获取专业帮助</p>
            <div class="quick-prompts">
              <div class="prompt-chip" @click="fillPrompt('帮我设计一套登录功能的测试用例')">
                <div class="chip-icon" style="background: rgba(198, 123, 92, 0.15);">
                  <el-icon :size="14" color="#C67B5C"><Edit /></el-icon>
                </div>
                <span>设计测试用例</span>
              </div>
              <div class="prompt-chip" @click="fillPrompt('解释一下什么是RESTful API')">
                <div class="chip-icon" style="background: rgba(16, 185, 129, 0.15);">
                  <el-icon :size="14" color="#10b981"><InfoFilled /></el-icon>
                </div>
                <span>技术问答</span>
              </div>
              <div class="prompt-chip" @click="fillPrompt('帮我优化这段代码')">
                <div class="chip-icon" style="background: rgba(59, 130, 246, 0.15);">
                  <el-icon :size="14" color="#3b82f6"><Setting /></el-icon>
                </div>
                <span>代码优化</span>
              </div>
              <div class="prompt-chip" @click="fillPrompt('生成API接口文档')">
                <div class="chip-icon" style="background: rgba(245, 158, 11, 0.15);">
                  <el-icon :size="14" color="#f59e0b"><Document /></el-icon>
                </div>
                <span>文档生成</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="chat-content">
          <header class="chat-header">
            <div class="header-left">
              <div class="header-title">{{ store.currentSession.name }}</div>
              <el-tag v-if="store.currentSession.knowledge_base_name" size="small" type="warning" class="kb-badge">
                <el-icon :size="12"><FolderOpened /></el-icon>
                {{ store.currentSession.knowledge_base_name }}
              </el-tag>
            </div>
            <div class="header-right">
              <el-button text size="small" @click="handleNewSession" class="btn-header">
                <el-icon :size="14"><Plus /></el-icon>
                新对话
              </el-button>
            </div>
          </header>

          <div ref="messageContainer" class="message-list">
            <div
              v-for="message in store.messages"
              :key="message.id"
              :class="['message-block', message.role === 'user' ? 'is-user' : 'is-ai']"
            >
              <div class="avatar-wrapper">
                <div :class="['avatar', message.role === 'user' ? 'avatar-user' : 'avatar-ai']">
                  <el-icon :size="16" :color="message.role === 'user' ? '#3b82f6' : '#C67B5C'"><User /></el-icon>
                </div>
              </div>
              <div :class="['bubble', message.role === 'user' ? 'bubble-user' : 'bubble-ai']">
                <div v-if="message.role === 'assistant'" class="bubble-header">
                  <span class="bubble-name">AI 助手</span>
                  <span class="bubble-time">{{ formatTime(message.created_at) }}</span>
                </div>
                <div v-if="message.role === 'assistant'" class="bubble-content markdown-content" v-html="renderMarkdown(message.content)"></div>
              <div v-else class="bubble-content">{{ message.content }}</div>
                <div v-if="message.role === 'user'" class="bubble-footer">
                  <span class="bubble-time">{{ formatTime(message.created_at) }}</span>
                </div>
                <div v-if="message.files.length > 0" class="bubble-files">
                  <div v-for="file in message.files" :key="file.id" class="file-tag">
                    <el-icon v-if="file.is_image" :size="12"><Picture /></el-icon>
                    <el-icon v-else :size="12"><Document /></el-icon>
                    <span>{{ file.file_name }}</span>
                  </div>
                </div>
                <div v-if="message.role === 'assistant'" class="bubble-actions">
                  <el-button text size="small" :type="message.rating === 'up' ? 'primary' : 'default'" @click="handleRate(message.id, 'up')">
                    <el-icon :size="12"><Check /></el-icon>
                    <span>有用</span>
                  </el-button>
                  <el-button text size="small" :type="message.rating === 'down' ? 'danger' : 'default'" @click="handleRate(message.id, 'down')">
                    <el-icon :size="12"><Close /></el-icon>
                    <span>无用</span>
                  </el-button>
                  <el-button text size="small" @click="handleCopy(message.content)">
                    <el-icon :size="12"><CopyDocument /></el-icon>
                    <span>复制</span>
                  </el-button>
                </div>
              </div>
            </div>

            <div v-if="store.isStreaming" class="message-block is-ai">
              <div class="avatar-wrapper">
                <div class="avatar avatar-ai">
                  <el-icon :size="16" color="#C67B5C"><User /></el-icon>
                </div>
              </div>
              <div class="bubble bubble-ai">
                <div class="bubble-header">
                  <span class="bubble-name">AI 助手</span>
                  <span class="bubble-time">正在回复...</span>
                </div>
                <div class="typing-indicator">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="typing-text">AI 正在思考中</span>
                </div>
              </div>
            </div>
          </div>

          <footer class="chat-footer">
            <div v-if="uploadedFiles.length > 0" class="upload-preview">
              <div v-for="(file, index) in uploadedFiles" :key="index" class="upload-item">
                <el-icon v-if="isImage(file.name)" :size="12"><Picture /></el-icon>
                <el-icon v-else :size="12"><Document /></el-icon>
                <span class="file-name">{{ file.name }}</span>
                <el-button text size="small" type="danger" @click="removeUploadedFile(index)" circle>
                  <el-icon :size="10"><Close /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="input-area">
              <div class="input-tools">
                <el-button text size="small" @click="triggerFileUpload" class="tool-btn" title="上传附件">
                  <el-icon :size="16"><Paperclip /></el-icon>
                </el-button>
                <el-button text size="small" @click="triggerImageUpload" class="tool-btn" title="上传图片">
                  <el-icon :size="16"><Picture /></el-icon>
                </el-button>
                <input ref="fileInput" type="file" multiple class="hidden-input" @change="handleFileSelect" accept=".docx,.doc,.xmind,.md,.xlsx,.xls,.csv,.txt,.htm,.html,.pdf,.xml" />
                <input ref="imageInput" type="file" multiple class="hidden-input" @change="handleImageSelect" accept="image/*" />
              </div>
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="2"
                placeholder="输入消息，按 Ctrl/Cmd + Enter 发送..."
                :autosize="{ minRows: 2, maxRows: 6 }"
                :disabled="store.isStreaming"
                @keydown.enter.meta="handleSend"
                @keydown.enter.ctrl="handleSend"
                class="message-input"
              />
              <el-button
                type="primary"
                :loading="store.isStreaming"
                @click="handleSend"
                :disabled="!inputMessage.trim() && uploadedFiles.length === 0"
                class="btn-send"
              >
                <el-icon :size="16"><Edit /></el-icon>
              </el-button>
            </div>
          </footer>
        </div>
      </main>

      <aside class="chat-sidebar-right">
        <div class="panel-section">
          <div class="panel-header">
            <el-icon :size="14" color="#C67B5C"><Setting /></el-icon>
            <span class="panel-title">模型设置</span>
          </div>
          <div class="panel-body">
            <el-select v-model="store.selectedModel" placeholder="选择模型" size="small" style="width: 100%" @change="handleModelChange">
              <el-option v-for="item in store.modelOptions" :key="item.value" :label="item?.label || ''" :value="item.value" />
            </el-select>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-header">
            <el-icon :size="14" color="#C67B5C"><FolderOpened /></el-icon>
            <span class="panel-title">关联知识库</span>
          </div>
          <div class="panel-body">
            <div class="kb-list">
              <div
                v-for="kb in store.knowledgeBases"
                :key="kb.id"
                :class="['kb-item', { active: store.selectedKnowledgeBaseId === kb.id }]"
                @click="handleKBSelect(kb.id)"
              >
                <el-checkbox :checked="store.selectedKnowledgeBaseId === kb.id" @change.stop="handleKBSelect(kb.id)" />
                <div class="kb-info">
                  <span class="kb-name">{{ kb.name }}</span>
                  <span class="kb-count">{{ kb.document_count }} 文档</span>
                </div>
              </div>
              <div v-if="store.knowledgeBases.length === 0" class="empty-kb">
                <span>暂无知识库</span>
                <el-button text size="small" type="primary" @click="showCreateKBDialog = true" class="btn-create-kb">
                  <el-icon :size="12"><Plus /></el-icon>
                  创建
                </el-button>
              </div>
            </div>
          </div>
          <div class="panel-footer">
            <el-button text size="small" style="width: 100%" @click="showKBUploadDialog = true" class="btn-upload-kb">
              <el-icon :size="12"><Upload /></el-icon>
              上传知识库
            </el-button>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-header">
            <el-icon :size="14" color="#C67B5C"><InfoFilled /></el-icon>
            <span class="panel-title">快捷指令</span>
          </div>
          <div class="panel-body">
            <div class="command-grid">
              <div class="command-item" @click="fillPrompt('帮我分析这段代码的潜在问题')">
                <el-icon :size="14" color="#C67B5C"><Search /></el-icon>
                <span>代码分析</span>
              </div>
              <div class="command-item" @click="fillPrompt('生成单元测试用例')">
                <el-icon :size="14" color="#10b981"><CircleCheck /></el-icon>
                <span>测试用例</span>
              </div>
              <div class="command-item" @click="fillPrompt('解释技术概念')">
                <el-icon :size="14" color="#3b82f6"><FolderOpened /></el-icon>
                <span>技术解释</span>
              </div>
              <div class="command-item" @click="fillPrompt('优化SQL查询')">
                <el-icon :size="14" color="#f59e0b"><Document /></el-icon>
                <span>性能优化</span>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-header">
            <el-icon :size="14" color="#C67B5C"><Document /></el-icon>
            <span class="panel-title">使用提示</span>
          </div>
          <div class="panel-body">
            <ul class="tips-list">
              <li>支持上传文档和图片</li>
              <li>可关联知识库进行问答</li>
              <li>支持 Markdown 格式输出</li>
              <li>Ctrl/Cmd + Enter 发送消息</li>
            </ul>
          </div>
        </div>
      </aside>
    </div>

    <el-dialog v-model="showKBUploadDialog" title="上传文档到知识库" width="520px" class="custom-dialog">
      <el-form :model="kbUploadForm" class="dialog-form">
        <el-form-item label="选择知识库" required>
          <el-select v-model="kbUploadForm.kbId" placeholder="请选择知识库" style="width: 100%" class="form-select">
            <el-option v-for="kb in store.knowledgeBases" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
            ref="kbUploadRef"
            :auto-upload="false"
            :on-change="handleKBFileSelect"
            :on-remove="handleKBFileRemove"
            :file-list="kbUploadFiles"
            multiple
            accept=".docx,.doc,.xmind,.md,.xlsx,.xls,.csv,.txt,.htm,.html,.pdf,.xml"
            drag
            class="upload-area"
          >
            <el-icon :size="40" color="#C67B5C"><UploadFilled /></el-icon>
            <div class="upload-text">拖拽文件到此处，或点击上传</div>
            <div class="upload-tip">支持 docx、doc、xmind、md、xlsx、xls、csv、txt、htm、html、pdf、xml</div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showKBUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleKBUpload" :loading="isUploading">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreateKBDialog" title="新建知识库" width="520px" class="custom-dialog">
      <el-form :model="createKBForm" class="dialog-form">
        <el-form-item label="知识库名称" required>
          <el-input v-model="createKBForm.name" placeholder="请输入知识库名称" class="form-input" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createKBForm.description" type="textarea" :rows="3" placeholder="请输入知识库描述" class="form-input" />
        </el-form-item>
        <el-form-item label="上传文档（可选）">
          <el-upload
            ref="createKBUploadRef"
            :auto-upload="false"
            :on-change="handleCreateKBFileSelect"
            :on-remove="handleCreateKBFileRemove"
            :file-list="createKBFiles"
            multiple
            accept=".docx,.doc,.xmind,.md,.xlsx,.xls,.csv,.txt,.htm,.html,.pdf,.xml"
            drag
            class="upload-area"
          >
            <el-icon :size="40" color="#C67B5C"><UploadFilled /></el-icon>
            <div class="upload-text">拖拽文件到此处，或点击上传</div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateKBDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateKB" :loading="isCreating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import {
  ChatDotRound,
  User,
  Paperclip,
  Picture,
  Document,
  CopyDocument,
  Delete,
  Setting,
  FolderOpened,
  Upload,
  Plus,
  Edit,
  Search,
  CircleCheck,
  Close,
  UploadFilled,
  Check,
  InfoFilled,
} from '@element-plus/icons-vue'
import { useChatStore } from '../../../stores/ai_chat/chat'
import type { ChatSession } from '../../../types/ai_chat'

const store = useChatStore()

const isMobile = ref(false)
const showMobileSidebar = ref(false)
const inputMessage = ref('')
const uploadedFiles = ref<File[]>([])
const uploadedFileIds = ref<number[]>([])
const messageContainer = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const searchKeyword = ref('')

const showKBUploadDialog = ref(false)
const showCreateKBDialog = ref(false)
const kbUploadForm = ref({ kbId: 0 })
const kbUploadFiles = ref<any[]>([])
const createKBForm = ref({ name: '', description: '' })
const createKBFiles = ref<any[]>([])
const isUploading = ref(false)
const isCreating = ref(false)

const filteredSessions = computed(() => {
  if (!searchKeyword.value) return store.sessions
  const keyword = searchKeyword.value.toLowerCase()
  return store.sessions.filter((s) => s.name.toLowerCase().includes(keyword))
})

function isImage(fileName: string): boolean {
  return /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(fileName)
}

async function handleNewSession() {
  await store.createSession()
}

async function handleSelectSession(session: ChatSession) {
  await store.selectSession(session)
}

async function handleDeleteSession(id: number) {
  try {
    await ElMessageBox.confirm(
      '确定删除这个会话吗？此操作不可恢复。',
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await store.deleteSession(id)
    ElMessage.success('会话已删除')
  } catch {
    // 用户取消删除
  }
}

async function handleModelChange() {
  if (store.currentSession) {
    await store.updateSession(store.currentSession.id, { model: store.selectedModel })
  }
}

async function handleKBSelect(kbId: number) {
  if (store.selectedKnowledgeBaseId === kbId) {
    store.selectedKnowledgeBaseId = null
  } else {
    store.selectedKnowledgeBaseId = kbId
  }
  if (store.currentSession) {
    await store.updateSession(store.currentSession.id, { knowledge_base_id: store.selectedKnowledgeBaseId ?? undefined })
  }
}

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
    const result = await store.uploadFile(file)
    uploadedFileIds.value.push(result.id)
  }
  target.value = ''
}

async function handleImageSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  for (const file of files) {
    uploadedFiles.value.push(file)
    const result = await store.uploadFile(file)
    uploadedFileIds.value.push(result.id)
  }
  target.value = ''
}

function removeUploadedFile(index: number) {
  uploadedFiles.value.splice(index, 1)
  uploadedFileIds.value.splice(index, 1)
}

function fillPrompt(text: string) {
  inputMessage.value = text
}

async function handleSend() {
  if (!inputMessage.value.trim() && uploadedFiles.value.length === 0) {
    ElMessage.warning('请输入消息或选择文件')
    return
  }

  store.isStreaming = true
  const userMessageContent = inputMessage.value.trim()
  const sendFileIds = [...uploadedFileIds.value]
  const userMessage = {
    id: Date.now(),
    session_id: store.currentSession!.id,
    role: 'user' as const,
    content: userMessageContent,
    files: sendFileIds.map(id => ({ id, file_name: '', file_size: 0, file_type: '', is_image: false })),
    created_at: new Date().toISOString(),
  }
  store.addMessage(userMessage)
  await nextTick()
  scrollToBottom()
  inputMessage.value = ''
  uploadedFiles.value = []
  uploadedFileIds.value = []

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
          const content = line.substring(6)
          if (content === '[DONE]') {
            store.isStreaming = false
            await nextTick()
            scrollToBottom()
            continue
          }
          const json = JSON.parse(content)
          if (json.type === 'token') {
            assistantContent += json.content
            if (assistantMessageId === 0) {
              const newMessage = {
                id: Date.now(),
                session_id: store.currentSession!.id,
                role: 'assistant' as const,
                content: assistantContent,
                files: [],
                created_at: new Date().toISOString(),
              }
              store.addMessage(newMessage)
              assistantMessageId = newMessage.id
            } else {
              store.updateMessageContent(assistantMessageId, assistantContent)
            }
            await nextTick()
            scrollToBottom()
          } else if (json.type === 'complete') {
            if (assistantMessageId !== 0) {
              store.updateMessageContent(assistantMessageId, json.content)
            }
            store.isStreaming = false
            await nextTick()
            scrollToBottom()
          } else if (json.type === 'error') {
            ElMessage.error(json.message)
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
      ElMessage.error('发送失败: ' + error.message)
    }
    store.isStreaming = false
  }

  store.sendMessage(
      userMessageContent,
      sendFileIds,
      onChunk,
      onError
    )
}

async function handleRate(messageId: number, rating: string) {
  await store.rateMessage(messageId, rating)
}

async function handleCopy(content: string) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制')
  } catch {
    // 降级方案：clipboard API 不可用时使用 textarea
    const textarea = document.createElement('textarea')
    textarea.value = content
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制')
  }
}

function handleKBFileSelect(file: any) {
  kbUploadFiles.value.push(file)
}

function handleKBFileRemove(file: any) {
  const index = kbUploadFiles.value.findIndex((f) => f.name === file.name)
  if (index !== -1) {
    kbUploadFiles.value.splice(index, 1)
  }
}

async function handleKBUpload() {
  if (!kbUploadForm.value.kbId) {
    ElMessage.warning('请选择知识库')
    return
  }
  if (kbUploadFiles.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }
  isUploading.value = true
  const files = kbUploadFiles.value.map((f) => f.raw)
  await store.uploadToKnowledgeBase(kbUploadForm.value.kbId, files)
  await store.loadKnowledgeBases()
  showKBUploadDialog.value = false
  kbUploadFiles.value = []
  isUploading.value = false
  ElMessage.success('上传成功')
}

function handleCreateKBFileSelect(file: any) {
  createKBFiles.value.push(file)
}

function handleCreateKBFileRemove(file: any) {
  const index = createKBFiles.value.findIndex((f) => f.name === file.name)
  if (index !== -1) {
    createKBFiles.value.splice(index, 1)
  }
}

async function handleCreateKB() {
  if (!createKBForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  isCreating.value = true
  const kb = await store.createKnowledgeBase(createKBForm.value.name, createKBForm.value.description)
  if (createKBFiles.value.length > 0) {
    const files = createKBFiles.value.map((f) => f.raw)
    await store.uploadToKnowledgeBase(kb.id, files)
    await store.loadKnowledgeBases()
  }
  showCreateKBDialog.value = false
  createKBForm.value = { name: '', description: '' }
  createKBFiles.value = []
  isCreating.value = false
  ElMessage.success('创建成功')
}

function scrollToBottom() {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

import { formatTime as _formatTime } from '@/utils'
function formatTime(time?: string): string {
  return _formatTime(time)
}

function renderMarkdown(content: string): string {
  const html = marked.parse(content) as string
  // 使用 DOMPurify 清理 HTML，防止 XSS 攻击
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre', 'blockquote',
      'ul', 'ol', 'li', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'div', 'span',
    ],
    ALLOWED_ATTR: [
      'href', 'target', 'rel', 'src', 'alt', 'title', 'class', 'id',
    ],
  })
}

onMounted(async () => {
  // 检测移动端
  const checkMobile = () => {
    isMobile.value = window.innerWidth < 768
  }
  checkMobile()
  window.addEventListener('resize', checkMobile)

  try {
    await store.loadSessions()
  } catch (error) {
    console.error('加载会话失败:', error)
    ElMessage.warning('加载会话失败，请稍后重试')
  }
  try {
    await store.loadKnowledgeBases()
  } catch (error) {
    console.error('加载知识库失败:', error)
    ElMessage.warning('加载知识库失败，请稍后重试')
  }
})

onUnmounted(() => {
  store.abortCurrentRequest()
  window.removeEventListener('resize', () => {})
})
</script>

<style scoped>
.chat-app {
  height: 100%;
  background: var(--bg);
}

.chat-container {
  display: flex;
  height: calc(100vh - var(--topbar-height, 64px) - 48px);
}

.chat-sidebar {
  width: 260px;
  background: var(--card-bg);
  border-right: var(--border);
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 20px rgba(180, 150, 120, 0.04);
}

.sidebar-header {
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: var(--border);
  background: linear-gradient(180deg, #FFFDF9 0%, #FDF8F0 100%);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(198, 123, 92, 0.3);
}

.logo-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}

.btn-new-chat {
  border-radius: 10px;
  font-size: 12px;
  padding: 6px 14px;
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(198, 123, 92, 0.25);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-new-chat:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(198, 123, 92, 0.35);
}

.search-wrapper {
  padding: 14px 16px;
  border-bottom: var(--border);
}

.search-input .el-input__wrapper {
  border-radius: 10px;
  background: rgba(198, 123, 92, 0.04);
  border-color: rgba(198, 123, 92, 0.08);
  box-shadow: none;
}

.search-input .el-input__wrapper:hover {
  background: rgba(198, 123, 92, 0.06);
}

.search-input .el-input__wrapper.is-focus {
  background: var(--card-bg);
  border-color: rgba(198, 123, 92, 0.2);
  box-shadow: 0 0 0 3px rgba(198, 123, 92, 0.06);
}

.session-nav {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.session-item:hover {
  background: rgba(198, 123, 92, 0.05);
  transform: translateX(2px);
}

.session-item.active {
  background: linear-gradient(135deg, rgba(198, 123, 92, 0.12) 0%, rgba(212, 165, 116, 0.08) 100%);
  box-shadow: 0 2px 8px rgba(198, 123, 92, 0.1);
}

.session-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 24px;
  background: linear-gradient(180deg, #C67B5C 0%, #D4A574 100%);
  border-radius: 0 3px 3px 0;
}

.session-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: rgba(198, 123, 92, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.25s;
}

.session-item.active .session-icon {
  background: rgba(198, 123, 92, 0.18);
}

.session-info {
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

.session-title {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-time {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 3px;
}

.session-delete {
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-delete {
  opacity: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(212, 165, 116, 0.15) 0%, rgba(198, 123, 92, 0.08) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  animation: float-icon 3s ease-in-out infinite;
}

@keyframes float-icon {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 6px 0;
}

.empty-desc {
  font-size: 12px;
  margin: 0;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  min-height: 0;
  overflow: hidden;
}

.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.welcome-content {
  text-align: center;
}

.welcome-illustration {
  position: relative;
  margin-bottom: 32px;
}

.illustration-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(198, 123, 92, 0.1) 0%, rgba(212, 165, 116, 0.06) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 2px solid rgba(198, 123, 92, 0.12);
}

.ring-1 {
  width: 144px;
  height: 144px;
  animation: ring-pulse 2.5s ease-in-out infinite;
}

.ring-2 {
  width: 170px;
  height: 170px;
  animation: ring-pulse 2.5s ease-in-out infinite 0.8s;
}

@keyframes ring-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
  50% { transform: translate(-50%, -50%) scale(1.08); opacity: 0.2; }
}

.welcome-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 12px 0;
  letter-spacing: -0.02em;
}

.welcome-desc {
  font-size: 15px;
  color: var(--text-muted);
  margin: 0 0 32px 0;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.prompt-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: var(--card-bg);
  border-radius: 24px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  border: 1px solid rgba(198, 123, 92, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(180, 150, 120, 0.04);
}

.prompt-chip:hover {
  background: rgba(198, 123, 92, 0.05);
  border-color: rgba(198, 123, 92, 0.15);
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(198, 123, 92, 0.1);
}

.chip-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.chat-header {
  padding: 16px 28px;
  background: var(--card-bg);
  border-bottom: var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(180, 150, 120, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.kb-badge {
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

.btn-header {
  padding: 6px 14px;
  border-radius: 8px;
  color: var(--text-secondary);
  transition: all 0.25s;
}

.btn-header:hover {
  background: rgba(198, 123, 92, 0.06);
  color: #C67B5C;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
}

.message-block {
  display: flex;
  gap: 14px;
  margin-bottom: 24px;
  animation: fade-slide-in 0.3s ease-out;
}

@keyframes fade-slide-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-block.is-user {
  flex-direction: row-reverse;
}

.avatar-wrapper {
  flex-shrink: 0;
}

.avatar {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s;
}

.avatar-ai {
  background: linear-gradient(135deg, rgba(198, 123, 92, 0.12) 0%, rgba(212, 165, 116, 0.08) 100%);
}

.avatar-user {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(96, 165, 250, 0.08) 100%);
}

.bubble {
  max-width: 65%;
  padding: 16px 20px;
  border-radius: 20px;
  position: relative;
}

.bubble-ai {
  background: var(--card-bg);
  border: 1px solid rgba(198, 123, 92, 0.06);
  border-radius: 20px 20px 20px 8px;
  box-shadow: 0 4px 16px rgba(180, 150, 120, 0.06);
}

.bubble-user {
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 100%);
  color: #fff;
  border-radius: 20px 20px 8px 20px;
  box-shadow: 0 6px 20px rgba(198, 123, 92, 0.3);
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.bubble-name {
  font-size: 13px;
  font-weight: 600;
  color: #C67B5C;
}

.bubble-time {
  font-size: 11px;
  color: var(--text-muted);
}

.bubble-user .bubble-time {
  color: rgba(255, 255, 255, 0.6);
}

.bubble-content {
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-content {
  font-size: 14px;
  line-height: 1.8;
  word-break: break-word;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
  line-height: 1.4;
}

.markdown-content h1 {
  font-size: 20px;
  border-bottom: 1px solid rgba(180, 150, 120, 0.1);
  padding-bottom: 8px;
}

.markdown-content h2 {
  font-size: 18px;
  border-bottom: 1px solid rgba(180, 150, 120, 0.08);
  padding-bottom: 6px;
}

.markdown-content h3 {
  font-size: 16px;
}

.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  font-size: 14px;
}

.markdown-content p {
  margin: 8px 0;
}

.markdown-content ul,
.markdown-content ol {
  padding-left: 24px;
  margin: 8px 0;
}

.markdown-content ul {
  list-style-type: disc;
}

.markdown-content ol {
  list-style-type: decimal;
}

.markdown-content li {
  margin: 4px 0;
}

.markdown-content blockquote {
  border-left: 3px solid #C67B5C;
  padding-left: 12px;
  margin: 12px 0;
  color: var(--text-muted);
  background: rgba(198, 123, 92, 0.04);
  padding: 10px 16px;
  border-radius: 0 8px 8px 0;
}

.markdown-content code {
  background: rgba(198, 123, 92, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #C67B5C;
}

.markdown-content pre {
  background: rgba(0, 0, 0, 0.03);
  padding: 16px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid rgba(180, 150, 120, 0.06);
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: var(--text);
}

.markdown-content a {
  color: #C67B5C;
  text-decoration: underline;
}

.markdown-content a:hover {
  color: #D49472;
}

.markdown-content hr {
  border: none;
  border-top: 1px solid rgba(180, 150, 120, 0.1);
  margin: 20px 0;
}

.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid rgba(180, 150, 120, 0.1);
  padding: 8px 12px;
  text-align: left;
}

.markdown-content th {
  background: rgba(198, 123, 92, 0.06);
  font-weight: 600;
}

.markdown-content img {
  max-width: 100%;
  border-radius: 8px;
  margin: 8px 0;
}

.markdown-content strong {
  font-weight: 600;
}

.markdown-content em {
  font-style: italic;
}

.bubble-footer {
  margin-top: 10px;
  text-align: right;
}

.bubble-files {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.file-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.bubble-user .file-tag {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
}

.bubble-actions {
  display: flex;
  gap: 16px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(180, 150, 120, 0.06);
  opacity: 0;
  transition: opacity 0.25s;
}

.bubble:hover .bubble-actions {
  opacity: 1;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
}

.dot {
  width: 8px;
  height: 8px;
  background: #C67B5C;
  border-radius: 50%;
  animation: typing-dot 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing-dot {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.typing-text {
  font-size: 13px;
  color: var(--text-muted);
}

.chat-footer {
  padding: 20px 28px;
  background: var(--card-bg);
  border-top: var(--border);
  box-shadow: 0 -2px 8px rgba(180, 150, 120, 0.04);
}

.upload-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.upload-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(198, 123, 92, 0.06);
  border-radius: 10px;
  font-size: 12px;
}

.upload-item .file-name {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
}

.input-area {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-tools {
  display: flex;
  gap: 6px;
}

.tool-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  color: var(--text-muted);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.tool-btn:hover {
  color: #C67B5C;
  background: rgba(198, 123, 92, 0.1);
  transform: translateY(-2px);
}

.hidden-input {
  display: none;
}

.message-input {
  flex: 1;
}

.message-input .el-textarea__inner {
  border-radius: 16px;
  border-color: rgba(198, 123, 92, 0.08);
  background: rgba(198, 123, 92, 0.02);
  padding: 14px 18px;
  font-size: 14px;
  resize: none;
  transition: all 0.25s;
}

.message-input .el-textarea__inner:focus {
  border-color: rgba(198, 123, 92, 0.25);
  background: var(--card-bg);
  box-shadow: 0 0 0 3px rgba(198, 123, 92, 0.06);
}

.btn-send {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 100%);
  border: none;
  box-shadow: 0 4px 14px rgba(198, 123, 92, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-send:not(:disabled):hover {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(198, 123, 92, 0.4);
}

.btn-send:disabled {
  opacity: 0.4;
  transform: none;
}

.chat-sidebar-right {
  width: 280px;
  background: var(--card-bg);
  border-left: var(--border);
  padding: 16px;
  overflow-y: auto;
  box-shadow: -4px 0 20px rgba(180, 150, 120, 0.04);
}

.panel-section {
  margin-bottom: 16px;
  padding: 16px;
  background: rgba(198, 123, 92, 0.02);
  border-radius: 16px;
  border: 1px solid rgba(198, 123, 92, 0.04);
  transition: all 0.25s;
}

.panel-section:hover {
  background: rgba(198, 123, 92, 0.03);
  border-color: rgba(198, 123, 92, 0.06);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.panel-body {
  font-size: 13px;
}

.panel-footer {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(198, 123, 92, 0.04);
}

.kb-list {
  max-height: 160px;
  overflow-y: auto;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 6px;
  transition: all 0.25s;
}

.kb-item:hover {
  background: rgba(198, 123, 92, 0.04);
}

.kb-item.active {
  background: rgba(198, 123, 92, 0.12);
  border: 1px solid rgba(198, 123, 92, 0.1);
}

.kb-info {
  flex: 1;
  overflow: hidden;
}

.kb-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-count {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
}

.empty-kb {
  padding: 16px;
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
}

.btn-create-kb {
  margin-top: 10px;
}

.btn-upload-kb {
  background: rgba(198, 123, 92, 0.06);
  color: #C67B5C;
  border-radius: 10px;
  padding: 8px;
  transition: all 0.25s;
}

.btn-upload-kb:hover {
  background: rgba(198, 123, 92, 0.12);
}

.command-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.command-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 10px;
  background: rgba(198, 123, 92, 0.03);
  border-radius: 12px;
  font-size: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.command-item:hover {
  background: rgba(198, 123, 92, 0.08);
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(198, 123, 92, 0.08);
}

.command-item span {
  color: var(--text-secondary);
}

.tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tips-list li {
  padding: 8px 0;
  font-size: 12px;
  color: var(--text-muted);
  position: relative;
  padding-left: 18px;
}

.tips-list li::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 11px;
  width: 5px;
  height: 5px;
  background: #C67B5C;
  border-radius: 50%;
}

.custom-dialog .el-dialog__header {
  border-bottom: var(--border);
  padding: 22px;
}

.custom-dialog .el-dialog__body {
  padding: 24px;
}

.custom-dialog .el-dialog__footer {
  border-top: var(--border);
  padding: 18px 22px;
}

.dialog-form .form-select,
.dialog-form .form-input {
  width: 100%;
}

.upload-area {
  margin-top: 10px;
}

.upload-area .el-upload-dragger {
  border-radius: 14px;
  border-color: rgba(198, 123, 92, 0.12);
}

.upload-area .el-upload-dragger:hover {
  border-color: #C67B5C;
  background: rgba(198, 123, 92, 0.02);
}

.upload-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.upload-tip {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}

.el-icon--upload {
  margin-bottom: 10px;
}

@media (max-width: 1200px) {
  .chat-sidebar {
    width: 240px;
  }
  .chat-sidebar-right {
    width: 260px;
  }
}

@media (max-width: 900px) {
  .chat-sidebar-right {
    display: none;
  }
}

@media (max-width: 768px) {
  .chat-sidebar {
    display: none;
  }
}

/* 移动端汉堡菜单按钮 */
.mobile-menu-btn {
  position: fixed;
  top: calc(var(--topbar-height, 64px) + 12px);
  left: 12px;
  z-index: 100;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--primary);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s;
}

.mobile-menu-btn:hover {
  transform: scale(1.05);
}

/* 移动端侧边栏抽屉内容 */
.mobile-sidebar-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
}

/* 移动端聊天区域需要留出汉堡菜单的空间 */
@media (max-width: 768px) {
  .chat-main {
    margin-left: 0 !important;
  }
}
</style>