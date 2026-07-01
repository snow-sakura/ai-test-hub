<template>
  <div class="page-wrap">
    <h1 class="page-title">AI 用例生成</h1>

    <!-- 面板 1：需求输入 -->
    <el-collapse v-model="activePanels" class="panel-collapse">
      <el-collapse-item title="📄 需求输入" name="input">
        <el-card shadow="never" class="input-card">
          <div class="input-grid">
            <!-- 左侧：手动输入 -->
            <div class="input-col">
              <h4 class="col-title">手动输入需求</h4>
              <el-input
                v-model="requirementText"
                type="textarea"
                :rows="10"
                placeholder="请输入测试需求描述，例如：&#10;&#10;针对用户登录功能设计测试用例&#10;1. 支持用户名/密码登录&#10;2. 支持验证码登录&#10;3. 登录失败有错误提示"
                :disabled="isGenerating"
              />
            </div>
            <!-- 右侧：文档上传 -->
            <div class="input-col">
              <h4 class="col-title">上传文档</h4>
              <div
                class="upload-zone"
                :class="{ 'is-dragover': dragOver }"
                @dragover.prevent="dragOver = true"
                @dragleave="dragOver = false"
                @drop.prevent="handleDrop"
              >
                <template v-if="!uploadedFile">
                  <el-icon :size="36" color="#C67B5C"><Upload /></el-icon>
                  <p class="upload-text">拖拽文件到此处，或点击上传</p>
                  <p class="upload-hint">支持 PDF、Word、TXT、MD 格式</p>
                  <el-button size="small" @click="triggerFileInput">选择文件</el-button>
                  <input ref="fileInputRef" type="file" accept=".pdf,.doc,.docx,.txt,.md" style="display:none" @change="handleFileSelect" />
                </template>
                <template v-else>
                  <el-icon :size="36" color="#10b981"><Document /></el-icon>
                  <p class="upload-text">{{ uploadedFile.name }}</p>
                  <p class="upload-hint">{{ (uploadedFile.size / 1024).toFixed(1) }} KB · 已解析</p>
                  <el-button size="small" text @click="uploadedFile = null">重新选择</el-button>
                  <el-button size="small" @click="applyUploadedContent">应用内容</el-button>
                </template>
              </div>
            </div>
          </div>
          <!-- 配置选项 -->
          <div class="config-row">
            <el-select v-model="selectedWriterModelId" placeholder="选择模型" size="small" style="width:200px" filterable>
              <el-option
                v-for="m in modelList"
                :key="m.id"
                :label="m.name + ' (' + m.model_name + ')'"
                :value="m.id"
              />
            </el-select>
            <el-select v-model="selectedWriterPromptId" placeholder="选择提示词" size="small" style="width:200px" filterable>
              <el-option
                v-for="p in promptList"
                :key="p.id"
                :label="p.name"
                :value="p.id"
              />
            </el-select>
            <el-checkbox v-model="enableAutoReview">自动评审</el-checkbox>
            <el-select v-model="pipelineType" size="small" style="width:150px;margin-left:12px">
              <el-option label="传统管线" value="traditional" />
              <el-option label="LangGraph" value="langgraph" />
              <el-option label="AutoGen" value="autogen" />
            </el-select>
          </div>
          <!-- 操作 -->
          <div class="input-actions">
            <el-button type="primary" :loading="isGenerating" :disabled="!requirementText.trim() && !uploadedFile" @click="handleGenerate">
              <el-icon><MagicStick /></el-icon>
              {{ isGenerating ? '生成中...' : '开始生成' }}
            </el-button>
            <el-button v-if="isGenerating" type="danger" ghost @click="handleCancel">取消</el-button>
            <el-button 
              v-if="currentStatus === 'failed'" 
              type="warning" 
              @click="handleRegenerate"
              :loading="isGenerating"
            >
              <el-icon><Refresh /></el-icon>
              {{ hasPartialProgress ? '继续生成' : '重新生成' }}
            </el-button>
          </div>
        </el-card>
      </el-collapse-item>

      <!-- 面板 2：生成进度 -->
      <el-collapse-item title="⚙️ 生成进度" name="progress">
        <el-card shadow="never" class="progress-card">
          <!-- StepIndicator -->
          <StepIndicator :current-stage="currentStage" :status="currentStatus" />

          <!-- 进度条 -->
          <el-progress :percentage="progress" :stroke-width="8" color="#C67B5C" class="progress-bar" />

          <!-- 阶段状态 -->
          <div class="stage-cards">
            <div class="stage-card" :class="{ active: currentStage === 'analyze', done: stageDone('analyze') }">
              <div class="stage-icon">🔍</div>
              <div class="stage-info">
                <div class="stage-name">需求分析</div>
                <div class="stage-status">{{ stageStatus('analyze') }}</div>
              </div>
            </div>
            <div class="stage-card" :class="{ active: currentStage === 'writing', done: stageDone('writing') }">
              <div class="stage-icon">✏️</div>
              <div class="stage-info">
                <div class="stage-name">用例编写</div>
                <div class="stage-status">{{ stageStatus('writing') }}</div>
              </div>
            </div>
            <div class="stage-card" :class="{ active: currentStage === 'review', done: stageDone('review') }">
              <div class="stage-icon">📋</div>
              <div class="stage-info">
                <div class="stage-name">AI 评审</div>
                <div class="stage-status">{{ stageStatus('review') }}</div>
              </div>
            </div>
            <div class="stage-card" :class="{ active: currentStage === 'revise', done: stageDone('revise') }">
              <div class="stage-icon">🔄</div>
              <div class="stage-info">
                <div class="stage-name">改进完善</div>
                <div class="stage-status">{{ stageStatus('revise') }}</div>
              </div>
            </div>
          </div>

        </el-card>

        <!-- 2×2 阶段内容卡片网格 -->
        <div v-if="stageOrderList.length > 0" class="stage-content-grid">
          <div
            v-for="stage in stageOrderList"
            :key="stage"
            class="stage-content-card"
            :class="{ expanded: !stageCollapsed[stage] }"
          >
            <div class="stage-content-header" @click="stageCollapsed[stage] = !stageCollapsed[stage]">
              <div class="stage-content-title">
                <span class="stage-content-icon">{{ stageIcons[stage] }}</span>
                <span>{{ stageLabels[stage] }}</span>
                <span v-if="stage === currentStage && isGenerating" class="stage-content-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                </span>
                <span v-else-if="stageContents[stage] && stageOrderList.indexOf(stage) < stageOrderList.length - 1" class="stage-content-done" />
              </div>
              <el-icon :size="14" :class="{ 'arrow-rotated': !stageCollapsed[stage] }"><ArrowDown /></el-icon>
            </div>
            <el-collapse-transition>
              <div v-show="!stageCollapsed[stage]" class="stage-content-body">
                <template v-if="stage === 'review'">
                  <ReviewVisualization v-if="reviewResult" :review-data="reviewResult" />
                  <div v-else-if="stageContents[stage]" class="stage-content-text">{{ stageContents[stage] }}</div>
                  <div v-else-if="stage === currentStage && isGenerating" class="stage-content-empty">
                    <el-icon class="is-loading" :size="14"><Loading /></el-icon> 评审进行中...
                  </div>
                  <div v-if="stageContents[stage]" class="review-detail-wrapper">
                    <el-collapse v-model="reviewDetailCollapse">
                      <el-collapse-item title="评审详情" name="detail">
                        <div class="stage-content-text">{{ stageContents[stage] }}</div>
                      </el-collapse-item>
                    </el-collapse>
                  </div>
                </template>
                <template v-else>
                  <div v-if="stageContents[stage]" class="stage-content-text">{{ stageContents[stage] }}</div>
                  <div v-else class="stage-content-empty">
                    <el-icon class="is-loading" :size="14" v-if="stage === currentStage"><Loading /></el-icon>
                    <span v-else>等待执行...</span>
                  </div>
                </template>
              </div>
            </el-collapse-transition>
          </div>
        </div>

        <!-- 实时日志面板 -->
        <el-card v-if="logs.length > 0" shadow="never" class="log-card">
          <template #header>
            <div class="log-header">
              <span style="font-weight:600">📝 实时生成日志</span>
              <span class="log-count">{{ logs.length }} 条</span>
            </div>
          </template>
          <div ref="logContainer" class="log-container">
            <div
              v-for="(log, idx) in logs"
              :key="idx"
              class="log-entry"
              :class="'log-level-' + log.level"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-level-tag" :class="'level-' + log.level">{{ log.level }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </el-card>
      </el-collapse-item>

      <!-- 面板 3：生成结果 -->
      <el-collapse-item title="📊 生成结果" name="results">
        <el-card shadow="never" class="results-card">
          <!-- 结果操作 -->
          <div class="result-actions" v-if="testCases.length > 0">
            <el-button type="success" size="small" @click="handleSaveToLibrary" :disabled="savedToLibrary">
              <el-icon><FolderAdd /></el-icon>
              {{ savedToLibrary ? '已保存' : '保存到用例库' }}
            </el-button>
            <el-tag v-if="savedToLibrary" type="success" size="small" effect="plain" class="saved-tag">
              <el-icon style="margin-right:4px"><Check /></el-icon>已保存
            </el-tag>
            <el-button size="small" @click="handleExportExcel">
              <el-icon><Download /></el-icon>
              导出 Excel
            </el-button>
            <el-button size="small" text @click="handleViewDetail">查看详情</el-button>
          </div>

          <!-- 空状态 -->
          <div v-if="testCases.length === 0 && !isGenerating" class="empty-result">
            <el-icon :size="48" color="#C67B5C"><MagicStick /></el-icon>
            <p>输入需求后点击「开始生成」</p>
          </div>

          <!-- 生成中状态 -->
          <div v-if="isGenerating && testCases.length === 0" class="generating-status">
            <el-icon class="is-loading" :size="24"><Loading /></el-icon>
            <p>{{ currentStatusText }}</p>
          </div>

          <!-- 候选用例表格 -->
          <div v-if="testCases.length > 0" class="cases-table">
            <el-table :data="testCases" stripe size="small" max-height="400" style="width:100%">
              <el-table-column label="编号" width="60">
                <template #default="{ row }">{{ row.case_id }}</template>
              </el-table-column>
              <el-table-column label="模块" width="100" prop="module" />
              <el-table-column label="标题" min-width="180" prop="title" />
              <el-table-column label="优先级" width="80">
                <template #default="{ row }">
                  <PriorityBadge :priority="row.priority" />
                </template>
              </el-table-column>
              <el-table-column label="前置条件" min-width="140">
                <template #default="{ row }">{{ row.precondition || '-' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button size="small" text type="primary" @click="handleRowClick(row)">
                    查看
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-collapse-item>
    </el-collapse>

    <!-- 用例详情抽屉 -->
    <el-drawer v-model="showDetail" title="用例详情" size="500px">
      <div v-if="selectedCase" class="case-detail">
        <div class="detail-field">
          <label>标题</label>
          <p>{{ selectedCase.title }}</p>
        </div>
        <div class="detail-field">
          <label>模块</label>
          <p>{{ selectedCase.module || '-' }}</p>
        </div>
        <div class="detail-field">
          <label>优先级</label>
          <PriorityBadge :priority="selectedCase.priority" />
        </div>
        <div class="detail-field">
          <label>前置条件</label>
          <p>{{ selectedCase.precondition || '-' }}</p>
        </div>
        <div class="detail-field">
          <label>测试步骤</label>
          <p style="white-space:pre-wrap">{{ selectedCase.test_steps || '-' }}</p>
        </div>
        <div class="detail-field">
          <label>预期结果</label>
          <p>{{ selectedCase.expected_result || '-' }}</p>
        </div>
      </div>
    </el-drawer>

    <!-- 保存到用例库弹窗 -->
    <el-dialog v-model="showSaveModal" title="保存到用例库" width="600px">
      <el-form label-width="100px">
        <el-form-item label="目标项目">
          <el-select v-model="saveProjectId" placeholder="选择项目" filterable style="width:100%">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用例数">
          <span>{{ testCases.length }} 条用例</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveModal = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="confirmSave">确认保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Upload, Document, FolderAdd, Download, Loading, ArrowDown, Check, Refresh } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'
