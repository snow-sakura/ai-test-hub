<template>
  <!--
    AI 用例生成 - 结果展示面板组件

    右侧结果展示，包含：
    - 生成状态 + 进度条
    - 用例表格（实时流式更新）
    - 评审/改进结果显示
    - 操作按钮（导出 Excel、复制、保存）
  -->
  <div class="result-panel">
    <div class="panel-header">
      <el-icon :size="20"><Document /></el-icon>
      <span>生成结果</span>

      <!-- 状态标签 -->
      <el-tag
        v-if="currentStatus"
        :type="statusTagType"
        size="small"
        effect="dark"
        class="status-tag"
      >
        {{ statusLabel }}
      </el-tag>
    </div>

    <!-- 进度条 -->
    <div v-if="showProgress" class="progress-section">
      <el-progress
        :percentage="progress"
        :status="progressStatus"
        :stroke-width="8"
        :duration="300"
      />
    </div>

    <!-- 空状态 -->
    <div v-if="!hasCases && !isGenerating && !hasError" class="empty-state">
      <el-empty
        description="请在左侧输入需求并点击「开始生成」"
        :image-size="160"
      >
        <template #image>
          <div class="empty-icon">
            <el-icon :size="64"><Document /></el-icon>
          </div>
        </template>
      </el-empty>
    </div>

    <!-- 用例表格 -->
    <div v-if="hasCases" class="table-section">
      <div class="table-toolbar">
        <span class="table-title">
          测试用例（{{ (testCases?.length || 0) }} 条）
        </span>
        <div class="toolbar-actions">
          <el-button
            size="small"
            @click="handleCopy"
          >
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
          <el-button
            size="small"
            type="primary"
            @click="handleExportExcel"
          >
            <el-icon><Download /></el-icon>
            导出 Excel
          </el-button>
          <el-button
            size="small"
            plain
            @click="handleSave"
          >
            <el-icon><FolderAdd /></el-icon>
            保存到用例库
          </el-button>
        </div>
      </div>

      <el-table
        :data="tableData"
        border
        stripe
        size="small"
        max-height="500"
        style="width: 100%"
        :default-sort="{ prop: 'case_id', order: 'ascending' }"
        class="cases-table"
      >
        <el-table-column
          prop="case_id"
          label="用例编号"
          width="100"
          sortable
          fixed
        />
        <el-table-column
          prop="module"
          label="模块"
          width="120"
        />
        <el-table-column
          prop="title"
          label="标题"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column
          prop="precondition"
          label="前置条件"
          min-width="160"
          show-overflow-tooltip
        />
        <el-table-column
          prop="test_steps"
          label="测试步骤"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          prop="expected_result"
          label="预期结果"
          min-width="160"
          show-overflow-tooltip
        />
        <el-table-column
          prop="priority"
          label="优先级"
          width="90"
          sortable
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="priorityTagType(row.priority)"
              size="small"
              effect="dark"
            >
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 评审反馈（折叠面板） -->
    <el-collapse v-if="reviewFeedback" class="review-section" :model-value="['review']">
      <el-collapse-item title="AI 评审反馈" name="review">
        <div class="review-content">
          <pre class="review-text">{{ reviewFeedback }}</pre>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 改进后结果 -->
    <el-collapse v-if="revisedContent" class="revise-section">
      <el-collapse-item title="改进后结果" name="revise">
        <div class="revise-content">
          <pre class="revise-text">{{ revisedContent }}</pre>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 错误提示 -->
    <el-alert
      v-if="hasError"
      :title="errorMessage"
      type="error"
      show-icon
      closable
      class="error-alert"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Document,
  Download,
  CopyDocument,
  FolderAdd,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { GeneratedTestCase } from '@/types/aitest'
import * as XLSX from 'xlsx'

/** 组件事件 */
const emit = defineEmits<{
  save: []
}>()

/** 组件 Props */
const props = defineProps<{
  /** 当前状态 */
  currentStatus?: string
  /** 进度百分比 */
  progress?: number
  /** 是否正在生成 */
  isGenerating?: boolean
  /** 生成的测试用例列表 */
  testCases?: GeneratedTestCase[]
  /** 评审反馈 */
  reviewFeedback?: string
  /** 改进后文本 */
  revisedContent?: string
  /** 错误消息 */
  errorMessage?: string
}>()

