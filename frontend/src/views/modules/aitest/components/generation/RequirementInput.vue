<template>
  <div class="requirement-input">
    <el-form label-width="80px" size="small">
      <el-form-item label="需求标题">
        <el-input v-model="title" placeholder="输入需求标题（可选）" maxlength="200" />
      </el-form-item>
      <el-form-item label="需求描述">
        <el-input
          v-model="requirementText"
          type="textarea"
          :rows="6"
          placeholder="请描述待测试的功能需求..."
          maxlength="50000"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <DocumentUpload @content-parsed="handleDocParsed" />

    <el-row :gutter="12" class="config-row">
      <el-col :span="8">
        <el-form-item label="编写模型">
          <el-select v-model="writerModelId" placeholder="选择编写模型" style="width: 100%">
            <el-option v-for="m in writerModels" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="评审模型">
          <el-select v-model="reviewerModelId" placeholder="选择评审模型（可选）" style="width: 100%" clearable>
            <el-option v-for="m in reviewerModels" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="关联项目">
          <el-select v-model="projectId" placeholder="选择项目（可选）" style="width: 100%" clearable>
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>

    <el-row :gutter="12" class="config-row">
      <el-col :span="12">
        <el-checkbox v-model="enableAutoReview">启用自动评审</el-checkbox>
      </el-col>
      <el-col :span="12" class="text-right">
        <el-button type="warning" :loading="generating" @click="handleGenerate" :disabled="!canGenerate">
          <el-icon><Lightning /></el-icon> 开始生成
        </el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Lightning } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'
import type { AIModelConfigSummary } from '@/types/aitest'
import type { ProjectSummary } from '@/types/project'
import DocumentUpload from './DocumentUpload.vue'

const emit = defineEmits<{
  (e: 'generate', params: GenerateParams): void
}>()

export interface GenerateParams {
  requirement_text: string
  title: string
  writer_model_config_id: number
  reviewer_model_config_id?: number
  project_id?: number
  enable_auto_review: boolean
}

const requirementText = ref('')
const title = ref('')
const writerModelId = ref<number | null>(null)
const reviewerModelId = ref<number | null>(null)
const projectId = ref<number | null>(null)
const enableAutoReview = ref(true)
const generating = ref(false)

const writerModels = ref<AIModelConfigSummary[]>([])
const reviewerModels = ref<AIModelConfigSummary[]>([])
const projects = ref<ProjectSummary[]>([])

const canGenerate = computed(() =>
  requirementText.value.trim().length > 0 && writerModelId.value !== null
)

async function loadOptions() {
  try {
    const [writersRes, reviewersRes, projectsRes] = await Promise.all([
      aitestApi.getModelList('writer'),
      aitestApi.getModelList('reviewer'),
      aitestApi.getProjectSummaryList(),
    ])
    writerModels.value = writersRes.data || []
    reviewerModels.value = reviewersRes.data || []
    projects.value = projectsRes.data || []

    // 自动选中第一个编写模型
    if (!writerModelId.value && writerModels.value.length > 0) {
      writerModelId.value = writerModels.value[0].id
    }
  } catch { /* ignore */ }
}

function handleDocParsed(content: string) {
  requirementText.value = content
}

async function handleGenerate() {
  if (!canGenerate.value) return
  generating.value = true
  try {
    emit('generate', {
      requirement_text: requirementText.value,
      title: title.value || requirementText.value.slice(0, 50),
      writer_model_config_id: writerModelId.value!,
      reviewer_model_config_id: reviewerModelId.value || undefined,
      project_id: projectId.value || undefined,
      enable_auto_review: enableAutoReview.value,
    })
  } finally {
    generating.value = false
  }
}

onMounted(loadOptions)
</script>

<style scoped lang="scss">
.requirement-input {
  .config-row {
    margin-top: 12px;
  }
  .text-right {
    text-align: right;
  }
}
</style>
