<template>
  <div class="review-visualization" v-if="reviewData">
    <!-- 总体评分 -->
    <div class="overall-score-row">
      <el-progress
        type="circle"
        :percentage="Math.round(reviewData.score * 10)"
        :stroke-width="8"
        :color="scoreColor"
        :width="80"
      >
        <span class="score-value">{{ reviewData.score.toFixed(1) }}</span>
      </el-progress>
      <div class="score-meta">
        <el-tag :type="reviewData.passed ? 'success' : 'danger'" size="small" effect="dark">
          {{ reviewData.passed ? '评审通过' : '需要修订' }}
        </el-tag>
        <span class="passed-hint">{{ reviewData.passed ? '可直接发布' : '需根据反馈修订后重新评审' }}</span>
        <div class="score-threshold">
          <span class="threshold-label">合格线：</span>
          <el-progress :percentage="70" :stroke-width="6" color="#E6A23C" :show-text="false" />
        </div>
      </div>
    </div>

    <!-- 9 维度进度条 -->
    <div class="dimensions-section" v-if="dimensionsList.length">
      <h4 class="section-title">评分维度</h4>
      <div v-for="dim in dimensionsList" :key="dim.name" class="dimension-row">
        <span class="dimension-name">{{ dim.name }}</span>
        <div class="dimension-bar-wrapper">
          <el-progress
            :percentage="dim.score * 10"
            :stroke-width="14"
            :color="dimensionColor(dim.score)"
            :text-inside="true"
          >
            {{ dim.score }}/10
          </el-progress>
        </div>
      </div>
    </div>

    <!-- 问题列表 -->
    <div class="issues-section" v-if="reviewData.issues?.length">
      <h4 class="section-title">发现问题（{{ reviewData.issues.length }}）</h4>
      <div v-for="(issue, i) in reviewData.issues" :key="i" class="issue-item">
        <div class="issue-header">
          <el-tag :type="severityTagType(issue.severity)" size="small" effect="dark" class="severity-tag">
            {{ severityLabel(issue.severity) }}
          </el-tag>
          <span class="issue-title">{{ issue.title }}</span>
        </div>
        <p v-if="issue.description" class="issue-desc">{{ issue.description }}</p>
        <p v-if="issue.fix_suggestion" class="issue-fix">
          <el-icon><Edit /></el-icon> 修复建议：{{ issue.fix_suggestion }}
        </p>
      </div>
    </div>

    <!-- 改进建议 -->
    <div class="improvements-section" v-if="reviewData.improvements?.length">
      <h4 class="section-title">改进建议</h4>
      <ul>
        <li v-for="(imp, i) in reviewData.improvements" :key="i">{{ imp }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Edit } from '@element-plus/icons-vue'

interface ReviewDimension {
  name: string
  score: number
}

interface ReviewIssue {
  severity: 'high' | 'mid' | 'low'
  title: string
  description?: string
  fix_suggestion?: string
}

interface ReviewResult {
  score: number
  passed: boolean
  dimensions: Record<string, number>
  issues: ReviewIssue[]
  improvements: string[]
}

const props = defineProps<{
  reviewData: ReviewResult | null
}>()

const dimensionsList = computed<ReviewDimension[]>(() => {
  if (!props.reviewData?.dimensions) return []
  return Object.entries(props.reviewData.dimensions).map(([name, score]) => ({
    name,
    score,
  }))
})

const scoreColor = computed(() => {
  const s = props.reviewData?.score ?? 0
  if (s >= 7) return '#67C23A'
  if (s >= 5) return '#E6A23C'
  return '#F56C6C'
})

function dimensionColor(score: number): string {
  if (score >= 8) return '#67C23A'
  if (score >= 6) return '#E6A23C'
  return '#F56C6C'
}

function severityTagType(severity: string): 'danger' | 'warning' | 'info' {
  if (severity === 'high') return 'danger'
  if (severity === 'mid') return 'warning'
  return 'info'
}

function severityLabel(severity: string): string {
  const map: Record<string, string> = {
    high: '严重',
    mid: '一般',
    low: '轻微',
  }
  return map[severity] || severity
}
</script>

<style scoped>
.review-visualization {
  padding: 4px 0;
}

/* 总体评分 */
.overall-score-row {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0ebe3;
}
.score-value {
  font-size: 18px;
  font-weight: 700;
  color: #3d2e1f;
}
.score-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}
.passed-hint {
  font-size: 12px;
  color: #8b7355;
}
.score-threshold {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 200px;
}
.threshold-label {
  font-size: 11px;
  color: #a0917a;
  white-space: nowrap;
}

/* 维度进度条 */
.dimensions-section {
  margin-bottom: 20px;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #3d2e1f;
  margin: 0 0 10px;
  padding-left: 2px;
}
.dimension-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.dimension-name {
  min-width: 72px;
  font-size: 12px;
  color: #5c4a38;
  text-align: right;
  flex-shrink: 0;
}
.dimension-bar-wrapper {
  flex: 1;
}

/* 问题列表 */
.issues-section {
  margin-bottom: 20px;
}
.issue-item {
  padding: 8px 10px;
  margin-bottom: 6px;
  background: #faf8f5;
  border-radius: 6px;
}
.issue-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.severity-tag {
  flex-shrink: 0;
}
.issue-title {
  font-size: 13px;
  font-weight: 500;
  color: #3d2e1f;
}
.issue-desc {
  font-size: 12px;
  color: #8b7355;
  margin: 4px 0 0;
  line-height: 1.6;
}
.issue-fix {
  font-size: 12px;
  color: #c67b5c;
  margin: 4px 0 0;
  display: flex;
  align-items: flex-start;
  gap: 4px;
}

/* 改进建议 */
.improvements-section {
  margin-bottom: 4px;
}
.improvements-section ul {
  margin: 0;
  padding-left: 20px;
}
.improvements-section li {
  font-size: 13px;
  line-height: 2;
  color: #5c4a38;
}
</style>
