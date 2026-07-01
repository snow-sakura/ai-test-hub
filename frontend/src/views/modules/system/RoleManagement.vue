<template>
  <!--
    角色权限管理页面

    左侧角色列表（支持搜索、新建、编辑、删除），右侧角色详情+权限配置。
  -->
  <div class="role-management">
    <!-- 主内容区：左右分栏 -->
    <div class="content-layout">
      <!-- 左侧角色列表 -->
      <div class="roles-panel">
        <el-card shadow="never" class="panel-card">
          <div class="panel-header">
            <span class="panel-title">角色列表</span>
            <el-button size="small" type="warning" :icon="Plus" @click="openCreateRoleDialog" />
          </div>

          <!-- 搜索框 -->
          <div class="role-search">
            <el-input
              v-model="roleSearchKeyword"
              placeholder="搜索角色..."
              clearable
              size="small"
              @clear="filterRoles"
              @input="filterRoles"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="role-list">
            <div
              v-for="role in filteredRoles"
              :key="role.id"
              class="role-item"
              :class="{ active: selectedRole?.id === role.id }"
              @click="selectRole(role)"
            >
              <div class="role-item-main">
                <div class="role-name">
                  {{ role.name }}
                  <el-tag v-if="role.is_system" size="small" type="info" effect="plain" class="system-tag">系统</el-tag>
                </div>
                <div class="role-meta">
                  <span>{{ role.description || role.code }}</span>
                </div>
              </div>
              <div class="role-item-actions" v-if="!role.is_system">
                <el-button size="small" text @click.stop="openEditRoleDialog(role)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click.stop="handleDeleteRole(role)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>

            <div v-if="filteredRoles.length === 0" class="empty-tip">
              {{ roleSearchKeyword ? '未找到匹配角色' : '暂无角色数据' }}
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧权限配置 -->
      <div class="perms-panel">
        <el-card v-if="selectedRole" shadow="never" class="panel-card">
          <div class="panel-header">
            <span class="panel-title">权限配置 - {{ selectedRole.name }}</span>
            <div class="header-actions">
              <el-button size="small" text type="primary" @click="openEditRoleDialog(selectedRole)">
                编辑角色
              </el-button>
              <el-button
                v-if="!selectedRole.is_system"
                size="small"
                text
                type="danger"
                @click="handleDeleteRole(selectedRole)"
              >
                删除角色
              </el-button>
            </div>
          </div>

          <!-- 角色信息卡片 -->
          <div class="role-info-card">
            <div class="info-item">
              <span class="info-label">角色编码</span>
              <span class="info-value">{{ selectedRole.code }}</span>
            </div>
            <div class="info-item" v-if="selectedRole.description">
              <span class="info-label">角色描述</span>
              <span class="info-value">{{ selectedRole.description }}</span>
            </div>
          </div>

          <!-- 权限列表 -->
          <div v-for="section in permissionSections" :key="section.key" class="perm-section">
            <div class="perm-section-title">{{ section.label }}</div>
            <div class="perm-grid">
              <div
                v-for="perm in section.permissions"
                :key="perm.key"
                class="perm-item"
              >
                <span class="perm-label">{{ perm.label }}</span>
                <el-checkbox
                  v-model="perm.checked"
                  size="small"
                  @change="handlePermChange"
                />
              </div>
            </div>
          </div>

          <div class="btn-group">
            <el-button @click="resetPerms">取消</el-button>
            <el-button type="warning" :loading="savingPerms" @click="handleSavePerms">
              保存权限
            </el-button>
          </div>
        </el-card>

        <el-card v-else shadow="never" class="panel-card">
          <div class="empty-state">
            <el-icon :size="48" color="#d4a574"><Lock /></el-icon>
            <p>请从左侧选择一个角色</p>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 新建/编辑角色弹窗 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditingRole ? '编辑角色' : '新建角色'"
      width="480px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleFormRules"
        label-width="90px"
        label-position="top"
      >
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="如：测试主管" />
        </el-form-item>
        <el-form-item label="角色编码" prop="code">
          <el-input v-model="roleForm.code" placeholder="如：test_leader" :disabled="isEditingRole" />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            :rows="3"
            placeholder="描述该角色的权限范围..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="warning" :loading="submittingRole" @click="handleSubmitRole">
          {{ isEditingRole ? '保存修改' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Lock, Edit, Delete, Search } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import type { RoleInfo, RoleCreate, RoleUpdate } from '@/types/admin'
import type { FormInstance, FormRules } from 'element-plus'

// ====================================================================
// 权限配置（可扩展的权限模块定义）
// ====================================================================

interface PermissionItem {
  key: string
  label: string
  checked: boolean
}

interface PermissionSection {
  key: string
  label: string
  permissions: PermissionItem[]
}

const defaultPermSections: PermissionSection[] = [
  {
    key: 'dashboard',
    label: '首页仪表盘',
    permissions: [
      { key: 'dashboard:view', label: '查看仪表盘', checked: true },
      { key: 'dashboard:export', label: '导出报告', checked: false },
    ],
  },
  {
    key: 'aitest',
    label: 'AI智能测试',
    permissions: [
      { key: 'aitest:view', label: '查看', checked: true },
      { key: 'aitest:create', label: '新增用例', checked: false },
      { key: 'aitest:edit', label: '编辑用例', checked: false },
      { key: 'aitest:delete', label: '删除用例', checked: false },
      { key: 'aitest:execute', label: '执行测试', checked: false },
      { key: 'aitest:export', label: '导出用例', checked: false },
      { key: 'aitest:view_plan', label: '查看计划', checked: true },
      { key: 'aitest:create_plan', label: '新建计划', checked: false },
      { key: 'aitest:edit_plan', label: '编辑计划', checked: false },
      { key: 'aitest:delete_plan', label: '删除计划', checked: false },
      { key: 'aitest:view_report', label: '查看报告', checked: false },
      { key: 'aitest:export_report', label: '导出报告', checked: false },
    ],
  },
  {
    key: 'api_testing',
    label: 'API接口测试',
    permissions: [
      { key: 'api_testing:view', label: '查看', checked: true },
      { key: 'api_testing:create', label: '新增请求', checked: false },
      { key: 'api_testing:edit', label: '编辑请求', checked: false },
      { key: 'api_testing:execute', label: '执行测试', checked: false },
    ],
  },
  {
    key: 'ui_automation',
    label: 'UI自动化测试',
    permissions: [
      { key: 'ui_automation:view', label: '查看', checked: true },
      { key: 'ui_automation:create', label: '创建测试', checked: false },
      { key: 'ui_automation:edit', label: '编辑测试', checked: false },
      { key: 'ui_automation:execute', label: '执行测试', checked: false },
      { key: 'ui_automation:report', label: '查看报告', checked: false },
      { key: 'ui_automation:delete', label: '删除测试', checked: false },
    ],
  },
  {
    key: 'configuration',
    label: '配置中心',
    permissions: [
      { key: 'configuration:view', label: '查看配置', checked: true },
      { key: 'configuration:edit', label: '编辑配置', checked: false },
    ],
  },
  {
    key: 'system',
    label: '系统管理',
    permissions: [
      { key: 'system:user', label: '用户管理', checked: false },
      { key: 'system:role', label: '角色权限', checked: false },
      { key: 'system:settings', label: '系统设置', checked: false },
      { key: 'system:audit', label: '审计日志', checked: false },
    ],
  },
]

// ====================================================================
// 状态管理
// ====================================================================

const roleList = ref<RoleInfo[]>([])
const selectedRole = ref<RoleInfo | null>(null)
const permissionSections = ref<PermissionSection[]>([])
const savingPerms = ref(false)

/** 角色搜索关键词 */
const roleSearchKeyword = ref('')

/** 过滤后的角色列表 */
const filteredRoles = computed(() => {
  if (!roleSearchKeyword.value) return roleList.value
  const kw = roleSearchKeyword.value.toLowerCase()
  return roleList.value.filter(
    r => r.name.toLowerCase().includes(kw) || r.code.toLowerCase().includes(kw)
  )
})

function filterRoles() {
  // computed 自动响应
}

const roleDialogVisible = ref(false)
const isEditingRole = ref(false)
const editingRoleId = ref<number | null>(null)
const submittingRole = ref(false)
const roleFormRef = ref<FormInstance>()

const roleForm = reactive<RoleCreate>({
  name: '',
  code: '',
  description: '',
})

const roleFormRules: FormRules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
}

