<template>
  <!--
    用户管理页面

    el-table 展示用户列表，支持搜索过滤、状态切换、新建/编辑弹窗。
    暖色主题风格，与原型设计一致。
  -->
  <div class="page-wrap">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <el-button type="warning" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建用户
      </el-button>
    </div>

    <!-- 搜索过滤栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名、邮箱..."
        clearable
        class="search-input"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select
        v-model="searchStatus"
        placeholder="全部状态"
        clearable
        style="width: 140px"
        @change="handleSearch"
      >
        <el-option label="全部状态" value="" />
        <el-option label="已启用" :value="true" />
        <el-option label="已禁用" :value="false" />
      </el-select>
      <el-button type="warning" plain @click="handleSearch">搜索</el-button>
      <el-button plain @click="resetSearch">重置</el-button>
    </div>

    <!-- 用户表格 -->
    <el-card shadow="never" class="config-table-card">
      <el-table
        :data="userList"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无用户数据"
      >
        <el-table-column label="用户" min-width="200" show-overflow-tooltip align="center">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="user-avatar" :class="avatarColor(row.username)">
                {{ row.username.charAt(0) }}
              </div>
              <div class="user-info">
                <div class="user-name">{{ row.username }}</div>
                <div class="user-email">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" min-width="100" show-overflow-tooltip align="center" />
        <el-table-column prop="position" label="职位" min-width="100" show-overflow-tooltip align="center" />
        <el-table-column label="角色" min-width="160" align="center">
          <template #default="{ row }">
            <div class="role-tags">
              <el-tag v-if="row.is_superuser" size="small" type="warning" effect="plain" class="role-tag">管理员</el-tag>
              <el-tag
                v-for="role in row.roles"
                :key="role.id"
                size="small"
                effect="plain"
                class="role-tag"
              >
                {{ role.name }}
              </el-tag>
              <span v-if="!row.is_superuser && (!row.roles || row.roles.length === 0)" class="no-role">未分配</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="100" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="() => handleToggleActive(row)"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column label="最后登录" min-width="130" show-overflow-tooltip align="center">
          <template #default="{ row }">
            <span class="time-text">{{ row.last_login ? formatTime(row.last_login) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="130" show-overflow-tooltip align="center">
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="210" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button size="small" text type="primary" @click="openResetPwdDialog(row)">
              重置密码
            </el-button>
            <el-button size="small" text type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
          @change="loadUsers"
        />
      </div>
    </el-card>

    <!-- 新建/编辑用户弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑用户' : '新建用户'"
      width="580px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        label-position="top"
        size="default"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="formData.username" placeholder="输入用户名" :disabled="isEditing" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="formData.email" placeholder="输入邮箱地址" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="密码" prop="password" v-if="!isEditing">
              <el-input v-model="formData.password" type="password" show-password placeholder="设置密码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="formData.phone" placeholder="输入手机号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="部门">
              <el-input v-model="formData.department" placeholder="所属部门" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位">
              <el-input v-model="formData.position" placeholder="职位" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="formData.is_active" active-text="已启用" inactive-text="已禁用" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="超级管理员">
              <el-switch v-model="formData.is_superuser" active-text="是" inactive-text="否" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="关联角色">
              <el-select
                v-model="formData.role_ids"
                multiple
                filterable
                placeholder="选择要关联的角色"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="role in allRoles"
                  :key="role.id"
                  :label="role.name"
                  :value="role.id"
                >
                  <span>{{ role.name }}</span>
                  <span style="color: #8b7355; font-size: 12px; margin-left: 8px">{{ role.code }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="warning" :loading="submitting" @click="handleSubmit">
          {{ isEditing ? '保存修改' : '创建用户' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 重置密码弹窗 -->
    <el-dialog
      v-model="resetPwdVisible"
      title="重置密码"
      width="420px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="resetPwdFormRef"
        :model="resetPwdForm"
        :rules="resetPwdRules"
        label-width="80px"
      >
        <el-form-item label="新密码" prop="password">
          <el-input
            v-model="resetPwdForm.password"
            type="password"
            show-password
            placeholder="输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="warning" :loading="submitting" @click="handleResetPwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import type { AdminUserInfo, AdminUserCreate, AdminUserUpdate, ResetPasswordRequest, RoleInfo } from '@/types/admin'
import type { FormInstance, FormRules } from 'element-plus'

// ====================================================================
// 状态管理
// ====================================================================

const userList = ref<AdminUserInfo[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const searchKeyword = ref('')
const searchStatus = ref<boolean | ''>('')

/** 所有角色列表（用于选择器） */
const allRoles = ref<RoleInfo[]>([])

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const resetPwdVisible = ref(false)
const resetPwdUserId = ref<number | null>(null)
const resetPwdFormRef = ref<FormInstance>()
const resetPwdForm = reactive<ResetPasswordRequest>({ password: '' })

/** 表单数据 */
const formData = reactive<AdminUserCreate>({
  username: '',
  email: '',
  password: '',
  phone: '',
  department: '',
  position: '',
  is_active: true,
  is_superuser: false,
  role_ids: [],
})

/** 表单校验规则 */
const formRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于6位', trigger: 'blur' },
  ],
}

/** 重置密码校验规则 */
const resetPwdRules: FormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于6位', trigger: 'blur' },
  ],
}

// ====================================================================
// 生命周期
// ====================================================================

onMounted(() => {
  loadUsers()
  loadRoles()
})

// ====================================================================
// 方法
// ====================================================================

/** 加载用户列表 */
async function loadUsers() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchStatus.value !== '') params.is_active = searchStatus.value

    const res = await adminApi.getUsers(params)
    userList.value = res.data || []
    total.value = res.pagination?.total || 0
  } catch {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

/** 加载角色列表（用于选择器） */
async function loadRoles() {
  try {
    const res = await adminApi.getRoles()
    allRoles.value = res.data || []
  } catch {
    // 角色加载失败不影响主流程
    console.warn('加载角色列表失败')
  }
}

/** 搜索 */
function handleSearch() {
  currentPage.value = 1
  loadUsers()
}

/** 重置搜索 */
function resetSearch() {
  searchKeyword.value = ''
  searchStatus.value = ''
  currentPage.value = 1
  loadUsers()
}

/** 用户头像颜色 */
function avatarColor(name: string): string {
  const colors = ['avatar-purple', 'avatar-blue', 'avatar-green', 'avatar-orange', 'avatar-gray']
  const index = name.charCodeAt(0) % colors.length
  return colors[index]
}

import { formatDateTime } from '@/utils'

/** 格式化时间 */
function formatTime(time?: string): string {
  if (!time) return '-'
  return formatDateTime(time)
}

/** 打开创建对话框 */
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

/** 打开编辑对话框 */
function openEditDialog(row: AdminUserInfo) {
  isEditing.value = true
  editingId.value = row.id
  formData.username = row.username
  formData.email = row.email
  formData.phone = row.phone || ''
  formData.department = row.department || ''
  formData.position = row.position || ''
  formData.is_active = row.is_active
  formData.is_superuser = row.is_superuser
  formData.password = ''
  // 从用户已关联的角色中提取 role_ids
  formData.role_ids = row.roles ? row.roles.map(r => r.id) : []
  dialogVisible.value = true
}

/** 打开重置密码对话框 */
function openResetPwdDialog(row: AdminUserInfo) {
  resetPwdUserId.value = row.id
  resetPwdForm.password = ''
  resetPwdVisible.value = true
  resetPwdFormRef.value?.clearValidate()
}

/** 重置表单 */
function resetForm() {
  formData.username = ''
  formData.email = ''
  formData.password = ''
  formData.phone = ''
  formData.department = ''
  formData.position = ''
  formData.is_active = true
  formData.is_superuser = false
  formData.role_ids = []
  formRef.value?.clearValidate()
}

/** 提交表单 */
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      const updateData: AdminUserUpdate = {
        email: formData.email,
        phone: formData.phone || undefined,
        department: formData.department || undefined,
        position: formData.position || undefined,
        is_active: formData.is_active,
        is_superuser: formData.is_superuser,
        role_ids: formData.role_ids,
      }
      await adminApi.updateUser(editingId.value, updateData)
      ElMessage.success('用户信息已更新')
    } else {
      const createData: AdminUserCreate = {
        ...formData,
        role_ids: formData.role_ids && formData.role_ids.length > 0 ? formData.role_ids : undefined,
      }
      await adminApi.createUser(createData)
      ElMessage.success('用户已创建')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.response?.data?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

/** 切换用户启用/禁用状态 */
async function handleToggleActive(row: AdminUserInfo) {
  try {
    await adminApi.updateUser(row.id, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? '用户已禁用' : '用户已启用')
    await loadUsers()
  } catch {
    ElMessage.error('操作失败')
  }
}

/** 删除用户 */
async function handleDelete(row: AdminUserInfo) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户「${row.username}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await adminApi.deleteUser(row.id)
    ElMessage.success('用户已删除')
    await loadUsers()
  } catch {
    // 取消删除不做处理
  }
}

