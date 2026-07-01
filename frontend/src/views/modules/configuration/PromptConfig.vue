<template>
  <!--
    提示词配置管理页面

    表格展示所有提示词配置，支持新建、编辑、删除操作。
    提示词编辑器使用大文本框，内容预览可展开。
  -->
  <div class="page-wrap">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">提示词配置</h1>
      <el-button type="warning" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建提示词
      </el-button>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-bar">
      <span class="batch-info">已选择 {{ selectedIds.length }} 项</span>
      <el-button size="small" type="danger" @click="handleBatchDelete">批量删除</el-button>
      <el-button size="small" @click="clearSelection">取消选择</el-button>
    </div>

    <!-- 提示词表格 -->
    <el-card shadow="never" class="config-table-card">
      <el-table
        ref="tableRef"
        :data="promptList"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无提示词配置"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column prop="name" label="配置名称" min-width="160" align="center" show-overflow-tooltip />
        <el-table-column label="类型" min-width="130" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.prompt_type === 'writer' ? 'success' : 'primary'"
              size="small"
              effect="plain"
            >
              {{ row.prompt_type === 'writer' ? '编写提示词' : row.prompt_type === 'analyzer' ? '需求分析提示词' : row.prompt_type === 'improver' ? '用例改进提示词' : '评审提示词' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="内容预览" min-width="300" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="content-preview">{{ row.content }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.is_active ? 'success' : 'info'"
              size="small"
              effect="plain"
            >
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="160" fixed="right" align="center">
          <template #default="{ row }">
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
      :title="isEditing ? '编辑提示词' : '新建提示词'"
      width="700px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        label-position="top"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="配置名称" prop="name">
              <el-input v-model="formData.name" placeholder="例如：标准评审提示词" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="提示词类型" prop="prompt_type">
              <el-select v-model="formData.prompt_type" placeholder="选择类型" style="width: 100%">
                <el-option label="编写提示词(writer)" value="writer" />
                <el-option label="评审提示词(reviewer)" value="reviewer" />
                <el-option label="需求分析提示词(analyzer)" value="analyzer" />
                <el-option label="用例改进提示词(improver)" value="improver" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="提示词内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="12"
            placeholder="请输入提示词内容..."
          />
        </el-form-item>

        <div class="content-hint">
          提示：使用 <code>{context}</code>、<code>{test_cases}</code> 等占位符表示动态插入的内容。
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="warning" :loading="submitting" @click="handleSubmit">
          {{ isEditing ? '保存修改' : '创建提示词' }}
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
import type { PromptConfigDetail, PromptConfigCreate, PromptConfigUpdate } from '@/types/ai'
import type { FormInstance, FormRules } from 'element-plus'

// ====================================================================
// 状态管理
// ====================================================================

/** 提示词配置列表 */
const promptList = ref<PromptConfigDetail[]>([])
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
      `确定删除选中的 ${selectedIds.value.length} 个提示词配置吗？`,
      '批量删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await configApi.batchDeletePrompts(selectedIds.value)
    ElMessage.success('批量删除成功')
    clearSelection()
    await loadPromptList()
  } catch (e: any) {
    if (e?.code !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '批量删除失败')
    }
  }
}

/** 表单数据 */
const formData = reactive<PromptConfigCreate>({
  name: '',
  prompt_type: '',
  content: '',
})

/** 表单校验规则 */
const formRules: FormRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  prompt_type: [{ required: true, message: '请选择提示词类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入提示词内容', trigger: 'blur' }],
}

// ====================================================================
// 生命周期
// ====================================================================

onMounted(() => {
  loadPromptList()
})

// ====================================================================
// 方法
// ====================================================================

/** 加载提示词配置列表 */
async function loadPromptList() {
  loading.value = true
  try {
    const res = await configApi.getPromptList()
    promptList.value = res.data || []
  } catch {
    ElMessage.error('加载提示词配置失败')
  } finally {
    loading.value = false
  }
}

/** 打开创建对话框 */
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  formData.name = ''
  formData.prompt_type = ''
  formData.content = ''
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

/** 打开编辑对话框 */
function openEditDialog(row: PromptConfigDetail) {
  isEditing.value = true
  editingId.value = row.id
  formData.name = row.name
  formData.prompt_type = row.prompt_type
  formData.content = row.content
  dialogVisible.value = true
}

/** 提交表单 */
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      const updateData: PromptConfigUpdate = { ...formData }
      await configApi.updatePrompt(editingId.value, updateData)
      ElMessage.success('提示词已更新')
    } else {
      await configApi.createPrompt(formData)
      ElMessage.success('提示词已创建')
    }
    dialogVisible.value = false
    await loadPromptList()
  } catch (err: any) {
    const msg = err?.response?.data?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

/** 删除提示词 */
async function handleDelete(row: PromptConfigDetail) {
  try {
    await ElMessageBox.confirm(
      `确定要删除提示词「${row.name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await configApi.deletePrompt(row.id)
    ElMessage.success('提示词已删除')
    await loadPromptList()
  } catch {
    // 取消删除不做处理
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

  .content-preview {
    font-size: 12px;
    color: #8b7355;
    line-height: 1.6;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    max-height: 2.8em;
  }

  .content-hint {
    font-size: 12px;
    color: #8b7355;
    line-height: 1.6;
    margin-top: -12px;
    margin-bottom: 4px;

    code {
      background: rgba(198, 123, 92, 0.1);
      color: #c67b5c;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 11px;
    }
  }
}
</style>
