<template>
  <span class="status-tag" :class="[`status-${status}`]">
    <span class="status-dot" />
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
  mapping?: Record<string, { label: string }>
}>()

const defaultMapping: Record<string, string> = {
  active: '进行中', paused: '已暂停', completed: '已完成', archived: '已归档',
  pending: '待评审', in_progress: '评审中', approved: '已通过', rejected: '已驳回', cancelled: '已取消',
  passed: '已通过',
  draft: '草稿', review: '评审中', done: '已完成',
}

const label = computed(() => {
  if (props.mapping && props.mapping[props.status]) return props.mapping[props.status].label
  return defaultMapping[props.status] || props.status
})
</script>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
/* 进行中 / active */
.status-active { background: rgba(16, 185, 129, 0.08); color: #059669; }
.status-active .status-dot { background: #10b981; }
/* 已暂停 */
.status-paused { background: rgba(245, 158, 11, 0.08); color: #d97706; }
.status-paused .status-dot { background: #f59e0b; }
/* 已完成 / completed / passed / done / approved */
.status-completed,
.status-passed,
.status-done,
.status-approved { background: rgba(59, 130, 246, 0.08); color: #2563eb; }
.status-completed .status-dot,
.status-passed .status-dot,
.status-done .status-dot,
.status-approved .status-dot { background: #3b82f6; }
/* 已归档 / 已取消 */
.status-archived,
.status-cancelled { background: rgba(107, 114, 128, 0.08); color: #5C4A38; }
.status-archived .status-dot,
.status-cancelled .status-dot { background: #7A6855; }
/* 待评审 / draft */
.status-pending,
.status-draft { background: rgba(168, 98, 74, 0.08); color: #A8624A; }
.status-pending .status-dot,
.status-draft .status-dot { background: #C67B5C; }
/* 评审中 / in_progress / review */
.status-in_progress,
.status-review { background: rgba(198, 123, 92, 0.1); color: #C67B5C; }
.status-in_progress .status-dot,
.status-review .status-dot { background: #C67B5C; }
/* 已驳回 / rejected */
.status-rejected { background: rgba(239, 68, 68, 0.08); color: #dc2626; }
.status-rejected .status-dot { background: #ef4444; }
</style>
