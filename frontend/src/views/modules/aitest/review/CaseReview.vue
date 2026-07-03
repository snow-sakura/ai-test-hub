<template>
  <div class="page-wrap">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">用例评审</h2>
        <span class="page-count">共 {{ filteredReviews.length }} 个评审</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建评审</el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">全部评审</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #909399">{{ stats.pending }}</div>
        <div class="stat-label">待评审</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #67C23A">{{ stats.passed }}</div>
        <div class="stat-label">已通过</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #F56C6C">{{ stats.rejected }}</div>
        <div class="stat-label">已驳回</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索评审名称、关联项目..."
        clearable
        class="search-input"
        @input="handleSearch"
      />
      <el-select
        v-model="statusFilter"
        placeholder="状态筛选"
        clearable
        class="filter-select"
        @change="handleSearch"
      >
        <el-option
          v-for="opt in REVIEW_STATUS_OPTIONS"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>
    </div>

    <!-- 评审列表表格 -->
    <el-card shadow="never" class="config-table-card">
      <el-table :data="filteredReviews" v-loading="loading" style="width:100%">
        <el-table-column prop="name" label="评审名称" min-width="180" show-overflow-tooltip align="center" />
        <el-table-column label="关联项目" min-width="150" show-overflow-tooltip align="center">
          <template #default="{ row }">
            {{ row.project_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="评审人" min-width="130" show-overflow-tooltip align="center">
          <template #default="{ row }">
            <div class="avatar-group" v-if="row.assignments && row.assignments.length > 0">
              <el-tooltip
                v-for="(a, i) in row.assignments"
                :key="a.id || i"
                :content="a.username || `用户#${a.user_id}`"
                placement="top"
              >
                <el-avatar :size="28" :style="{ backgroundColor: avatarColor(a.username || `user_${a.user_id}`) }">
                  {{ (a.username || String(a.user_id)).charAt(0) }}
                </el-avatar>
              </el-tooltip>
            </div>
            <span v-else class="no-assignee">—</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag :color="STATUS_COLORS[row.status] || '#909399'" effect="dark" size="small">
              {{ STATUS_LABELS[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="130" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text size="small" type="primary" @click="handleViewDetail(row)">详情</el-button>
            <el-button
              v-if="row.status === 'pending'"
              text size="small" type="success"
              @click="handleApprove(row, 'pass')"
            >通过</el-button>
            <el-button
              v-if="row.status === 'pending'"
              text size="small" type="danger"
              @click="handleReject(row)"
            >驳回</el-button>
            <el-popconfirm title="确定删除该评审？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button text size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无评审" />
        </template>
      </el-table>
    </el-card>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="filteredReviews.length"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        small
      />
    </div>

    <!-- 新建评审弹窗 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建评审"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createFormRules"
        label-width="80px"
        label-position="top"
      >
        <el-form-item label="评审名称" prop="name">
          <el-input
            v-model="createForm.name"
            placeholder="请输入评审名称"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="关联项目" prop="project_id">
          <el-select v-model="createForm.project_id" placeholder="请选择关联项目" style="width: 100%">
            <el-option
              v-for="p in projects"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="评审人">
          <el-select
            v-model="createForm.reviewerIds"
            multiple
            placeholder="请选择评审人"
            style="width: 100%"
            filterable
            @visible-change="(visible: boolean) => visible && loadAllUsers()"
          >
            <el-option
              v-for="u in allUsers"
              :key="u.id"
              :label="`${u.username}${u.department ? ' · ' + u.department : ''}${u.position ? ' - ' + u.position : ''}`"
              :value="u.id"
            >
              <div class="user-option-item">
                <span class="user-option-name">{{ u.username }}</span>
                <span class="user-option-dept" v-if="u.department || u.position">
                  {{ u.department || '' }}{{ u.department && u.position ? ' - ' : '' }}{{ u.position || '' }}
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="关联用例">
          <div style="overflow-x:auto;width:100%">
          <el-table
            :data="projectCases"
            ref="caseTableRef"
            @selection-change="(rows: any[]) => { createForm.caseIds = rows.map((r: any) => r.id) }"
            max-height="280"
            size="small"
            border
            style="min-width:900px"
          >
            <el-table-column type="selection" width="42" />
            <el-table-column type="index" label="序号" width="55" align="center" />
            <el-table-column prop="name" label="用例标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="module" label="所属模块" min-width="120" />
            <el-table-column label="优先级" min-width="90" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.priority === 'p0' ? 'danger' : row.priority === 'p1' ? 'warning' : 'info'"
                  size="small"
                  effect="plain"
                >
                  {{ row.priority === 'p0' ? 'P0（最高）' : row.priority === 'p1' ? 'P1（高）' : row.priority === 'p2' ? 'P2（中）' : row.priority === 'p3' ? 'P3（低）' : row.priority }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="用例类型" min-width="100" align="center">
              <template #default="{ row }">
                {{ row.test_type === 'functional' ? '功能测试' : row.test_type === 'api' ? '接口测试' : row.test_type === 'ui' ? 'UI 测试' : row.test_type === 'app' ? '应用测试' : row.test_type || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="状态" min-width="90" align="center">
              <template #default="{ row }">
                <el-tag
                  size="small"
                  :type="row.status === 'active' ? 'success' : row.status === 'deprecated' ? 'warning' : 'info'"
                  effect="plain"
                >
                  {{ row.status === 'active' ? '已启用' : row.status === 'draft' ? '草稿' : '已废弃' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="执行结果" min-width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  v-if="(row as any)?.latest_execution_status"
                  size="small"
                  effect="plain"
                  :type="((row as any).latest_execution_status === 'pass' ? 'success' : (row as any).latest_execution_status === 'fail' ? 'danger' : (row as any).latest_execution_status === 'blocked' ? 'warning' : 'info')"
                >
                  {{ (row as any).latest_execution_status === 'pass' ? '通过' : (row as any).latest_execution_status === 'fail' ? '失败' : (row as any).latest_execution_status === 'blocked' ? '阻塞' : '跳过' }}
                </el-tag>
                <span v-else style="color:#999;font-size:12px;">未执行</span>
              </template>
            </el-table-column>
          </el-table>
          </div>
          <div v-if="!createForm.project_id" style="color:#999;font-size:13px;padding:4px 0">
            请先选择关联项目以加载用例
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createSubmitting" @click="handleCreateSubmit">创建</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="detailReview?.name || '评审详情'"
      width="800px"
    >
      <template v-if="detailReview">
        <el-descriptions :column="2" border size="small" class="detail-descriptions">
          <el-descriptions-item label="评审名称">{{ detailReview.name }}</el-descriptions-item>
          <el-descriptions-item label="关联项目">{{ detailReview.project_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :color="STATUS_COLORS[detailReview.status] || '#909399'" effect="dark" size="small">
              {{ STATUS_LABELS[detailReview.status] || detailReview.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建者">{{ detailReview.creator_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(detailReview.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="评审人" v-if="detailReview.assignments && detailReview.assignments.length > 0">
            <div class="avatar-group">
              <el-tooltip
                v-for="(a, i) in detailReview.assignments"
                :key="a.id || i"
                :content="a.username || `用户#${a.user_id}`"
                placement="top"
              >
                <el-avatar :size="28" :style="{ backgroundColor: avatarColor(a.username || `user_${a.user_id}`) }">
                  {{ (a.username || String(a.user_id)).charAt(0) }}
                </el-avatar>
              </el-tooltip>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <div class="cases-section" v-if="detailReview.cases && detailReview.cases.length > 0">
          <h4 class="section-title">用例列表（{{ detailReview.cases.length }} 条）</h4>
          <el-card shadow="never" class="config-table-card">
          <div style="overflow-x:auto">
          <el-table :data="detailReview.cases" size="small" max-height="360" style="min-width:900px">
            <el-table-column type="index" label="序号" width="55" align="center" />
            <el-table-column label="用例标题" min-width="200" show-overflow-tooltip>
              <template #default="{ row: caseItem }">
                <template v-if="typeof caseItem === 'number'">
                  <router-link :to="`/modules/aitest/testcases/${caseItem}`" class="case-link">
                    用例 #{{ caseItem }}
                  </router-link>
                </template>
                <template v-else-if="(caseItem as any)?.id">
                  <router-link :to="`/modules/aitest/testcases/${(caseItem as any).id}`" class="case-link">
                    {{ (caseItem as any).title || (caseItem as any).name || `用例 #${(caseItem as any).id}` }}
                  </router-link>
                </template>
                <span v-else>{{ caseItem }}</span>
              </template>
            </el-table-column>
            <el-table-column label="所属模块" min-width="120">
              <template #default="{ row: caseItem }">
                {{ (caseItem as any)?.module || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="优先级" min-width="90" align="center">
              <template #default="{ row: caseItem }">
                <el-tag
                  v-if="(caseItem as any)?.priority"
                  :type="(caseItem as any).priority === 'p0' ? 'danger' : (caseItem as any).priority === 'p1' ? 'warning' : 'info'"
                  size="small"
                  effect="plain"
                >
                  {{ (caseItem as any).priority === 'p0' ? 'P0（最高）' : (caseItem as any).priority === 'p1' ? 'P1（高）' : (caseItem as any).priority === 'p2' ? 'P2（中）' : (caseItem as any).priority === 'p3' ? 'P3（低）' : (caseItem as any).priority }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" min-width="90" align="center">
              <template #default="{ row: caseItem }">
                <template v-if="typeof caseItem === 'string'">
                  <el-tag size="small" type="info">{{ caseItem }}</el-tag>
                </template>
                <template v-else>
                  <el-tag
                    size="small"
                    effect="plain"
                    :type="((caseItem as any)?.review_status || (caseItem as any)?.status) === 'approved' ? 'success' : ((caseItem as any)?.review_status || (caseItem as any)?.status) === 'rejected' ? 'danger' : 'info'"
                  >
                    {{ (caseItem as any)?.review_status === 'approved' ? '已通过' : (caseItem as any)?.review_status === 'rejected' ? '已驳回' : (caseItem as any)?.status === 'active' ? '已启用' : (caseItem as any)?.status === 'draft' ? '草稿' : '待评审' }}
                  </el-tag>
                </template>
              </template>
            </el-table-column>
            <el-table-column label="执行结果" min-width="100" align="center">
              <template #default="{ row: caseItem }">
                <el-tag
                  v-if="(caseItem as any)?.latest_execution_status"
                  size="small"
                  effect="plain"
                  :type="((caseItem as any).latest_execution_status === 'pass' ? 'success' : (caseItem as any).latest_execution_status === 'fail' ? 'danger' : (caseItem as any).latest_execution_status === 'blocked' ? 'warning' : 'info')"
                >
                  {{ (caseItem as any).latest_execution_status === 'pass' ? '通过' : (caseItem as any).latest_execution_status === 'fail' ? '失败' : (caseItem as any).latest_execution_status === 'blocked' ? '阻塞' : '跳过' }}
                </el-tag>
                <el-tag v-else size="small" type="info" effect="plain">未执行</el-tag>
              </template>
            </el-table-column>
          </el-table>
          </div>
          </el-card>
        </div>

        <div class="conclusion-section" v-if="detailReview.conclusion">
          <h4 class="section-title">评审结论</h4>
          <el-input :model-value="detailReview.conclusion" type="textarea" :rows="4" readonly />
        </div>
      </template>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 驳回弹窗 -->
    <el-dialog
      v-model="rejectDialogVisible"
      title="驳回评审"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form ref="rejectFormRef" :model="rejectForm" :rules="rejectFormRules" label-position="top">
        <el-form-item label="驳回原因（必填）" prop="conclusion">
          <el-input
            v-model="rejectForm.conclusion"
            type="textarea"
            :rows="4"
            placeholder="请填写驳回原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejectSubmitting" @click="handleRejectSubmit">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'
import type { TestCase, TestProject, TestReview } from '@/types/aitest'
import { REVIEW_STATUS_OPTIONS } from '@/types/aitest'
import type { AdminUserInfo } from '@/types/admin'
import type { FormInstance } from 'element-plus'

// 头像颜色工具
const AVATAR_COLORS = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#C67B5C', '#909399']

function avatarColor(name: string): string {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}

// 状态映射
const STATUS_COLORS: Record<string, string> = {
  pending: '#909399',
  passed: '#67C23A',
  rejected: '#F56C6C',
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待评审',
  passed: '已通过',
  rejected: '已驳回',
}

// 数据
const loading = ref(false)
const reviews = ref<TestReview[]>([])
const projects = ref<TestProject[]>([])
const searchKeyword = ref('')
const statusFilter = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)

// 统计
const stats = computed(() => {
  const total = reviews.value.length
  const pending = reviews.value.filter(r => r.status === 'pending').length
  const passed = reviews.value.filter(r => r.status === 'passed').length
  const rejected = reviews.value.filter(r => r.status === 'rejected').length
  return { total, pending, passed, rejected }
})

// 筛选 + 分页
const filteredReviews = computed(() => {
  let list = reviews.value
  if (statusFilter.value) {
    list = list.filter(r => r.status === statusFilter.value)
  }
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  return list.slice(start, start + pageSize.value)
})

// 创建弹窗
interface CreateForm {
  name: string
  project_id: number | undefined
  reviewerIds: number[]
  caseIds: number[]
}

const createDialogVisible = ref(false)
const createSubmitting = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = ref<CreateForm>({
  name: '',
  project_id: undefined,
  reviewerIds: [],
  caseIds: [],
})

const caseTableRef = ref()

// 用户列表（评审人选择用）
const allUsers = ref<AdminUserInfo[]>([])

async function loadAllUsers() {
  if (allUsers.value.length > 0) return
  try {
    const res = await aitestApi.listUsers()
    allUsers.value = res.data || []
  } catch { /* ignore */ }
}
const createFormRules = {
  name: [{ required: true, message: '请输入评审名称', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择关联项目', trigger: 'change' }],
}

// 项目用例列表（创建弹窗中选择用例用）
const projectCases = ref<TestCase[]>([])

// 选择项目后自动加载该项目下的用例
watch(() => createForm.value.project_id, async (newVal) => {
  createForm.value.caseIds = []
  if (!newVal) {
    projectCases.value = []
    return
  }
  try {
    const res = await aitestApi.listTestCases({ project_id: newVal })
    projectCases.value = res.data || []
  } catch {
    projectCases.value = []
  }
})

// 详情弹窗
const detailDialogVisible = ref(false)
const detailReview = ref<TestReview | null>(null)

// 驳回弹窗
const rejectDialogVisible = ref(false)
const rejectSubmitting = ref(false)
const rejectReviewId = ref<number | null>(null)
const rejectFormRef = ref<FormInstance>()
const rejectForm = ref<{ conclusion: string }>({ conclusion: '' })
const rejectFormRules = {
  conclusion: [{ required: true, message: '请填写驳回原因', trigger: 'blur' }],
}

// 数据加载
async function loadReviews() {
  loading.value = true
  try {
    const params: { search?: string } = {}
    if (searchKeyword.value) params.search = searchKeyword.value
    const res = await aitestApi.listReviews(params)
    reviews.value = res.data || []
    currentPage.value = 1
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载评审列表失败')
  } finally {
    loading.value = false
  }
}

async function loadProjects() {
  try {
    const res = await aitestApi.listProjects({ status: 'active' })
    projects.value = res.data || []
  } catch { /* ignore */ }
}

// 搜索防抖
let searchTimer: ReturnType<typeof setTimeout> | null = null
function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { loadReviews() }, 300)
}

// 新建评审
function handleCreate() {
  createForm.value = { name: '', project_id: undefined, reviewerIds: [], caseIds: [] }
  projectCases.value = []
  createDialogVisible.value = true
  loadAllUsers()
}

async function handleCreateSubmit() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return
  createSubmitting.value = true
  try {
    await aitestApi.createReview({
      project_id: createForm.value.project_id!,
      name: createForm.value.name,
      cases: createForm.value.caseIds.length > 0 ? createForm.value.caseIds : undefined,
      reviewer_ids: createForm.value.reviewerIds.length > 0 ? createForm.value.reviewerIds : undefined,
    })
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    await loadReviews()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  } finally {
    createSubmitting.value = false
  }
}

// 查看详情
async function handleViewDetail(review: TestReview) {
  try {
    const res = await aitestApi.getReview(review.id)
    detailReview.value = res.data
    // 获取用例的完整信息（模块、优先级、执行结果等），替换纯 ID 数据
    const casesRes = await aitestApi.listReviewCases(review.id)
    if (casesRes.data && casesRes.data.length > 0) {
      detailReview.value.cases = casesRes.data
    }
  } catch {
    detailReview.value = review
  }
  detailDialogVisible.value = true
}

// 审批
async function handleApprove(review: TestReview, action: 'pass' | 'reject') {
  try {
    await aitestApi.approveReview(review.id, { action })
    ElMessage.success(action === 'pass' ? '评审已通过' : '已驳回')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    await loadReviews()
  }
}

function handleReject(review: TestReview) {
  rejectReviewId.value = review.id
  rejectForm.value = { conclusion: '' }
  rejectDialogVisible.value = true
}

async function handleRejectSubmit() {
  const valid = await rejectFormRef.value?.validate().catch(() => false)
  if (!valid) return
  rejectSubmitting.value = true
  try {
    await aitestApi.approveReview(rejectReviewId.value!, {
      action: 'reject',
      conclusion: rejectForm.value.conclusion,
    })
    ElMessage.success('已驳回')
    rejectDialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '驳回失败')
  } finally {
    rejectSubmitting.value = false
    await loadReviews()
  }
}

// 删除
async function handleDelete(review: TestReview) {
  try {
    await aitestApi.deleteReview(review.id)
    ElMessage.success('删除成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  } finally {
    await loadReviews()
  }
}

import { formatDateTime } from '@/utils'

// 格式化
function formatTime(time: string): string {
  if (!time) return '—'
  return formatDateTime(time)
}

onMounted(() => {
  loadProjects()
  loadReviews()
})
</script>

<style scoped lang="scss">
.page-wrap {
  margin: 0 auto;
  padding: 24px 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text, #3D2E1F);
  margin: 0;
}

.page-count {
  font-size: 13px;
  color: var(--text-muted, #8B7355);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  padding: 20px 24px;
  background: var(--card-bg, #FFFDF9);
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 10px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text, #3D2E1F);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted, #8B7355);
  margin-top: 2px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
  min-width: 200px;
  max-width: 420px;
}

.filter-select {
  width: 140px;
}

.config-table-card {
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;

  :deep(.el-card__body) {
    padding: 0;
  }
}

/* 详情弹窗描述列表居中 */
.detail-descriptions {
  :deep(.el-descriptions__cell) {
    text-align: center;
  }
}

.avatar-group {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

.no-assignee {
  color: var(--text-muted, #8B7355);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text, #3D2E1F);
  margin: 0 0 12px;
}

.cases-section {
  margin-top: 20px;
}

.conclusion-section {
  margin-top: 20px;
}

/* 用户选项下拉样式 */
.user-option-item {
  display: flex;
  flex-direction: column;
  padding: 2px 0;
}
.user-option-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--text, #3D2E1F);
}
.case-link { color: var(--primary, #C67B5C); text-decoration: none; font-weight: 500; }
.case-link:hover { color: var(--primary-light, #D49472); text-decoration: underline; }

.user-option-dept {
  font-size: 11px;
  color: var(--text-muted, #8B7355);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
