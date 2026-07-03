<template>
  <div class="page-wrap">
    <!-- 面包屑 -->
    <div class="back-nav">
      <span class="back-arrow" @click="router.push('/modules/aitest/projects')">←</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-link" @click="router.push('/modules/aitest/projects')">项目列表</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-current">{{ project?.name || '项目详情' }}</span>
    </div>

    <div v-loading="loading" class="detail-wrap">
      <!-- 头部 -->
      <div class="detail-header">
        <div class="header-left">
          <h1 class="page-title">{{ project?.name }}</h1>
          <el-tag v-if="project" :type="statusTagType(project.status)" size="small" effect="plain">{{ statusLabel(project.status) }}</el-tag>
        </div>
        <div class="header-actions">
          <el-button size="small" @click="handleEditProject">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDeleteProject">删除</el-button>
        </div>
      </div>

      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" @tab-click="onTabClick" class="detail-tabs">
        <!-- Tab 1: 项目信息 -->
        <el-tab-pane label="项目信息" name="info">
          <div v-if="project">
            <div class="stats-row">
              <div class="stat-card" >
                <div class="stat-value">{{ project.member_count ?? 0 }}</div>
                <div class="stat-label">成员数</div>
              </div>
              <div class="stat-card"><div class="stat-value">{{ project.version_count ?? 0 }}</div><div class="stat-label">版本数</div></div>
              <div class="stat-card"><div class="stat-value">{{ caseCount }}</div><div class="stat-label">用例数</div></div>
            </div>
            <el-descriptions :column="2" border class="info-descriptions">
              <el-descriptions-item label="负责人">{{ project.leader || '—' }}</el-descriptions-item>
              <el-descriptions-item label="开始日期">{{ project.start_date || '—' }}</el-descriptions-item>
              <el-descriptions-item label="结束日期">{{ project.end_date || '—' }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatTime(project.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(project.updated_at) }}</el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">{{ project.description || '暂无描述' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- Tab 2: 版本管理 -->
        <el-tab-pane label="版本管理" name="versions">
          <div class="tab-toolbar">
            <span class="tab-count">共 {{ versionTotal }} 个版本</span>
            <el-button size="small" type="primary" @click="handleCreateVersion">新建版本</el-button>
          </div>
          <el-table :data="storeVersions" v-loading="versionsLoading" stripe style="width:100%">
            <el-table-column prop="name" label="版本号" min-width="140" align="center" />
            <el-table-column prop="project_name" label="关联项目" min-width="140" show-overflow-tooltip align="center">
              <template #default="{ row }">{{ row.project_name || project?.name || '—' }}</template>
            </el-table-column>
            <el-table-column label="状态" min-width="120" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="versionTagType(row.status)"
                  size="small" effect="plain"
                  style="cursor:pointer"
                  @click="handleVersionStatusTransition(row)"
                >
                  {{ versionLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="changelog" label="变更内容" min-width="200" show-overflow-tooltip align="center">
              <template #default="{ row }">{{ row.changelog || '—' }}</template>
            </el-table-column>
            <el-table-column label="创建时间" min-width="120" align="center">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button text size="small" type="primary" @click="handleEditVersion(row)">编辑</el-button>
                <el-button text size="small" type="danger" :disabled="row.status === 'released'" @click="handleDeleteVersion(row)">删除</el-button>
              </template>
            </el-table-column>
            <template #empty><el-empty description="暂无版本" /></template>
          </el-table>
        </el-tab-pane>

        <!-- Tab 3: 项目成员 -->
        <el-tab-pane label="项目成员" name="members">
          <div class="member-tab-header">
            <div class="member-filter-bar">
              <el-input v-model="memberSearchKeyword" placeholder="搜索用户名、邮箱、部门、职位..." clearable class="search-input" @input="onMemberSearch" />
              <el-select v-model="memberRoleFilter" placeholder="角色筛选" clearable class="role-select" @change="onMemberFilterChange">
                <el-option v-for="opt in ROLE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </div>
            <el-button type="primary" size="small" :icon="Plus" @click="handleAddMember">添加成员</el-button>
          </div>
          <div v-if="selectedMemberIds.length > 0" class="batch-bar">
            <span class="batch-info">已选择 {{ selectedMemberIds.length }} 项</span>
            <el-button size="small" type="danger" @click="handleBatchRemove">批量移除</el-button>
            <el-button size="small" @click="clearMemberSelection">取消选择</el-button>
          </div>
          <el-table ref="memberTableRef" :data="filteredMembers" v-loading="projectStore.membersLoading" stripe style="width:100%" @selection-change="onMemberSelectionChange">
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
                <el-button text size="small" type="danger" :disabled="row.user_id === currentUserId" @click="handleRemoveMember(row)">移除</el-button>
              </template>
            </el-table-column>
            <template #empty><el-empty description="暂无成员" /></template>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 编辑项目弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑项目" width="540px" :close-on-click-modal="false" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="80px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入项目名称" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="负责人" prop="leader">
          <el-input v-model="editForm.leader" placeholder="请输入负责人" maxlength="50" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="editForm.start_date" type="date" placeholder="选择开始日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="editForm.end_date" type="date" placeholder="选择结束日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="项目描述（选填）" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" placeholder="选择状态" style="width:100%">
            <el-option v-for="opt in PROJECT_STATUS_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleEditSubmit">确认保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建/编辑版本弹窗 -->
    <el-dialog v-model="versionDialogVisible" :title="isEditingVersion ? '编辑版本' : '新建版本'" width="480px" :close-on-click-modal="false" destroy-on-close>
      <el-form ref="versionFormRef" :model="versionForm" :rules="versionFormRules" label-width="80px">
        <el-form-item label="版本号" prop="name">
          <el-input v-model="versionForm.name" placeholder="如 v2.1.0" maxlength="100" />
        </el-form-item>
        <el-form-item label="变更内容" prop="changelog">
          <el-input v-model="versionForm.changelog" type="textarea" :rows="3" placeholder="本次变更内容（选填）" />
        </el-form-item>
        <el-form-item label="状态" prop="status" v-if="isEditingVersion">
          <el-select v-model="versionForm.status" placeholder="选择状态" style="width:100%">
            <el-option v-for="opt in VERSION_STATUS_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="versionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="versionSubmitting" @click="handleVersionSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员弹窗 -->
    <el-dialog v-model="addMemberDialogVisible" title="添加成员" width="540px" :close-on-click-modal="false" destroy-on-close>
      <el-form ref="addMemberFormRef" :model="addMemberForm" :rules="addMemberFormRules" label-width="80px">
        <el-form-item label="选择用户" prop="user_id">
          <el-select
            v-model="addMemberForm.user_id"
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
            <template #loading>
              <div style="padding:16px;text-align:center;color:#8B7355;font-size:13px;">正在搜索用户...</div>
            </template>
            <template #empty>
              <div style="padding:24px;text-align:center;color:#8B7355;font-size:13px;">
                <p style="margin:0 0 4px;">未找到匹配用户</p>
                <p style="margin:0;font-size:12px;">可输入用户名、邮箱搜索</p>
              </div>
            </template>
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="addMemberForm.role" style="flex-wrap:nowrap;white-space:nowrap">
            <el-radio-button value="admin">管理员</el-radio-button>
            <el-radio-button value="tester">测试人员</el-radio-button>
            <el-radio-button value="viewer">只读成员</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addMemberDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addMemberSubmitting" @click="handleAddMemberSubmit">确认添加</el-button>
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
import { useVersionStore } from '@/stores/aitest/version'
import {
  PROJECT_STATUS_OPTIONS, VERSION_STATUS_OPTIONS, ROLE_OPTIONS, ROLE_COLORS,
} from '@/types/aitest'
import type { TestVersionCreate, TestVersionUpdate, ProjectMember } from '@/types/aitest'
import type { AdminUserInfo } from '@/types/admin'
import type { FormInstance } from 'element-plus'
import { adminApi } from '@/api/admin'
import { aitestApi } from '@/api/aitest'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const versionStore = useVersionStore()

const projectId = computed(() => Number(route.params.id))
const project = computed(() => projectStore.currentProject)

const activeTab = ref('info')
const loading = ref(false)

// ===== 统计 =====
const caseCount = ref(0)

// ===== 成员管理 =====
const memberSearchKeyword = ref('')
const memberRoleFilter = ref('')
const selectedMemberIds = ref<number[]>([])
const memberTableRef = ref<any>(null)
const editingRoleUserId = ref<number | null>(null)
const editingRoleValue = ref<'admin' | 'tester' | 'viewer'>('tester')
const addMemberDialogVisible = ref(false)
const addMemberSubmitting = ref(false)
const addMemberFormRef = ref<FormInstance>()
const addMemberForm = ref<{ user_id: number | undefined; role: 'admin' | 'tester' | 'viewer' }>({ user_id: undefined, role: 'tester' })
const addMemberFormRules = {
  user_id: [{ required: true, message: '请选择用户', trigger: 'change' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}
const userOptions = ref<AdminUserInfo[]>([])
const userSearchLoading = ref(false)

const currentUserId = computed(() => {
  try { return Number(JSON.parse(localStorage.getItem('user') || '{}')?.id || 0) } catch { return 0 }
})

const filteredMembers = computed(() => {
  const members = projectStore.members
  return members.filter(m => {
    if (memberSearchKeyword.value) {
      const kw = memberSearchKeyword.value.toLowerCase()
      if (!(m.username || '').toLowerCase().includes(kw) &&
          !(m.email || '').toLowerCase().includes(kw) &&
          !(m.department || '').toLowerCase().includes(kw) &&
          !(m.position || '').toLowerCase().includes(kw)) return false
    }
    if (memberRoleFilter.value && m.role !== memberRoleFilter.value) return false
    return true
  })
})

// ===== 版本管理 =====
const storeVersions = computed(() => versionStore.versions)
const versionTotal = computed(() => versionStore.total)
const versionsLoading = ref(false)
const versionDialogVisible = ref(false)
const isEditingVersion = ref(false)
const editingVersionId = ref<number | null>(null)
const versionSubmitting = ref(false)
const versionFormRef = ref<FormInstance>()
const versionForm = ref({ name: '', changelog: '', status: 'in_progress' })
const versionFormRules = { name: [{ required: true, message: '请输入版本号', trigger: 'blur' }] }

// ===== 编辑项目弹窗 =====
const editDialogVisible = ref(false)
const submitting = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = ref({ name: '', leader: '', description: '', start_date: '', end_date: '', status: 'active' })
const editFormRules = { name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] }

// ===== 加载数据 =====
async function loadData() {
  loading.value = true
  try {
    await projectStore.fetchProject(projectId.value)
    if (projectStore.currentProject) {
      try {
        const statsRes = await (await import('@/api/aitest')).aitestApi.getTestCaseStats(projectId.value)
        caseCount.value = (statsRes.data as any)?.total ?? 0
      } catch { caseCount.value = 0 }
    }
  } catch { /* handled in store */ }
  loading.value = false
}

// ===== 成员管理 =====
async function loadMembers() {
  await projectStore.fetchMembers(projectId.value)
}

function onMemberSearch() { /* computed handles filtering */ }
function onMemberFilterChange() { /* computed handles filtering */ }

function onMemberSelectionChange(rows: any[]) {
  selectedMemberIds.value = rows.map((r: any) => r.user_id)
}

function clearMemberSelection() {
  memberTableRef.value?.clearSelection()
  selectedMemberIds.value = []
}

async function handleBatchRemove() {
  if (selectedMemberIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定移除选中的 ${selectedMemberIds.value.length} 个成员吗？`, '批量移除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await aitestApi.batchRemoveMembers(projectId.value, selectedMemberIds.value)
    ElMessage.success('批量移除成功')
    clearMemberSelection()
    await loadMembers()
    await loadData()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '批量移除失败')
    }
  }
}

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

function handleAddMember() {
  addMemberForm.value = { user_id: undefined, role: 'tester' }
  userOptions.value = []
  addMemberDialogVisible.value = true
}

async function handleAddMemberSubmit() {
  const valid = await addMemberFormRef.value?.validate().catch(() => false)
  if (!valid || !addMemberForm.value.user_id) {
    ElMessage.warning('请完善成员信息')
    return
  }
  addMemberSubmitting.value = true
  try {
    await projectStore.addMember(projectId.value, addMemberForm.value.user_id, addMemberForm.value.role)
    ElMessage.success('添加成功')
    addMemberDialogVisible.value = false
    await loadMembers()
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '添加失败')
  } finally { addMemberSubmitting.value = false }
}

async function handleRemoveMember(member: ProjectMember) {
  try {
    await ElMessageBox.confirm(`确定移除成员「${member.username || member.user_id}」吗？`, '确认移除', { type: 'warning' })
    const ok = await projectStore.removeMember(projectId.value, member.user_id)
    if (ok) {
      ElMessage.success('已移除')
      await loadMembers()
      await loadData()
    }
  } catch { /* cancel */ }
}

function avatarColor(name: string): string {
  const colors = ['#C67B5C', '#7BA87D', '#8B9DC3', '#D4745C', '#B8A07A', '#A87D9E']
  let hash = 0; for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

function roleLabel(role: string): string {
  return ROLE_OPTIONS.find(o => o.value === role)?.label || role
}

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

function onTabClick(tab: any) {
  if (tab.props.name === 'versions' && storeVersions.value.length === 0) {
    loadVersions()
  }
  if (tab.props.name === 'members' && projectStore.members.length === 0) {
    loadMembers()
  }
}

async function loadVersions() {
  versionsLoading.value = true
  versionStore.projectFilter = projectId.value
  versionStore.page = 1
  versionStore.pageSize = 50
  await versionStore.fetchVersions()
  versionsLoading.value = false
}

// ===== 版本 CRUD =====
function handleCreateVersion() {
  isEditingVersion.value = false
  editingVersionId.value = null
  versionForm.value = { name: '', changelog: '', status: 'in_progress' }
  versionDialogVisible.value = true
}

function handleEditVersion(v: any) {
  isEditingVersion.value = true
  editingVersionId.value = v.id
  versionForm.value = { name: v.name, changelog: v.changelog || '', status: v.status }
  versionDialogVisible.value = true
}

async function handleVersionSubmit() {
  const valid = await versionFormRef.value?.validate().catch(() => false)
  if (!valid) return
  versionSubmitting.value = true
  if (isEditingVersion.value && editingVersionId.value) {
    const data: TestVersionUpdate = { name: versionForm.value.name }
    if (versionForm.value.changelog) data.changelog = versionForm.value.changelog
    data.status = versionForm.value.status as any
    const ok = await versionStore.updateVersion(editingVersionId.value, data)
    if (!ok) { ElMessage.error('版本更新失败'); versionSubmitting.value = false; return }
    ElMessage.success('版本更新成功')
  } else {
    const data: TestVersionCreate = {
      project_id: projectId.value,
      name: versionForm.value.name,
    }
    if (versionForm.value.changelog) data.changelog = versionForm.value.changelog
    const created = await versionStore.createVersion(data)
    if (!created) { ElMessage.error('版本创建失败'); versionSubmitting.value = false; return }
    ElMessage.success('版本创建成功')
  }
  versionDialogVisible.value = false
  versionSubmitting.value = false
  // 刷新版本列表和项目统计
  await loadVersions()
  await loadData()
}

function handleVersionStatusTransition(v: any) {
  if (v.status === 'released') {
    ElMessageBox.confirm(`将版本「${v.name}」状态改为「已废弃」？`, '状态变更', { type: 'info' })
      .then(async () => {
        await versionStore.updateVersion(v.id, { status: 'obsolete' })
        ElMessage.success('状态已更新')
      }).catch(() => {})
  }
}

async function handleDeleteVersion(v: any) {
  try {
    await ElMessageBox.confirm(`确定删除版本「${v.name}」吗？`, '确认删除', { type: 'warning' })
    const ok = await versionStore.deleteVersion(v.id)
    if (ok) {
      ElMessage.success('删除成功')
      await loadData()
    }
  } catch { /* cancel */ }
}

// ===== 编辑项目 =====
function handleEditProject() {
  if (!project.value) return
  editForm.value = {
    name: project.value.name, leader: project.value.leader || '',
    description: project.value.description || '',
    start_date: project.value.start_date || '', end_date: project.value.end_date || '',
    status: project.value.status,
  }
  editDialogVisible.value = true
}

async function handleEditSubmit() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await projectStore.updateProject(projectId.value, editForm.value as any)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '更新失败')
  } finally { submitting.value = false }
}

async function handleDeleteProject() {
  if (!project.value) return
  try {
    await ElMessageBox.confirm(`确定删除项目「${project.value.name}」吗？`, '确认删除', { type: 'warning' })
    await projectStore.deleteProject(projectId.value)
    ElMessage.success('已删除')
    router.push('/modules/aitest/projects')
  } catch { /* cancel */ }
}

// ===== 工具函数 =====
function statusTagType(status?: string): string {
  const m: Record<string, string> = { active: 'success', completed: 'primary', archived: 'info' }
  return m[status || ''] || 'info'
}
function statusLabel(status?: string): string {
  const o = PROJECT_STATUS_OPTIONS.find(p => p.value === status)
  return o?.label || status || '—'
}
function versionTagType(status?: string): string {
  const m: Record<string, string> = { released: 'success', in_progress: 'primary', obsolete: 'info' }
  return m[status || ''] || 'info'
}
function versionLabel(status?: string): string {
  const o = VERSION_STATUS_OPTIONS.find(v => v.value === status)
  return o?.label || status || '—'
}
import { formatDate } from '@/utils'

function formatTime(t?: string | null): string {
  return formatDate(t)
}

onMounted(loadData)
</script>

<style scoped>
.page-wrap { margin: 0 auto; padding: 24px 16px; }
.back-nav { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #7A6855; margin-bottom: 16px; }
.back-arrow { font-size: 16px; cursor: pointer; color: var(--primary, #C67B5C); }
.back-arrow:hover { color: var(--primary-light, #D49472); }
.breadcrumb-link { cursor: pointer; }
.breadcrumb-link:hover { color: var(--primary, #C67B5C); }
.breadcrumb-sep { color: rgba(180,150,120,0.3); }
.breadcrumb-current { color: var(--text, #3D2E1F); font-weight: 500; }

.detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text, #3D2E1F); margin: 0; }
.header-actions { display: flex; gap: 8px; }

.stats-row { display: flex; gap: 16px; margin-bottom: 20px; }
.stat-card { flex: 1; padding: 20px; background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; text-align: center; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--primary, #C67B5C); line-height: 1.2; }
.stat-label { font-size: 13px; color: var(--text-muted, #8B7355); margin-top: 2px; }

.detail-tabs { background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; padding: 16px 20px; }
.info-descriptions { margin-bottom: 0; }
.tab-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.tab-count { font-size: 13px; color: var(--text-muted, #8B7355); }

/* 成员管理 */
.member-tab-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }
.member-filter-bar { display: flex; gap: 12px; flex: 1; }
.member-filter-bar :deep(.search-input) { flex: 1; min-width: 200px; max-width: 420px; }
.member-filter-bar :deep(.role-select) { width: 140px; }

.batch-bar { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: rgba(198,123,92,0.06); border-radius: 8px; margin-bottom: 12px; }
.batch-info { font-size: 13px; color: var(--text-secondary, #5C4A38); margin-right: 8px; }

.user-cell { display: flex; align-items: center; gap: 10px; }
.user-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; font-weight: 600; flex-shrink: 0; }
.user-info { display: flex; flex-direction: column; }
.user-name { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); }
.user-email { font-size: 11px; color: var(--text-muted, #8B7355); }

@media (max-width: 768px) {
  .page-wrap { padding: 16px 12px; }
  .stats-row { flex-direction: column; }
  .detail-header { flex-direction: column; align-items: flex-start; gap: 12px; }
}
</style>

<!-- 非 scoped 样式：el-select 远程搜索下拉面板被 teleport 到 body，scoped 样式无法穿透 -->
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
  overflow: hidden !important;
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
