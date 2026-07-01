<template>
  <div class="page-wrap">
    <div class="back-nav">
      <span class="back-arrow" @click="router.push('/modules/aitest/testcases')">←</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-link" @click="router.push('/modules/aitest/testcases')">用例列表</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-current">{{ testCase.name }}</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrap">
      <el-icon class="is-loading" :size="20"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <!-- 错误状态 -->
    <el-result v-else-if="error" icon="error" title="加载失败" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="loadTestCase">重试</el-button>
        <el-button @click="router.push('/modules/aitest/testcases')">返回列表</el-button>
      </template>
    </el-result>

    <template v-else>
      <!-- 头部 -->
      <div class="detail-header">
        <div class="header-left">
          <h1 class="page-title">{{ testCase.name }}</h1>
          <StatusTag :status="testCase.status" />
          <PriorityBadge :priority="testCase.priority?.toUpperCase()" />
        </div>
        <div class="header-actions">
          <el-button size="small" @click="handleEdit">编辑</el-button>
        </div>
      </div>

      <!-- 信息栏 -->
      <div class="info-bar">
        <div class="info-item">
          <span class="info-label">模块</span>
          <span class="info-value">{{ testCase.module || '—' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">类型</span>
          <span class="info-value">{{ typeLabel }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">来源</span>
          <span class="info-value">{{ sourceLabel }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">创建时间</span>
          <span class="info-value">{{ formatTime(testCase.created_at) }}</span>
        </div>
      </div>

      <!-- 内容卡片：前置条件 -->
      <div class="content-section">
        <h3 class="section-title">前置条件</h3>
        <div class="content-body" v-html="renderMarkdown(testCase.precondition || '—')"></div>
      </div>

      <!-- 内容卡片：测试步骤 -->
      <div class="content-section">
        <h3 class="section-title">测试步骤</h3>
        <div class="content-body" v-html="renderMarkdown(testCase.test_steps || '—')"></div>
      </div>

      <!-- 内容卡片：预期结果 -->
      <div class="content-section">
        <h3 class="section-title">预期结果</h3>
        <div class="content-body" v-html="renderMarkdown(testCase.expected_result || '—')"></div>
      </div>

      <!-- 内容卡片：评审历史 -->
      <div class="content-section">
        <h3 class="section-title">评审历史</h3>
        <el-table v-if="reviewHistory.length > 0" :data="reviewHistory" stripe size="small" style="width:100%">
          <el-table-column label="评审名称" min-width="160">
            <template #default="{ row }">
              <router-link :to="`/modules/aitest/reviews/${row.id}`" class="review-link">
                {{ row.name }}
              </router-link>
            </template>
          </el-table-column>
          <el-table-column label="评审结果" min-width="100">
            <template #default="{ row }">
              <el-tag :type="reviewStatusTag(row.status)" size="small">{{ reviewStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="结论" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ row.conclusion || '—' }}</template>
          </el-table-column>
          <el-table-column label="创建人" min-width="100">
            <template #default="{ row }">{{ row.creator_name || '—' }}</template>
          </el-table-column>
          <el-table-column label="评审时间" min-width="160">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-section">该用例尚未参与任何评审</div>
      </div>

      <!-- 内容卡片：用例执行 -->
      <div class="content-section">
        <div class="section-header">
          <h3 class="section-title">用例执行</h3>
          <el-button
            v-if="testCase.status === 'active'"
            size="small"
            type="primary"
            @click="executeDialogVisible = true"
          >
            执行用例
          </el-button>
        </div>

        <!-- 不可执行提示 -->
        <div v-if="testCase.status !== 'active'" class="empty-section">
          <el-icon style="vertical-align:middle;margin-right:4px"><WarningFilled /></el-icon>
          用例评审通过后方可执行（当前状态：{{ statusLabel(testCase.status) }}）
        </div>

        <!-- 执行历史 -->
        <div v-else-if="executions.length === 0" class="empty-section">
          暂无执行记录
        </div>
        <div v-else class="execution-list">
          <div v-for="exec in executions" :key="exec.id" class="execution-item">
            <el-tag :type="executionTagType(exec.status)" size="small" effect="dark" style="min-width:56px;text-align:center">
              {{ executionLabel(exec.status) }}
            </el-tag>
            <span class="exec-actual">{{ exec.actual_result || '—' }}</span>
            <span class="exec-meta">
              {{ exec.executor_name || '用户' }}
              {{ formatTime(exec.created_at) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 内容卡片：标签 -->
      <div class="content-section" v-if="testCase.tags && testCase.tags.length > 0">
        <h3 class="section-title">标签</h3>
        <div class="tags-row">
          <el-tag v-for="tag in testCase.tags" :key="tag" size="small" effect="plain" style="margin-right:6px;margin-bottom:4px">
            {{ tag }}
          </el-tag>
        </div>
      </div>

      <!-- 附件区域 -->
      <div class="content-section">
        <div class="section-header">
          <h3 class="section-title">附件</h3>
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :on-success="onUploadSuccess"
            :on-error="onUploadError"
            :show-file-list="false"
            :data="{ case_id: caseId }"
          >
            <el-button size="small" type="primary" text>
              <el-icon><Upload /></el-icon>
              上传附件
            </el-button>
          </el-upload>
        </div>
        <div v-if="attachments.length === 0" class="empty-section">
          暂无附件
        </div>
        <div v-else class="attachment-list">
          <div v-for="att in attachments" :key="att.id" class="attachment-item">
            <el-icon><Document /></el-icon>
            <div class="att-info">
              <span class="att-name">{{ att.file_name }}</span>
              <span class="att-size">{{ formatSize(att.file_size) }}</span>
            </div>
            <el-button text size="small" @click="downloadAttachment(att.id)" title="下载">
              <el-icon><Download /></el-icon>
            </el-button>
            <el-button text size="small" type="danger" @click="deleteAttachment(att.id)" title="删除">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 评论区域 -->
      <div class="content-section">
        <h3 class="section-title">评论 ({{ comments.length }})</h3>
        <!-- 评论列表 -->
        <div v-if="comments.length === 0" class="empty-section">暂无评论</div>
        <div v-else class="comment-list">
          <div v-for="(comment, idx) in comments" :key="idx" class="comment-item">
            <div class="comment-header">
              <span class="comment-author">{{ comment.author_name || '用户' }}</span>
              <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            </div>
            <div class="comment-content" v-html="renderMarkdown(comment.content)"></div>
            <div class="comment-actions" v-if="comment.id">
              <el-button text size="small" @click="startEditComment(comment)">编辑</el-button>
              <el-button text size="small" type="danger" @click="deleteComment(comment.id)">删除</el-button>
            </div>
            <!-- 内联编辑 -->
            <div v-if="editingCommentId === comment.id" class="comment-edit">
              <el-input v-model="editCommentText" type="textarea" :rows="2" size="small" />
              <div class="comment-edit-actions">
                <el-button size="small" type="primary" text @click="saveCommentEdit(comment)">保存</el-button>
                <el-button size="small" text @click="editingCommentId = null">取消</el-button>
              </div>
            </div>
          </div>
        </div>
        <!-- 新建评论 -->
        <div class="new-comment">
          <el-input
            v-model="newCommentText"
            type="textarea"
            :rows="2"
            placeholder="添加评论..."
            size="small"
          />
          <div class="new-comment-actions">
            <el-button size="small" type="primary" :disabled="!newCommentText.trim()" @click="submitComment">
              发表评论
            </el-button>
          </div>
        </div>
      </div>
    </template>

    <!-- 执行用例弹窗 -->
    <el-dialog v-model="executeDialogVisible" title="执行用例" width="480px">
      <el-form label-position="top">
        <el-form-item label="执行结果" required>
          <el-select v-model="executeForm.status" placeholder="请选择执行结果" style="width:100%">
            <el-option label="通过 (Pass)" value="pass" />
            <el-option label="失败 (Fail)" value="fail" />
            <el-option label="阻塞 (Blocked)" value="blocked" />
            <el-option label="跳过 (Skip)" value="skip" />
          </el-select>
        </el-form-item>
        <el-form-item label="实际结果">
          <el-input
            v-model="executeForm.actual_result"
            type="textarea"
            :rows="4"
            placeholder="描述实际执行结果..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!executeForm.status" :loading="executing" @click="handleExecute">
          提交执行结果
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Upload, Document, Download, Delete, WarningFilled } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'
import { useMarkdownRenderer } from '@/composables/useMarkdownRenderer'
import StatusTag from '@/components/aitest/common/StatusTag.vue'
import PriorityBadge from '@/components/aitest/common/PriorityBadge.vue'
import type { TestCase, CaseAttachment, CaseComment, TestCaseExecution, CaseReviewSummary } from '@/types/aitest'
import client from '@/api/client'

const { render: renderMarkdown } = useMarkdownRenderer()
const route = useRoute()
const router = useRouter()

const caseId = computed(() => Number(route.params.id))
const loading = ref(false)
const error = ref('')
const testCase = ref<TestCase>({
  id: 0, project_id: null, version_id: null, module: null, name: '',
  description: null, priority: 'p2', precondition: null, test_steps: null,
  expected_result: null, status: 'draft', test_type: 'functional', source: 'manual',
  tags: null, created_by: 0, created_at: null, updated_at: null,
})
const attachments = ref<CaseAttachment[]>([])
const comments = ref<CaseComment[]>([])
const newCommentText = ref('')
const editingCommentId = ref<number | null>(null)
const editCommentText = ref('')

// ==================== 用例执行 ====================

const executions = ref<TestCaseExecution[]>([])
const executeDialogVisible = ref(false)
const executing = ref(false)
const executeForm = ref({ status: '', actual_result: '' })

// ==================== 评审历史 ====================

const reviewHistory = ref<CaseReviewSummary[]>([])

function reviewStatusTag(status: string): string {
  const map: Record<string, string> = { pending: 'info', passed: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

function reviewStatusLabel(status: string): string {
  const map: Record<string, string> = { pending: '待评审', passed: '已通过', rejected: '已驳回' }
  return map[status] || status
}

/** 执行结果对应的 el-tag 类型 */
function executionTagType(status: string): string {
  const map: Record<string, string> = { pass: 'success', fail: 'danger', blocked: 'warning', skip: 'info' }
  return map[status] || 'info'
}

/** 执行结果中文标签 */
function executionLabel(status: string): string {
  const map: Record<string, string> = { pass: '通过', fail: '失败', blocked: '阻塞', skip: '跳过' }
  return map[status] || status
}

/** 用例状态中文标签 */
function statusLabel(status: string): string {
  const map: Record<string, string> = { draft: '草稿', active: '已启用', deprecated: '已废弃' }
  return map[status] || status
}

const uploadUrl = computed(() => `${(client.defaults as any).baseURL || ''}/v1/cases/${caseId.value}/attachments`)
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

const typeLabel = computed(() => {
  const map: Record<string, string> = { functional: '功能测试', api: '接口测试', ui: 'UI 测试', app: '应用测试' }
  return map[testCase.value.test_type] || testCase.value.test_type
})
const sourceLabel = computed(() => {
  const map: Record<string, string> = { manual: '手动', auto: '自动生成', imported: '导入', 'ai-generated': 'AI 生成' }
  return map[testCase.value.source || ''] || testCase.value.source
})

function formatTime(time: string | null | undefined): string {
  if (!time) return '—'
  return new Date(time).toLocaleDateString('zh-CN')
}

function formatSize(bytes?: number): string {
  if (!bytes) return ''
  return bytes < 1024 ? `${bytes} B` : `${(bytes / 1024).toFixed(1)} KB`
}

async function loadTestCase() {
  loading.value = true
  error.value = ''
  try {
    const res = await aitestApi.getTestCase(caseId.value)
    testCase.value = res.data
    await Promise.all([loadAttachments(), loadComments(), loadExecutions(), loadReviewHistory()])
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadAttachments() {
  try {
    const res = await aitestApi.listAttachments(caseId.value)
    attachments.value = res.data || []
  } catch { attachments.value = [] }
}

async function loadComments() {
  try {
    const res = await aitestApi.listComments(caseId.value)
    comments.value = res.data || []
  } catch { comments.value = [] }
}

async function loadExecutions() {
  try {
    const res = await aitestApi.listTestCaseExecutions(caseId.value)
    executions.value = res.data || []
  } catch { executions.value = [] }
}

async function loadReviewHistory() {
  try {
    const res = await aitestApi.getCaseReviews(caseId.value)
    reviewHistory.value = res.data || []
  } catch { reviewHistory.value = [] }
}

async function handleExecute() {
  if (!executeForm.value.status) return
  executing.value = true
  try {
    await aitestApi.executeTestCase(caseId.value, {
      status: executeForm.value.status as any,
      actual_result: executeForm.value.actual_result || undefined,
    })
    ElMessage.success('执行结果已记录')
    executeDialogVisible.value = false
    executeForm.value = { status: '', actual_result: '' }
    await loadExecutions()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '执行失败')
  } finally {
    executing.value = false
  }
}

function onUploadSuccess() {
  ElMessage.success('上传成功')
  loadAttachments()
}
function onUploadError() { ElMessage.error('上传失败') }

async function downloadAttachment(attId: number) {
  window.open(aitestApi.getAttachmentDownloadUrl(attId), '_blank')
}

async function deleteAttachment(attId: number) {
  try {
    await aitestApi.deleteAttachment(attId)
    ElMessage.success('已删除')
    loadAttachments()
  } catch { ElMessage.error('删除失败') }
}

async function submitComment() {
  if (!newCommentText.value.trim()) return
  try {
    await aitestApi.createComment(caseId.value, { content: newCommentText.value })
    newCommentText.value = ''
    ElMessage.success('评论已发表')
    loadComments()
  } catch { ElMessage.error('发表评论失败') }
}

function startEditComment(comment: CaseComment) {
  editingCommentId.value = comment.id
  editCommentText.value = comment.content
}

async function saveCommentEdit(comment: CaseComment) {
  if (!comment.id) return
  try {
    await aitestApi.updateComment(comment.id, { content: editCommentText.value })
    editingCommentId.value = null
    ElMessage.success('已更新')
    loadComments()
  } catch { ElMessage.error('更新失败') }
}

async function deleteComment(commentId: number) {
  try {
    await aitestApi.deleteComment(commentId)
    ElMessage.success('已删除')
    loadComments()
  } catch { ElMessage.error('删除失败') }
}

function handleEdit() {
  router.push(`/modules/aitest/testcases/${caseId.value}/edit`)
}

onMounted(loadTestCase)
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
.info-bar { display: flex; align-items: center; gap: 32px; padding: 12px 20px; background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.info-item { display: flex; align-items: center; gap: 6px; }
.info-label { font-size: 12px; color: #7A6855; }
.info-value { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); }

/* 内容卡片 */
.content-section { background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.section-title { font-size: 15px; font-weight: 600; color: var(--text, #3D2E1F); margin: 0 0 12px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-header .section-title { margin-bottom: 0; }
.content-body { font-size: 14px; line-height: 1.7; color: var(--text-secondary, #5C4A38); }
.content-body :deep(pre) { background: #1e1e1e; border-radius: 8px; padding: 12px; overflow-x: auto; margin: 8px 0; }
.content-body :deep(code) { font-size: 13px; }
.content-body :deep(p) { margin: 4px 0; }
.content-body :deep(ul), .content-body :deep(ol) { padding-left: 20px; margin: 4px 0; }
.content-body :deep(table) { border-collapse: collapse; width: 100%; font-size: 13px; margin: 8px 0; }
.content-body :deep(th), .content-body :deep(td) { border: 1px solid rgba(180,150,120,0.2); padding: 6px 10px; }
.empty-section { font-size: 13px; color: var(--text-muted, #8B7355); padding: 8px 0; }
.tags-row { display: flex; flex-wrap: wrap; }

/* 附件 */
.attachment-list { display: flex; flex-direction: column; gap: 6px; }
.attachment-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; background: var(--bg, #FBF7F0); }
.attachment-item:hover { background: rgba(198,123,92,0.04); }
.att-info { flex: 1; display: flex; flex-direction: column; }
.att-name { font-size: 13px; color: var(--text, #3D2E1F); }
.att-size { font-size: 11px; color: var(--text-muted, #8B7355); }

/* 评论 */
.comment-list { display: flex; flex-direction: column; gap: 8px; }
.comment-item { padding: 12px; border-radius: 8px; background: var(--bg, #FBF7F0); }
.comment-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.comment-author { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); }
.comment-time { font-size: 11px; color: var(--text-muted, #8B7355); }
.comment-content { font-size: 14px; line-height: 1.6; color: var(--text-secondary, #5C4A38); }
.comment-actions { display: flex; gap: 8px; margin-top: 4px; }
.comment-edit { margin-top: 8px; }
.comment-edit-actions { display: flex; gap: 8px; margin-top: 4px; }
.new-comment { margin-top: 12px; }
.new-comment-actions { display: flex; gap: 8px; margin-top: 8px; }

/* 评审历史链接 */
.review-link { color: var(--primary, #C67B5C); text-decoration: none; font-weight: 500; }
.review-link:hover { color: var(--primary-light, #D49472); text-decoration: underline; }

/* 用例执行 */
.execution-list { display: flex; flex-direction: column; gap: 6px; }
.execution-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 8px; background: var(--bg, #FBF7F0); }
.execution-item:hover { background: rgba(198,123,92,0.04); }
.exec-actual { flex: 1; font-size: 13px; color: var(--text-secondary, #5C4A38); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.exec-meta { font-size: 11px; color: var(--text-muted, #8B7355); white-space: nowrap; }
</style>