import { useSSE } from '@/composables/useSSE'
import StepIndicator from '@/components/aitest/generation/StepIndicator.vue'
import PriorityBadge from '@/components/aitest/common/PriorityBadge.vue'
import ReviewVisualization from './ReviewVisualization.vue'
import type { SSEEvent, TestProject, AIModelConfigSummary, PromptConfigSummary } from '@/types/aitest'

const route = useRoute()

// 面板控制
const activePanels = ref(['input', 'progress', 'results'])

// 需求输入
const requirementText = ref('')
const selectedWriterModelId = ref<number | undefined>(undefined)
const selectedWriterPromptId = ref<number | undefined>(undefined)
const enableAutoReview = ref(true)
const pipelineType = ref<'traditional' | 'langgraph' | 'autogen'>('traditional')
const fileInputRef = ref<HTMLInputElement | null>(null)
const dragOver = ref(false)
const uploadedFile = ref<{ name: string; size: number; content: string } | null>(null)
/** 可用模型配置列表（writer 角色） */
const modelList = ref<AIModelConfigSummary[]>([])
/** 可用提示词配置列表（writer 类型） */
const promptList = ref<PromptConfigSummary[]>([])

// 生成状态
const isGenerating = ref(false)
const currentStage = ref<string | null>(null)
const currentStatus = ref('')
const progress = ref(0)
const testCases = ref<any[]>([])
const reviewFeedback = ref('')
const errorMessage = ref('')
const currentTaskId = ref('')
const savedToLibrary = ref(false)
const reviewDetailCollapse = ref<string[]>(['detail'])
/** 实时日志列表 */
const logs = ref<{ time: string; message: string; level: string }[]>([])
/** 日志容器引用，用于自动滚动 */
const logContainer = ref<HTMLElement | null>(null)

