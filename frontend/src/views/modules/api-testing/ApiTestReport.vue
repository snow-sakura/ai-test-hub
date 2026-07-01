<template>
  <div class="api-test-report">
    <!-- 筛选区 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filters" size="default">
        <el-form-item label="项目">
          <el-select v-model="filters.project_id" placeholder="全部项目" clearable style="width:160px">
            <el-option label="全部" :value="null" />
          </el-select>
        </el-form-item>
        <el-form-item label="套件名称">
          <el-input
            v-model="filters.suite_name"
            placeholder="搜索套件名称"
            clearable
            style="width:180px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width:120px">
            <el-option label="全部" :value="null" />
            <el-option label="通过" value="passed" />
            <el-option label="失败" value="failed" />
            <el-option label="部分通过" value="partial" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filters.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width:240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchReports">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报告表格 -->
    <el-card shadow="hover" class="table-card">
      <el-table :data="reports" stripe style="width:100%" @row-click="showDetail">
        <el-table-column prop="name" label="报告名称" min-width="160" />
        <el-table-column prop="project_name" label="项目" width="120" />
        <el-table-column prop="total" label="总数" width="70" align="center" />
        <el-table-column prop="passed" label="通过" width="70" align="center" />
        <el-table-column prop="failed" label="失败" width="70" align="center" />
        <el-table-column label="通过率" width="180">
          <template #default="scope">
            <el-progress
              :percentage="Math.round(scope.row.pass_rate * 100)"
              :color="passRateColor"
              :stroke-width="16"
            />
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="scope">{{ scope.row.duration }}ms</template>
        </el-table-column>
        <el-table-column prop="created_at" label="执行时间" width="170" />
      </el-table>
      <el-empty v-if="reports.length === 0 && !loading" description="暂无报告数据" />
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="detailData.name || '报告详情'"
      width="800px"
      top="5vh"
    >
      <template v-if="detailData.id">
        <!-- 统计卡片 -->
        <el-row :gutter="16" class="detail-stats">
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ detailData.total }}</div>
              <div class="detail-stat-label">总计</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card success">
              <div class="detail-stat-value">{{ detailData.passed }}</div>
              <div class="detail-stat-label">通过</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card danger">
              <div class="detail-stat-value">{{ detailData.failed }}</div>
              <div class="detail-stat-label">失败</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="detail-stat-card">
              <div class="detail-stat-value">{{ (detailData.pass_rate * 100).toFixed(1) }}%</div>
              <div class="detail-stat-label">通过率</div>
            </div>
          </el-col>
        </el-row>

        <!-- 逐接口详情 -->
        <el-table :data="detailData.details" stripe style="width:100%;margin-top:16px">
          <el-table-column prop="endpoint" label="接口路径" min-width="200" />
          <el-table-column prop="method" label="方法" width="80" align="center">
            <template #default="scope">
              <el-tag :type="methodTag(scope.row.method)" size="small">
                {{ scope.row.method }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status_code" label="状态码" width="80" align="center" />
          <el-table-column prop="duration" label="耗时(ms)" width="90" align="center" />
          <el-table-column prop="result" label="结果" width="80" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.result === 'passed' ? 'success' : 'danger'" size="small">
                {{ scope.row.result === 'passed' ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <el-empty v-else description="暂无详情数据" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { Search } from '@element-plus/icons-vue'

const route = useRoute()

const filters = reactive({
  project_id: null as number | null,
  suite_name: '',
  status: null as string | null,
  date_range: null as [string, string] | null,
})

const reports = ref<any[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const detailData = ref<any>({})

function passRateColor(pct: number): string {
  if (pct >= 80) return '#52c41a'
  if (pct >= 50) return '#fa8c16'
  return '#ff4d4f'
}

function methodTag(method: string): string {
  const map: Record<string, string> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'info',
  }
  return map[method] || 'info'
}

async function fetchReports() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (route.query.report_id) {
      params.set('id', route.query.report_id as string)
    }
    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/v1/api-testing/reports?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json()
    if (json.code === 0 && json.data) {
      reports.value = json.data.items || []
    }
  } catch {
    reports.value = []
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.project_id = null
  filters.suite_name = ''
  filters.status = null
  filters.date_range = null
  fetchReports()
}

async function showDetail(row: any) {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/v1/api-testing/reports/${row.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json()
    if (json.code === 0 && json.data) {
      detailData.value = json.data
    }
  } catch {
    detailData.value = row
  }
  detailVisible.value = true
}

onMounted(fetchReports)
</script>

<style scoped>
.api-test-report {
  padding: 20px;
}
.filter-card {
  margin-bottom: 16px;
}
.table-card {
  min-height: 300px;
}
.detail-stats {
  margin-bottom: 16px;
}
.detail-stat-card {
  text-align: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}
.detail-stat-card.success {
  background: #f6ffed;
  border-color: #b7eb8f;
}
.detail-stat-card.danger {
  background: #fff2f0;
  border-color: #ffccc7;
}
.detail-stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
}
.detail-stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}
</style>
