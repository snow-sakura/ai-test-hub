<template>
  <div class="page-wrap">
    <div class="back-nav">
      <span class="back-arrow" @click="router.push('/modules/aitest/generate/records')">←</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-link" @click="router.push('/modules/aitest/generate/records')">生成记录</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-current">任务详情</span>
    </div>

    <div v-if="loading" class="loading-wrap">
      <el-icon class="is-loading" :size="20"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <el-result v-else-if="error" icon="error" title="加载失败" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="loadTask">重试</el-button>
        <el-button @click="router.push('/modules/aitest/generate/records')">返回列表</el-button>
      </template>
    </el-result>

    <template v-else-if="task">
      <!-- 头部信息 -->
      <div class="detail-header">
        <div class="header-left">
          <h1 class="page-title">{{ task.title || '任务 #' + task.id }}</h1>
          <StatusTag :status="task.status" />
        </div>
        <div class="header-actions">
          <el-button size="small" @click="handleReGenerate" :disabled="task.status === 'generating'">
            重新生成
          </el-button>
          <el-button size="small" type="danger" ghost @click="handleDeleteTask">删除</el-button>
        </div>
      </div>

      <!-- 基础信息 -->
      <div class="info-bar">
        <div class="info-item">
          <span class="info-label">任务 ID</span>
          <span class="info-value">{{ task.task_id }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">创建时间</span>
          <span class="info-value">{{ formatTime(task.created_at) }}</span>
        </div>
        <div class="info-item" v-if="task.completed_at">
          <span class="info-label">完成时间</span>
          <span class="info-value">{{ formatTime(task.completed_at) }}</span>
        </div>
      </div>

      <!-- 需求文本 -->
      <div class="content-section">
        <h3 class="section-title">需求描述</h3>
        <div class="content-body" v-html="renderMarkdown(task.requirement_text || '无需求描述')"></div>
      </div>

      <!-- 四阶段结果 -->
      <el-collapse v-if="task.generated_content || task.review_feedback || task.final_content" v-model="activeStages" class="stages-collapse">
        <el-collapse-item title="生成阶段结果" name="generated">
          <div class="content-body" v-if="task.generated_content" v-html="renderMarkdown(JSON.stringify(task.generated_content, null, 2))"></div>
          <span v-else class="empty-text">暂无生成结果</span>
        </el-collapse-item>
        <el-collapse-item title="AI 评审反馈" name="review">
          <div class="content-body" v-if="task.review_feedback" v-html="renderMarkdown(task.review_feedback)"></div>
          <span v-else class="empty-text">暂无评审反馈</span>
        </el-collapse-item>
        <el-collapse-item title="改进完善结果" name="revised">
          <div class="content-body" v-if="task.final_content" v-html="renderMarkdown(JSON.stringify(task.final_content, null, 2))"></div>
          <span v-else class="empty-text">暂无完善结果</span>
        </el-collapse-item>
      </el-collapse>

      <!-- 候选用例 -->
      <div class="content-section">
        <div class="section-header">
          <h3 class="section-title" style="margin-bottom:0">候选用例 ({{ candidateCases.length }})</h3>
          <div class="header-actions" style="gap:8px">
            <el-button size="small" type="success" :disabled="selectedIds.length === 0" @click="handleBatchAdopt">
              批量采纳
            </el-button>
            <el-button size="small" type="danger" :disabled="selectedIds.length === 0" @click="handleBatchDiscard">
              批量丢弃
            </el-button>
            <el-button size="small" text :disabled="selectedIds.length === 0" @click="handleSaveToLibrary">
              保存到用例库
            </el-button>
          </div>
        </div>
        <div v-if="candidateCases.length === 0" class="empty-section">暂无候选用例</div>
        <div v-else>
          <div class="case-table-header">
            <el-checkbox v-model="selectAll" :indeterminate="isIndeterminate" @change="handleSelectAll" size="small" />
            <span class="header-cell title-col">标题</span>
            <span class="header-cell priority-col">优先级</span>
            <span class="header-cell module-col">模块</span>
            <span class="header-cell status-col">状态</span>
            <span class="header-cell action-col">操作</span>
          </div>
          <div v-for="c in candidateCases" :key="c.id || c.case_id" class="case-row" :class="{ selected: selectedIds.includes(c.id!) }">
            <el-checkbox v-model="selectedIds" :label="c.id" size="small" @change="onSelectionChange" />
            <span class="cell title-col">{{ c.title }}</span>
            <span class="cell priority-col"><PriorityBadge :priority="(c.priority || 'P2').toUpperCase()" /></span>
            <span class="cell module-col">{{ c.module || '—' }}</span>
            <span class="cell status-col">{{ statusLabel(c.status) }}</span>
            <span class="cell action-col">
              <el-button text size="small" @click="toggleCaseExpand(c)">详情</el-button>
            </span>
            <!-- 展开详情 -->
            <div v-if="expandedCaseId === (c.id || c.case_id)" class="case-detail-expand">
              <div class="detail-section"><span class="detail-label">前置条件</span><p>{{ c.precondition || '—' }}</p></div>
              <div class="detail-section"><span class="detail-label">测试步骤</span><p style="white-space:pre-wrap">{{ c.test_steps || '—' }}</p></div>
              <div class="detail-section"><span class="detail-label">预期结果</span><p>{{ c.expected_result || '—' }}</p></div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 保存到用例库 - 项目选择弹窗 -->
    <el-dialog v-model="showSaveModal" title="选择目标项目" width="420px" :close-on-click-modal="false">
      <p style="margin-bottom:12px;font-size:13px;color:#8B7355">请选择要将已采纳用例保存到的项目：</p>
      <el-select v-model="saveProjectId" placeholder="选择项目" style="width:100%">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <template #footer>
        <el-button @click="showSaveModal = false">取消</el-button>
        <el-button type="warning" :loading="saving" @click="confirmSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'
import { useMarkdownRenderer } from '@/composables/useMarkdownRenderer'
import StatusTag from '@/components/aitest/common/StatusTag.vue'
import PriorityBadge from '@/components/aitest/common/PriorityBadge.vue'
import type { AIGenerationTask, GeneratedTestCase } from '@/types/aitest'

const { render: renderMarkdown } = useMarkdownRenderer()
const route = useRoute()
const router = useRouter()

const taskId = computed(() => route.params.id as string)
const loading = ref(false)
const error = ref('')
const task = ref<AIGenerationTask | null>(null)
const candidateCases = ref<GeneratedTestCase[]>([])
const selectedIds = ref<number[]>([])
const activeStages = ref<string[]>([])
const expandedCaseId = ref<string | null>(null)
const showSaveModal = ref(false)
const saveProjectId = ref<number | null>(null)
const projects = ref<any[]>([])
const saving = ref(false)

const selectAll = computed({
  get: () => candidateCases.value.length > 0 && selectedIds.value.length === candidateCases.value.length,
  set: (val: boolean) => {
    if (val) selectedIds.value = candidateCases.value.map(c => c.id!).filter(Boolean)
    else selectedIds.value = []
  },
})
const isIndeterminate = computed(() => selectedIds.value.length > 0 && selectedIds.value.length < candidateCases.value.length)

function formatTime(t: string | null | undefined): string {
  if (!t) return '—'
  const d = new Date(t)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { pending: '待处理', adopted: '已采纳', discarded: '已丢弃' }
  return map[s] || s
}

function toggleCaseExpand(c: GeneratedTestCase) {
  const key = String(c.id || c.case_id)
  expandedCaseId.value = expandedCaseId.value === key ? null : key
}

function onSelectionChange() { /* 计算属性自动处理 */ }

function handleSelectAll(checked: boolean) { selectAll.value = checked }

async function loadTask() {
  loading.value = true
  error.value = ''
  try {
    const res = await aitestApi.getTaskDetail(taskId.value)
    task.value = res.data
    candidateCases.value = res.data?.test_cases || []
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleBatchAdopt() {
  if (selectedIds.value.length === 0) return
  try {
    await aitestApi.batchUpdateCaseItems(taskId.value, {
      case_ids: selectedIds.value,
      status: 'adopted',
    })
    ElMessage.success(`已采纳 ${selectedIds.value.length} 个用例`)
    selectedIds.value = []
    await loadTask()
  } catch { ElMessage.error('批量采纳失败') }
}

async function handleBatchDiscard() {
  if (selectedIds.value.length === 0) return
  try {
    await aitestApi.batchUpdateCaseItems(taskId.value, {
      case_ids: selectedIds.value,
      status: 'discarded',
    })
    ElMessage.success(`已丢弃 ${selectedIds.value.length} 个用例`)
    selectedIds.value = []
    await loadTask()
  } catch { ElMessage.error('批量丢弃失败') }
}

async function handleSaveToLibrary() {
  if (selectedIds.value.length === 0) return
  try {
    const res = await aitestApi.listProjects()
    projects.value = res.data || []
    // 默认选中任务关联的项目
    saveProjectId.value = task.value?.project_id || null
    showSaveModal.value = true
  } catch {
    ElMessage.error('获取项目列表失败')
  }
}

async function confirmSave() {
  if (!saveProjectId.value) {
    ElMessage.warning('请选择目标项目')
    return
  }
  saving.value = true
  try {
    await aitestApi.saveCaseItemsToLibrary(taskId.value, {
      project_id: saveProjectId.value,
      case_ids: selectedIds.value.length > 0 ? selectedIds.value : undefined,
    })
    const count = selectedIds.value.length > 0 ? selectedIds.value.length : '全部已采纳'
    ElMessage.success(`已保存 ${count} 个用例到用例库`)
    showSaveModal.value = false
    selectedIds.value = []
    await loadTask()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e?.response?.data?.detail || e?.message || ''))
  } finally {
    saving.value = false
  }
}

async function handleReGenerate() {
  try {
    await aitestApi.reviseGenerationTask(taskId.value)
    ElMessage.success('已重新生成')
    await loadTask()
  } catch { ElMessage.error('操作失败') }
}

async function handleDeleteTask() {
  try {
    await ElMessageBox.confirm('确认删除该任务？删除后不可恢复。', '确认删除', { type: 'warning' })
    await aitestApi.deleteGenerationTask(taskId.value)
    ElMessage.success('已删除')
    router.push('/modules/aitest/generate/records')
  } catch { /* 取消或失败 */ }
}

onMounted(loadTask)
</script>

<style scoped>
.page-wrap { max-width: 900px; margin: 0 auto; padding: 32px 24px 64px; }
.back-nav { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #7A6855; margin-bottom: 20px; }
.back-arrow { font-size: 16px; cursor: pointer; color: var(--primary, #C67B5C); }
.back-arrow:hover { color: var(--primary-light, #D49472); }
.breadcrumb-link { cursor: pointer; }
.breadcrumb-link:hover { color: var(--primary, #C67B5C); }
.breadcrumb-sep { color: rgba(180,150,120,0.3); }
.breadcrumb-current { color: var(--text, #3D2E1F); font-weight: 500; }
.loading-wrap { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 64px 0; }
.detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text, #3D2E1F); margin: 0; }
.header-actions { display: flex; gap: 8px; }
.info-bar { display: flex; gap: 32px; padding: 12px 20px; background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.info-item { display: flex; align-items: center; gap: 6px; }
.info-label { font-size: 12px; color: #7A6855; }
.info-value { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); }
.content-section { background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-title { font-size: 15px; font-weight: 600; color: var(--text, #3D2E1F); margin: 0 0 12px; }
.content-body { font-size: 14px; line-height: 1.7; color: var(--text-secondary, #5C4A38); }
.content-body :deep(pre) { background: #1e1e1e; border-radius: 8px; padding: 12px; overflow-x: auto; }
.empty-section, .empty-text { font-size: 13px; color: var(--text-muted, #8B7355); padding: 8px 0; }
.stages-collapse { margin-bottom: 16px; }
.case-table-header { display: flex; align-items: center; gap: 8px; padding: 8px 12px; font-size: 12px; font-weight: 600; color: #7A6855; background: rgba(180,150,120,0.04); border-radius: 8px 8px 0 0; }
.case-row { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-bottom: 1px solid rgba(180,150,120,0.06); flex-wrap: wrap; }
.case-row:hover { background: rgba(198,123,92,0.03); }
.case-row.selected { background: rgba(198,123,92,0.05); }
.header-cell, .cell { font-size: 13px; color: var(--text, #3D2E1F); }
.title-col { flex: 2; min-width: 120px; }
.priority-col { width: 60px; }
.module-col { width: 80px; }
.status-col { width: 60px; }
.action-col { width: 60px; text-align: right; }
.case-detail-expand { width: 100%; padding: 12px 24px 8px; background: rgba(198,123,92,0.03); border-radius: 0 0 8px 8px; }
.detail-section { margin-bottom: 8px; }
.detail-label { font-size: 11px; font-weight: 600; color: #7A6855; }
.detail-section p { margin: 4px 0 0; font-size: 13px; line-height: 1.6; color: var(--text, #3D2E1F); }
</style>
