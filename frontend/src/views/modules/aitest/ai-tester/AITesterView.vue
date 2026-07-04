<template>
  <div class="tester-page">
    <div class="tester-layout">
      <!-- 左栏：会话历史 -->
      <div class="sidebar-card">
        <div class="sidebar-header">
          <span class="sidebar-title">会话历史</span>
          <el-button text size="small" type="primary" style="font-size:12px" @click="handleClearHistory">
            清空
          </el-button>
        </div>
        <el-button class="new-chat-btn" type="primary" size="small" @click="handleNewChat">
          + 新建对话
        </el-button>
        <div class="session-list">
          <div
            v-for="session in store.sessions"
            :key="session.id"
            :class="['session-item', { active: store.currentSessionId === session.id }]"
            @click="store.selectSession(session.id)"
          >
            <div class="session-info">
              <span class="session-name">{{ getSessionTitle(session) }}</span>
              <span class="session-time">{{ formatTime(session.created_at) }}</span>
            </div>
            <div class="session-actions" @click.stop>
              <el-button text size="small" @click="handleRename(session)" title="重命名">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button text size="small" type="danger" @click="handleDeleteSession(session)" title="删除">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <div v-if="store.sessions.length === 0" class="session-empty">
            暂无历史会话
          </div>
        </div>
      </div>

      <!-- 右栏：聊天区 -->
      <div class="chat-area">
        <!-- 顶栏 -->
        <div class="chat-header">
          <div class="chat-header-inner">
            <span class="chat-title">{{ currentSession?.name || 'AI 评测师' }}</span>
            <el-select
              v-model="selectedModel"
              :options="modelOptions"
              size="small"
              style="width: 180px"
              placeholder="选择模型"
              filterable
            >
              <template #default="{ item }">
                <span>{{ item?.label || '' }}</span>
              </template>
            </el-select>
          </div>
        </div>

        <!-- 消息列表 -->
        <div ref="messageContainerRef" class="message-container">
          <div v-if="store.isLoading && store.messages.length === 0" class="message-empty">
            <el-icon class="is-loading" :size="24"><Loading /></el-icon>
            <p>加载中...</p>
          </div>

          <div
            v-for="(msg, idx) in store.messages"
            :key="idx"
            :class="['message-row', msg.role === 'user' ? 'message-row-user' : 'message-row-ai']"
          >
            <div v-if="msg.role === 'assistant'" class="avatar-col">
              <div class="avatar ai-avatar">AI</div>
            </div>
            <div :class="['message-bubble', msg.role === 'user' ? 'bubble-user' : 'bubble-ai']">
              <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
              <div v-if="msg.created_at" class="message-time">{{ formatTime(msg.created_at) }}</div>
              <!-- AI 消息操作按钮 -->
              <div v-if="msg.role === 'assistant' && msg.id" class="message-actions">
                <el-button text size="small" @click="handleCopy(msg.content)" title="复制">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
                <el-button
                  text size="small"
                  :type="(msg as any).rating === 'up' ? 'primary' : 'default'"
                  @click="handleRate(msg, 'up')"
                  title="有用"
                >
                  <el-icon><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M14 9h5.77a2 2 0 011.94 2.5l-1.5 6A2 2 0 0118.27 19H9V7l5-5a2 2 0 014 2v5zM3 9h3v10H3V9z"/></svg></el-icon>
                </el-button>
                <el-button
                  text size="small"
                  :type="(msg as any).rating === 'down' ? 'danger' : 'default'"
                  @click="handleRate(msg, 'down')"
                  title="无用"
                >
                  <el-icon><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M10 15H4.23a2 2 0 01-1.94-2.5l1.5-6A2 2 0 015.73 5H15v7l-5 5a2 2 0 01-4-2v-5zm11-6h-3v10h3V9z"/></svg></el-icon>
                </el-button>
              </div>
            </div>
            <div v-if="msg.role === 'user'" class="avatar-col">
              <div class="avatar user-avatar">我</div>
            </div>
          </div>

          <!-- 流式输出消息 -->
          <div v-if="isStreaming" class="message-row message-row-ai">
            <div class="avatar-col">
              <div class="avatar ai-avatar">AI</div>
            </div>
            <div class="message-bubble bubble-ai">
              <div class="message-text" v-html="renderMarkdown(streamContent || '思考中...')"></div>
              <span v-if="streamContent" class="streaming-cursor">▊</span>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="store.messages.length === 0 && !store.isSending && !isStreaming" class="message-empty">
            <div class="empty-icon">
              <el-icon :size="48"><MagicStick /></el-icon>
            </div>
            <p class="empty-title">开始一个新的测试对话吧</p>
            <div class="example-questions">
              <div class="example-item" @click="fillExample('请帮我评审以下测试用例：\n用例1：登录功能验证\n1. 输入正确用户名密码\n2. 点击登录按钮\n预期：成功跳转到首页')">
                评审测试用例
              </div>
              <div class="example-item" @click="fillExample('针对用户注册功能，帮我设计一套完整的测试用例，包括正常流程和异常场景。')">
                设计测试用例
              </div>
              <div class="example-item" @click="fillExample('API 接口测试中，如何验证接口的幂等性？请给出具体的测试方法。')">
                接口测试咨询
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="input-area">
          <div class="input-row">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              placeholder="输入您的问题..."
              :autosize="{ minRows: 2, maxRows: 6 }"
              @keydown.enter.prevent="handleSend"
            />
            <el-button
              circle
              type="primary"
              :disabled="!inputText.trim() || store.isSending"
              :loading="store.isSending"
              @click="handleSend"
              style="flex-shrink:0"
            >
              <el-icon><Promotion /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 重命名弹窗 -->
    <el-dialog v-model="showRenameModal" title="重命名会话" width="400px">
      <el-input v-model="renameText" placeholder="输入新名称" />
      <template #footer>
        <el-button @click="showRenameModal = false">取消</el-button>
        <el-button type="primary" @click="handleRenameConfirm">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Delete, CopyDocument, Promotion, MagicStick, Loading } from '@element-plus/icons-vue'
