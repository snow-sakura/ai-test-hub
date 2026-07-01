<template>
  <div class="page-wrap">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrap">
      <el-icon class="is-loading" :size="20"><Loading /></el-icon>
      <span class="loading-text">加载中...</span>
    </div>

    <!-- 错误状态 -->
    <el-result v-else-if="error" icon="error" title="加载失败" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="loadData">重试</el-button>
        <el-button @click="router.push('/modules/aitest/reviews')">返回列表</el-button>
      </template>
    </el-result>

    <template v-else-if="review">
      <!-- 返回导航 -->
      <div class="back-nav">
        <span class="back-arrow" @click="router.push('/modules/aitest/reviews')">←</span>
        <span class="breadcrumb-sep">/</span>
        <span class="breadcrumb-link" @click="router.push('/modules/aitest/reviews')">评审列表</span>
        <span class="breadcrumb-sep">/</span>
        <span class="breadcrumb-current">{{ review.name }}</span>
      </div>

      <!-- 头部 -->
      <div class="detail-header">
        <div class="header-left">
          <h1 class="page-title">{{ review.name }}</h1>
          <StatusTag :status="review.status" />
          <PriorityBadge v-if="(review as any).priority" :priority="(review as any).priority" />
        </div>
        <div class="header-actions" v-if="review.status === 'pending'">
          <el-button size="small" @click="handleEdit">编辑</el-button>
          <el-button size="small" type="danger" ghost @click="handleCancel">取消评审</el-button>
        </div>
      </div>

      <!-- 评审信息 -->
      <div class="info-bar">
        <div class="info-item">
          <span class="info-label">项目</span>
          <span class="info-value">{{ review.project_name || '—' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">创建人</span>
          <span class="info-value">{{ (review as any).creator_name || '—' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">用例数</span>
          <span class="info-value">{{ reviewCases.length }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">创建时间</span>
          <span class="info-value">{{ formatTime(review.created_at) }}</span>
        </div>
      </div>

      <!-- 左右两栏 -->
      <div class="detail-columns">
        <!-- 左栏：评审用例列表 -->
        <div class="left-column">
          <h3 class="section-title">评审用例</h3>
          <div class="table-card">
            <el-table :data="reviewCases" stripe style="width:100%" size="small" @row-click="toggleExpand">
              <el-table-column label="序号" width="60" type="index" />
              <el-table-column label="用例标题" min-width="160">
                <template #default="{ row, $index }">
                  <span class="case-title-wrapper" @click.stop="toggleExpand(row, $index)">
                    <router-link
                      :to="`/modules/aitest/testcases/${row.case_id}`"
                      class="case-title-link"
                      @click.stop
                    >
                      {{ row.case_title || row.case_id }}
                    </router-link>
                    <span class="expand-icon" @click.stop="toggleExpand(row, $index)">{{ expandedIndex === $index ? '▲' : '▼' }}</span>
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="优先级" width="80">
                <template #default="{ row }">
                  <PriorityBadge v-if="row.case_priority" :priority="row.case_priority" />
                  <span v-else style="color:#8B7355">—</span>
                </template>
              </el-table-column>
              <el-table-column label="执行结果" width="90" align="center">
                <template #default="{ row }">
                  <el-tag
                    v-if="row.latest_execution_status"
                    :type="executionTagType(row.latest_execution_status)"
                    size="small"
                  >
                    {{ executionTagLabel(row.latest_execution_status) }}
                  </el-tag>
                  <span v-else style="color:#8B7355;font-size:12px;">未执行</span>
                </template>
              </el-table-column>
              <el-table-column label="评审意见" min-width="140">
                <template #default="{ row, $index }">
                  <div class="comment-cell">
                    <el-input
                      v-if="editCommentIndex === $index"
                      v-model="inlineComment"
                      type="textarea"
                      :rows="2"
                      placeholder="输入评审意见..."
                      size="small"
                      @keydown.escape="editCommentIndex = null"
                      @click.stop
                    />
                    <span
                      v-else
                      class="comment-text editable"
                      @click.stop="startEditComment(row, $index)"
                      title="点击编辑评审意见"
                    >{{ row.comment || '点击添加意见' }}</span>
                    <div v-if="editCommentIndex === $index" class="comment-edit-actions" @click.stop>
                      <el-button size="small" text type="primary" @click="saveComment(row)">保存</el-button>
                      <el-button size="small" text @click="editCommentIndex = null">取消</el-button>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <StatusTag :status="row.status || 'pending'" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="170" fixed="right">
                <template #default="{ row }">
                  <div class="case-actions" v-if="review.status === 'pending'">
                    <el-button
                      size="small" type="success" text
                      :disabled="row.status === 'approved'"
                      @click.stop="handleReviewCase(row, 'approved')"
                    >通过</el-button>
                    <el-button
                      size="small" type="danger" text
                      :disabled="row.status === 'rejected'"
                      @click.stop="handleReviewCase(row, 'rejected')"
                    >拒绝</el-button>
                  </div>
                </template>
              </el-table-column>

              <!-- 展开行：用例详情 -->
              <template #empty>
                <div style="text-align:center;padding:32px;color:#8B7355">暂无关联用例</div>
              </template>
            </el-table>

            <!-- 展开的用例详情面板 -->
            <div v-if="expandedCase" class="expanded-case-panel">
              <div class="case-detail-panel">
                <div class="detail-section" v-if="expandedCase.preconditions">
                  <span class="detail-label">前置条件</span>
                  <p class="detail-content">{{ expandedCase.preconditions }}</p>
                </div>
                <div class="detail-section" v-if="expandedCase.steps">
                  <span class="detail-label">测试步骤</span>
                  <p class="detail-content" style="white-space:pre-wrap">{{ expandedCase.steps }}</p>
                </div>
                <div class="detail-section" v-if="expandedCase.expected_results">
                  <span class="detail-label">预期结果</span>
                  <p class="detail-content">{{ expandedCase.expected_results }}</p>
                </div>
                <div v-if="!expandedCase.preconditions && !expandedCase.steps && !expandedCase.expected_results" class="detail-empty">
                  暂无详细描述
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右栏：评审进度 -->
        <div class="right-column">
          <h3 class="section-title">评审进度</h3>
          <el-card shadow="never" class="progress-card">
            <div class="overall-progress">
              <span class="progress-title">整体评审进度</span>
              <el-progress
                :percentage="reviewProgress"
                :stroke-width="10"
                color="#C67B5C"
              />
            </div>
            <div class="progress-stats">
              已评审：{{ reviewedCount }} / {{ reviewCases.length }}
            </div>
          </el-card>

          <div class="bottom-actions">
            <template v-if="review.status === 'pending'">
              <el-button type="success" size="large" @click="handleApprove" style="width:100%">
                通过评审
              </el-button>
              <el-button type="danger" size="large" @click="handleReject" style="width:100%">
                拒绝评审
              </el-button>
            </template>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import StatusTag from '@/components/aitest/common/StatusTag.vue'
import PriorityBadge from '@/components/aitest/common/PriorityBadge.vue'
import { useReviewStore, type ReviewCaseItem } from '@/stores/aitest/review'
import { aitestApi } from '@/api/aitest'

const route = useRoute()
const router = useRouter()
const store = useReviewStore()

const review = computed(() => store.currentReview)
const reviewCases = ref<ReviewCaseItem[]>([])
const expandedIndex = ref<number | null>(null)
const expandedCase = computed(() => expandedIndex.value !== null ? reviewCases.value[expandedIndex.value] : null)
const editCommentIndex = ref<number | null>(null)
const inlineComment = ref('')
const loading = ref(false)
const error = ref('')

const reviewedCount = computed(() =>
  reviewCases.value.filter(tc => tc.status === 'approved' || tc.status === 'rejected').length
)
const reviewProgress = computed(() => {
  if (reviewCases.value.length === 0) return 0
  return Math.round((reviewedCount.value / reviewCases.value.length) * 100)
})

function toggleExpand(_row: any, index: number) {
  expandedIndex.value = expandedIndex.value === index ? null : index
}

function startEditComment(tc: ReviewCaseItem, index: number) {
  editCommentIndex.value = index
  inlineComment.value = tc.comment || ''
}

async function handleReviewCase(tc: ReviewCaseItem, status: 'approved' | 'rejected') {
  const comment = editCommentIndex.value !== null ? inlineComment.value : tc.comment
  try {
    const reviewId = Number(route.params.id)
    await aitestApi.updateReviewCase(reviewId, Number(tc.case_id), {
      status,
      comment: comment || '',
    })
    tc.status = status
    tc.comment = comment || ''
    editCommentIndex.value = null
    inlineComment.value = ''
    ElMessage.success(status === 'approved' ? '已批准该用例' : '已拒绝该用例')
    await store.fetchReview(reviewId)
  } catch (e) {
    console.error('更新评审状态失败:', e)
    ElMessage.error('操作失败')
  }
}

async function saveComment(tc: ReviewCaseItem) {
  try {
    const reviewId = Number(route.params.id)
    await aitestApi.updateReviewCase(reviewId, Number(tc.case_id), {
      status: tc.status || 'pending',
      comment: inlineComment.value,
    })
    tc.comment = inlineComment.value
    editCommentIndex.value = null
    ElMessage.success('评审意见已保存')
  } catch (e) {
    console.error('保存评审意见失败:', e)
    ElMessage.error('保存失败')
  }
}

function handleEdit() {
  router.push(`/modules/aitest/reviews/create?edit=${route.params.id}`)
}

async function handleCancel() {
  if (!review.value) return
  try {
    await store.updateReview(review.value.id, { status: 'cancelled' } as any)
    ElMessage.success('已取消评审')
    await loadData()
  } catch (e) {
    console.error('取消评审失败:', e)
    ElMessage.error('操作失败')
  }
}

async function handleApprove() {
  if (!review.value) return
  try {
    await aitestApi.approveReview(review.value.id, { action: 'pass' })
    ElMessage.success('评审已通过')
    await loadData()
  } catch (e: any) {
    console.error('通过评审失败:', e)
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

async function handleReject() {
  if (!review.value) return
  try {
    await aitestApi.approveReview(review.value.id, {
      action: 'reject',
      conclusion: '已拒绝',
    })
    ElMessage.success('评审已拒绝')
    await loadData()
  } catch (e: any) {
    console.error('拒绝评审失败:', e)
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

function executionTagType(status: string): string {
  const map: Record<string, string> = { pass: 'success', fail: 'danger', blocked: 'warning', skip: 'info' }
  return map[status] || 'info'
}

function executionTagLabel(status: string): string {
  const map: Record<string, string> = { pass: '通过', fail: '失败', blocked: '阻塞', skip: '跳过' }
  return map[status] || status
}

function formatTime(time: string | null | undefined): string {
  if (!time) return '—'
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const id = Number(route.params.id)
    await store.fetchReview(id)
    // 获取评审关联用例（使用专用 API）
    try {
      const res = await aitestApi.listReviewCases(id)
      reviewCases.value = (res.data || []).map((rc: any) => ({
        id: String(rc.id),
        case_id: String(rc.id),
        case_title: rc.name,
        case_priority: rc.priority,
        preconditions: rc.precondition || '',
        steps: rc.test_steps || '',
        expected_results: rc.expected_result || '',
        status: rc.review_status || 'pending',
        comment: rc.review_comment || '',
        latest_execution_status: rc.latest_execution_status || null,
      }))
    } catch {
      reviewCases.value = []
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-wrap { max-width: 1200px; margin: 0 auto; padding: 32px 24px 64px; }
.loading-wrap { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 64px 0; }
.loading-text { font-size: 14px; color: #8B7355; }
.back-nav { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #7A6855; margin-bottom: 20px; }
.back-arrow { font-size: 16px; cursor: pointer; transition: color 0.15s; color: var(--primary, #C67B5C); }
.back-arrow:hover { color: var(--primary-light, #D49472); }
.breadcrumb-link { cursor: pointer; transition: color 0.15s; }
.breadcrumb-link:hover { color: var(--primary, #C67B5C); }
.breadcrumb-sep { color: rgba(180,150,120,0.3); }
.breadcrumb-current { color: var(--text, #3D2E1F); font-weight: 500; }
.detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text, #3D2E1F); letter-spacing: -0.02em; margin: 0; }
.header-actions { display: flex; gap: 8px; }
.info-bar { display: flex; align-items: center; gap: 32px; padding: 16px 20px; background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 10px; margin-bottom: 24px; flex-wrap: wrap; }
.info-item { display: flex; align-items: center; gap: 8px; }
.info-label { font-size: 12px; color: #7A6855; }
.info-value { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); }
.detail-columns { display: flex; gap: 20px; align-items: flex-start; }
.left-column { flex: 3; min-width: 0; }
.right-column { flex: 2; min-width: 0; }
.section-title { font-size: 16px; font-weight: 600; color: var(--text, #3D2E1F); margin: 0 0 12px; }
.table-card { background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; overflow: hidden; }
.case-title-wrapper { display: inline-flex; align-items: center; gap: 4px; }
.case-title-link { color: var(--primary, #C67B5C); font-weight: 500; font-size: 13px; text-decoration: none; cursor: pointer; }
.case-title-link:hover { color: var(--primary-light, #D49472); text-decoration: underline; }
.expand-icon { font-size: 10px; color: #bbb5aa; cursor: pointer; }
.expand-icon { font-size: 10px; color: #bbb5aa; }
.comment-cell { min-width: 120px; }
.comment-text { font-size: 13px; color: var(--text-secondary, #5C4A38); }
.comment-text.editable { cursor: pointer; border-bottom: 1px dashed transparent; transition: border-color 0.15s; }
.comment-text.editable:hover { border-color: var(--primary, #C67B5C); }
.comment-edit-actions { display: flex; gap: 4px; margin-top: 4px; }
.case-actions { display: flex; gap: 4px; justify-content: center; }
.expanded-case-panel { border-top: 1px dashed rgba(180,150,120,0.2); background: rgba(198,123,92,0.03); }
.case-detail-panel { padding: 12px 24px 16px; }
.detail-section { margin-bottom: 10px; }
.detail-label { font-size: 11px; font-weight: 600; color: #7A6855; text-transform: uppercase; letter-spacing: 0.5px; }
.detail-content { margin: 4px 0 0; font-size: 13px; line-height: 1.6; color: var(--text, #3D2E1F); }
.detail-empty { font-size: 12px; color: #bbb5aa; padding: 8px 0; }
.progress-card { margin-bottom: 12px; }
.overall-progress { margin-bottom: 8px; }
.progress-title { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); display: block; margin-bottom: 8px; }
.progress-stats { font-size: 12px; color: #7A6855; }
.bottom-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--border, rgba(180,150,120,0.12)); }

@media (max-width: 768px) {
  .page-wrap { padding: 16px 12px 48px; }
  .detail-header { flex-direction: column; align-items: flex-start; gap: 12px; }
  .info-bar { flex-wrap: wrap; gap: 12px; }
  .detail-columns { flex-direction: column; }
  .left-column, .right-column { width: 100%; }
  .bottom-actions { flex-direction: column; align-items: stretch; }
  .case-detail-panel { padding: 12px 16px; }
}
</style>