// ====================================================================
// 生命周期
// ====================================================================

onMounted(() => {
  loadRoles()
})

// ====================================================================
// 方法
// ====================================================================

/** 加载角色列表 */
async function loadRoles() {
  try {
    const res = await adminApi.getRoles()
    roleList.value = res.data || []
    // 默认选中第一个
    if (roleList.value.length > 0) {
      selectRole(roleList.value[0])
    }
  } catch {
    ElMessage.error('加载角色列表失败')
  }
}

/** 选择角色 */
function selectRole(role: RoleInfo) {
  selectedRole.value = role
  // 从角色 stored permissions 或默认值构建权限列表
  const storedPerms = role.permissions || {}
  permissionSections.value = defaultPermSections.map((section) => ({
    ...section,
    permissions: section.permissions.map((perm) => ({
      ...perm,
      checked: storedPerms[perm.key] !== undefined ? !!storedPerms[perm.key] : perm.checked,
    })),
  }))
}

/** 权限变更处理 */
function handlePermChange() {
  // 标记权限已修改，等待保存
}

/** 重置权限到角色存储值 */
function resetPerms() {
  if (selectedRole.value) {
    selectRole(selectedRole.value)
  }
}

/** 保存权限 */
async function handleSavePerms() {
  if (!selectedRole.value) return

  savingPerms.value = true
  try {
    // 构建 permissions 字典
    const permissions: Record<string, boolean> = {}
    permissionSections.value.forEach((section) => {
      section.permissions.forEach((perm) => {
        permissions[perm.key] = perm.checked
      })
    })

    await adminApi.updateRole(selectedRole.value.id, { permissions })
    ElMessage.success('权限已保存')
    await loadRoles()
  } catch {
    ElMessage.error('保存权限失败')
  } finally {
    savingPerms.value = false
  }
}