import { useAITesterStore } from '@/stores/aitest/ai_tester'
import { useMarkdownRenderer } from '@/composables/useMarkdownRenderer'
import { aitestApi } from '@/api/aitest'
import type { AITesterSession } from '@/types/aitest'

const store = useAITesterStore()

const inputText = ref('')
const selectedModel = ref('other:opencode/mimo-v2-pro-free')
const messageContainerRef = ref<HTMLElement | null>(null)
const showRenameModal = ref(false)
const renameText = ref('')
const renamingSessionId = ref<number | null>(null)
const isStreaming = ref(false)
const streamContent = ref('')
const abortController = ref<AbortController | null>(null)

const modelOptions = computed(() => {
  return [
    { label: 'OpenCode Mimo V2 Pro', value: 'other:opencode/mimo-v2-pro-free' },
    { label: 'Qwen3.7-Max', value: 'qwen:qwen3.7-max' },
    { label: 'DeepSeek V4 Flash', value: 'deepseek:deepseek-v4-flash' },
  ]
})

const { render: renderMarkdown } = useMarkdownRenderer()

const currentSession = computed(() =>
  store.sessions.find(s => s.id === store.currentSessionId)
)

import { formatTime as _formatTime } from '@/utils'

function formatTime(isoStr: string | null | undefined): string {
  if (!isoStr) return ''
  return _formatTime(isoStr)
}

