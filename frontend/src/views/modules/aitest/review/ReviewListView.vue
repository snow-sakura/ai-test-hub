<template>
  <!-- 评审列表页面：展示所有用例评审记录，支持项目筛选、搜索和分页 -->
  <div class="page-wrap">
    <!-- 页面头部：标题 + 新建按钮 -->
    <div class="page-header">
      <h1 class="page-title">评审管理</h1>
      <el-button type="primary" :icon="Plus" @click="goToCreate">
        新建评审
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select
        v-model="filterProjectId"
        placeholder="选择项目"
        clearable
        style="width: 140px"
        @change="handleFilterChange"
      >
        <el-option
          v-for="p in projects"
          :key="p.id"
          :label="p.name"
          :value="p.id"
        />
      </el-select>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索评审名称..."
        :prefix-icon="Search"
        clearable
        class="search-input"
        @input="handleSearch"
      />
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-bar">
      <span class="batch-info">已选择 {{ selectedIds.length }} 项</span>
      <el-button size="small" type="danger" @click="handleBatchDelete">
        批量删除
      </el-button>
      <el-button size="small" @click="clearSelection">
        取消选择
      </el-button>
    </div>

    <!-- 评审列表表格 -->
    <el-card shadow="never" class="config-table-card">
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="pagedReviews"
      stripe
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="评审名称" min-width="200" show-overflow-tooltip align="center">
        <template #default="{ row }">
          <router-link :to="`/modules/aitest/reviews/${row.id}`" class="review-name-link">
            {{ row.name }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column label="关联项目" min-width="160" show-overflow-tooltip align="center">
        <template #default="{ row }">
          {{ row.project_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="用例数" min-width="70" align="center">
        <template #default="{ row }">
          {{ (row as any).cases?.length || 0 }}
        </template>
      </el-table-column>
      <el-table-column label="评审人" min-width="120" show-overflow-tooltip align="center">
        <template #default="{ row }">
          {{ row.creator_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" min-width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="reviewStatusType(row.status)" size="small" effect="plain">
            {{ reviewStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="130" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="160" fixed="right" align="center">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click.stop="goToDetail(row)">
            查看
          </el-button>
          <el-button text size="small" type="danger" @click.stop="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
      <!-- 空状态 -->
      <template #empty>
        <el-empty description="暂无评审" />
      </template>
    </el-table>
    </el-card>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'
import type { TestProject, TestReview } from '@/types/aitest'
import { REVIEW_STATUS_OPTIONS } from '@/types/aitest'

const router = useRouter()

// ==================== 筛选与列表状态 ====================

/** 加载中 */
const loading = ref(false)
/** 完整评审列表 */
const reviews = ref<TestReview[]>([])
/** 项目列表（下拉选择器用） */
const projects = ref<TestProject[]>([])
/** 项目筛选 ID */
const filterProjectId = ref<number | undefined>(undefined)
/** 搜索关键词 */
const searchKeyword = ref('')
/** 当前分页 */
const currentPage = ref(1)
/** 每页条数 */
const pageSize = ref(10)

// ==================== 多选 ====================

const selectedIds = ref<number[]>([])
const tableRef = ref<any>(null)

function handleSelectionChange(rows: any[]) {
  selectedIds.value = rows.map((r: any) => r.id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selectedIds.value = []
}

// ==================== 过滤与分页计算 ====================

/** 根据筛选条件过滤后的评审列表 */
const filteredReviews = computed(() => {
  let list = reviews.value
  if (filterProjectId.value) {
    list = list.filter((r) => r.project_id === filterProjectId.value)
  }
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter((r) => r.name.toLowerCase().includes(kw))
  }
  return list
})

/** 总记录数 */
const total = computed(() => filteredReviews.value.length)

/** 当前页可见数据 */
const pagedReviews = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredReviews.value.slice(start, start + pageSize.value)
})

// ==================== 状态工具函数 ====================

/** 根据评审状态返回 el-tag 类型 */
function reviewStatusType(status: string): string {
  const map: Record<string, string> = {
    pending: 'info',
    passed: 'success',
    rejected: 'danger',
  }
  return map[status] || 'info'
}

/** 获取评审状态中文标签 */
function reviewStatusLabel(status: string): string {
  const opt = REVIEW_STATUS_OPTIONS.find((o) => o.value === status)
  return opt?.label || status
}

import { formatDateTime } from '@/utils'

/** 格式化日期时间 YYYY-MM-DD HH:mm */
function formatTime(time: string): string {
  if (!time) return '-'
  return formatDateTime(time)
}

// ==================== 数据加载 ====================

/** 加载评审列表 */
async function loadReviews() {
  loading.value = true
  try {
    const params: { project_id?: number; search?: string } = {}
    if (filterProjectId.value) params.project_id = filterProjectId.value
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

/** 加载项目列表（供下拉选择使用） */
async function loadProjects() {
  try {
    const res = await aitestApi.listProjects()
    projects.value = res.data || []
  } catch {
    // 项目列表非关键数据，加载失败静默处理
  }
}

// ==================== 筛选交互 ====================

let searchTimer: ReturnType<typeof setTimeout>

/** 搜索输入防抖 */
function handleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadReviews()
  }, 300)
}

/** 筛选变更时重新加载 */
function handleFilterChange() {
  loadReviews()
}

// ==================== 删除操作 ====================

/** 单行删除 */
async function handleDelete(review: TestReview) {
  try {
    await ElMessageBox.confirm(
      `确定删除评审「${review.name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await aitestApi.deleteReview(review.id)
    ElMessage.success('删除成功')
    await loadReviews()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '删除失败')
    }
  }
}

/** 批量删除 */
async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedIds.value.length} 个评审吗？`,
      '批量删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await aitestApi.batchDeleteReviews(selectedIds.value)
    ElMessage.success('批量删除成功')
    clearSelection()
    await loadReviews()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '批量删除失败')
    }
  }
}

// ==================== 路由导航 ====================

/** 跳转到新建评审页 */
function goToCreate() {
  router.push('/modules/aitest/reviews/create')
}

/** 跳转到评审详情页 */
function goToDetail(review: TestReview) {
  router.push(`/modules/aitest/reviews/${review.id}`)
}

// ==================== 初始化 ====================

onMounted(() => {
  loadProjects()
  loadReviews()
})
</script>

<style scoped lang="scss">
.page-wrap {
  padding: 24px 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .page-title {
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
    margin: 0;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;

  .search-input {
    flex: 1;
    min-width: 200px;
    max-width: 420px;
  }
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(198, 123, 92, 0.06);
  border-radius: 8px;
  margin-bottom: 12px;
}

.batch-info {
  font-size: 13px;
  color: var(--text-secondary, #5c4a38);
  margin-right: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.review-name-link { color: var(--primary, #C67B5C); text-decoration: none; font-weight: 500; }
.review-name-link:hover { color: var(--primary-light, #D49472); text-decoration: underline; }

.config-table-card {
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;

  :deep(.el-card__body) {
    padding: 0;
  }
}
</style>
