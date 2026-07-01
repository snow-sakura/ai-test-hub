<template>
  <div class="page-wrap">
    <!-- 面包屑 -->
    <div class="back-nav">
      <span class="back-arrow" @click="goBack">←</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-link" @click="goBack">项目详情</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-current">成员管理</span>
    </div>

    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">{{ project?.name || '项目成员' }}</h2>
        <span class="page-count">共 {{ members.length }} 个成员</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="handleAdd">添加成员</el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input v-model="searchKeyword" placeholder="搜索用户名、邮箱、部门、职位..." clearable class="search-input" @input="onSearch" />
      <el-select v-model="roleFilter" placeholder="角色筛选" clearable class="role-select" @change="onFilterChange">
        <el-option v-for="opt in ROLE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-bar">
      <span class="batch-info">已选择 {{ selectedIds.length }} 项</span>
      <el-button size="small" type="danger" @click="handleBatchRemove">批量移除</el-button>
      <el-button size="small" @click="clearSelection">取消选择</el-button>
    </div>

    <!-- 成员表格 -->
    <el-card shadow="never" class="config-table-card">
    <el-table
      ref="tableRef"
      :data="filteredMembers"
      v-loading="membersLoading"
      stripe
      style="width:100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="用户" min-width="160" show-overflow-tooltip align="center">
        <template #default="{ row }">
          <div class="user-cell">
            <span class="user-avatar" :style="{ background: avatarColor(row.username || row.email || String(row.user_id)) }">
              {{ (row.username || '?')[0].toUpperCase() }}
            </span>
            <div class="user-info">
              <span class="user-name">{{ row.username || '未知用户' }}</span>
              <span class="user-email">{{ row.email || '' }}</span>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="department" label="部门" min-width="100" show-overflow-tooltip align="center">
        <template #default="{ row }">{{ row.department || '—' }}</template>
      </el-table-column>
      <el-table-column prop="position" label="职位" min-width="100" show-overflow-tooltip align="center">
        <template #default="{ row }">{{ row.position || '—' }}</template>
      </el-table-column>
      <el-table-column label="角色" min-width="130" align="center">
        <template #default="{ row }">
          <div v-if="editingRoleUserId === row.user_id" @click.stop>
            <el-select
              v-model="editingRoleValue"
              size="small"
              @change="saveMemberRole(row)"
              @blur="editingRoleUserId = null"
              ref="roleSelectRef"
              style="width:120px"
            >
              <el-option v-for="r in ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
            </el-select>
          </div>
          <el-tag
            v-else
            :style="{ background: ROLE_COLORS[row.role], color: '#fff', border: 'none', cursor: 'pointer' }"
            size="small"
            @click="startEditRole(row)"
          >
            {{ roleLabel(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="加入时间" min-width="110" align="center">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="110" fixed="right" align="center">
        <template #default="{ row }">
          <el-button text size="small" type="danger" :disabled="row.user_id === currentUserId" @click="handleRemove(row)">移除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无成员" />
      </template>
    </el-table>
    </el-card>

    <!-- 添加成员弹窗 -->
    <el-dialog v-model="dialogVisible" title="添加成员" width="540px" :close-on-click-modal="false" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="70px">
        <el-form-item label="选择用户" prop="user_id">
          <el-select
            v-model="formData.user_id"
            filterable
            remote
            :remote-method="searchUsers"
            :loading="userSearchLoading"
            placeholder="输入用户名/邮箱搜索..."
            style="width:100%"
            popper-class="member-search-popper"
          >
            <el-option v-for="u in userOptions" :key="u.id" :value="u.id" :label="u.username">
              <div class="member-option-item">
                <span class="member-option-avatar" :style="{ background: avatarColor(u.username) }">{{ u.username[0].toUpperCase() }}</span>
                <div class="member-option-info">
                  <div class="member-option-name">{{ u.username }}</div>
                  <div class="member-option-email">{{ u.email }}</div>
                  <div v-if="u.department || u.position" class="member-option-dept">
                    {{ [u.department, u.position].filter(Boolean).join(' · ') }}
                  </div>
                </div>
              </div>
            </el-option>
            <template #loading>正在搜索用户...</template>
            <template #empty>
              <div style="padding:20px;text-align:center;color:#8B7355;font-size:13px;">
                <p style="margin:0 0 4px">未找到匹配用户</p>
                <p style="margin:0;font-size:12px;">可输入用户名、邮箱或部门名称搜索</p>
              </div>
            </template>
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="formData.role" style="flex-wrap:nowrap;white-space:nowrap">
            <el-radio-button value="admin">管理员</el-radio-button>
            <el-radio-button value="tester">测试人员</el-radio-button>
            <el-radio-button value="viewer">只读成员</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/aitest/project'
import { aitestApi } from '@/api/aitest'
import { adminApi } from '@/api/admin'
import { ROLE_OPTIONS, ROLE_COLORS } from '@/types/aitest'
import type { ProjectMember } from '@/types/aitest'
import type { AdminUserInfo } from '@/types/admin'
import type { FormInstance } from 'element-plus'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => Number(route.params.id))

const project = computed(() => projectStore.currentProject)
const members = computed(() => projectStore.members)
const membersLoading = computed(() => projectStore.membersLoading)

const searchKeyword = ref('')
const roleFilter = ref('')

const filteredMembers = computed(() => {
  return members.value.filter(m => {
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      const matchName = (m.username || '').toLowerCase().includes(kw)
      const matchEmail = (m.email || '').toLowerCase().includes(kw)
      const matchDept = (m.department || '').toLowerCase().includes(kw)
      const matchPos = (m.position || '').toLowerCase().includes(kw)
      if (!matchName && !matchEmail && !matchDept && !matchPos) return false
    }
    if (roleFilter.value && m.role !== roleFilter.value) return false
    return true
  })
})

const currentUserId = computed(() => {
  try { return Number(JSON.parse(localStorage.getItem('user') || '{}')?.id || 0) } catch { return 0 }
})

// ==================== 多选 ====================

const selectedIds = ref<number[]>([])
const tableRef = ref<any>(null)

function handleSelectionChange(rows: any[]) {
  selectedIds.value = rows.map((r: any) => r.user_id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selectedIds.value = []
}

async function handleBatchRemove() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定移除选中的 ${selectedIds.value.length} 个成员吗？`,
      '批量移除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await aitestApi.batchRemoveMembers(projectId.value, selectedIds.value)
    ElMessage.success('批量移除成功')
    clearSelection()
    await loadMembers()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '批量移除失败')
    }
  }
}

// 内联角色编辑
const editingRoleUserId = ref<number | null>(null)
const editingRoleValue = ref<'admin' | 'tester' | 'viewer'>('tester')
const roleSelectRef = ref()

function startEditRole(member: ProjectMember) {
  editingRoleUserId.value = member.user_id
  editingRoleValue.value = member.role
  nextTick(() => {
    const el = document.querySelector('.el-select')
    if (el) (el as HTMLElement).focus()
  })
}

async function saveMemberRole(member: ProjectMember) {
  if (editingRoleValue.value === member.role) {
    editingRoleUserId.value = null
    return
  }
  try {
    const ok = await projectStore.updateMemberRole(projectId.value, member.user_id, editingRoleValue.value)
    if (ok) {
      ElMessage.success('角色已更新')
      editingRoleUserId.value = null
      await loadMembers()
    }
  } catch { ElMessage.error('更新角色失败') }
}

// 添加成员弹窗
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const formData = ref<{ user_id: number | undefined; role: 'admin' | 'tester' | 'viewer' }>({ user_id: undefined, role: 'tester' })
const formRules = {
  user_id: [{ required: true, message: '请选择用户', trigger: 'change' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const userOptions = ref<AdminUserInfo[]>([])
const userSearchLoading = ref(false)

async function searchUsers(query: string) {
  if (!query) {
    userOptions.value = []
    return
  }
  userSearchLoading.value = true
  try {
    const res = await adminApi.getUsers({ keyword: query, page_size: 20 })
    userOptions.value = res.data || []
  } catch (e) { console.error('搜索用户失败:', e); userOptions.value = [] }
  userSearchLoading.value = false
}

function handleAdd() {
  formData.value = { user_id: undefined, role: 'tester' }
  userOptions.value = []
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid || !formData.value.user_id) { ElMessage.warning('请完善成员信息'); return }
  submitting.value = true
  try {
    await projectStore.addMember(projectId.value, formData.value.user_id, formData.value.role)
    ElMessage.success('添加成功')
    dialogVisible.value = false
    await loadMembers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '添加失败')
  } finally { submitting.value = false }
}

// 移除成员
async function handleRemove(member: ProjectMember) {
  try {
    await ElMessageBox.confirm(`确定移除成员「${member.username || member.user_id}」吗？`, '确认移除', { type: 'warning' })
    const ok = await projectStore.removeMember(projectId.value, member.user_id)
    if (ok) {
      ElMessage.success('已移除')
      await loadMembers()
    }
  } catch { /* cancel */ }
}

// 数据加载
async function loadMembers() {
  await projectStore.fetchMembers(projectId.value)
}

async function loadProject() {
  try {
    await projectStore.fetchProject(projectId.value)
  } catch { /* ignore */ }
}

function onSearch() { /* computed handles filtering */ }
function onFilterChange() { /* computed handles filtering */ }

function goBack() {
  router.push(`/modules/aitest/projects/${projectId.value}`)
}

function roleLabel(role: string): string {
  return ROLE_OPTIONS.find(o => o.value === role)?.label || role
}

function avatarColor(name: string): string {
  const colors = ['#C67B5C', '#7BA87D', '#8B9DC3', '#D4745C', '#B8A07A', '#A87D9E']
  let hash = 0; for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

function formatTime(t?: string | null): string {
  if (!t) return '—'
  const d = new Date(t)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(async () => {
  await loadProject()
  await loadMembers()
})
</script>

<style scoped lang="scss">
.page-wrap { margin: 0 auto; padding: 24px 16px; }

.back-nav { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #7A6855; margin-bottom: 16px; }
.back-arrow { font-size: 16px; cursor: pointer; color: var(--primary, #C67B5C); }
.back-arrow:hover { color: var(--primary-light, #D49472); }
.breadcrumb-link { cursor: pointer; }
.breadcrumb-link:hover { color: var(--primary, #C67B5C); }
.breadcrumb-sep { color: rgba(180,150,120,0.3); }
.breadcrumb-current { color: var(--text, #3D2E1F); font-weight: 500; }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text, #3D2E1F); margin: 0; }
.page-count { font-size: 13px; color: var(--text-muted, #8B7355); }

.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.search-input { flex: 1; min-width: 200px; max-width: 420px; }
.role-select { width: 140px; }

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

.user-cell { display: flex; align-items: center; gap: 10px; }
.user-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; font-weight: 600; flex-shrink: 0; }
.user-info { display: flex; flex-direction: column; }
.user-name { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); }
.user-email { font-size: 11px; color: var(--text-muted, #8B7355); }

</style>

<style>
.member-search-popper .member-option-item {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  padding: 4px 0 !important;
  white-space: nowrap !important;
}
.member-search-popper .member-option-avatar {
  width: 28px !important;
  height: 28px !important;
  min-width: 28px !important;
  border-radius: 50% !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  color: #fff !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  flex-shrink: 0 !important;
}
.member-search-popper .member-option-info {
  display: inline-flex !important;
  flex-direction: column !important;
  line-height: 1.4 !important;
  vertical-align: middle !important;
  min-width: 0 !important;
}
.member-search-popper .member-option-name {
  font-size: 13px !important;
  font-weight: 500 !important;
  color: #3D2E1F !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.member-search-popper .member-option-email {
  font-size: 11px !important;
  color: #8B7355 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.member-search-popper .member-option-dept {
  font-size: 11px !important;
  color: #8B7355 !important;
  opacity: 0.7 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
</style>
