<template>
  <!--
    AI 测试报告页面

    展示所有已完成的 AI 生成任务的测试报告，支持按项目和时间筛选。
    点击列表项可查看包含统计卡片、通过率、模块分布、用例明细等信息的详情弹窗。
  -->
  <div class="page-wrap">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">AI 测试报告</h2>
      <p class="page-desc">查看 AI 生成的测试用例执行报告和统计数据</p>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :inline="true" size="default">
        <el-form-item label="项目">
          <el-select
            v-model="filter.project_id"
            placeholder="全部项目"
            clearable
            style="width: 140px"
          >
            <el-option
              v-for="p in projects"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 报告列表 -->
    <el-card shadow="never" class="config-table-card">
      <el-table
        :data="reportList"
        v-loading="loading"
        stripe
        style="width: 100%"
        @row-click="handleViewReport"
      >
        <el-table-column prop="title" label="报告名称" min-width="220" show-overflow-tooltip align="center" />
        <el-table-column prop="project_name" label="项目" min-width="160" show-overflow-tooltip align="center" />
        <el-table-column label="执行时间" min-width="130" show-overflow-tooltip align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="通过率" min-width="180" align="center">
          <template #default="{ row }">
            <div class="pass-rate-cell">
              <el-progress
                :percentage="Math.round(row.pass_rate)"
                :color="passRateColor(row.pass_rate)"
                :stroke-width="16"
                :text-inside="true"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="通过" min-width="75" align="center">
          <template #default="{ row }">
            <span class="num-pass">{{ row.passed }}</span>
          </template>
        </el-table-column>
        <el-table-column label="失败" min-width="75" align="center">
          <template #default="{ row }">
            <span class="num-fail">{{ row.failed }}</span>
          </template>
        </el-table-column>
        <el-table-column label="阻塞" min-width="75" align="center">
          <template #default="{ row }">
            <span class="num-blocked">{{ row.blocked }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="140" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="handleViewReport(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="!loading && reportList.length === 0" description="暂无测试报告数据" />

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @current-change="fetchReports"
        @size-change="fetchReports"
      />
    </div>

    <!-- 报告详情弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="detail?.summary?.title || '报告详情'"
      width="1000px"
      top="30px"
      destroy-on-close
      class="report-dialog"
    >
      <template v-if="detailLoading">
        <div class="detail-loading">
          <el-skeleton :rows="6" animated />
        </div>
      </template>
      <template v-else-if="detail">
        <!-- 4 个统计卡片 -->
        <div class="stats-cards">
          <div class="stat-card card-total">
            <div class="stat-value">{{ detail.stats.total_cases }}</div>
            <div class="stat-label">总用例数</div>
          </div>
          <div class="stat-card card-pass">
            <div class="stat-value">{{ detail.stats.passed }}</div>
            <div class="stat-label">通过</div>
          </div>
          <div class="stat-card card-fail">
            <div class="stat-value">{{ detail.stats.failed }}</div>
            <div class="stat-label">失败</div>
          </div>
          <div class="stat-card card-blocked">
            <div class="stat-value">{{ detail.stats.blocked }}</div>
            <div class="stat-label">阻塞</div>
          </div>
        </div>

        <!-- 通过率 + 模块分布（两列布局） -->
        <div class="stats-double-row">
          <!-- 左侧：通过率 -->
          <div class="pass-rate-section">
            <h4>通过率</h4>
            <div class="pass-rate-big">
              <div class="big-number" :style="{ color: passRateColor(detail.stats.pass_rate) }">
                {{ detail.stats.pass_rate.toFixed(1) }}%
              </div>
              <el-progress
                :percentage="Math.round(detail.stats.pass_rate)"
                :color="passRateColor(detail.stats.pass_rate)"
                :stroke-width="20"
                style="margin-top: 12px"
              />
            </div>
          </div>
          <!-- 右侧：模块分布条形图 -->
          <div class="module-chart-section">
            <h4>模块分布</h4>
            <div class="module-bars">
              <div
                v-for="item in detail.stats.module_stats"
                :key="item.module"
                class="module-bar-row"
              >
                <span class="module-label" :title="item.module">{{ item.module }}</span>
                <div class="module-bar-track">
                  <div
                    class="module-bar-fill module-bar-pass"
                    :style="{ width: (item.total / maxModuleTotal) * 100 + '%' }"
                  />
                  <div
                    v-if="item.failed > 0"
                    class="module-bar-fill module-bar-fail"
                    :style="{
                      width: (item.failed / maxModuleTotal) * 100 + '%',
                      marginLeft: (item.passed / maxModuleTotal) * 100 + '%',
                    }"
                  />
                </div>
                <span class="module-count">{{ item.total }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 全部用例明细 -->
        <div class="section-block">
          <h4>全部用例明细</h4>
          <el-table :data="detail.cases" stripe size="small" max-height="300" style="width: 100%">
            <el-table-column prop="case_id" label="编号" width="100" />
            <el-table-column prop="title" label="用例标题" min-width="180" show-overflow-tooltip />
            <el-table-column prop="module" label="模块" width="120" />
            <el-table-column prop="priority" label="优先级" width="80" align="center" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">
                  {{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="precondition" label="前置条件" min-width="160" show-overflow-tooltip />
            <el-table-column prop="test_steps" label="测试步骤" min-width="200" show-overflow-tooltip />
            <el-table-column prop="expected_result" label="预期结果" min-width="200" show-overflow-tooltip />
          </el-table>
        </div>

        <!-- 失败用例详情 -->
        <div class="section-block" v-if="detail.stats.failed_cases.length > 0">
          <h4>失败用例详情（{{ detail.stats.failed_cases.length }} 项）</h4>
          <el-collapse accordion>
            <el-collapse-item
              v-for="fc in detail.stats.failed_cases"
              :key="fc.case_id"
              :title="`[${fc.case_id}] ${fc.title}`"
              :name="fc.case_id"
            >
              <div class="failed-case-detail">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="用例编号">{{ fc.case_id }}</el-descriptions-item>
                  <el-descriptions-item label="优先级">{{ fc.priority }}</el-descriptions-item>
                  <el-descriptions-item label="所属模块">{{ fc.module }}</el-descriptions-item>
                  <el-descriptions-item label="当前状态">
                    <el-tag :type="statusTagType(fc.status)" size="small">
                      {{ statusLabel(fc.status) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="失败原因" :span="2">
                    <span style="color: var(--el-color-danger)">{{ fc.reason }}</span>
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 按模块统计表 -->
        <div class="section-block" v-if="detail.stats.module_stats.length > 0">
          <h4>按模块统计</h4>
          <el-table :data="detail.stats.module_stats" stripe size="small" style="width: 100%">
            <el-table-column prop="module" label="模块名称" min-width="160" />
            <el-table-column prop="total" label="总用例数" width="100" align="center" />
            <el-table-column prop="passed" label="通过" width="80" align="center">
              <template #default="{ row }">
                <span style="color: var(--el-color-success)">{{ row.passed }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="failed" label="失败" width="80" align="center">
              <template #default="{ row }">
                <span style="color: var(--el-color-danger)">{{ row.failed }}</span>
              </template>
            </el-table-column>
            <el-table-column label="通过率" width="180">
              <template #default="{ row }">
                <el-progress
                  :percentage="Math.round(row.pass_rate)"
                  :color="passRateColor(row.pass_rate)"
                  :stroke-width="14"
                  :text-inside="true"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { reportApi } from '@/api/report'
import { aitestApi } from '@/api/aitest'
import type { AIReportSummary, AIReportDetail } from '@/types/report'
import type { ProjectSummary } from '@/types/project'

// ======================================================================
// 状态
// ======================================================================

/** 加载状态 */
const loading = ref(false)
const detailLoading = ref(false)

/** 报告列表数据 */
const reportList = ref<AIReportSummary[]>([])

/** 总记录数 */
const total = ref(0)

/** 分页信息 */
const pagination = ref({
  page: 1,
  page_size: 10,
})

/** 项目列表（用于筛选下拉） */
const projects = ref<ProjectSummary[]>([])

/** 筛选条件 */
const filter = ref<{
  project_id: number | null
  start_date: string | null
  end_date: string | null
}>({
  project_id: null,
  start_date: null,
  end_date: null,
})

/** 日期范围绑定 */
const dateRange = ref<[string, string] | null>(null)

/** 弹窗显示状态 */
const dialogVisible = ref(false)

/** 报告详情数据 */
const detail = ref<AIReportDetail | null>(null)

// ======================================================================
// 计算属性
// ======================================================================

/** 模块分布条形图的最大值（用于计算宽度比例） */
const maxModuleTotal = computed(() => {
  if (!detail.value?.stats.module_stats.length) return 1
  return Math.max(...detail.value.stats.module_stats.map((m) => m.total))
})

// ======================================================================
// 方法
// ======================================================================

import { formatDateTime } from '@/utils'

/**
 * 格式化时间
 */
function formatTime(t: string): string {
  if (!t) return '-'
  try {
    return formatDateTime(t)
  } catch {
    return t
  }
}

/**
 * 根据通过率返回进度条颜色
 * 高 >= 80%：绿色，中 >= 60%：橙色，低 < 60%：红色
 */
function passRateColor(rate: number): string {
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 根据状态返回标签类型
 */
function statusTagType(status: string): string {
  switch (status) {
    case 'approved':
    case 'adopted':
      return 'success'
    case 'rejected':
      return 'danger'
    case 'reviewing':
      return 'warning'
    case 'reviewed':
      return 'info'
    default:
      return 'info'
  }
}

/**
 * 根据状态返回中文标签
 */
function statusLabel(status: string): string {
  switch (status) {
    case 'generated':
      return '已生成'
    case 'reviewing':
      return '评审中'
    case 'reviewed':
      return '已评审'
    case 'approved':
      return '已通过'
    case 'rejected':
      return '已拒绝'
    case 'adopted':
      return '已采纳'
    default:
      return status
  }
}

/**
 * 获取报告列表
 */
async function fetchReports() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
    }
    if (filter.value.project_id) params.project_id = filter.value.project_id
    if (filter.value.start_date) params.start_date = filter.value.start_date
    if (filter.value.end_date) params.end_date = filter.value.end_date

    const res = await reportApi.getReportList(params)
    if (res.code === 0) {
      reportList.value = res.data || []
      total.value = res.pagination?.total || 0
    } else {
      ElMessage.error(res.message || '获取报告列表失败')
    }
  } catch (e) {
    ElMessage.error('获取报告列表失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

/**
 * 获取项目列表（用于筛选下拉）
 */
async function fetchProjects() {
  try {
    const res = await aitestApi.getProjectSummaryList()
    if (res.code === 0) {
      projects.value = res.data || []
    }
  } catch {
    // 静默处理
  }
}

/**
 * 点击查询按钮
 */
function handleSearch() {
  if (dateRange.value) {
    filter.value.start_date = dateRange.value[0]
    filter.value.end_date = dateRange.value[1]
  } else {
    filter.value.start_date = null
    filter.value.end_date = null
  }
  pagination.value.page = 1
  fetchReports()
}

/**
 * 点击重置按钮
 */
function handleReset() {
  filter.value = { project_id: null, start_date: null, end_date: null }
  dateRange.value = null
  pagination.value.page = 1
  fetchReports()
}

/**
 * 点击查看报告详情
 */
async function handleViewReport(row: AIReportSummary) {
  detail.value = null
  dialogVisible.value = true
  detailLoading.value = true

  try {
    const res = await reportApi.getReportDetail(row.task_id)
    if (res.code === 0) {
      detail.value = res.data
    } else {
      ElMessage.error(res.message || '获取报告详情失败')
    }
  } catch (e) {
    ElMessage.error('获取报告详情失败')
    console.error(e)
  } finally {
    detailLoading.value = false
  }
}

// ======================================================================
// 初始化
// ======================================================================

onMounted(() => {
  fetchProjects()
  fetchReports()
})
</script>

<style scoped lang="scss">
/* 暖色主题变量 */
$warm-bg: #fdf6ec;
$warm-border: #f5d9b0;
$card-green: #e1f3d8;
$card-red: #fde2e2;
$card-blue: #d9ecff;
$card-orange: #fdecd9;

.page-wrap {
  padding: 24px 16px;
}

.page-header {
  margin-bottom: 20px;

  .page-title {
    margin: 0 0 6px;
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
  }

  .page-desc {
    margin: 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

/* 筛选栏 */
.filter-bar {
  background: $warm-bg;
  border: 1px solid $warm-border;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 20px;

  :deep(.el-form-item) {
    margin-bottom: 0;
  }
}

/* 报告表格卡片 */
.config-table-card {
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;

  :deep(.el-card__body) {
    padding: 0;
  }

  :deep(.el-table) {
    cursor: pointer;
  }
}

.pass-rate-cell {
  padding: 4px 0;
}

.num-pass {
  color: var(--el-color-success);
  font-weight: 600;
}

.num-fail {
  color: var(--el-color-danger);
  font-weight: 600;
}

.num-blocked {
  color: var(--el-color-warning);
  font-weight: 600;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 报告详情弹窗 */
.report-dialog {
  :deep(.el-dialog__body) {
    padding: 20px 24px;
  }

  h4 {
    margin: 0 0 12px;
    font-size: 15px;
    color: var(--el-text-color-primary);
    position: relative;
    padding-left: 12px;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 3px;
      bottom: 3px;
      width: 3px;
      border-radius: 2px;
      background: var(--el-color-primary);
    }
  }
}

.detail-loading {
  padding: 20px;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;

  .stat-card {
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s;

    &:hover {
      transform: translateY(-2px);
    }

    .stat-value {
      font-size: 32px;
      font-weight: 700;
      line-height: 1.2;
    }

    .stat-label {
      font-size: 13px;
      margin-top: 6px;
      color: var(--el-text-color-secondary);
    }
  }

  .card-total {
    background: linear-gradient(135deg, #e8f4fd, #d9ecff);
    .stat-value { color: #409eff; }
  }

  .card-pass {
    background: linear-gradient(135deg, #e1f3d8, #d0edc5);
    .stat-value { color: #67c23a; }
  }

  .card-fail {
    background: linear-gradient(135deg, #fde2e2, #fcd3d3);
    .stat-value { color: #f56c6c; }
  }

  .card-blocked {
    background: linear-gradient(135deg, #fdecd9, #fce3c5);
    .stat-value { color: #e6a23c; }
  }
}

/* 双列布局（通过率 + 模块分布） */
.stats-double-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;

  .pass-rate-section,
  .module-chart-section {
    background: #fafafa;
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 16px;
  }

  .pass-rate-big {
    text-align: center;
    padding: 20px 0;

    .big-number {
      font-size: 42px;
      font-weight: 700;
    }
  }
}

/* 模块分布条形图（纯 CSS 实现） */
.module-bars {
  .module-bar-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }

  .module-label {
    width: 80px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    text-align: right;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .module-bar-track {
    flex: 1;
    height: 18px;
    background: #f0f0f0;
    border-radius: 9px;
    position: relative;
    overflow: hidden;
  }

  .module-bar-fill {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    border-radius: 9px;
    transition: width 0.3s ease;
  }

  .module-bar-pass {
    background: linear-gradient(90deg, #67c23a, #85ce61);
  }

  .module-bar-fail {
    background: linear-gradient(90deg, #f56c6c, #f78989);
  }

  .module-count {
    width: 30px;
    font-size: 12px;
    font-weight: 600;
    text-align: right;
    color: var(--el-text-color-primary);
    flex-shrink: 0;
  }
}

/* 区块容器 */
.section-block {
  margin-bottom: 24px;
}
</style>
