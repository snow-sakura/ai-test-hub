<script setup lang="ts">
/**
 * 生成序列看板：展示同一 batch 内所有任务的执行状态
 * - 免费模型（serial）：串行执行，显示排队位次
 * - 付费模型（parallel）：并行执行，显示并行度
 */
import { computed } from 'vue'
import type { GenerationBatchStatus, BatchTaskStatusItem } from '@/types/aitest'

const props = defineProps<{
  status: GenerationBatchStatus | null
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'view-task', taskId: string): void
}>()

const STATUS_TEXT: Record<string, string> = {
  queued: '排队中',
  pending: '准备中',
  analyzing: '需求分析',
  generating: '用例编写',
  reviewing: 'AI 评审',
  revising: '改进完善',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

const STATUS_TAG: Record<string, 'info' | 'primary' | 'success' | 'warning' | 'danger'> = {
  queued: 'info',
  pending: 'info',
  analyzing: 'primary',
  generating: 'primary',
  reviewing: 'primary',
  revising: 'primary',
  completed: 'success',
  failed: 'danger',
  cancelled: 'info',
}

function statusText(s: string): string {
  return STATUS_TEXT[s] || s
}

function statusTag(s: string) {
  return STATUS_TAG[s] || 'info'
}

const progressPercent = computed(() => {
  const st = props.status
  if (!st || st.total === 0) return 0
  return Math.round(((st.completed + st.failed) / st.total) * 100)
})

function subLabel(t: BatchTaskStatusItem): string {
  if (t.status === 'queued') {
    return '# 排队第 ' + String((t.queue_position ?? 0) + 1) + ' 位'
  }
  if (t.status === 'completed') return String(t.case_count) + ' 条用例'
  if (t.status === 'failed' && t.error_message) {
    return t.error_message.length > 40 ? t.error_message.slice(0, 40) + '…' : t.error_message
  }
  return '进度 ' + t.progress + '%'
}

function isRunning(s: string): boolean {
  return ['pending', 'analyzing', 'generating', 'reviewing', 'revising'].includes(s)
}
</script>

<template>
  <div v-if="status" class="batch-board">
    <!-- 批次头 -->
    <div class="batch-head">
      <div class="batch-head-left">
        <span class="batch-id">生成序列 {{ status.batch_id }}</span>
        <el-tag
          size="small"
          :type="status.execution_mode === 'parallel' ? 'warning' : 'info'"
          effect="plain"
        >
          {{ status.execution_mode === 'parallel'
            ? '付费模型 · 并行执行（最多 ' + status.max_concurrency + ' 路）'
            : '免费模型 · 单任务序列（严格串行）' }}
        </el-tag>
      </div>
      <div class="batch-head-right">
        <span class="mini-stat ok">完成 {{ status.completed }}</span>
        <span class="mini-stat run">进行 {{ status.running }}</span>
        <span class="mini-stat wait">排队 {{ status.queued }}</span>
        <span v-if="status.failed > 0" class="mini-stat bad">失败 {{ status.failed }}</span>
      </div>
    </div>

    <el-progress
      :percentage="progressPercent"
      :stroke-width="6"
      color="#C67B5C"
      class="batch-progress"
    />

    <!-- 任务序列卡片 -->
    <div class="batch-tasks">
      <div
        v-for="(t, idx) in status.tasks"
        :key="t.task_id"
        class="batch-task"
        :class="{ running: isRunning(t.status), failed: t.status === 'failed', done: t.status === 'completed' }"
      >
        <div class="bt-seq">{{ idx + 1 }}</div>
        <div class="bt-body">
          <div class="bt-title" :title="t.title">{{ t.title }}</div>
          <div class="bt-meta">
            <el-tag size="small" :type="statusTag(t.status)" :effect="isRunning(t.status) ? 'dark' : 'light'">
              <span v-if="isRunning(t.status)" class="dot-pulse" />
              {{ statusText(t.status) }}
            </el-tag>
            <span class="bt-sub" :class="'sub-' + t.status">{{ subLabel(t) }}</span>
          </div>
        </div>
        <el-button
          v-if="t.status === 'completed' || t.status === 'failed'"
          size="small"
          text
          type="primary"
          @click="emit('view-task', t.task_id)"
        >
          查看
        </el-button>
      </div>
    </div>
  </div>
  <el-empty v-else-if="!loading" description="暂无生成序列，提交多条需求后在此查看" :image-size="80" />
</template>

<style scoped lang="scss">
.batch-board {
  .batch-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;

    .batch-head-left {
      display: flex;
      align-items: center;
      gap: 10px;

      .batch-id {
        font-weight: 600;
        font-size: 14px;
        color: #3d2c22;
      }
    }

    .batch-head-right {
      display: flex;
      gap: 12px;
      font-size: 12px;

      .mini-stat {
        color: #8a7265;

        &.ok { color: #10b981; }
        &.bad { color: #ef4444; }
        &.run { color: #409eff; }
      }
    }
  }

  .batch-progress {
    margin-bottom: 14px;
  }

  .batch-tasks {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .batch-task {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border: 1px solid #f0e4dc;
      border-radius: 8px;
      background: #fdfaf8;
      transition: all 0.2s;

      &.running {
        border-color: #f3c9a8;
        background: #fff7ef;
      }

      &.done {
        border-color: #d7f0e2;
        background: #f6fcf9;
      }

      &.failed {
        border-color: #fbd5d5;
        background: #fef7f7;
      }

      .bt-seq {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #f0e4dc;
        color: #8a7265;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
        flex-shrink: 0;
      }

      .bt-body {
        flex: 1;
        min-width: 0;

        .bt-title {
          font-size: 13px;
          color: #3d2c22;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .bt-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 4px;

          .bt-sub {
            font-size: 12px;
            color: #a58a7b;

            &.sub-failed {
              color: #ef4444;
            }

            &.sub-completed {
              color: #10b981;
            }
          }
        }
      }
    }
  }
}

.dot-pulse {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  margin-right: 4px;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}
</style>
