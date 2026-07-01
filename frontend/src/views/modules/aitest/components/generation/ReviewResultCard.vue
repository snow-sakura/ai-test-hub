<template>
  <div class="review-result-card">
    <div v-if="result.overall_score !== undefined" class="score-row">
      <div class="score-circle" :style="{ borderColor: scoreColor }">
        <span class="score-value">{{ Math.round(result.overall_score) }}</span>
        <span class="score-label">综合评分</span>
      </div>
      <div class="score-status">
        <el-tag :type="result.passed ? 'success' : 'danger'" size="small">
          {{ result.passed ? '评审通过' : '待修订' }}
        </el-tag>
      </div>
    </div>

    <el-divider v-if="result.issues?.length" />

    <div v-if="result.issues?.length" class="issues-section">
      <h4>问题列表</h4>
      <div v-for="(issue, i) in result.issues" :key="i" class="issue-item">
        <el-tag :type="severityType(issue.severity)" size="small" class="issue-severity">
          {{ issue.severity }}
        </el-tag>
        <span class="issue-title">{{ issue.title }}</span>
        <p v-if="issue.description" class="issue-desc">{{ issue.description }}</p>
      </div>
    </div>

    <div v-if="result.suggestions?.length" class="suggestions-section">
      <h4>改进建议</h4>
      <ul>
        <li v-for="(s, i) in result.suggestions" :key="i">{{ s }}</li>
      </ul>
    </div>

    <div v-if="result.raw" class="raw-section">
      <el-collapse>
        <el-collapse-item title="原始评审文本" name="raw">
          <pre class="raw-text">{{ result.raw }}</pre>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  result: {
    overall_score?: number
    passed?: boolean
    issues?: Array<{ severity: string; title: string; description?: string }>
    suggestions?: string[]
    raw?: string
  }
}>()

const scoreColor = computed(() => {
  const s = props.result.overall_score || 0
  if (s >= 80) return '#52c41a'
  if (s >= 60) return '#faad14'
  return '#f56c6c'
})

function severityType(s: string): string {
  const map: Record<string, string> = { high: 'danger', mid: 'warning', low: 'info' }
  return map[s] || 'info'
}
</script>

<style scoped lang="scss">
.review-result-card {
  .score-row {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .score-circle {
    width: 80px;
    height: 80px;
    border: 4px solid #52c41a;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    .score-value { font-size: 28px; font-weight: 700; line-height: 1; }
    .score-label { font-size: 11px; color: #8b7355; }
  }
  h4 { margin: 0 0 8px; font-size: 14px; color: #6b5a4a; }
  .issue-item {
    padding: 6px 0;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    .issue-severity { flex-shrink: 0; }
    .issue-title { font-weight: 500; }
    .issue-desc {
      width: 100%;
      margin: 2px 0 0;
      font-size: 12px;
      color: #8b7355;
    }
  }
  .suggestions-section ul {
    margin: 0;
    padding-left: 20px;
    li { font-size: 13px; line-height: 1.8; color: #6b5a4a; }
  }
  .raw-text {
    white-space: pre-wrap;
    font-size: 12px;
    color: #666;
    max-height: 200px;
    overflow-y: auto;
  }
}
</style>