function scrollToBottom() {
  nextTick(() => {
    const el = messageContainerRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch(() => store.messages.length, () => { scrollToBottom() })
watch(streamContent, () => { scrollToBottom() })

async function handleNewChat() {
  await store.createSession({ name: '新会话' })
  ElMessage.success('已创建新对话')
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value || store.isSending) return
  inputText.value = ''

  if (!store.currentSessionId) {
    try {
      await store.createSession({ name: '新会话' })
    } catch (e) {
      console.error('创建会话失败:', e)
      ElMessage.error('创建会话失败，请稍后重试')
      return
    }
  }

  const sid = store.currentSessionId!
  store.messages.push({ id: 0, session_id: sid, role: 'user', content: text, rating: null, created_at: new Date().toISOString() })

  isStreaming.value = true
  streamContent.value = ''
  
  try {
    const streamUrl = aitestApi.getTesterStreamUrl(sid)
    const token = localStorage.getItem('access_token') || ''

    abortController.value = new AbortController()

    const response = await fetch(streamUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ content: text, model: selectedModel.value }),
      signal: abortController.value.signal,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
    }

    if (!response.body) throw new Error('服务器返回空响应')
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'chunk' && data.content) {
              streamContent.value += data.content
            } else if (data.type === 'complete') {
              break
            } else if (data.type === 'error') {
              streamContent.value += `\n\n[错误: ${data.message || '未知错误'}]`
            } else if (data.type === 'done') {
              break
            }
          } catch (parseErr) {
            console.warn('解析SSE数据失败:', parseErr)
          }
        }
      }
    }
  } catch (e: any) {
    if (e.name === 'AbortError') {
      console.warn('请求已取消')
      return
    }
    console.error('流式输出错误:', e)
    const errorMsg = e?.message || '连接失败，请检查网络或稍后重试'
    streamContent.value += `\n\n[错误: ${errorMsg}]`
    ElMessage.error('消息发送失败: ' + errorMsg)
  } finally {
    isStreaming.value = false
    abortController.value = null
    if (store.currentSessionId) {
      try {
        await store.selectSession(store.currentSessionId)
        await store.fetchSessions()
      } catch (e) {
        console.error('刷新会话失败:', e)
      }
    }
  }
}

function handleRename(session: AITesterSession) {
  renamingSessionId.value = session.id
  renameText.value = session.name
  showRenameModal.value = true
}

async function handleRenameConfirm() {
  if (!renamingSessionId.value || !renameText.value.trim()) {
    showRenameModal.value = false
    return
  }
  try {
    await store.updateSession(renamingSessionId.value, { name: renameText.value.trim() })
    ElMessage.success('已重命名')
  } catch (e) {
    console.error('重命名失败:', e)
    ElMessage.error('重命名失败')
  }
  showRenameModal.value = false
}

async function handleDeleteSession(session: AITesterSession) {
  await store.deleteSession(session.id)
  ElMessage.success('会话已删除')
}

async function handleClearHistory() {
  const ids = store.sessions.map(s => s.id)
  if (ids.length === 0) return
  try {
    await store.batchDeleteSessions(ids)
    ElMessage.success(`已清空 ${ids.length} 个会话`)
  } catch (e) {
    console.error('清空会话失败:', e)
    ElMessage.error('清空失败')
  }
}

function getSessionTitle(session: AITesterSession): string {
  const firstMsg = session.first_message?.trim() || ''
  if (firstMsg.length > 0) {
    return firstMsg.length > 10 ? firstMsg.substring(0, 10) + '...' : firstMsg
  }
  return session.name
}

function fillExample(text: string) {
  inputText.value = text
}

async function handleCopy(content: string) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

async function handleRate(msg: any, rating: 'up' | 'down') {
  try {
    const newRating = msg.rating === rating ? null : rating
    await aitestApi.rateTesterMessage(msg.id, { rating: newRating as 'up' | 'down' | null })
    msg.rating = newRating
    ElMessage.success(newRating ? '已评价' : '已取消评价')
  } catch (e: any) {
    ElMessage.error('评价失败: ' + (e.message || '未知错误'))
  }
}

onMounted(async () => {
  store.fetchSessions()
})
</script>

<style scoped>
.tester-page { height: 100%; padding: 0; overflow: hidden; }
.tester-layout { display: flex; height: 100%; gap: 0; }

