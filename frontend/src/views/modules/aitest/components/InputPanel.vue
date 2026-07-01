<template>
  <!--
    AI 用例生成 - 输入面板组件

    左侧输入面板，包含：
    - 项目选择
    - AI 模型选择
    - 提示词配置选择
    - 需求描述文本域
    - 高级选项
    - 生成按钮
  -->
  <div class="input-panel">
    <div class="panel-header">
      <el-icon :size="20"><Edit /></el-icon>
      <span>生成配置</span>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      label-position="top"
      class="input-form"
    >
      <!-- 项目选择 -->
      <el-form-item label="选择项目">
        <el-select
          v-model="form.project_id"
          placeholder="请选择项目（可选）"
          clearable
          filterable
          class="full-width"
          :loading="loading.projects"
          @change="emit('update:projectId', $event)"
        >
          <el-option
            v-for="p in projects"
            :key="p.id"
            :label="p.name"
            :value="p.id"
          />
        </el-select>
      </el-form-item>

      <!-- AI 模型选择 -->
      <el-form-item label="编写模型">
        <el-select
          v-model="form.writer_model_config_id"
          placeholder="请选择编写 AI 模型"
          clearable
          filterable
          class="full-width"
          :loading="loading.models"
          @change="emit('update:writerModelConfigId', $event)"
        >
          <el-option
            v-for="m in writerModels"
            :key="m.id"
            :label="`${m.name} (${m.model_name})`"
            :value="m.id"
          />
        </el-select>
      </el-form-item>

      <!-- 评审模型选择 -->
      <el-form-item label="评审模型（可选）">
        <el-select
          v-model="form.reviewer_model_config_id"
          placeholder="请选择评审 AI 模型"
          clearable
          filterable
          class="full-width"
          :loading="loading.models"
          @change="emit('update:reviewerModelConfigId', $event)"
        >
          <el-option
            v-for="m in reviewerModels"
            :key="m.id"
            :label="`${m.name} (${m.model_name})`"
            :value="m.id"
          />
        </el-select>
      </el-form-item>

      <!-- 提示词配置选择 -->
      <el-form-item label="编写提示词">
        <el-select
          v-model="form.writer_prompt_config_id"
          placeholder="请选择编写提示词"
          clearable
          filterable
          class="full-width"
          :loading="loading.prompts"
          @change="emit('update:writerPromptConfigId', $event)"
        >
          <el-option
            v-for="p in writerPrompts"
            :key="p.id"
            :label="p.name"
            :value="p.id"
          />
        </el-select>
      </el-form-item>

      <!-- 评审提示词选择 -->
      <el-form-item label="评审提示词（可选）">
        <el-select
          v-model="form.reviewer_prompt_config_id"
          placeholder="请选择评审提示词"
          clearable
          filterable
          class="full-width"
          :loading="loading.prompts"
          @change="emit('update:reviewerPromptConfigId', $event)"
        >
          <el-option
            v-for="p in reviewerPrompts"
            :key="p.id"
            :label="p.name"
            :value="p.id"
          />
        </el-select>
      </el-form-item>

      <!-- 需求描述文本域 -->
      <el-form-item
        label="需求描述"
        :error="requirementError"
      >
        <el-input
          v-model="form.requirement_text"
          type="textarea"
          :rows="12"
          placeholder="请输入测试需求描述，例如：&#10;&#10;1. 用户登录功能&#10;2. 支持用户名/密码登录&#10;3. 支持手机验证码登录&#10;4. 登录失败有错误提示&#10;5. 连续失败5次锁定账号"
          maxlength="10000"
          show-word-limit
          resize="vertical"
          class="requirement-input"
        />
      </el-form-item>

      <!-- 高级选项 -->
      <el-collapse class="advanced-options">
        <el-collapse-item title="高级选项" name="advanced">
          <el-form-item label="输出模式">
            <el-radio-group
              v-model="form.output_mode"
              @change="emit('update:outputMode', $event)"
            >
              <el-radio value="stream">流式输出（推荐）</el-radio>
              <el-radio value="complete">完整输出</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="自动评审">
            <el-switch
              :model-value="form.enable_auto_review"
              @update:model-value="emit('update:enableAutoReview', $event)"
              active-text="启用（生成后自动评审并改进）"
            />
          </el-form-item>
        </el-collapse-item>
      </el-collapse>

      <!-- 生成按钮 -->
      <div class="form-actions">
        <el-button
          type="primary"
          size="large"
          :loading="generating"
          :disabled="!canGenerate"
          class="generate-btn"
          @click="handleGenerate"
        >
          <el-icon v-if="!generating"><Lightning /></el-icon>
          {{ generating ? '生成中...' : '开始生成' }}
        </el-button>

        <el-button
          v-if="generating"
          size="large"
          type="danger"
          plain
          @click="emit('cancel')"
        >
          取消生成
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  Edit,
  Lightning,
} from '@element-plus/icons-vue'
import type { ProjectSummary } from '@/types/project'
import type { AIModelConfigSummary, PromptConfigSummary, GenerationFormData } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'
import { ElMessage } from 'element-plus'