/** 各阶段积累的流式内容 */
const stageContents = ref<Record<string, string>>({
  analyze: '',
  writing: '',
  review: '',
  revise: '',
})
/** 各阶段折叠状态 */
const stageCollapsed = ref<Record<string, boolean>>({
  analyze: true,
  writing: true,
  review: true,
  revise: true,
})
/** 记录阶段出现的顺序 */
const stageOrderList = ref<string[]>([])
/** 阶段中文名称映射 */
const stageLabels: Record<string, string> = {
  analyze: '需求分析',
  writing: '用例编写',
  review: 'AI 评审',
  revise: '改进完善',
}
/** 阶段图标映射 */
const stageIcons: Record<string, string> = {
  analyze: '🔍',
  writing: '✏️',
  review: '📋',
  revise: '🔄',
}

/** 从评审阶段内容解析 JSON 结果 */
const reviewResult = computed(() => {
  const content = stageContents.value['review'] || ''
  if (!content) return null
  // 尝试从 ```json ... ``` 代码块中提取 JSON
  const match = content.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/)
  if (match) {
    try { return JSON.parse(match[1]) }
    catch { return null }
  }
  // 回退：尝试直接解析整个内容
  try { return JSON.parse(content) }
  catch { return null }
})

/** 是否有部分进度（用于判断显示"继续生成"还是"重新生成"） */
const hasPartialProgress = computed(() => {
  return stageOrderList.value.length > 0 || progress.value > 0
})

