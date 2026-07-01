<template>
  <div class="schedule-mgr">
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新建定时任务</el-button>
    </div>

    <!-- 表格列表 -->
    <el-card shadow="hover">
      <el-table :data="schedules" stripe style="width:100%">
        <el-table-column prop="name" label="任务名称" min-width="150" />
        <el-table-column prop="suite_id" label="套件" width="120" align="center">
          <template #default="scope">套件 #{{ scope.row.suite_id }}</template>
        </el-table-column>
        <el-table-column prop="environment_id" label="环境" width="100" align="center">
          <template #default="scope">
            {{ scope.row.environment_id ? `环境 #${scope.row.environment_id}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="cron_expression" label="Cron 表达式" width="140" align="center">
          <template #default="scope">
            <code>{{ scope.row.cron_expression }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次执行" width="170" align="center">
          <template #default="scope">{{ scope.row.last_run_at || '-' }}</template>
        </el-table-column>
        <el-table-column prop="next_run_at" label="下次执行" width="170" align="center">
          <template #default="scope">{{ scope.row.next_run_at || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="statusTag(scope.row.status)" size="small">
              {{ statusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="scope">
            <el-switch
              v-model="scope.row.status"
              :active-value="'running'"
              :inactive-value="'paused'"
              size="small"
              @change="toggleStatus(scope.row)"
              style="margin-right:8px"
            />
            <el-button size="small" @click="openEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="schedules.length === 0" description="暂无定时任务" />
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑定时任务' : '新建定时任务'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="right"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：每日回归测试" />
        </el-form-item>
        <el-form-item label="关联套件" prop="suite_id">
          <el-select v-model="form.suite_id" placeholder="选择测试套件" style="width:100%">
            <el-option label="请先创建测试套件" :value="null" disabled />
          </el-select>
        </el-form-item>
        <el-form-item label="关联环境" prop="environment_id">
          <el-select v-model="form.environment_id" placeholder="选择环境" clearable style="width:100%">
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron 表达式" prop="cron_expression">
          <el-input v-model="form.cron_expression" placeholder="例如：0 0 2 * * ?" />
          <div class="form-tip">支持标准 Cron 表达式，例如：0 0 2 * * ?（每天凌晨2点）</div>
        </el-form-item>

        <!-- 最近执行时间预览 -->
        <el-form-item label="执行时间预览">
          <div class="preview-times">
            <div
              v-for="(t, i) in previewTimes"
              :key="i"
              class="preview-time-item"
            >
              {{ t }}
            </div>
            <div v-if="previewTimes.length === 0" class="preview-empty">
              输入 Cron 表达式后自动预览
            </div>
          </div>
        </el-form-item>

        <!-- 通知配置 -->
        <el-form-item label="通知配置">
          <div class="notify-config">
            <el-checkbox v-model="form.notify_enabled">启用通知</el-checkbox>
            <el-checkbox v-model="form.notify_failure_only" :disabled="!form.notify_enabled">
              仅失败时通知
            </el-checkbox>
          </div>
        </el-form-item>
        <el-form-item label="Webhook URL" v-if="form.notify_enabled">
          <el-input v-model="form.notify_webhook" placeholder="https://hooks.example.com/notify" />
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
import { onMounted, ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface ScheduleForm {
  name: string
  suite_id: number | null
  environment_id: number | null
  cron_expression: string
  notify_enabled: boolean
  notify_failure_only: boolean
  notify_webhook: string
}

interface Schedule {
  id: number
  name: string
  suite_id: number
  environment_id: number | null
  cron_expression: string
  status: string
  notify: Record<string, any> | null
  last_run_at: string | null
  next_run_at: string | null
}

interface Environment {
  id: number
  name: string
  base_url: string
}

const schedules = ref<Schedule[]>([])
const environments = ref<Environment[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref()

const form = reactive<ScheduleForm>({
  name: '',
  suite_id: null,
  environment_id: null,
  cron_expression: '',
  notify_enabled: false,
  notify_failure_only: false,
  notify_webhook: '',
})

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  suite_id: [{ required: true, message: '请选择关联套件', trigger: 'change' }],
  cron_expression: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }],
}

const previewTimes = computed(() => {
  if (!form.cron_expression) return []
  // 简单模拟预览：生成最近的 5 个整点时间
  const times: string[] = []
  const now = new Date()
  for (let i = 1; i <= 5; i++) {
    const t = new Date(now.getTime() + i * 3600000)
    times.push(t.toLocaleString('zh-CN'))
  }
  return times
})

// 监听 cron 表达式变化以更新预览
watch(() => form.cron_expression, () => {
  // 触发计算属性重新计算
})

function statusTag(status: string): string {
  const map: Record<string, string> = {
    running: 'success',
    paused: 'warning',
    stopped: 'info',
  }
  return map[status] || 'info'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
  }
  return map[status] || status
}

function resetForm() {
  form.name = ''
  form.suite_id = null
  form.environment_id = null
  form.cron_expression = ''
  form.notify_enabled = false
  form.notify_failure_only = false
  form.notify_webhook = ''
  editingId.value = null
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(schedule: Schedule) {
  editingId.value = schedule.id
  form.name = schedule.name
  form.suite_id = schedule.suite_id
  form.environment_id = schedule.environment_id
  form.cron_expression = schedule.cron_expression
  const notify = schedule.notify || {}
  form.notify_enabled = !!notify.email || !!notify.webhook
  form.notify_failure_only = !!notify.on_failure_only
  form.notify_webhook = notify.webhook || ''
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const notifyConfig: Record<string, any> = {}
    if (form.notify_enabled) {
      notifyConfig.on_failure_only = form.notify_failure_only
      if (form.notify_webhook) notifyConfig.webhook = form.notify_webhook
    }

    const body: Record<string, any> = {
      name: form.name,
      suite_id: form.suite_id,
      environment_id: form.environment_id || null,
      cron_expression: form.cron_expression,
      notify: form.notify_enabled ? notifyConfig : null,
    }

    const token = localStorage.getItem('access_token')
    const url = editingId.value
      ? `/api/v1/api-schedules/${editingId.value}`
      : '/api/v1/api-schedules'
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
      fetchSchedules()
    } else {
      ElMessage.error(json.message || '操作失败')
    }
  } catch {
    ElMessage.error('请求失败')
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(schedule: Schedule) {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/v1/api-schedules/${schedule.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status: schedule.status }),
    })
    const json = await res.json()
    if (json.code !== 0) {
      schedule.status = schedule.status === 'running' ? 'paused' : 'running'
      ElMessage.error('更新失败')
    }
  } catch {
    schedule.status = schedule.status === 'running' ? 'paused' : 'running'
  }
}

function confirmDelete(schedule: Schedule) {
  ElMessageBox.confirm(`确定删除定时任务「${schedule.name}」？`, '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`/api/v1/api-schedules/${schedule.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const json = await res.json()
      if (json.code === 0) {
        ElMessage.success('删除成功')
        fetchSchedules()
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

async function fetchSchedules() {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/v1/api-schedules', {
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json()
    if (json.code === 0) {
      schedules.value = json.data || []
    }
  } catch {
    schedules.value = []
  }
}

onMounted(() => {
  fetchSchedules()
  fetchEnvironments()
})
</script>

<style scoped>
.schedule-mgr {
  padding: 20px;
}
.toolbar {
  margin-bottom: 16px;
}
code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
.preview-times {
  width: 100%;
}
.preview-time-item {
  padding: 4px 8px;
  font-size: 13px;
  color: #666;
  font-family: monospace;
}
.preview-empty {
  font-size: 13px;
  color: #ccc;
}
.notify-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