/* 左栏 */
.sidebar-card {
  width: 30%; min-width: 240px; max-width: 320px;
  border-right: 1px solid var(--border, rgba(180,150,120,0.12));
  display: flex; flex-direction: column;
  padding: 16px;
  background: var(--card-bg, #FFFDF9);
}
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.sidebar-title { font-size: 15px; font-weight: 600; color: var(--text, #3D2E1F); }
.new-chat-btn { margin-bottom: 12px; }
.session-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.session-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border-radius: 8px; cursor: pointer;
  transition: background 0.2s;
}
.session-item:hover { background: rgba(198,123,92,0.06); }
.session-item.active { background: rgba(198,123,92,0.1); }
.session-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.session-name { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-time { font-size: 11px; color: var(--text-muted, #8B7355); }
.session-actions { display: flex; gap: 2px; opacity: 0; transition: opacity 0.2s; }
.session-item:hover .session-actions { opacity: 1; }
.session-empty { text-align: center; color: var(--text-muted, #8B7355); font-size: 13px; padding: 32px 0; }

/* 右栏 */
.chat-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg, #FBF7F0); }
.chat-header {
  padding: 12px 20px; border-bottom: 1px solid var(--border, rgba(180,150,120,0.1));
  background: var(--card-bg, #FFFDF9);
}
.chat-header-inner { display: flex; align-items: center; justify-content: space-between; }
.chat-title { font-size: 16px; font-weight: 600; color: var(--text, #3D2E1F); }

/* 消息列表 */
.message-container { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }
.message-row { display: flex; gap: 10px; max-width: 75%; }
.message-row-user { align-self: flex-end; flex-direction: row-reverse; }
.message-row-ai { align-self: flex-start; }
.avatar-col { flex-shrink: 0; }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; }
.ai-avatar { background: var(--primary, #C67B5C); color: #fff; }
.user-avatar { background: #D4A574; color: #fff; }
.message-bubble { padding: 12px 16px; border-radius: 12px; position: relative; }
.bubble-ai { background: #F0EBE3; border-bottom-left-radius: 4px; min-width: 60px; }
.bubble-user { background: #EDE4D6; border-bottom-right-radius: 4px; }
.message-text { font-size: 14px; line-height: 1.7; color: var(--text, #3D2E1F); word-break: break-word; }
.message-text :deep(pre) { background: #1e1e1e; border-radius: 8px; padding: 12px 16px; overflow-x: auto; margin: 8px 0; }
.message-text :deep(code) { font-size: 13px; font-family: 'JetBrains Mono', 'Fira Code', monospace; }
.message-text :deep(p) { margin: 4px 0; }
.message-text :deep(ul), .message-text :deep(ol) { padding-left: 20px; margin: 4px 0; }
.message-text :deep(table) { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.message-text :deep(th), .message-text :deep(td) { border: 1px solid rgba(180,150,120,0.2); padding: 6px 10px; text-align: left; }
.message-text :deep(th) { background: rgba(198,123,92,0.08); font-weight: 600; }
.message-text :deep(blockquote) { border-left: 3px solid var(--primary, #C67B5C); margin: 8px 0; padding: 4px 12px; color: var(--text-secondary, #5C4A38); background: rgba(198,123,92,0.04); border-radius: 0 4px 4px 0; }
.streaming-cursor { display: inline-block; animation: blink 1s step-end infinite; font-size: 14px; color: var(--primary, #C67B5C); }
@keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }

.message-actions { display: flex; gap: 4px; margin-top: 6px; opacity: 0; transition: opacity 0.2s; }
.message-bubble:hover .message-actions { opacity: 1; }
.message-time { font-size: 11px; color: var(--text-muted, #8B7355); margin-top: 6px; text-align: right; }

.message-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-muted, #8B7355); }
.empty-icon { margin-bottom: 12px; }
.empty-title { font-size: 15px; margin-bottom: 16px; }
.example-questions { display: flex; flex-direction: column; gap: 8px; max-width: 360px; }
.example-item {
  padding: 10px 16px; border: 1px solid rgba(180,150,120,0.2); border-radius: 8px;
  font-size: 13px; color: var(--text-secondary, #5C4A38); cursor: pointer;
  transition: all 0.2s; text-align: left;
}
.example-item:hover { background: rgba(198,123,92,0.06); border-color: var(--primary, #C67B5C); color: var(--primary, #C67B5C); }

/* 输入区 */
.input-area { padding: 16px 20px; border-top: 1px solid var(--border, rgba(180,150,120,0.1)); background: var(--card-bg, #FFFDF9); }
.input-row { display: flex; gap: 12px; align-items: flex-end; }
.input-row .el-input { flex: 1; }

@media (max-width: 768px) {
  .tester-layout { flex-direction: column; }
  .sidebar-card { width: 100%; max-width: none; border-right: none; border-bottom: 1px solid var(--border); max-height: 200px; }
  .session-list { max-height: 120px; }
  .session-actions { opacity: 1; }
  .message-container { padding: 12px; }
  .message-row { max-width: 88%; }
}
</style>