/** 组件事件 */
const emit = defineEmits<{
  /** 点击生成 */
  generate: [form: GenerationFormData]
  /** 取消生成 */
  cancel: []
  /** 更新项目 ID */
  'update:projectId': [value: number | null]
  /** 更新编写模型 ID */
  'update:writerModelConfigId': [value: number | null]
  /** 更新评审模型 ID */
  'update:reviewerModelConfigId': [value: number | null]
  /** 更新编写提示词 ID */
  'update:writerPromptConfigId': [value: number | null]
  /** 更新评审提示词 ID */
  'update:reviewerPromptConfigId': [value: number | null]
  /** 更新输出模式 */
  'update:outputMode': [value: string]
  /** 更新自动评审 */
  'update:enableAutoReview': [value: boolean]
}>()

/** 组件 Props */
const props = defineProps<{
  /** 是否正在生成 */
  generating?: boolean
}>()

/** 生成表单数据（使用 types/ai.ts 中的定义） */
export type { GenerationFormData }

/** 表单数据 */
const form = reactive<GenerationFormData>({
  requirement_text: '',
  project_id: undefined,
  writer_model_config_id: undefined,
  reviewer_model_config_id: undefined,
  writer_prompt_config_id: undefined,
  reviewer_prompt_config_id: undefined,
  output_mode: 'stream',
  enable_auto_review: true,
})

/** 加载状态 */
const loading = reactive({
  projects: false,
  models: false,
  prompts: false,
})

/** 下拉数据列表 */
const projects = ref<ProjectSummary[]>([])
const writerModels = ref<AIModelConfigSummary[]>([])
const reviewerModels = ref<AIModelConfigSummary[]>([])
const writerPrompts = ref<PromptConfigSummary[]>([])
const reviewerPrompts = ref<PromptConfigSummary[]>([])

/** 需求描述校验错误 */
const requirementError = ref('')

/** 是否可以生成 */
const canGenerate = computed(() => {
  return form.requirement_text.trim().length > 0 && !props.generating
})

/** 表单引用 */
const formRef = ref()

/**
 * 加载下拉数据
 */
async function loadDropdownData() {
  // 加载项目列表
  loading.projects = true
  try {
    const res = await aitestApi.getProjectSummaryList()
    projects.value = res.data || []
  } catch {
    ElMessage.warning('获取项目列表失败')
  } finally {
    loading.projects = false
  }

  // 加载编写模型
  loading.models = true
  try {
    const [writerRes, reviewerRes] = await Promise.all([
      aitestApi.getModelList('writer'),
      aitestApi.getModelList('reviewer'),
    ])
    writerModels.value = writerRes.data || []
    reviewerModels.value = reviewerRes.data || []
  } catch {
    ElMessage.warning('获取模型列表失败')
  } finally {
    loading.models = false
  }

  // 加载提示词
  loading.prompts = true
  try {
    const [writerRes, reviewerRes] = await Promise.all([
      aitestApi.getPromptList('writer'),
      aitestApi.getPromptList('reviewer'),
    ])
    writerPrompts.value = writerRes.data || []
    reviewerPrompts.value = reviewerRes.data || []
  } catch {
    ElMessage.warning('获取提示词列表失败')
  } finally {
    loading.prompts = false
  }
}

/**
 * 点击生成按钮
 */
function handleGenerate() {
  // 校验
  if (!form.requirement_text.trim()) {
    requirementError.value = '请输入需求描述'
    return
  }
  requirementError.value = ''

  emit('generate', { ...form })
}

// 挂载时加载下拉数据
onMounted(() => {
  loadDropdownData()
})
</script>

<style scoped lang="scss">
.input-panel {
  background: var(--card-bg);
  border-radius: var(--radius);
  border: var(--border);
  padding: 20px;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: var(--border);

  .el-icon {
    color: var(--primary);
  }
}

.input-form {
  .full-width {
    width: 100%;
  }

  .requirement-input {
    :deep(textarea) {
      font-family: var(--font);
      line-height: 1.6;
    }
  }
}

.advanced-options {
  margin-bottom: 16px;
  border-top: none;

  :deep(.el-collapse-item__header) {
    font-size: 14px;
    color: var(--text-secondary);
    padding-left: 0;
  }

  :deep(.el-collapse-item__content) {
    padding-bottom: 8px;
  }
}

.form-actions {
  display: flex;
  gap: 12px;
}

.generate-btn {
  flex: 1;
  height: 44px;
  font-size: 15px;

  .el-icon {
    margin-right: 4px;
  }
}
</style>
