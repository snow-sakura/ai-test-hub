<template>
  <!-- 测试用例列表页：多条件筛选、表格展示、新建/查看/编辑/删除操作 -->
  <div class="page-wrap">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">测试用例管理</h1>
      <div class="header-actions">
        <!-- 导出下拉菜单 -->
        <el-dropdown @command="handleExport" trigger="click">
          <el-button :icon="Download">
            导出 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="xlsx"><el-icon><Document /></el-icon> Excel (.xlsx)</el-dropdown-item>
              <el-dropdown-item command="csv"><el-icon><Document /></el-icon> CSV (.csv)</el-dropdown-item>
              <el-dropdown-item command="md"><el-icon><Document /></el-icon> Markdown (.md)</el-dropdown-item>
              <el-dropdown-item command="xmind"><el-icon><Share /></el-icon> XMind (.xmind)</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 导入按钮（支持多格式，后端自动识别） -->
        <el-button :icon="Upload" @click="handleImport">
          导入
        </el-button>

        <el-button type="primary" :icon="Plus" @click="handleCreate">
          新建用例
        </el-button>
      </div>
    </div>

    <!-- 筛选条件栏 -->
    <div class="filter-bar">
      <el-select
        v-model="filters.project_id"
        placeholder="所属项目"
        clearable
        filterable
        style="width: 140px"
        @change="loadVersions"
      >
        <el-option
          v-for="p in projects"
          :key="p.id"
          :label="p.name"
          :value="p.id"
        />
      </el-select>
      <el-select
        v-model="filters.version_id"
        placeholder="版本"
        clearable
        style="width: 140px"
        :disabled="!filters.project_id"
      >
        <el-option
          v-for="v in filteredVersions"
          :key="v.id"
          :label="v.name"
          :value="v.id"
        />
      </el-select>
      <el-select
        v-model="filters.test_type"
        placeholder="用例类型"
        clearable
        style="width: 140px"
      >
        <el-option
          v-for="opt in TEST_TYPE_OPTIONS"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>
      <el-select
        v-model="filters.priority"
        placeholder="优先级"
        clearable
        style="width: 120px"
      >
        <el-option
          v-for="opt in PRIORITY_OPTIONS"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>
      <el-input
        v-model="filters.search"
        placeholder="搜索用例名称..."
        :prefix-icon="Search"
        clearable
        class="search-input"
        @input="handleSearch"
      />
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-bar">
      <span class="batch-info">已选择 {{ selectedIds.length }} 项</span>
      <el-button size="small" type="primary" @click="handleBatchReview">
        批量评审
      </el-button>
      <el-button size="small" type="danger" @click="handleBatchDelete">
        批量删除
      </el-button>
      <el-button size="small" @click="clearSelection">
        取消选择
      </el-button>
    </div>

    <!-- 用例列表表格 -->
    <el-card shadow="never" class="config-table-card">
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="pagedData"
      stripe
      style="width: 100%"
      @selection-change="handleSelectionChange"
      @select="handleSelect"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="用例名称" min-width="200" show-overflow-tooltip align="center">
        <template #default="{ row }">
          <router-link :to="`/modules/aitest/testcases/${row.id}`" class="case-link">
            {{ row.name }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="module" label="所属模块" min-width="100" show-overflow-tooltip align="center">
        <template #default="{ row }">
          {{ row.module || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="所属项目" min-width="120" show-overflow-tooltip align="center">
        <template #default="{ row }">
          {{ projects.find(p => p.id === row.project_id)?.name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="优先级" min-width="80" align="center">
        <template #default="{ row }">
          <el-tag
            :type="priorityTagType(row.priority)"
            size="small"
            effect="plain"
          >
            {{ priorityLabel(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="用例类型" min-width="90" align="center">
        <template #default="{ row }">
          {{ typeLabel(row.test_type) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" min-width="80" align="center">
        <template #default="{ row }">
          <el-tag
            :type="statusTagType(row.status)"
            size="small"
            effect="plain"
          >
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="执行结果" min-width="90" align="center">
        <template #default="{ row }">
          <el-tag
            v-if="(row as any).latest_execution_status"
            :type="executionTagType((row as any).latest_execution_status)"
            size="small"
          >
            {{ executionTagLabel((row as any).latest_execution_status) }}
          </el-tag>
          <span v-else style="color:#8B7355;font-size:12px;">未执行</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="130" align="center">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="220" fixed="right" align="center">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click="handleView(row)">查看</el-button>
          <template v-if="row.status === 'draft'">
            <el-button text size="small" type="success" @click="handleAddToReview(row)">评审</el-button>
          </template>
          <template v-else-if="row.status === 'active'">
            <el-button text size="small" type="warning" @click="openExecuteDialog(row)">执行</el-button>
          </template>
          <el-button v-if="!row.latest_execution_status" text size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无测试用例" />
      </template>
    </el-table>
    </el-card>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="filteredCases.length"
        layout="total, sizes, prev, pager, next, jumper"
        background
      />
    </div>
  </div>

  <!-- 导入结果弹窗 -->
  <el-dialog v-model="importResultVisible" title="导入结果" width="500px">
    <el-alert
      v-if="importResult.imported > 0"
      :title="`成功导入 ${importResult.imported} 条用例`"
      type="success"
      show-icon
      style="margin-bottom:16px"
    />
    <el-alert
      v-if="importResult.errors.length > 0"
      :title="`${importResult.errors.length} 条导入失败`"
      type="warning"
      show-icon
      style="margin-bottom:16px"
    />
    <div v-if="importResult.errors.length > 0">
      <p style="font-weight:600;margin-bottom:8px">错误详情：</p>
      <ul style="font-size:13px;color:#F56C6C;padding-left:20px">
        <li v-for="(err, i) in importResult.errors" :key="i">{{ err }}</li>
      </ul>
    </div>
    <template #footer>
      <el-button type="primary" @click="importResultVisible = false">知道了</el-button>
    </template>
  </el-dialog>

  <!-- 导入选择项目弹窗 -->
  <el-dialog v-model="importDialogVisible" title="选择导入项目" width="420px">
    <el-form label-position="top">
      <el-form-item label="目标项目" required>
        <el-select
          v-model="importProjectId"
          placeholder="请选择项目"
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="p in projects"
            :key="p.id"
            :label="p.name"
            :value="p.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="importDialogVisible = false">取消</el-button>
      <el-button type="primary" :disabled="!importProjectId" @click="handleImportConfirm">
        选择文件
      </el-button>
    </template>
  </el-dialog>

  <!-- 隐藏的文件输入，用于导入文件 -->
  <input
    ref="importFileInput"
    type="file"
    accept=".xlsx,.xls,.csv,.md,.xmind,.mm"
    style="display:none"
    @change="handleImportFileChange"
  />

  <!-- 快速评审弹窗 -->
  <el-dialog v-model="reviewDialogVisible" title="创建评审" width="480px">
    <el-form label-position="top">
      <el-form-item label="评审名称" required>
        <el-input v-model="reviewDialogForm.name" placeholder="请输入评审名称" maxlength="200" />
      </el-form-item>
      <el-form-item label="关联项目">
        <el-input :model-value="reviewDialogForm.project_id ? projects.find(p => p.id === reviewDialogForm.project_id)?.name || '项目#' + reviewDialogForm.project_id : ''" disabled />
      </el-form-item>
      <el-form-item label="评审用例">
        <div style="font-size:13px;color:var(--text-secondary)">
          共 {{ reviewDialogCases.length }} 条用例
          <span v-if="reviewDialogCases.length <= 3">
            ：{{ reviewDialogCases.map(c => c.name).join('、') }}
          </span>
        </div>
      </el-form-item>
      <el-form-item label="评审人（可选）">
        <el-select
          v-model="reviewDialogForm.reviewer_ids"
          multiple
          filterable
          placeholder="选择评审人"
          style="width:100%"
        >
          <el-option
            v-for="u in reviewUsers"
            :key="u.id"
            :label="u.username"
            :value="u.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="reviewDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="reviewDialogSubmitting" @click="handleReviewSubmit">
        创建评审
      </el-button>
    </template>
  </el-dialog>

  <!-- 执行用例弹窗（行内快速执行，支持上下条导航） -->
  <el-dialog v-model="executeDialogVisible" width="520px">
    <template #header>
      <div style="display:flex;align-items:center;gap:8px">
        <span>执行用例</span>
        <span
          style="font-size:13px;color:var(--text-secondary);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
        >
          {{ executingCase?.name }}
        </span>
        <span v-if="executingCaseList.length > 1" style="font-size:12px;color:#999;margin-left:4px">
          ({{ executingCaseIndex + 1 }} / {{ executingCaseList.length }})
        </span>
      </div>
    </template>
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
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <el-button :disabled="!hasPrevCase" @click="goToPrevCase">上一条</el-button>
          <el-button :disabled="!hasNextCase" @click="goToNextCase">下一条</el-button>
        </div>
        <div>
          <el-button @click="executeDialogVisible = false">关闭</el-button>
          <el-button type="primary" :disabled="!executeForm.status" :loading="executing" @click="handleExecute">
            提交执行结果
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Download, Upload, ArrowDown, Document, Share } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'
import type { TestCase, TestProject, TestVersion, TestCaseExecuteRequest } from '@/types/aitest'

// ==================== 常量定义 ====================

/** 用例类型选项 */
const TEST_TYPE_OPTIONS = [
  { value: 'functional', label: '功能测试' },
  { value: 'api', label: '接口测试' },
  { value: 'ui', label: 'UI 测试' },
  { value: 'app', label: '应用测试' },
] as const

/** 优先级选项 */
const PRIORITY_OPTIONS = [
  { value: 'p0', label: 'P0（最高）' },
  { value: 'p1', label: 'P1（高）' },
  { value: 'p2', label: 'P2（中）' },
  { value: 'p3', label: 'P3（低）' },
] as const

/** 用例状态选项 */
const STATUS_OPTIONS = [
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '已启用' },
  { value: 'deprecated', label: '已废弃' },
] as const

// ==================== 状态映射常量 ====================

const EXECUTION_STATUS_MAP: Record<string, { type: string; label: string }> = {
  pass: { type: 'success', label: '通过' },
  fail: { type: 'danger', label: '失败' },
  blocked: { type: 'warning', label: '阻塞' },
  skip: { type: 'info', label: '跳过' },
}

// ==================== 执行用例弹窗状态 ====================

const executeDialogVisible = ref(false)
const executing = ref(false)
const executingCase = ref<TestCase | null>(null)
const executeForm = ref({ status: '', actual_result: '' })

/** 当前执行用例在 filteredCases 中的索引，用于上下条导航 */
const executingCaseIndex = ref(-1)
/** 引用当前筛选后的全部用例列表作为导航范围 */
const executingCaseList = computed(() => filteredCases.value)
/** 是否有上一条 */
const hasPrevCase = computed(() => executingCaseIndex.value > 0)
/** 是否有下一条 */
const hasNextCase = computed(() => executingCaseIndex.value < executingCaseList.value.length - 1)

// ==================== 快速评审弹窗状态 ====================

const reviewDialogVisible = ref(false)
const reviewDialogSubmitting = ref(false)
const reviewDialogCases = ref<TestCase[]>([])
const reviewDialogForm = ref({
  name: '',
  project_id: 0,
  reviewer_ids: [] as number[],
})
const reviewUsers = ref<Array<{ id: number; username: string }>>([])

async function loadReviewUsers() {
  if (reviewUsers.value.length > 0) return
  try {
    const res = await aitestApi.listUsers({ page_size: 100 })
    reviewUsers.value = (res.data || []).map((u: any) => ({ id: u.id, username: u.username || u.email || `用户#${u.id}` }))
  } catch { /* ignore */ }
}

// ==================== 路由 ====================

const router = useRouter()

// ==================== 筛选条件 ====================

/** 筛选条件表单 */
const filters = ref({
  project_id: undefined as number | undefined,
  version_id: undefined as number | undefined,
  test_type: '' as string,
  priority: '' as string,
  search: '' as string,
})

// ==================== 下拉数据 ====================

const projects = ref<TestProject[]>([])
const allVersions = ref<TestVersion[]>([])

/** 当前选中项目下的版本列表 */
const filteredVersions = computed(() => {
  if (!filters.value.project_id) return []
  return allVersions.value.filter((v) => v.project_id === filters.value.project_id)
})

// ==================== 用例数据 ====================

const loading = ref(false)
const allCases = ref<TestCase[]>([])

/** 根据筛选条件过滤后的用例列表 */
const filteredCases = computed(() => {
  return allCases.value.filter((c) => {
    if (filters.value.project_id && c.project_id !== filters.value.project_id) return false
    if (filters.value.version_id && c.version_id !== filters.value.version_id) return false
    if (filters.value.test_type && c.test_type !== filters.value.test_type) return false
    if (filters.value.priority && c.priority !== filters.value.priority) return false
    if (filters.value.search && !c.name.toLowerCase().includes(filters.value.search.toLowerCase())) return false
    return true
  })
})

// ==================== 分页 ====================

const page = ref(1)
const pageSize = ref(10)

/** 当前分页数据 */
const pagedData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredCases.value.slice(start, start + pageSize.value)
})

// 筛选条件变化时重置到第一页
watch(filteredCases, () => {
  page.value = 1
})

// ==================== 多选 ====================

const selectedIds = ref<number[]>([])
const tableRef = ref<any>(null)

function handleSelectionChange(rows: any[]) {
  selectedIds.value = rows.map((r: any) => r.id)
}

/** 行选择时拦截跨项目混选 */
function handleSelect(selection: any[], row: any) {
  if (selection.length <= 1) return
  const rowProjectId = row.project_id
  if (!rowProjectId) {
    tableRef.value?.toggleRowSelection(row, false)
    ElMessage.warning('该用例未关联项目，无法参与评审')
    return
  }
  const existingProjectId = selection.find(r => r.id !== row.id)?.project_id
  if (existingProjectId && rowProjectId !== existingProjectId) {
    tableRef.value?.toggleRowSelection(row, false)
    ElMessage.warning('只能选择同一项目的用例进行评审')
    return
  }
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selectedIds.value = []
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedIds.value.length} 条用例吗？此操作不可恢复。`,
      '批量删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await aitestApi.batchDeleteTestCases(selectedIds.value)
    ElMessage.success('批量删除成功')
    clearSelection()
    await loadTestCases()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '批量删除失败')
    }
  }
}

// ==================== 搜索防抖 ====================

let searchTimer: ReturnType<typeof setTimeout> | null = null

function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadTestCases()
  }, 300)
}

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

// ==================== 数据加载 ====================

/** 加载项目列表 */
async function loadProjects() {
  try {
    const res = await aitestApi.listProjects()
    projects.value = res.data || []
  } catch {
    // 静默失败
  }
}

/** 加载版本列表 */
async function loadVersions() {
  if (!filters.value.project_id) {
    filters.value.version_id = undefined
    return
  }
  try {
    const res = await aitestApi.listVersions({ project_id: filters.value.project_id })
    allVersions.value = res.data || []
  } catch {
    allVersions.value = []
  }
}

/** 加载测试用例列表 */
async function loadTestCases() {
  loading.value = true
  try {
    const res = await aitestApi.listTestCases()
    allCases.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载测试用例失败')
  } finally {
    loading.value = false
  }
}

// ==================== 操作方法 ====================

/** 新建用例：跳转到创建页面 */
function handleCreate() {
  router.push('/modules/aitest/testcases/create')
}

/** 查看用例详情（只读） */
function handleView(testCase: TestCase) {
  router.push(`/modules/aitest/testcases/${testCase.id}`)
}

/** 编辑用例 */
function handleEdit(testCase: TestCase) {
  router.push(`/modules/aitest/testcases/${testCase.id}/edit`)
}

/** 删除用例（含确认弹窗） */
async function handleDelete(testCase: TestCase) {
  try {
    await ElMessageBox.confirm(
      `确定删除用例「${testCase.name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await aitestApi.deleteTestCase(testCase.id)
    ElMessage.success('删除成功')
    await loadTestCases()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '删除失败')
    }
  }
}

// ==================== 工具函数 ====================

/** 优先级对应的 el-tag 类型 */
function priorityTagType(priority: string): string {
  const map: Record<string, string> = {
    p0: 'danger',
    p1: 'warning',
    p2: 'primary',
    p3: 'info',
  }
  return map[priority] || 'info'
}

/** 优先级中文标签 */
function priorityLabel(priority: string): string {
  const opt = PRIORITY_OPTIONS.find((o) => o.value === priority)
  return opt?.label || priority
}

/** 用例类型中文标签 */
function typeLabel(type: string): string {
  const opt = TEST_TYPE_OPTIONS.find((o) => o.value === type)
  return opt?.label || type
}

/** 用例状态对应的 el-tag 类型 */
function statusTagType(status: string): string {
  const map: Record<string, string> = {
    draft: 'info',
    active: 'success',
    deprecated: 'warning',
  }
  return map[status] || 'info'
}

/** 用例状态中文标签 */
function statusLabel(status: string): string {
  const opt = STATUS_OPTIONS.find((o) => o.value === status)
  return opt?.label || status
}

/** 执行结果对应的 el-tag 类型 */
function executionTagType(status: string): string {
  return EXECUTION_STATUS_MAP[status]?.type || 'info'
}

/** 执行结果中文标签 */
function executionTagLabel(status: string): string {
  return EXECUTION_STATUS_MAP[status]?.label || status
}

/** 打开执行弹窗 */
function openExecuteDialog(testCase: TestCase) {
  const idx = filteredCases.value.findIndex(c => c.id === testCase.id)
  executingCaseIndex.value = idx
  executingCase.value = testCase
  executeForm.value = { status: '', actual_result: '' }
  executeDialogVisible.value = true
}

/** 切换到上一条用例 */
function goToPrevCase() {
  if (!hasPrevCase.value) return
  executingCaseIndex.value--
  executingCase.value = executingCaseList.value[executingCaseIndex.value]
  executeForm.value = { status: '', actual_result: '' }
}

/** 切换到下一条用例 */
function goToNextCase() {
  if (!hasNextCase.value) return
  executingCaseIndex.value++
  executingCase.value = executingCaseList.value[executingCaseIndex.value]
  executeForm.value = { status: '', actual_result: '' }
}

/** 提交执行结果 */
async function handleExecute() {
  if (!executeForm.value.status || !executingCase.value) return
  executing.value = true
  try {
    await aitestApi.executeTestCase(executingCase.value.id, {
      status: executeForm.value.status as TestCaseExecuteRequest['status'],
      actual_result: executeForm.value.actual_result || undefined,
    })
    ElMessage.success('执行结果已记录')
    // 刷新列表展示最新执行状态，自动跳下一条
    await loadTestCases()
    if (hasNextCase.value) {
      goToNextCase()
    } else {
      executeForm.value = { status: '', actual_result: '' }
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '执行失败')
  } finally {
    executing.value = false
  }
}

/** 打开快速评审弹窗（单条用例） */
function handleAddToReview(testCase: TestCase) {
  reviewDialogCases.value = [testCase]
  openReviewDialog()
}

/** 打开批量评审弹窗 */
function handleBatchReview() {
  if (selectedIds.value.length === 0) return
  const selected = allCases.value.filter(c => selectedIds.value.includes(c.id))
  reviewDialogCases.value = selected
  openReviewDialog()
}

/** 打开快速评审弹窗 */
function openReviewDialog() {
  const cases = reviewDialogCases.value
  if (cases.length === 0) return

  // 检查所有用例是否属于同一项目
  const projectIds = new Set(cases.filter(c => c.project_id).map(c => c.project_id))
  if (projectIds.size > 1) {
    ElMessage.warning('选中的用例属于不同项目，请选择同一项目的用例进行评审')
    return
  }

  const projectId = cases[0]?.project_id
  if (!projectId) {
    ElMessage.warning('用例未关联项目，无法创建评审')
    return
  }

  const projectName = projects.value.find(p => p.id === projectId)?.name || ''
  reviewDialogForm.value = {
    name: cases.length === 1
      ? cases[0].name
      : `批量评审 ${cases.length} 条用例 - ${projectName}`,
    project_id: projectId,
    reviewer_ids: [],
  }
  reviewDialogVisible.value = true
  loadReviewUsers()
}

/** 提价快速评审 */
async function handleReviewSubmit() {
  const cases = reviewDialogCases.value
  if (!reviewDialogForm.value.name.trim()) {
    ElMessage.warning('请输入评审名称')
    return
  }
  reviewDialogSubmitting.value = true
  try {
    await aitestApi.createReview({
      project_id: reviewDialogForm.value.project_id,
      name: reviewDialogForm.value.name,
      cases: cases.map(c => c.id),
      reviewer_ids: reviewDialogForm.value.reviewer_ids.length > 0 ? reviewDialogForm.value.reviewer_ids : undefined,
    })
    ElMessage.success(`评审已创建，包含 ${cases.length} 条用例`)
    reviewDialogVisible.value = false
    clearSelection()
    router.push('/modules/aitest/reviews')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建评审失败')
  } finally {
    reviewDialogSubmitting.value = false
  }
}

/** 格式化时间到日期 YYYY-MM-DD */
function formatTime(time: string | null | undefined): string {
  if (!time) return '-'
  const d = new Date(time)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// ==================== 导入导出 ====================

const importFileInput = ref<HTMLInputElement>()
const importResultVisible = ref(false)
const importResult = ref<{ imported: number; errors: string[] }>({ imported: 0, errors: [] })

/** 导入弹窗状态 */
const importDialogVisible = ref(false)
const importProjectId = ref<number | undefined>(undefined)

/** 导出：通过 axios 下载 blob（携带 token） */
async function handleExport(format: string) {
  try {
    const blob = await aitestApi.exportTestCasesDownload({
      format,
      project_id: filters.value.project_id,
      version_id: filters.value.version_id,
      test_type: filters.value.test_type || undefined,
    })
    const ext = format === 'xmind' ? 'xmind' : format
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `测试用例_${new Date().toISOString().slice(0, 10)}.${ext}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e: any) {
    let errorMsg = '导出失败'
    try {
      // 当 responseType 为 blob 时，错误数据也是 blob，需读取文本
      if (e?.response?.data instanceof Blob) {
        const text = await (e.response.data as Blob).text()
        const parsed = JSON.parse(text)
        errorMsg = parsed?.detail || (Array.isArray(parsed?.detail) ? parsed.detail[0]?.msg : null) || errorMsg
      } else if (e?.response?.data?.detail) {
        errorMsg = e.response.data.detail
      } else if (e?.message) {
        errorMsg = e.message
      }
    } catch {
      // 解析失败使用默认提示
    }
    ElMessage.error(errorMsg)
  }
}

/** 导入：打开项目选择弹窗 */
function handleImport() {
  importProjectId.value = undefined
  importDialogVisible.value = true
}

/** 确认选择项目后打开文件选择器 */
function handleImportConfirm() {
  if (!importProjectId.value) return
  importDialogVisible.value = false
  importFileInput.value?.click()
}

/** 文件选择后上传导入 */
async function handleImportFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file || !importProjectId.value) return
  try {
    const res = await aitestApi.importTestCasesExcel(file, importProjectId.value)
    importResult.value = res.data || { imported: 0, errors: [] }
    importResultVisible.value = true
    await loadTestCases()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '导入失败')
  } finally {
    importProjectId.value = undefined
    if (importFileInput.value) importFileInput.value.value = ''
  }
}

// ==================== 初始化 ====================

onMounted(() => {
  loadProjects()
  loadTestCases()
})
</script>

<style scoped lang="scss">
.page-wrap {
  padding: 24px 16px;
}

// ==================== 页面头部 ====================

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

  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }
}

// ==================== 筛选条件栏 ====================

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;

  .search-input {
    flex: 1;
    min-width: 200px;
    max-width: 420px;
  }
}

// ==================== 批量操作栏 ====================

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

// ==================== 分页 ====================

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.case-link { color: var(--primary, #C67B5C); text-decoration: none; font-weight: 500; }
.case-link:hover { color: var(--primary-light, #D49472); text-decoration: underline; }

.config-table-card {
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;

  :deep(.el-card__body) {
    padding: 0;
  }
}
</style>