/** 添加一条实时日志 */
function addLog(message: string, level: string = 'info') {
  const now = new Date()
  const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  logs.value.push({ time, message, level })
  // 自动滚动到底部
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const stageOrder = ['analyze', 'writing', 'review', 'revise']
const currentStatusText = computed(() => {
  const map: Record<string, string> = {
    pending: '准备中...',
    generating: 'AI 正在生成用例...',
    reviewing: 'AI 正在评审...',
    revising: 'AI 正在改进...',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[currentStatus.value] || currentStatus.value || '等待中...'
})

function stageDone(stage: string): boolean {
  if (currentStatus.value === 'completed') return true
  if (!currentStage.value) return false
  return stageOrder.indexOf(currentStage.value) > stageOrder.indexOf(stage)
}
function stageStatus(stage: string): string {
  if (currentStatus.value === 'completed') return '已完成 ✓'
  if (!currentStage.value) return '等待中'
  if (stageOrder.indexOf(currentStage.value) > stageOrder.indexOf(stage)) return '已完成 ✓'
  if (currentStage.value === stage) return '进行中...'
  return '等待中'
}

// 结果操作
const showDetail = ref(false)
const selectedCase = ref<any>(null)
const showSaveModal = ref(false)
const saveProjectId = ref<number | undefined>(undefined)
const saving = ref(false)
const projects = ref<TestProject[]>([])

/**
 * 将后端状态值映射到前端 stageOrder
 * generating -> writing, reviewing -> review, revising -> revise
 */
const STATUS_STAGE_MAP: Record<string, string> = {
  analyzing: 'analyze',
  generating: 'writing',
  reviewing: 'review',
  revising: 'revise',
}

// SSE
const { setUrl: setSSEUrl, connect: connectSSE, close: closeSSE } = useSSE(
  '',
  (data: unknown) => {
    const event = data as SSEEvent
    switch (event.type) {
      case 'log':
        addLog(event.message || '', event.level || 'info')
        break
      case 'status': {
        currentStatus.value = event.status || ''
        // 映射后端状态到前端阶段
        const rawStatus = event.status || ''
        currentStage.value = STATUS_STAGE_MAP[rawStatus] || rawStatus || null
        progress.value = event.progress || 0
        break
      }
      case 'testing_stage': {
        // LangGraph 阶段切换事件
        const newStage = event.stage || ''
        if (newStage) {
          currentStage.value = newStage
          if (!stageOrderList.value.includes(newStage)) {
            stageOrderList.value.push(newStage)
            stageCollapsed.value[newStage] = false
          }
          addLog(`🔍 ${event.label || newStage}`, 'info')
        }
        break
      }
      case 'testing_review': {
        reviewFeedback.value = (event as any).raw || reviewFeedback.value
        progress.value = 70
        ElMessage.info(`AI 评审完成（评分：${(event as any).overall_score}/10）`)
        break
      }
      case 'testing_done': {
        currentStatus.value = 'completed'
        currentStage.value = null
        progress.value = 100
        isGenerating.value = false
        addLog('✅ 用例生成完成', 'success')
        ElMessage.success('用例生成完成')
        break
      }
      case 'chunk': {
        // LangGraph 的 chunk 携带 stage 字段；传统 pipeline 的 chunk 归入 writing
        const targetStage = (event as any).stage || 'writing'
        if (!stageOrderList.value.includes(targetStage)) {
          stageOrderList.value.push(targetStage)
          stageCollapsed.value[targetStage] = false
        }
        stageContents.value[targetStage] += event.content || ''
        break
      }
      case 'review_chunk': {
        if (!stageOrderList.value.includes('review')) {
          stageOrderList.value.push('review')
          stageCollapsed.value['review'] = false
        }
        stageContents.value['review'] += event.content || ''
        break
      }
      case 'revise_chunk': {
        if (!stageOrderList.value.includes('revise')) {
          stageOrderList.value.push('revise')
          stageCollapsed.value['revise'] = false
        }
        stageContents.value['revise'] += event.content || ''
        break
      }
      case 'cases':
        if (event.cases && event.cases.length > 0) {
          testCases.value = event.cases
          progress.value = event.progress || 50
          addLog(`已生成 ${event.cases.length} 条测试用例`, 'success')
          ElMessage.success(`已生成 ${event.cases.length} 条测试用例`)
        }
        break
      case 'review_complete':
        reviewFeedback.value = event.feedback || reviewFeedback.value
        progress.value = event.progress || 80
        ElMessage.info('AI 评审完成')
        break
      case 'revise_complete':
        progress.value = event.progress || 95
        ElMessage.success('改进完成')
        break
      case 'complete':
        currentStatus.value = 'completed'
        currentStage.value = null
        progress.value = 100
        isGenerating.value = false
        addLog('测试用例生成完成', 'success')
        ElMessage.success('测试用例生成完成')
        break
      case 'error':
        errorMessage.value = event.message || '生成过程出现异常'
        currentStatus.value = 'failed'
        currentStage.value = null
        isGenerating.value = false
        addLog(errorMessage.value, 'error')
        ElMessage.error(errorMessage.value)
        break
      case 'done':
        isGenerating.value = false
        break
    }
  },
  { autoReconnect: false },
)

// 文档上传
function triggerFileInput() { fileInputRef.value?.click() }

async function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) await uploadFile(file)
  target.value = ''
}

