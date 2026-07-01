<template>
  <div class="environment-mgr">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新建环境</el-button>
    </div>

    <!-- 卡片列表 -->
    <el-row :gutter="20">
      <el-col
        v-for="env in environments"
        :key="env.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
        class="env-col"
      >
        <el-card shadow="hover" :class="['env-card', `env-${envType(env.name)}`]">
          <div class="env-card__header">
            <div class="env-card__title">
              <span class="env-badge" :class="`badge-${envType(env.name)}`" />
              <span class="env-name">{{ env.name }}</span>
            </div>
            <el-switch
              v-model="env.status"
              :active-value="'active'"
              :inactive-value="'inactive'"
              @change="toggleStatus(env)"
            />
          </div>
          <div class="env-card__body">
            <div class="env-url">{{ env.base_url }}</div>
            <div class="env-meta">
              <span>变量: {{ env.variables ? Object.keys(env.variables).length : 0 }}</span>
              <span>请求头: {{ env.headers ? Object.keys(env.headers).length : 0 }}</span>
            </div>
          </div>
          <div class="env-card__actions">
            <el-button size="small" @click="openEdit(env)">编辑</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(env)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="environments.length === 0" description="暂无环境配置" />

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑环境' : '新建环境'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：开发环境、测试环境" />
        </el-form-item>
        <el-form-item label="基础URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="https://api.example.com" />
        </el-form-item>

        <!-- 环境变量（动态键值对） -->
        <el-form-item label="环境变量">
          <div class="kv-list">
            <div v-for="(item, index) in form.variables_list" :key="index" class="kv-row">
              <el-input v-model="item.key" placeholder="Key" style="width:200px" size="small" />
              <el-input v-model="item.value" placeholder="Value" style="width:240px" size="small" />
              <el-button type="danger" :icon="Delete" size="small" @click="removeVar(index)" />
            </div>
            <el-button type="primary" link @click="addVar">+ 添加变量</el-button>
          </div>
        </el-form-item>

        <!-- 请求头（动态键值对） -->
        <el-form-item label="请求头">
          <div class="kv-list">
            <div v-for="(item, index) in form.headers_list" :key="index" class="kv-row">
              <el-input v-model="item.key" placeholder="Key" style="width:200px" size="small" />
              <el-input v-model="item.value" placeholder="Value" style="width:240px" size="small" />
              <el-button type="danger" :icon="Delete" size="small" @click="removeHeader(index)" />
            </div>
            <el-button type="primary" link @click="addHeader">+ 添加请求头</el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

interface EnvItem {
  key: string
  value: string
}

interface EnvForm {
  name: string
  base_url: string
  variables_list: EnvItem[]
  headers_list: EnvItem[]
}

interface Environment {
  id: number
  name: string
  base_url: string
  variables: Record<string, string> | null
  headers: Record<string, string> | null
  status: string
}

const environments = ref<Environment[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref()

const form = reactive<EnvForm>({
  name: '',
  base_url: '',
  variables_list: [],
  headers_list: [],
})

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入基础URL', trigger: 'blur' }],
}

function envType(name: string): string {
  const lower = name.toLowerCase()
  if (lower.includes('开发') || lower.includes('dev') || lower.includes('develop')) return 'dev'
  if (lower.includes('测试') || lower.includes('test')) return 'test'
  if (lower.includes('预发') || lower.includes('预发布') || lower.includes('staging') || lower.includes('stage')) return 'staging'
  if (lower.includes('生产') || lower.includes('prod') || lower.includes('production')) return 'prod'
  return 'dev'
}

function kvToArray(obj: Record<string, string> | null | undefined): EnvItem[] {
  if (!obj) return []
  return Object.entries(obj).map(([key, value]) => ({ key, value }))
}

function arrayToKv(arr: EnvItem[]): Record<string, string> {
  const obj: Record<string, string> = {}
  for (const item of arr) {
    if (item.key) obj[item.key] = item.value
  }
  return obj
}

function addVar() {
  form.variables_list.push({ key: '', value: '' })
}

function removeVar(index: number) {
  form.variables_list.splice(index, 1)
}

function addHeader() {
  form.headers_list.push({ key: '', value: '' })
}

function removeHeader(index: number) {
  form.headers_list.splice(index, 1)
}

function resetForm() {
  form.name = ''
  form.base_url = ''
  form.variables_list = []
  form.headers_list = []
  editingId.value = null
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(env: Environment) {
  editingId.value = env.id
  form.name = env.name
  form.base_url = env.base_url
  form.variables_list = kvToArray(env.variables)
  form.headers_list = kvToArray(env.headers)
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const body = {
      name: form.name,
      base_url: form.base_url,
      variables: arrayToKv(form.variables_list),
      headers: arrayToKv(form.headers_list),
    }

    const token = localStorage.getItem('access_token')
    const url = editingId.value
      ? `/api/v1/api-environments/${editingId.value}`
      : '/api/v1/api-environments'
    const method = editingId.value ? 'PUT' : 'POST'

    const res = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    })
    const json = await res.json()
    if (json.code === 0) {
      ElMessage.success(editingId.value ? '更新成功' : '创建成功')
      dialogVisible.value = false
      fetchEnvironments()
    } else {
      ElMessage.error(json.message || '操作失败')
    }
  } catch {
    ElMessage.error('请求失败')
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(env: Environment) {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/v1/api-environments/${env.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status: env.status }),
    })
    const json = await res.json()
    if (json.code !== 0) {
      env.status = env.status === 'active' ? 'inactive' : 'active'
      ElMessage.error('更新失败')
    }
  } catch {
    env.status = env.status === 'active' ? 'inactive' : 'active'
  }
}

function confirmDelete(env: Environment) {
  ElMessageBox.confirm(`确定删除环境「${env.name}」？`, '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`/api/v1/api-environments/${env.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const json = await res.json()
      if (json.code === 0) {
        ElMessage.success('删除成功')
        fetchEnvironments()
      } else {
        ElMessage.error(json.message || '删除失败')
      }
    } catch {
      ElMessage.error('请求失败')
    }
  })
}

async function fetchEnvironments() {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/v1/api-environments', {
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json()
    if (json.code === 0) {
      environments.value = json.data || []
    }
  } catch {
    environments.value = []
  }
}

onMounted(fetchEnvironments)
</script>

<style scoped>
.environment-mgr {
  padding: 20px;
}
.toolbar {
  margin-bottom: 16px;
}
.env-col {
  margin-bottom: 20px;
}
.env-card {
  border-top: 3px solid #1890ff;
  transition: box-shadow 0.3s;
}
.env-card.env-dev {
  border-top-color: #1890ff;
}
.env-card.env-test {
  border-top-color: #52c41a;
}
.env-card.env-staging {
  border-top-color: #fa8c16;
}
.env-card.env-prod {
  border-top-color: #ff4d4f;
}
.env-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.env-card__title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.env-badge {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.badge-dev {
  background: #1890ff;
}
.badge-test {
  background: #52c41a;
}
.badge-staging {
  background: #fa8c16;
}
.badge-prod {
  background: #ff4d4f;
}
.env-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.env-card__body {
  margin-bottom: 12px;
}
.env-url {
  font-size: 13px;
  color: #666;
  word-break: break-all;
  margin-bottom: 8px;
  font-family: monospace;
}
.env-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}
.env-card__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}
.kv-list {
  width: 100%;
}
.kv-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
