<template>
  <div class="step-indicator">
    <div
      v-for="(step, idx) in steps"
      :key="step.key"
      class="step-item"
      :class="{
        active: !isCompleted && currentStageKey === step.key,
        done: isCompleted || stageOrder.indexOf(currentStageKey) > stageOrder.indexOf(step.key),
        pending: !isCompleted && stageOrder.indexOf(currentStageKey) < stageOrder.indexOf(step.key),
      }"
    >
      <div class="step-circle">{{ isCompleted ? '✓' : (stageOrder.indexOf(currentStageKey) > stageOrder.indexOf(step.key) ? '✓' : idx + 1) }}</div>
      <div class="step-label">{{ step.label }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  currentStage: string | null
  status?: string
}>()

const steps = [
  { key: 'analyze', label: '需求分析' },
  { key: 'writing', label: '用例编写' },
  { key: 'review', label: 'AI 评审' },
  { key: 'revise', label: '改进完善' },
]

const stageOrder = ['analyze', 'writing', 'review', 'revise']

const currentStageKey = computed(() => props.currentStage || '')

const isCompleted = computed(() => props.status === 'completed')
</script>

<style scoped>
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 16px 0;
}
.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}
.step-item + .step-item::before {
  content: '';
  width: 60px;
  height: 2px;
  background: rgba(180, 150, 120, 0.2);
  margin: 0 12px;
}
.step-item.done + .step-item::before {
  background: var(--primary, #C67B5C);
}
.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  border: 2px solid rgba(180, 150, 120, 0.2);
  color: var(--text-muted, #8B7355);
  background: var(--card-bg, #FFFDF9);
  transition: all 0.3s;
}
.step-item.active .step-circle {
  border-color: var(--primary, #C67B5C);
  background: var(--primary, #C67B5C);
  color: #fff;
  box-shadow: 0 0 0 4px rgba(198, 123, 92, 0.15);
}
.step-item.done .step-circle {
  border-color: #10b981;
  background: #10b981;
  color: #fff;
}
.step-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted, #8B7355);
  white-space: nowrap;
}
.step-item.active .step-label {
  color: var(--primary, #C67B5C);
  font-weight: 600;
}
.step-item.done .step-label {
  color: #10b981;
}
</style>