/** 重置密码 */
async function handleResetPwd() {
  const valid = await resetPwdFormRef.value?.validate().catch(() => false)
  if (!valid || !resetPwdUserId.value) return

  submitting.value = true
  try {
    await adminApi.resetPassword(resetPwdUserId.value, resetPwdForm)
    ElMessage.success('密码重置成功')
    resetPwdVisible.value = false
  } catch (err: any) {
    const msg = err?.response?.data?.message || '密码重置失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}
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
    color: var(--text, #3D2E1F);
    margin: 0;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;

  .search-input {
    flex: 1;
    min-width: 200px;
    max-width: 420px;
  }
}

.config-table-card {
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;

  :deep(.el-card__body) {
    padding: 0;
  }

  .pagination-wrap {
    display: flex;
    justify-content: flex-end;
    padding: 16px 0 4px;
  }

  .time-text {
    font-size: 13px;
    color: #8b7355;
  }
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;

  &.avatar-purple { background: rgba(130, 100, 180, 0.12); color: #6a5090; }
  &.avatar-blue { background: rgba(70, 130, 180, 0.12); color: #2c5f8a; }
  &.avatar-green { background: rgba(107, 158, 107, 0.12); color: #4a7a4a; }
  &.avatar-orange { background: rgba(212, 165, 116, 0.15); color: #b8894a; }
  &.avatar-gray { background: rgba(180, 150, 120, 0.12); color: #8b7355; }
}

.user-info {
  .user-name {
    font-size: 14px;
    font-weight: 500;
    color: #3d2e1f;
  }
  .user-email {
    font-size: 12px;
    color: #8b7355;
  }
}

.role-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  justify-content: center;
}

.role-tag {
  border-color: rgba(198, 123, 92, 0.2) !important;
  color: #c67b5c !important;
  background: rgba(198, 123, 92, 0.06) !important;
}

.no-role {
  font-size: 12px;
  color: #8b7355;
}
</style>