async function handleDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) await uploadFile(file)
}

async function uploadFile(file: File) {
  try {
    const res = await aitestApi.uploadGenerationDoc(file as any)
    uploadedFile.value = {
      name: file.name,
      size: file.size,
      content: res.data.content || '',
    }
    ElMessage.success('文档已上传并解析')
  } catch (e: any) {
    ElMessage.error('文档上传失败: ' + (e.message || ''))
  }
}

function applyUploadedContent() {
  if (uploadedFile.value?.content) {
    requirementText.value = uploadedFile.value.content
    uploadedFile.value = null
    ElMessage.success('已应用文档内容')
  }
}

// 生成
async function handleGenerate() {
  // 如果需求文本为空但有上传文件，自动应用文档内容
  if (!requirementText.value.trim() && uploadedFile.value?.content) {
    requirementText.value = uploadedFile.value.content
    uploadedFile.value = null
    ElMessage.success('已自动应用文档内容')
  }
  if (!requirementText.value.trim()) {
    ElMessage.warning('请输入测试需求或上传需求文档')
    return
  }
  if (!selectedWriterModelId.value) {
    ElMessage.warning('请选择编写模型')
    return
  }
  if (!selectedWriterPromptId.value) {
    ElMessage.warning('请选择编写提示词')
    return
  }
  isGenerating.value = true
  currentStage.value = null
  currentStatus.value = 'pending'
  progress.value = 5
  testCases.value = []
  reviewFeedback.value = ''
  errorMessage.value = ''
  logs.value = []
  savedToLibrary.value = false
  stageContents.value = { analyze: '', writing: '', review: '', revise: '' }
  stageOrderList.value = []
  stageCollapsed.value = { analyze: true, writing: true, review: true, revise: true }
  
  const hasExistingTask = !!currentTaskId.value
  
  if (hasExistingTask) {
    addLog('🔄 重新生成已有任务...', 'info')
  } else {
    addLog('🚀 创建生成任务...', 'info')
  }
  
  try {
    let res
    if (hasExistingTask) {
      res = await aitestApi.reviseGenerationTask(currentTaskId.value, pipelineType.value)
    } else {
      res = await aitestApi.createGenerationTask({
        requirement_text: requirementText.value,
        writer_model_config_id: selectedWriterModelId.value,
        writer_prompt_config_id: selectedWriterPromptId.value,
        output_mode: 'stream',
        enable_auto_review: enableAutoReview.value,
        pipeline_type: pipelineType.value,
      })
    }
    currentTaskId.value = res.data.task_id
    const streamUrl = aitestApi.getStreamUrl(res.data.task_id)
    setSSEUrl(streamUrl)
    connectSSE()
  } catch (e: any) {
    isGenerating.value = false
    ElMessage.error(e?.response?.data?.message || (hasExistingTask ? '重新生成任务失败' : '创建任务失败'))
  }
}

/**
 * 重新生成/继续生成
 * 如果已有部分进度，则尝试从失败点继续；否则从头开始
 */
