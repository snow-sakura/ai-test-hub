<template>
  <!--
    AI 模型配置管理页面

    表格展示所有 AI 模型配置，支持新建、编辑、删除、设为活跃操作。
    API Key 显示脱敏（前4+后4），输入时使用密码框。
  -->
  <div class="page-wrap">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">AI 模型配置</h1>
      <el-button type="warning" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建模型配置
      </el-button>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-bar">
      <span class="batch-info">已选择 {{ selectedIds.length }} 项</span>
      <el-button size="small" type="danger" @click="handleBatchDelete">批量删除</el-button>
      <el-button size="small" @click="clearSelection">取消选择</el-button>
    </div>

    <!-- 模型表格 -->
    <el-card shadow="never" class="config-table-card">
      <el-table
        ref="tableRef"
        :data="modelList"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无模型配置"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column prop="name" label="配置名称" min-width="140" align="center" show-overflow-tooltip />
        <el-table-column label="模型类型" min-width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="modelTypeTag(row.model_type)" size="small" effect="plain">
              {{ row.model_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="130" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型名称" min-width="160" align="center" show-overflow-tooltip />
        <el-table-column prop="base_url" label="Base URL" min-width="200" show-overflow-tooltip align="center" />
        <el-table-column label="API Key" min-width="160" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="api-key-masked">{{ maskApiKey(row.api_key) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="参数" min-width="150" align="center">
          <template #default="{ row }">
            <span class="param-text">max_tokens: {{ row.max_tokens }}</span>
            <span class="param-text">temp: {{ row.temperature }}</span>
            <span class="param-text">top_p: {{ row.top_p }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="90" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="() => handleActivate(row)"
              active-text=""
              inactive-text=""
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="240" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" text type="success" @click="testConnection(row)">
              测试连接
            </el-button>
            <el-button size="small" text type="primary" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button size="small" text type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑模型配置' : '新建模型配置'"
      width="620px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        label-position="top"
        size="default"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="配置名称" prop="name">
              <el-input v-model="formData.name" placeholder="例如：DeepSeek V3 编写模型" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模型类型" prop="model_type">
              <el-select v-model="formData.model_type" placeholder="选择模型类型" style="width: 100%">
                <el-option label="DeepSeek" value="deepseek" />
                <el-option label="通义千问" value="qwen" />
                <el-option label="SiliconFlow" value="siliconflow" />
                <el-option label="OpenAI" value="openai" />
                <el-option label="Anthropic" value="anthropic" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色" prop="role">
              <el-select v-model="formData.role" placeholder="选择角色" style="width: 100%">
                <el-option label="编写模型(writer)" value="writer" />
                <el-option label="评审模型(reviewer)" value="reviewer" />
                <el-option label="浏览器操作(browser_use_text)" value="browser_use_text" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模型名称" prop="model_name">
              <el-input v-model="formData.model_name" placeholder="例如：deepseek-v4-flash" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="API Key" prop="api_key">
          <div class="api-key-row">
            <el-input
              v-model="formData.api_key"
              type="password"
              show-password
              :placeholder="isEditing ? '留空则不修改当前 Key' : '输入 API Key'"
              class="api-key-input"
            />
            <el-button
              size="small"
              type="success"
              :loading="testingConnection"
              @click="testConnectionFromForm"
            >
              测试连接
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="formData.base_url" placeholder="例如：https://api.deepseek.com" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="max_tokens">
              <el-slider
                v-model="formData.max_tokens"
                :min="512"
                :max="16384"
                :step="512"
                show-input
                input-size="small"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="temperature">
              <el-slider
                v-model="formData.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
                input-size="small"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="top_p">
              <el-slider
                v-model="formData.top_p"
                :min="0"
                :max="1"
                :step="0.05"
                show-input
                input-size="small"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="warning" :loading="submitting" @click="handleSubmit">
          {{ isEditing ? '保存修改' : '创建配置' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { configApi } from '@/api/configuration'
import { aitestApi } from '@/api/aitest'
import type { AIModelConfigDetail, AIModelConfigCreate, AIModelConfigUpdate } from '@/types/ai'
import type { TestConnectionRequest } from '@/types/aitest'
import type { FormInstance, FormRules } from 'element-plus'

// ====================================================================
// 状态管理
// ====================================================================

/** 模型配置列表 */
const modelList = ref<AIModelConfigDetail[]>([])
/** 加载状态 */
const loading = ref(false)
/** 对话框可见 */
const dialogVisible = ref(false)
/** 是否编辑模式 */
const isEditing = ref(false)
/** 当前编辑的 ID */
const editingId = ref<number | null>(null)
/** 提交中 */
const submitting = ref(false)
/** 测试连接中 */
const testingConnection = ref(false)
/** 表单引用 */
const formRef = ref<FormInstance>()

/** 多选删除 */
const selectedIds = ref<number[]>([])
const tableRef = ref<any>(null)

function handleSelectionChange(rows: any[]) {
  selectedIds.value = rows.map((r: any) => r.id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selectedIds.value = []
}

/** 批量删除 */
async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedIds.value.length} 个模型配置吗？`,
      '批量删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await configApi.batchDeleteModels(selectedIds.value)
    ElMessage.success('批量删除成功')
    clearSelection()
    await loadModelList()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '批量删除失败')
    }
  }
}

/** 表单数据 */
const formData = reactive<AIModelConfigCreate>({
  name: '',
  model_type: '',
  role: '',
  api_key: '',
  base_url: '',
  model_name: '',
  max_tokens: 4096,
  temperature: 0.7,
  top_p: 0.9,
})

/** 表单校验规则 */
const formRules: FormRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  model_type: [{ required: true, message: '请选择模型类型', trigger: 'change' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
}

// ====================================================================
// 生命周期
// ====================================================================

onMounted(() => {
  loadModelList()
})

// ====================================================================
// 方法
// ====================================================================

/** 加载模型配置列表 */
async function loadModelList() {
  loading.value = true
  try {
    const res = await configApi.getModelList()
    modelList.value = res.data || []
  } catch {
    ElMessage.error('加载模型配置失败')
  } finally {
    loading.value = false
  }
}

/** 模型类型标签颜色 */
function modelTypeTag(type: string): string {
  const map: Record<string, string> = {
    deepseek: 'success',
    qwen: 'primary',
    siliconflow: 'info',
    openai: 'warning',
    anthropic: 'danger',
  }
  return map[type] || 'info'
}

/** API Key 脱敏：仅显示前4+后4 */
function maskApiKey(key?: string): string {
  if (!key) return '-'
  if (key.length <= 8) return '****'
  return key.slice(0, 4) + '****' + key.slice(-4)
}

/** 打开创建对话框 */
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

/** 打开编辑对话框 */
function openEditDialog(row: AIModelConfigDetail) {
  isEditing.value = true
  editingId.value = row.id
  formData.name = row.name
  formData.model_type = row.model_type
  formData.role = row.role
  formData.api_key = ''  // 不预填脱敏值，留空表示不修改
  formData.base_url = row.base_url
  formData.model_name = row.model_name
  formData.max_tokens = row.max_tokens
  formData.temperature = row.temperature
  formData.top_p = row.top_p
  dialogVisible.value = true
}

/** 重置表单 */
function resetForm() {
  formData.name = ''
  formData.model_type = ''
  formData.role = ''
  formData.api_key = ''
  formData.base_url = ''
  formData.model_name = ''
  formData.max_tokens = 4096
  formData.temperature = 0.7
  formData.top_p = 0.9
  formRef.value?.clearValidate()
}

/** 提交表单 */
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      const updateData: AIModelConfigUpdate = { ...formData }
      // api_key 为空时表示不修改，从更新数据中移除
      if (!updateData.api_key) {
        delete updateData.api_key
      }
      await configApi.updateModel(editingId.value, updateData)
      ElMessage.success('模型配置已更新')
    } else {
      await configApi.createModel(formData)
      ElMessage.success('模型配置已创建')
    }
    dialogVisible.value = false
    await loadModelList()
  } catch (err: any) {
    const msg = err?.response?.data?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

/** 测试连接（从表格行数据） */
async function testConnection(row: AIModelConfigDetail) {
  testingConnection.value = true
  try {
    const req: TestConnectionRequest = {
      provider: row.model_type,
      api_key: '',
      base_url: row.base_url,
      model_name: row.model_name,
      max_tokens: row.max_tokens,
      temperature: row.temperature,
      top_p: row.top_p,
    }
    const res = await aitestApi.testAIConnection(req)
    if (res.data?.success) {
      ElMessage.success(`连接测试通过 ✅ (${res.data.model || row.model_name})`)
    } else {
      ElMessage.error(res.data?.message || '连接测试失败')
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '连接测试失败，请检查配置')
  } finally {
    testingConnection.value = false
  }
}

/** 测试连接（从对话框表单数据） */
async function testConnectionFromForm() {
  if (!formData.model_type || !formData.base_url || !formData.model_name) {
    ElMessage.warning('请先填写模型类型、Base URL 和模型名称')
    return
  }
  testingConnection.value = true
  try {
    const req: TestConnectionRequest = {
      provider: formData.model_type,
      api_key: formData.api_key || '',
      base_url: formData.base_url,
      model_name: formData.model_name,
      max_tokens: formData.max_tokens,
      temperature: formData.temperature,
      top_p: formData.top_p,
    }
    const res = await aitestApi.testAIConnection(req)
    if (res.data?.success) {
      ElMessage.success(`连接测试通过 ✅ (${res.data.model || formData.model_name})`)
    } else {
      ElMessage.error(res.data?.message || '连接测试失败')
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '连接测试失败，请检查配置')
  } finally {
    testingConnection.value = false
  }
}

/** 删除模型配置 */
async function handleDelete(row: AIModelConfigDetail) {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型配置「${row.name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await configApi.deleteModel(row.id)
    ElMessage.success('模型配置已删除')
    await loadModelList()
  } catch {
    // 取消删除不做处理
  }
}

/** 设为活跃 */
async function handleActivate(row: AIModelConfigDetail) {
  try {
    await configApi.activateModel(row.id)
    ElMessage.success(`「${row.name}」已设为活跃`)
    await loadModelList()
  } catch {
    ElMessage.error('设为活跃失败')
  }
}
</script>

<style scoped lang="scss">
.page-wrap {
  padding: 24px 16px;

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    .page-title {
      font-size: 22px;
      font-weight: 700;
      color: #3d2e1f;
      margin: 0;
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

    .batch-info {
      font-size: 13px;
      color: var(--text-secondary, #5C4A38);
      margin-right: 8px;
    }
  }

  .config-table-card {
    border: 1px solid rgba(180, 150, 120, 0.12);
    border-radius: 8px;
    background: #fffdf9;

    :deep(.el-card__body) {
      padding: 0;
    }
  }

  .api-key-masked {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: #8b7355;
    letter-spacing: 1px;
  }

  .api-key-row {
    display: flex;
    gap: 8px;
    width: 100%;

    .api-key-input {
      flex: 1;
    }
  }

  .param-text {
    display: block;
    font-size: 11px;
    color: #8b7355;
    line-height: 1.6;
  }
}
</style>
