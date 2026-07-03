<template>
  <!-- AI 生成记录页面：展示历史 AI 测试用例生成任务列表 -->
  <div class="page-wrap">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">AI 生成记录</h1>
    </div>

    <!-- 筛选栏：项目选择、日期范围、状态筛选 -->
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
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        style="width: 280px"
        @change="handleFilterChange"
      />
      <el-select
        v-model="filterStatus"
        placeholder="状态筛选"
        clearable
        style="width: 140px"
        @change="handleFilterChange"
      >
        <el-option
          v-for="opt in TASK_STATUS_OPTIONS"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>
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

    <!-- 生成记录表格 -->
    <el-card shadow="never" class="config-table-card">
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="pagedTasks"
      stripe
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column prop="task_id" label="任务 ID" min-width="180" show-overflow-tooltip align="center" />
      <el-table-column prop="title" label="任务标题" min-width="200" show-overflow-tooltip align="center" />
      <el-table-column label="状态" min-width="100" align="center">
        <template #default="{ row }">
          <template v-if="row.status === 'completed'">
            <el-tag v-if="row.saved_to_library" type="success" size="small" effect="dark">
              已完成
            </el-tag>
            <el-tag v-else type="info" size="small" effect="plain" hit>
              实时
            </el-tag>
          </template>
          <el-tag v-else :type="taskStatusType(row.status)" size="small" effect="plain">
            {{ taskStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" min-width="120" align="center">
        <template #default="{ row }">
          <el-progress :percentage="row.progress" :stroke-width="14" />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="130" show-overflow-tooltip align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="完成时间" min-width="130" show-overflow-tooltip align="center">
        <template #default="{ row }">
          {{ formatTime(row.completed_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="140" fixed="right" align="center">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click="goToGeneration(row)">
            查看
          </el-button>
          <el-button text size="small" type="danger" @click.stop="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
      <!-- 空状态 -->
      <template #empty>
        <el-empty description="暂无生成记录" />
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
import { aitestApi } from '@/api/aitest'
import type { AIGenerationTask, TestProject } from '@/types/aitest'

const router = useRouter()

// ==================== 常量定义 ====================

/** 任务状态配置：值、中文标签、对应 el-tag 类型 */
const TASK_STATUS_OPTIONS = [
  { value: 'pending', label: '待处理', type: 'info' },
  { value: 'generating', label: '生成中', type: 'warning' },
  { value: 'reviewing', label: '评审中', type: 'warning' },
  { value: 'revising', label: '修改中', type: 'warning' },
  { value: 'completed', label: '已完成', type: 'success' },
  { value: 'failed', label: '失败', type: 'danger' },
  { value: 'cancelled', label: '已取消', type: 'info' },
] as const

/** 任务状态联合类型 */
type TaskStatus = (typeof TASK_STATUS_OPTIONS)[number]['value']

// ==================== 筛选与列表状态 ====================

/** 加载中 */
const loading = ref(false)
/** 生成任务列表 */
const tasks = ref<AIGenerationTask[]>([])
/** 项目列表（下拉选择器用） */
const projects = ref<TestProject[]>([])
/** 项目筛选 ID */
const filterProjectId = ref<number | undefined>(undefined)
/** 日期范围筛选 */
const dateRange = ref<[string, string] | null>(null)
/** 状态筛选 */
const filterStatus = ref<TaskStatus | ''>('')
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

/** 根据筛选条件过滤后的任务列表 */
const filteredTasks = computed(() => {
  let list = tasks.value

  // 按项目筛选
  if (filterProjectId.value) {
    list = list.filter((t) => t.project_id === filterProjectId.value)
  }

  // 按状态筛选
  if (filterStatus.value) {
    list = list.filter((t) => t.status === filterStatus.value)
  }

  // 按创建日期范围筛选
  if (dateRange.value) {
    const [start, end] = dateRange.value
    const startTime = new Date(start).getTime()
    const endTime = new Date(end).getTime() + 86_400_000 - 1
    list = list.filter((t) => {
      const tTime = new Date(t.created_at).getTime()
      return tTime >= startTime && tTime <= endTime
    })
  }

  return list
})

/** 总记录数 */
const total = computed(() => filteredTasks.value.length)

/** 当前页可见数据 */
const pagedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTasks.value.slice(start, start + pageSize.value)
})

// ==================== 状态工具函数 ====================

/** 根据任务状态返回 el-tag 类型 */
function taskStatusType(status: string): string {
  const opt = TASK_STATUS_OPTIONS.find((o) => o.value === status)
  return opt?.type || 'info'
}

/** 获取任务状态中文标签 */
function taskStatusLabel(status: string): string {
  const opt = TASK_STATUS_OPTIONS.find((o) => o.value === status)
  return opt?.label || status
}

import { formatDateTime } from '@/utils'

/** 格式化日期时间 YYYY-MM-DD HH:mm */
function formatTime(time: string | null): string {
  if (!time) return '-'
  return formatDateTime(time).slice(0, 16)
}

// ==================== 数据加载 ====================

/** 加载 AI 生成任务列表 */
async function loadTasks() {
  loading.value = true
  try {
    const res = await aitestApi.getTaskList(currentPage.value, pageSize.value)
    tasks.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载生成记录失败')
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

let filterTimer: ReturnType<typeof setTimeout>

/** 筛选条件变更时重置分页并重新加载 */
function handleFilterChange() {
  clearTimeout(filterTimer)
  filterTimer = setTimeout(() => {
    currentPage.value = 1
    loadTasks()
  }, 300)
}

// ==================== 删除操作 ====================

/** 单行删除 */
async function handleDelete(task: AIGenerationTask) {
  try {
    await ElMessageBox.confirm(
      `确定删除任务「${task.title}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await aitestApi.deleteGenerationTask(task.task_id)
    ElMessage.success('删除成功')
    await loadTasks()
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
      `确定删除选中的 ${selectedIds.value.length} 个任务吗？`,
      '批量删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await aitestApi.batchDeleteGenerationTasks(selectedIds.value)
    ElMessage.success('批量删除成功')
    clearSelection()
    await loadTasks()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '批量删除失败')
    }
  }
}

// ==================== 路由导航 ====================

/** 跳转到生成页面，携带 task_id 查看对应任务详情 */
function goToGeneration(task: AIGenerationTask) {
  router.push(`/modules/aitest/generate?task_id=${task.task_id}`)
}

// ==================== 初始化 ====================

onMounted(() => {
  loadProjects()
  loadTasks()
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

.config-table-card {
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;

  :deep(.el-card__body) {
    padding: 0;
  }
}
</style>
