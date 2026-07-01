<template>
  <div class="api-dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card__inner">
            <div class="stat-card__icon" style="background: #e6f7ff; color: #1890ff">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ dashboard.total_projects }}</div>
              <div class="stat-card__label">项目数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card__inner">
            <div class="stat-card__icon" style="background: #f6ffed; color: #52c41a">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ dashboard.total_endpoints }}</div>
              <div class="stat-card__label">接口总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card__inner">
            <div class="stat-card__icon" style="background: #fff7e6; color: #fa8c16">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ dashboard.today_executions }}</div>
              <div class="stat-card__label">今日执行</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card__inner">
            <div class="stat-card__icon" style="background: #fff0f6; color: #eb2f96">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ (dashboard.pass_rate * 100).toFixed(1) }}%</div>
              <div class="stat-card__label">通过率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 趋势图 + 方法分布 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <span>执行趋势（近7天）</span>
          </template>
          <div class="trend-chart">
            <div class="trend-bars">
              <div
                v-for="(item, index) in dashboard.trend_data"
                :key="index"
                class="trend-bar-group"
              >
                <div class="trend-bar passed" :style="{ height: barHeight(item.passed, maxExec) + 'px' }" />
                <div class="trend-bar failed" :style="{ height: barHeight(item.failed, maxExec) + 'px' }" />
                <div class="trend-label">{{ item.date.slice(5) }}</div>
              </div>
            </div>
            <div class="trend-legend">
              <span class="legend-item"><span class="dot passed" />通过</span>
              <span class="legend-item"><span class="dot failed" />失败</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>HTTP 方法分布</span>
          </template>
          <div class="donut-chart">
            <div class="donut-ring">
              <svg viewBox="0 0 32 32" class="donut-svg">
                <circle
                  v-for="(item, index) in methodColors"
                  :key="index"
                  cx="16" cy="16" r="12"
                  :stroke="item.color"
                  :stroke-dasharray="dashArray(item.value, totalMethods)"
                  :stroke-dashoffset="dashOffset(index)"
                  fill="none"
                  stroke-width="4"
                  class="donut-segment"
                />
              </svg>
              <div class="donut-center">
                <div class="donut-total">{{ totalMethods }}</div>
                <div class="donut-total-label">总计</div>
              </div>
            </div>
            <div class="donut-legend">
              <div
                v-for="(item, index) in methodList"
                :key="index"
                class="donut-legend-item"
              >
                <span class="dot" :style="{ background: item.color }" />
                <span class="label">{{ item.method }}</span>
                <span class="value">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 近期报告 -->
    <el-card shadow="hover" class="reports-card">
      <template #header>
        <span>近期报告</span>
      </template>
      <el-empty v-if="dashboard.recent_reports.length === 0" description="暂无报告数据" />
      <el-table
        v-else
        :data="dashboard.recent_reports"
        stripe
        style="width: 100%"
        @row-click="goReport"
      >
        <el-table-column prop="name" label="报告名称" />
        <el-table-column prop="total" label="总数" width="80" />
        <el-table-column prop="passed" label="通过" width="80" />
        <el-table-column prop="failed" label="失败" width="80" />
        <el-table-column label="通过率" width="160">
          <template #default="scope">
            <el-progress
              :percentage="Math.round(scope.row.pass_rate * 100)"
              :color="passRateColor"
              :stroke-width="16"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Folder, Connection, Clock, DataAnalysis } from '@element-plus/icons-vue'

const router = useRouter()

interface TrendItem {
  date: string
  executions: number
  passed: number
  failed: number
}

interface DashboardData {
  total_projects: number
  total_endpoints: number
  total_suites: number
  total_executions: number
  today_executions: number
  pass_rate: number
  trend_data: TrendItem[]
  method_distribution: Record<string, number>
  recent_reports: any[]
}