/** 打开创建角色对话框 */
function openCreateRoleDialog() {
  isEditingRole.value = false
  editingRoleId.value = null
  roleForm.name = ''
  roleForm.code = ''
  roleForm.description = ''
  roleDialogVisible.value = true
  roleFormRef.value?.clearValidate()
}

/** 打开编辑角色对话框 */
function openEditRoleDialog(role: RoleInfo) {
  isEditingRole.value = true
  editingRoleId.value = role.id
  roleForm.name = role.name
  roleForm.code = role.code
  roleForm.description = role.description || ''
  roleDialogVisible.value = true
  roleFormRef.value?.clearValidate()
}

/** 提交角色（创建或编辑） */
async function handleSubmitRole() {
  const valid = await roleFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submittingRole.value = true
  try {
    if (isEditingRole.value && editingRoleId.value) {
      // 编辑模式
      const updateData: RoleUpdate = {
        name: roleForm.name,
        description: roleForm.description || undefined,
      }
      await adminApi.updateRole(editingRoleId.value, updateData)
      ElMessage.success('角色已更新')
    } else {
      // 创建模式
      await adminApi.createRole(roleForm)
      ElMessage.success('角色已创建')
    }
    roleDialogVisible.value = false
    await loadRoles()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.response?.data?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    submittingRole.value = false
  }
}

/** 删除角色 */
async function handleDeleteRole(role: RoleInfo) {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色「${role.name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await adminApi.deleteRole(role.id)
    ElMessage.success('角色已删除')
    // 如果删除的是当前选中的角色，清除选中
    if (selectedRole.value?.id === role.id) {
      selectedRole.value = null
    }
    await loadRoles()
  } catch {
    // 取消删除不做处理
  }
}
</script>

<style scoped lang="scss">
.role-management {
  .content-layout {
    display: flex;
    gap: 20px;
    align-items: flex-start;
  }

  .roles-panel {
    width: 300px;
    flex-shrink: 0;
  }

  .perms-panel {
    flex: 1;
    min-width: 0;
  }

  .panel-card {
    border: 1px solid rgba(180, 150, 120, 0.12);
    border-radius: 8px;
    background: #fffdf9;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(180, 150, 120, 0.12);

    .panel-title {
      font-size: 15px;
      font-weight: 600;
      color: #3d2e1f;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .role-search {
    margin-bottom: 12px;
  }

  .role-list {
    max-height: 500px;
    overflow-y: auto;
  }

  .role-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px;
    border-radius: 8px;
    border: 1px solid rgba(180, 150, 120, 0.12);
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 8px;

    &:hover {
      border-color: #d49472;

      .role-item-actions {
        opacity: 1;
      }
    }

    &.active {
      border-color: #c67b5c;
      background: rgba(198, 123, 92, 0.04);
    }

    .role-item-main {
      flex: 1;
      min-width: 0;
    }

    .role-item-actions {
      opacity: 0;
      transition: opacity 0.2s;
      display: flex;
      gap: 2px;
      margin-left: 8px;
    }
  }

  .role-name {
    font-size: 14px;
    font-weight: 600;
    color: #3d2e1f;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .system-tag {
    font-size: 10px;
    padding: 0 4px;
    height: 18px;
    line-height: 18px;
  }

  .role-meta {
    font-size: 12px;
    color: #8b7355;
    display: flex;
    gap: 12px;
  }

  .role-info-card {
    background: var(--bg, #fbf7f0);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 20px;
    display: flex;
    gap: 24px;

    .info-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .info-label {
      font-size: 12px;
      color: #8b7355;
    }

    .info-value {
      font-size: 13px;
      color: #3d2e1f;
      font-weight: 500;
    }
  }

  .empty-tip {
    text-align: center;
    color: #8b7355;
    font-size: 13px;
    padding: 20px 0;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 0;
    color: #8b7355;
    gap: 12px;

    p {
      font-size: 14px;
    }
  }

  .perm-section {
    margin-bottom: 20px;
  }

  .perm-section-title {
    font-size: 14px;
    font-weight: 600;
    color: #3d2e1f;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(180, 150, 120, 0.12);
  }

  .perm-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .perm-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid rgba(180, 150, 120, 0.12);
    background: #fffdf9;

    .perm-label {
      font-size: 14px;
      color: #5c4a38;
    }
  }

  .btn-group {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid rgba(180, 150, 120, 0.12);
  }
}
</style>