async function handleRegenerate() {
  if (!selectedWriterModelId.value) {
    ElMessage.warning('请选择编写模型')
    return
  }
  if (!selectedWriterPromptId.value) {
    ElMessage.warning('请选择编写提示词')
    return
  }
  
  isGenerating.value = true
  currentStatus.value = 'pending'
  errorMessage.value = ''
  
  // 确定从哪个阶段继续
  const stages = ['analyze', 'writing', 'review', 'revise']
  let continueFromStage = 'analyze'
  
  // 如果已有部分进度，找到最后一个有内容的阶段的下一个阶段
  if (hasPartialProgress.value && stageOrderList.value.length > 0) {
    const lastStage = stageOrderList.value[stageOrderList.value.length - 1]
    const lastIndex = stages.indexOf(lastStage)
    if (lastIndex >= 0 && lastIndex < stages.length - 1) {
      continueFromStage = stages[lastIndex + 1]
    } else if (lastIndex === stages.length - 1) {
      // 已经到最后一个阶段了，重新开始
      continueFromStage = 'analyze'
    }
    addLog(`🔄 继续生成（从 ${stageLabels[continueFromStage]} 阶段开始）...`, 'info')
  } else {
    addLog('🔄 重新开始生成...', 'info')
    // 没有进度，重置所有状态
    stageContents.value = { analyze: '', writing: '', review: '', revise: '' }
    stageOrderList.value = []
    stageCollapsed.value = { analyze: true, writing: true, review: true, revise: true }
    testCases.value = []
    reviewFeedback.value = ''
    logs.value = []
  }
  
  try {
    const res = await aitestApi.createGenerationTask({
      requirement_text: requirementText.value,
      writer_model_config_id: selectedWriterModelId.value,
      writer_prompt_config_id: selectedWriterPromptId.value,
      output_mode: 'stream',
      enable_auto_review: enableAutoReview.value,
      pipeline_type: pipelineType.value,
      continue_from_stage: hasPartialProgress.value ? continueFromStage : undefined,
      continue_task_id: hasPartialProgress.value ? currentTaskId.value : undefined,
    })
    currentTaskId.value = res.data.task_id
    const streamUrl = aitestApi.getStreamUrl(res.data.task_id)
    setSSEUrl(streamUrl)
    connectSSE()
  } catch (e: any) {
    isGenerating.value = false
    currentStatus.value = 'failed'
    ElMessage.error(e?.response?.data?.message || '重新生成失败')
  }
}

function handleViewDetail() {
  const taskId = currentTaskId.value
  if (taskId) {
    window.open(`/modules/aitest/generate/tasks/${taskId}`, '_blank')
  }
}

/** 加载模型和提示词配置列表 */
async function loadConfigs() {
  try {
    const [modelRes, promptRes] = await Promise.all([
      aitestApi.getModelList('writer'),
      aitestApi.getPromptList('writer'),
    ])
    modelList.value = modelRes.data || []
    promptList.value = promptRes.data || []
    // 只有一项时自动选中
    if (modelList.value.length === 1) selectedWriterModelId.value = modelList.value[0].id
    if (promptList.value.length === 1) selectedWriterPromptId.value = promptList.value[0].id
  } catch { /* 静默失败，用户可手动选择 */ }
}

/** 从 AI 生成记录列表加载已有任务（?task_id=xxx） */
async function loadExistingTask(taskId: string) {
  try {
    const res = await aitestApi.getTaskDetail(taskId)
    const task = res.data
    if (!task) return
    currentTaskId.value = taskId
    currentStatus.value = task.status
    requirementText.value = task.requirement_text || ''
    savedToLibrary.value = task.saved_to_library || false
    if (task.test_cases && task.test_cases.length > 0) {
      testCases.value = task.test_cases.map((tc: any) => ({
        case_id: tc.case_id,
        module: tc.module || '',
        title: tc.title,
        precondition: tc.precondition || '',
        test_steps: tc.test_steps || '',
        expected_result: tc.expected_result || '',
        priority: tc.priority,
        status: tc.status || 'generated',
      }))
    }
    // 填充阶段内容
    const genContent = task.generated_content as Record<string, string> | null
    if (genContent?.text) {
      stageContents.value['writing'] = genContent.text
      if (!stageOrderList.value.includes('writing')) stageOrderList.value.push('writing')
    }
    if (task.review_feedback) {
      stageContents.value['review'] = task.review_feedback
      if (!stageOrderList.value.includes('review')) stageOrderList.value.push('review')
    }
    const finalContent = task.final_content as Record<string, string> | null
    if (finalContent?.text) {
      stageContents.value['revise'] = finalContent.text
      if (!stageOrderList.value.includes('revise')) stageOrderList.value.push('revise')
    }
    // 如有 analyze 内容
    if (genContent?.analysis) {
      stageContents.value['analyze'] = genContent.analysis
      if (!stageOrderList.value.includes('analyze')) stageOrderList.value.push('analyze')
    }
    // 展开所有已加载的阶段卡片
    stageOrderList.value.forEach((s: string) => { stageCollapsed.value[s] = false })
    progress.value = task.progress || 100
    if (task.status === 'completed') {
      progress.value = 100
    }
  } catch (e: any) {
    ElMessage.error('加载任务失败: ' + (e.message || ''))
  }
}

