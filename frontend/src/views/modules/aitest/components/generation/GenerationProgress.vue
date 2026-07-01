<template>
  <div class="generation-progress">
    <StepIndicator :current-stage="currentStage" :stage-contents="stageContents" />

    <el-card v-if="reviewResult" shadow="never" class="review-card">
      <template #header>
        <span style="font-weight: 600; color: #6b5a4a;">AI 评审结果</span>
      </template>
      <ReviewResultCard :result="reviewResult" />
    </el-card>

    <el-card v-if="errorMessage" shadow="never" class="error-card">
      <template #header>
        <span style="color: #f56c6c;">生成出错</span>
      </template>
      <p>{{ errorMessage }}</p>
    </el-card>

    <div v-if="progress.total > 0" class="progress-bar-wrapper">
      <el-progress
        :percentage="Math.round((progress.current / progress.total) * 100)"
        :text-inside="true"
        :stroke-width="18"
        :status="isError ? 'exception' : isDone ? 'success' : undefined"
      />
      <p class="progress-msg">{{ progress.message }}</p>
    </div>

    <!-- 流式内容预览 -->
    <el-card v-for="(content, stage) in stageContents" :key="stage" v-show="content" shadow="never" class="stage-content-card">
      <template #header>
        <span style="font-weight: 600;">{{ STAGE_LABELS[stage] || stage }}</span>
      </template>
      <pre class="stage-content">{{ content }}</pre>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { STAGE_LABELS } from '@/composables/useGenerationStream'
import StepIndicator from '@/components/aitest/generation/StepIndicator.vue'

defineProps<{
  currentStage: string
  stageContents: Record<string, string>
  reviewResult: any
  errorMessage: string
  progress: { current: number; total: number; message: string }
  isDone: boolean
  isError: boolean
}>()

// Dynamic import of ReviewResultCard
import ReviewResultCard from './ReviewResultCard.vue'
</script>

<style scoped lang="scss">
.generation-progress {
  margin-top: 16px;
}
.review-card {
  margin-top: 16px;
  border: 1px solid #faad14;
}
.error-card {
  margin-top: 16px;
  border: 1px solid #f56c6c;
}
.progress-bar-wrapper {
  margin-top: 16px;
  .progress-msg {
    margin: 4px 0 0;
    font-size: 12px;
    color: #8b7355;
  }
}
.stage-content-card {
  margin-top: 12px;
  .stage-content {
    white-space: pre-wrap;
    font-size: 13px;
    line-height: 1.6;
    max-height: 300px;
    overflow-y: auto;
  }
}
</style>
