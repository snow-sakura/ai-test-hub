<template>
  <div class="page-wrap">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">测试项目管理</h1>
        <span class="page-count">共 {{ store.total }} 个项目</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建项目</el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="s in statsCards" :key="s.key" class="stat-card" :style="{ borderTop: `3px solid ${s.color}` }">
        <div class="stat-value">{{ s.count }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input v-model="store.searchKeyword" placeholder="搜索项目名称或负责人..." clearable class="search-input" @input="onSearch" />
      <el-select v-model="store.statusFilter" placeholder="项目状态" clearable class="status-select" @change="onStatusChange">
        <el-option v-for="opt in PROJECT_STATUS_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-bar">
      <span class="batch-info">已选择 {{ selectedIds.length }} 项</span>
      <el-button size="small" @click="handleBatchStatus('active')">设为进行中</el-button>
      <el-button size="small" @click="handleBatchStatus('completed')">设为已完成</el-button>
      <el-button size="small" type="danger" @click="handleBatchDelete">批量删除</el-button>
      <el-button size="small" @click="clearSelection">取消选择</el-button>
    </div>

    <!-- 项目表格 -->
    <el-card shadow="never" class="config-table-card">
    <el-table ref="tableRef" v-loading="store.isLoading" :data="store.projects" stripe style="width:100%" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column prop="name" label="项目名称" min-width="220" show-overflow-tooltip align="center" />
      <el-table-column prop="leader" label="负责人" min-width="120" show-overflow-tooltip align="center">
        <template #default="{ row }">{{ row.leader || '—' }}</template>
      </el-table-column>
      <el-table-column label="状态" min-width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small" effect="plain">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="成员数" min-width="75" align="center">
        <template #default="{ row }">{{ row.member_count || 0 }}</template>
      </el-table-column>
      <el-table-column label="用例数" min-width="75" align="center">
        <template #default="{ row }">{{ row.case_count ?? 0 }}</template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="130" show-overflow-tooltip align="center">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="180" fixed="right" align="center">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click.stop="$router.push(`/modules/aitest/projects/${row.id}`)">查看</el-button>
          <el-button text size="small" @click.stop="handleEdit(row)">编辑</el-button>
          <el-button text size="small" type="danger" @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无项目" />
      </template>
    </el-table>
    </el-card>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="store.page"
        v-model:page-size="store.pageSize"
        :total="store.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @current-change="store.fetchProjects"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑项目' : '新建项目'" width="540px" :close-on-click-modal="false" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="负责人" prop="leader">
          <el-input v-model="form.leader" placeholder="请输入负责人姓名" maxlength="50" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="form.start_date" type="date" placeholder="选择开始日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="form.end_date" type="date" placeholder="选择结束日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入项目描述（选填）" />
        </el-form-item>
        <el-form-item label="状态" prop="status" v-if="isEditing">
          <el-select v-model="form.status" placeholder="选择状态" style="width:100%">
            <el-option v-for="opt in PROJECT_STATUS_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/aitest/project'
import { PROJECT_STATUS_OPTIONS } from '@/types/aitest'
import type { TestProjectCreate, TestProjectUpdate } from '@/types/aitest'
import type { FormInstance } from 'element-plus'

const store = useProjectStore()

const selectedIds = ref<number[]>([])
const tableRef = ref<any>(null)
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

interface ProjectForm {
  name: string; description: string; leader: string
  start_date: string; end_date: string; status: string
}
const form = ref<ProjectForm>({ name: '', description: '', leader: '', start_date: '', end_date: '', status: 'active' })

const formRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

// 统计卡片（全量数据，独立于分页）
const statsCards = computed(() => {
  const s = store.stats
  return [
    { key: 'all', label: '全部项目', count: s.total, color: '#C67B5C' },
    { key: 'active', label: '进行中', count: s.active, color: '#10b981' },
    { key: 'completed', label: '已完成', count: s.completed, color: '#3b82f6' },
    { key: 'archived', label: '已归档', count: s.archived, color: '#8B7355' },
  ]
})

function onSelectionChange(rows: any[]) {
  selectedIds.value = rows.map(r => r.id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selectedIds.value = []
}

function onSearch() { store.fetchProjects() }
function onStatusChange() { store.fetchProjects() }
function handleSizeChange(size: number) { store.setPageSize(size); store.fetchProjects() }

function handleCreate() {
  isEditing.value = false; editingId.value = null
  form.value = { name: '', description: '', leader: '', start_date: '', end_date: '', status: 'active' }
  dialogVisible.value = true
}

function handleEdit(project: any) {
  isEditing.value = true; editingId.value = project.id
  form.value = {
    name: project.name, description: project.description || '', leader: project.leader || '',
    start_date: project.start_date || '', end_date: project.end_date || '', status: project.status,
  }
  dialogVisible.value = true
}

async function handleDelete(project: any) {
  try {
    await ElMessageBox.confirm(`确定删除项目「${project.name}」吗？`, '确认删除', { type: 'warning' })
    const ok = await store.deleteProject(project.id)
    if (ok) {
      ElMessage.success('删除成功')
      store.fetchProjectStats()
    } else ElMessage.error('删除失败')
  } catch { /* dialog cancelled */ }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      const data: TestProjectUpdate = { name: form.value.name, status: form.value.status as any }
      if (form.value.description) data.description = form.value.description
      if (form.value.leader) data.leader = form.value.leader
      if (form.value.start_date) data.start_date = form.value.start_date
      if (form.value.end_date) data.end_date = form.value.end_date
      await store.updateProject(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      const data: TestProjectCreate = { name: form.value.name }
      if (form.value.description) data.description = form.value.description
      if (form.value.leader) data.leader = form.value.leader
      if (form.value.start_date) data.start_date = form.value.start_date
      if (form.value.end_date) data.end_date = form.value.end_date
      await store.createProject(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleBatchStatus(status: string) {
  try {
    const { aitestApi } = await import('@/api/aitest')
    await aitestApi.batchUpdateProjects(selectedIds.value, { status: status as any })
    ElMessage.success('批量更新成功')
    selectedIds.value = []
    await Promise.all([store.fetchProjects(), store.fetchProjectStats()])
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '批量更新失败')
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 个项目吗？`, '批量删除', { type: 'warning' })
    const ok = await store.batchDeleteProjects(selectedIds.value)
    if (ok) {
      ElMessage.success('批量删除成功')
      clearSelection()
      store.fetchProjectStats()
    } else {
      ElMessage.error('批量删除失败')
    }
  } catch { /* dialog cancelled */ }
}

function statusTagType(status: string): string {
  const map: Record<string, string> = { active: 'success', completed: 'primary', archived: 'info' }
  return map[status] || 'info'
}

function statusLabel(status: string): string {
  const opt = PROJECT_STATUS_OPTIONS.find(o => o.value === status)
  return opt?.label || status
}

function formatTime(t: string | null): string {
  if (!t) return '—'
  const d = new Date(t)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  store.fetchProjects()
  store.fetchProjectStats()
})
</script>

<style scoped lang="scss">
.page-wrap { padding: 24px 16px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text, #3D2E1F); margin: 0; }
.page-count { font-size: 13px; color: var(--text-muted, #8B7355); }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { padding: 20px 24px; background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 10px; text-align: center; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--text, #3D2E1F); }
.stat-label { font-size: 12px; color: var(--text-muted, #8B7355); margin-top: 2px; }

.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.search-input { flex: 1; min-width: 200px; max-width: 420px; }
.status-select { width: 140px; }

.config-table-card {
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;

  :deep(.el-card__body) {
    padding: 0;
  }
}

.batch-bar { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: rgba(198,123,92,0.06); border-radius: 8px; margin-bottom: 12px; }
.batch-info { font-size: 13px; color: var(--text-secondary, #5C4A38); margin-right: 8px; }

.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .filter-bar { flex-wrap: wrap; }
  .search-input { min-width: 100%; max-width: 100%; }
  .status-select { width: 100%; }
}
</style>
