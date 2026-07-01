<template>
  <!--
    AI 评测师配置页面

    提供 AI 评测师的模型、提示词、温度等参数配置。
  -->
  <div class="tester-config-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>AI 评测师配置</h2>
      <p class="page-desc">配置 AI 评测使用的模型、提示词和生成参数</p>
    </div>

    <!-- 配置表单 -->
    <el-card class="config-card" shadow="never">
      <el-form
        ref="formRef"
        :model="form"
        label-width="140px"
        label-position="left"
        class="config-form"
        v-loading="loading"
      >
        <!-- 模型选择 -->
        <el-form-item label="AI 模型" prop="model_config_id">
          <el-select
            v-model="form.model_config_id"
            placeholder="请选择评测模型"
            style="width: 360px"
            clearable
          >
            <el-option
              v-for="m in modelList"
              :key="m.id"
              :label="m.name"
              :value="m.id"
            >
              <span>{{ m.name }}</span>
              <el-tag size="small" type="info" effect="plain" style="margin-left: 8px">
                {{ m.model_type }}
              </el-tag>
            </el-option>
          </el-select>
          <div class="form-item-hint">选择用于评测测试用例的 AI 模型</div>
        </el-form-item>

        <!-- 提示词选择 -->
        <el-form-item label="评测提示词" prop="prompt_config_id">
          <el-select
            v-model="form.prompt_config_id"
            placeholder="请选择评测提示词"
            style="width: 360px"
            clearable
          >
            <el-option
              v-for="p in promptList"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
          <div class="form-item-hint">选择用于评测的提示词模板</div>
        </el-form-item>

        <!-- 温度参数 -->
        <el-form-item label="Temperature" prop="temperature">
          <div class="slider-wrapper">
            <el-slider
              v-model="form.temperature"
              :min="0"
              :max="1"
              :step="0.1"
              show-input
              input-size="small"
              style="width: 360px"
            />
            <span class="slider-value">{{ form.temperature }}</span>
          </div>
          <div class="form-item-hint">
            控制输出的随机性（0: 精确保守，1: 富有创意）
          </div>
        </el-form-item>

        <!-- 最大 Token 数 -->
        <el-form-item label="最大 Token" prop="max_output_tokens">
          <el-input-number
            v-model="form.max_output_tokens"
            :min="512"
            :max="32768"
            :step="512"
            style="width: 360px"
          />
          <div class="form-item-hint">AI 评测单次响应的最大输出 Token 数量</div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="form-actions">
            <el-button type="primary" :loading="saving" @click="handleSave">
              {{ saving ? '保存中...' : '保存配置' }}
            </el-button>
            <el-button @click="handleReset">重置</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { aitestApi } from '@/api/aitest'
import type { AIModelConfigSummary, PromptConfigSummary } from '@/types/aitest'

// ====================================================================
// 表单数据接口
// ====================================================================
interface ConfigForm {
  model_config_id: number | undefined
  prompt_config_id: number | undefined
  temperature: number
  max_output_tokens: number
}

// ====================================================================
// 状态管理
// ====================================================================

/** 表单引用 */
const formRef = ref()
/** 页面加载状态 */
const loading = ref(false)
/** 保存状态 */
const saving = ref(false)
/** AI 模型下拉列表 */
const modelList = ref<AIModelConfigSummary[]>([])
/** 提示词下拉列表 */
const promptList = ref<PromptConfigSummary[]>([])

/** 初始配置快照（用于重置） */
let initialSnapshot = ''

/** 表单数据 */
const form = reactive<ConfigForm>({
  model_config_id: undefined,
  prompt_config_id: undefined,
  temperature: 0.7,
  max_output_tokens: 4096,
})

// ====================================================================
// 数据加载
// ====================================================================

/** 加载模型和提示词下拉列表 */
async function loadSelectOptions() {
  try {
    const [modelRes, promptRes] = await Promise.all([
      aitestApi.getModelList(),
      aitestApi.getPromptList(),
    ])
    modelList.value = modelRes.data || []
    promptList.value = promptRes.data || []
  } catch {
    // 下拉列表加载失败不阻塞页面
  }
}

/** 加载已保存的配置 */
async function loadSettings() {
  loading.value = true
  try {
    const res = await aitestApi.getSettings()
    if (res.code === 0 && res.data) {
      const s = res.data
      form.model_config_id = s.id
      form.prompt_config_id = undefined // settings 中没有 prompt 字段，保留 undefined
      form.temperature = s.temperature ?? 0.7
      form.max_output_tokens = s.max_output_tokens ?? 4096
      initialSnapshot = JSON.stringify({ ...form })
    }
  } catch {
    ElMessage.warning('加载配置失败，使用默认值')
  } finally {
    loading.value = false
  }
}

// ====================================================================
// 操作方法
// ====================================================================

/** 保存配置 */
async function handleSave() {
  saving.value = true
  try {
    await aitestApi.updateSettings({
      temperature: form.temperature,
      max_output_tokens: form.max_output_tokens,
    })
    ElMessage.success('配置保存成功')
    initialSnapshot = JSON.stringify({ ...form })
  } catch {
    ElMessage.error('保存配置失败，请重试')
  } finally {
    saving.value = false
  }
}

/** 重置为上次保存的配置 */
function handleReset() {
  if (initialSnapshot) {
    try {
      const saved = JSON.parse(initialSnapshot) as ConfigForm
      Object.assign(form, saved)
      ElMessage.info('已重置')
    } catch {
      ElMessage.warning('重置失败')
    }
  } else {
    form.model_config_id = undefined
    form.prompt_config_id = undefined
    form.temperature = 0.7
    form.max_output_tokens = 4096
    ElMessage.info('已重置为默认值')
  }
}

// ====================================================================
// 初始化
// ====================================================================

onMounted(async () => {
  await loadSelectOptions()
  await loadSettings()
})
</script>

<style scoped lang="scss">
.tester-config-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 6px;
    font-size: 22px;
    color: var(--el-text-color-primary);
  }

  .page-desc {
    margin: 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.config-card {
  max-width: 640px;
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;
}

.config-form {
  padding: 8px 0;
}

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;

  .slider-value {
    font-size: 13px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    min-width: 32px;
  }
}

.form-item-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
</style>