/** 是否有用例 */
const hasCases = computed(() => {
  return props.testCases && props.testCases.length > 0
})

/** 是否有错误 */
const hasError = computed(() => {
  return !!props.errorMessage
})

/** 是否显示进度条 */
const showProgress = computed(() => {
  return props.isGenerating || (props.progress !== undefined && props.progress > 0 && props.progress < 100)
})

/** 进度条状态 */
const progressStatus = computed(() => {
  if (props.errorMessage) return 'exception'
  if (props.progress === 100) return 'success'
  return ''
})

/** 表格数据（带行号展示） */
const tableData = computed(() => {
  return (props.testCases || []).map((tc, index) => ({
    ...tc,
    _index: index + 1,
  }))
})

/** 状态标签类型 */
const statusTagType = computed(() => {
  const map: Record<string, string> = {
    generating: 'warning',
    reviewing: 'warning',
    revising: 'warning',
    completed: 'success',
    failed: 'danger',
    pending: 'info',
    cancelled: 'info',
  }
  return map[props.currentStatus || ''] || 'info'
})

/** 状态标签文本 */
const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: '等待中',
    generating: '生成中',
    reviewing: '评审中',
    revising: '改进中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[props.currentStatus || ''] || props.currentStatus || ''
})

/**
 * 获取优先级标签类型
 */
function priorityTagType(priority: string): string {
  const map: Record<string, string> = {
    P0: 'danger',
    P1: 'warning',
    P2: 'primary',
    P3: 'info',
  }
  return map[priority] || 'info'
}

/**
 * 复制用例到剪贴板
 */
function handleCopy() {
  if (!props.testCases || props.testCases.length === 0) return

  const text = props.testCases.map((tc) => {
    return `| ${tc.case_id} | ${tc.module} | ${tc.title} | ${tc.precondition} | ${tc.test_steps} | ${tc.expected_result} | ${tc.priority} |`
  }).join('\n')

  const header = '| 用例编号 | 模块 | 标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |\n| --- | --- | --- | --- | --- | --- | --- |\n'

  navigator.clipboard.writeText(header + text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = header + text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制到剪贴板')
  })
}

/**
 * 导出 Excel
 */
function handleExportExcel() {
  if (!props.testCases || props.testCases.length === 0) {
    ElMessage.warning('没有可导出的用例')
    return
  }

  const excelData = props.testCases.map((tc) => ({
    '用例编号': tc.case_id,
    '模块': tc.module,
    '标题': tc.title,
    '前置条件': tc.precondition,
    '测试步骤': tc.test_steps,
    '预期结果': tc.expected_result,
    '优先级': tc.priority,
  }))

  const worksheet = XLSX.utils.json_to_sheet(excelData)

  // 设置列宽
  worksheet['!cols'] = [
    { wch: 12 },  // 用例编号
    { wch: 15 },  // 模块
    { wch: 30 },  // 标题
    { wch: 25 },  // 前置条件
    { wch: 35 },  // 测试步骤
    { wch: 30 },  // 预期结果
    { wch: 10 },  // 优先级
  ]

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '测试用例')

  // 生成文件名
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-')
  XLSX.writeFile(workbook, `AI生成测试用例_${timestamp}.xlsx`)

  ElMessage.success(`已导出 ${props.testCases.length} 条用例`)
}

/**
 * 保存到用例库
 */
function handleSave() {
  emit('save')
}
</script>

<style scoped lang="scss">
.result-panel {
  background: var(--card-bg);
  border-radius: var(--radius);
  border: var(--border);
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: var(--border);

  .el-icon {
    color: var(--primary);
  }
}

.status-tag {
  margin-left: auto;
}

.progress-section {
  margin-bottom: 16px;
}

// 空状态
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.empty-icon {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

// 表格区域
.table-section {
  flex: 1;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.table-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.cases-table {
  border-radius: var(--radius-sm);

  :deep(.el-table__header th) {
    background: var(--bg);
    color: var(--text-secondary);
    font-weight: 500;
  }

  :deep(.el-table__body td) {
    padding: 6px 0;
  }
}

// 评审反馈
.review-section {
  margin-top: 16px;
}

.review-content,
.revise-content {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.review-text,
.revise-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font);
  font-size: 13px;
  line-height: 1.6;
  color: var(--text);
}

// 错误提示
.error-alert {
  margin-top: 16px;
}
</style>