const dashboard = ref<DashboardData>({
  total_projects: 0,
  total_endpoints: 0,
  total_suites: 0,
  total_executions: 0,
  today_executions: 0,
  pass_rate: 0,
  trend_data: [],
  method_distribution: { GET: 0, POST: 0, PUT: 0, DELETE: 0, PATCH: 0 },
  recent_reports: [],
})

const methodColors = computed(() => [
  { method: 'GET', value: dashboard.value.method_distribution.GET || 0, color: '#52c41a' },
  { method: 'POST', value: dashboard.value.method_distribution.POST || 0, color: '#1890ff' },
  { method: 'PUT', value: dashboard.value.method_distribution.PUT || 0, color: '#fa8c16' },
  { method: 'DELETE', value: dashboard.value.method_distribution.DELETE || 0, color: '#ff4d4f' },
  { method: 'PATCH', value: dashboard.value.method_distribution.PATCH || 0, color: '#722ed1' },
])

const methodList = computed(() =>
  methodColors.value.filter((m) => m.value > 0)
)

const totalMethods = computed(() =>
  methodColors.value.reduce((sum, m) => sum + m.value, 0)
)

const maxExec = computed(() => {
  const max = Math.max(
    ...dashboard.value.trend_data.map((d) => d.passed + d.failed),
    1
  )
  return max
})

function barHeight(value: number, max: number): number {
  if (max === 0) return 0
  return (value / max) * 150
}

function dashArray(value: number, total: number): string {
  if (total === 0) return '0 100'
  const pct = (value / total) * 100
  return `${pct} ${100 - pct}`
}

function dashOffset(index: number): string {
  let offset = 0
  for (let i = 0; i < index; i++) {
    offset += methodColors.value[i].value
  }
  if (totalMethods.value === 0) return '0'
  return `${-((offset / totalMethods.value) * 100)}`
}

function passRateColor(pct: number): string {
  if (pct >= 80) return '#52c41a'
  if (pct >= 50) return '#fa8c16'
  return '#ff4d4f'
}

function goReport(row: any) {
  router.push(`/modules/api-testing/reports?report_id=${row.id}`)
}

async function fetchDashboard() {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/v1/api-testing/dashboard', {
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json()
    if (json.code === 0 && json.data) {
      dashboard.value = json.data
    }
  } catch {
    // 使用默认空数据
  }
}

onMounted(fetchDashboard)
</script>

<style scoped>
.api-dashboard {
  padding: 20px;
}
.stat-cards {
  margin-bottom: 20px;
}
.stat-card__inner {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-card__icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.stat-card__value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}
.stat-card__label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}
.chart-row {
  margin-bottom: 20px;
}
.trend-chart {
  padding: 10px 0;
}
.trend-bars {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  height: 180px;
  padding-bottom: 30px;
  position: relative;
}
.trend-bar-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  position: relative;
}
.trend-bar {
  width: 24px;
  border-radius: 4px 4px 0 0;
  min-height: 2px;
  transition: height 0.3s;
}
.trend-bar.passed {
  background: #52c41a;
}
.trend-bar.failed {
  background: #ff4d4f;
}
.trend-label {
  position: absolute;
  bottom: -24px;
  font-size: 12px;
  color: #999;
}
.trend-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.dot.passed {
  background: #52c41a;
}
.dot.failed {
  background: #ff4d4f;
}
.donut-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.donut-ring {
  width: 120px;
  height: 120px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.donut-segment {
  transition: stroke-dasharray 0.3s;
}
.donut-center {
  position: absolute;
  text-align: center;
}
.donut-total {
  font-size: 22px;
  font-weight: 700;
  color: #333;
}
.donut-total-label {
  font-size: 12px;
  color: #999;
}
.donut-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px 16px;
  margin-top: 12px;
}
.donut-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.donut-legend-item .label {
  color: #666;
}
.donut-legend-item .value {
  color: #333;
  font-weight: 600;
}
.reports-card {
  margin-top: 0;
}
</style>