onMounted(async () => {
  await loadConfigs()
  const taskId = route.query.task_id as string
  if (taskId) {
    await loadExistingTask(taskId)
  }
})

async function handleCancel() {
  try {
    await ElMessageBox.confirm('确定要取消当前生成任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '继续生成',
      type: 'warning',
    })
  } catch {
    return // 用户取消
  }
  closeSSE()
  try {
    await aitestApi.cancelGenerationTask(currentTaskId.value)
    ElMessage.success('任务已取消')
  } catch (e: any) {
    ElMessage.warning(e?.response?.data?.detail || '取消失败')
  }
  isGenerating.value = false
  currentStatus.value = 'cancelled'
}

function handleRowClick(row: any) {
  selectedCase.value = row
  showDetail.value = true
}

async function handleSaveToLibrary() {
  if (testCases.value.length === 0) return
  try {
    const res = await aitestApi.listProjects()
    projects.value = res.data || []
  } catch { /* ignore */ }
  showSaveModal.value = true
}

async function confirmSave() {
  if (!saveProjectId.value) {
    ElMessage.warning('请选择目标项目')
    return
  }
  saving.value = true
  try {
    await aitestApi.saveCaseItemsToLibrary(currentTaskId.value, {
      project_id: saveProjectId.value,
    })
    savedToLibrary.value = true
    ElMessage.success(`已保存 ${testCases.value.length} 条用例到用例库`)
    showSaveModal.value = false
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e?.response?.data?.detail || e.message || ''))
  } finally {
    saving.value = false
  }
}

function handleExportExcel() {
  if (testCases.value.length === 0) {
    ElMessage.warning('暂无测试用例可导出')
    return
  }
  
  try {
    import('xlsx').then((xlsx) => {
      // 准备数据
      const headers = [
        { key: 'case_id', label: '用例编号' },
        { key: 'module', label: '所属模块' },
        { key: 'title', label: '用例标题' },
        { key: 'priority', label: '优先级' },
        { key: 'precondition', label: '前置条件' },
        { key: 'test_steps', label: '测试步骤' },
        { key: 'expected_result', label: '预期结果' },
      ]
      
      // 转换数据格式
      const data = testCases.value.map((caseItem: any) => {
        const row: Record<string, string> = {}
        headers.forEach((h) => {
          row[h.key] = String(caseItem[h.key] || '')
        })
        return row
      })
      
      // 创建工作簿和工作表
      const worksheet = xlsx.utils.json_to_sheet(data)
      
      // 设置列宽
      const columnWidths = [
        { wch: 15 },  // 用例编号
        { wch: 15 },  // 所属模块
        { wch: 30 },  // 用例标题
        { wch: 10 },  // 优先级
        { wch: 30 },  // 前置条件
        { wch: 50 },  // 测试步骤
        { wch: 40 },  // 预期结果
      ]
      worksheet['!cols'] = columnWidths
      
      // 创建工作簿
      const workbook = xlsx.utils.book_new()
      xlsx.utils.book_append_sheet(workbook, worksheet, '测试用例')
      
      // 生成文件名
      const timestamp = new Date().toISOString().slice(0, 10)
      const fileName = `测试用例_${timestamp}.xlsx`
      
      // 导出文件
      xlsx.writeFile(workbook, fileName)
      
      ElMessage.success(`已成功导出 ${testCases.value.length} 条测试用例`)
    })
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

</script>

<style scoped>
.page-wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text, #3D2E1F); margin: 0 0 20px; letter-spacing: -0.02em; }
.panel-collapse { border: none; }
.panel-collapse :deep(.el-collapse-item__header) { font-size: 15px; font-weight: 600; padding: 0 4px; }
.panel-collapse :deep(.el-collapse-item__content) { padding-bottom: 16px; }

.input-card { border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; background: var(--card-bg, #FFFDF9); }
.input-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.col-title { font-size: 14px; font-weight: 600; color: var(--text, #3D2E1F); margin: 0 0 8px; }
.upload-zone {
  border: 2px dashed rgba(180,150,120,0.2); border-radius: 12px;
  padding: 32px; text-align: center; cursor: pointer; transition: all 0.2s;
  min-height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
}
.upload-zone:hover, .upload-zone.is-dragover { border-color: var(--primary, #C67B5C); background: rgba(198,123,92,0.04); }
.upload-text { font-size: 14px; color: var(--text, #3D2E1F); margin: 0; }
.upload-hint { font-size: 12px; color: var(--text-muted, #8B7355); margin: 0; }
.config-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.input-actions { display: flex; gap: 12px; }

.progress-card { border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; background: var(--card-bg, #FFFDF9); }
.progress-bar { margin: 8px 0 20px; }
.stage-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stage-card {
  padding: 16px; border-radius: 10px; border: 1px solid rgba(180,150,120,0.12);
  background: var(--bg, #FBF7F0); text-align: center; transition: all 0.3s;
}
.stage-card.active { border-color: var(--primary, #C67B5C); background: rgba(198,123,92,0.06); }
.stage-card.done { border-color: #10b981; background: rgba(16,185,129,0.06); }
.stage-icon { font-size: 24px; margin-bottom: 8px; }
.stage-name { font-size: 13px; font-weight: 600; color: var(--text, #3D2E1F); }
.stage-status { font-size: 11px; color: var(--text-muted, #8B7355); margin-top: 4px; }
.stage-card.active .stage-status { color: var(--primary, #C67B5C); }
.stage-card.done .stage-status { color: #10b981; }

/* 评审详情折叠面板 */
.stage-content-body :deep(.el-collapse-item__header) { font-size: 13px; font-weight: 500; }
.review-detail-wrapper { margin-top: 12px; border-top: 1px solid var(--border, rgba(180,150,120,0.1)); padding-top: 8px; }

/* 2×2 阶段内容卡片网格 */
.stage-content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 16px 0;
}
.stage-content-card {
  border: 1px solid var(--border, rgba(180,150,120,0.12));
  border-radius: 10px;
  background: var(--card-bg, #FFFDF9);
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.stage-content-card.expanded {
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.stage-content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}
.stage-content-header:hover {
  background: rgba(198,123,92,0.04);
}
.stage-content-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text, #3D2E1F);
}
.stage-content-icon { font-size: 16px; line-height: 1; }
.stage-content-loading { display: inline-flex; margin-left: 4px; color: var(--primary, #C67B5C); }
.stage-content-done { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10b981; margin-left: 6px; }
.arrow-rotated { transform: rotate(180deg); }
.stage-content-body {
  border-top: 1px solid var(--border, rgba(180,150,120,0.1));
  padding: 12px 14px;
  max-height: 300px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary, #5C4A38);
}
.stage-content-text {
  white-space: pre-wrap;
  word-break: break-all;
}
.stage-content-empty {
  color: var(--text-muted, #8B7355);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

/* 实时日志面板 */
.log-card { margin-top: 16px; border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 10px; }
.log-header { display: flex; align-items: center; justify-content: space-between; }
.log-count { font-size: 12px; color: var(--text-muted, #8B7355); }
.log-container {
  max-height: 300px;
  overflow-y: auto;
  background: #1a1a2e;
  border-radius: 8px;
  padding: 12px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
}
.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 2px 0;
  animation: logFadeIn 0.2s ease-out;
}
@keyframes logFadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
.log-time { color: #6c7293; flex-shrink: 0; user-select: none; min-width: 60px; }
.log-level-tag {
  font-size: 10px;
  padding: 0 5px;
  border-radius: 3px;
  flex-shrink: 0;
  min-width: 46px;
  text-align: center;
  font-weight: 600;
  text-transform: uppercase;
}
.level-info { background: rgba(96, 165, 250, 0.2); color: #60a5fa; }
.level-success { background: rgba(52, 211, 153, 0.2); color: #34d399; }
.level-warning { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.level-error { background: rgba(248, 113, 113, 0.2); color: #f87171; }
.log-message { color: #e2e8f0; word-break: break-all; }
/* 日志容器滚动条样式 */
.log-container::-webkit-scrollbar { width: 4px; }
.log-container::-webkit-scrollbar-track { background: transparent; }
.log-container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }

.results-card { border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; background: var(--card-bg, #FFFDF9); }
.result-actions { display: flex; gap: 8px; margin-bottom: 16px; }
.result-actions { align-items: center; }
.saved-tag { margin-left: 4px; }
.empty-result { text-align: center; padding: 48px 20px; color: var(--text-muted, #8B7355); }
.generating-status { text-align: center; padding: 48px 20px; color: var(--text-muted, #8B7355); display: flex; align-items: center; justify-content: center; gap: 8px; }
.cases-table { margin-top: 8px; }

.case-detail { padding: 16px; }
.detail-field { margin-bottom: 16px; }
.detail-field label { font-size: 12px; font-weight: 600; color: #7A6855; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 4px; }
.detail-field p { font-size: 14px; color: var(--text, #3D2E1F); line-height: 1.6; margin: 0; }

@media (max-width: 768px) {
  .input-grid { grid-template-columns: 1fr; }
  .stage-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
