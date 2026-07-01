<template>
  <div class="request-history">
    <!-- 筛选区 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filters" size="default">
        <el-form-item label="项目">
          <el-select v-model="filters.project_id" placeholder="全部" clearable style="width:140px">
            <el-option label="全部" :value="null" />
          </el-select>
        </el-form-item>
        <el-form-item label="方法">
          <el-select v-model="filters.methods" placeholder="全部" multiple clearable style="width:160px">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态码">
          <el-input-number v-model="filters.status_code_min" :min="100" :max="599" placeholder="最小" size="default" style="width:100px" />
          <span class="range-sep">-</span>
          <el-input-number v-model="filters.status_code_max" :min="100" :max="599" placeholder="最大" size="default" style="width:100px" />
        </el-form-item>
        <el-form-item label="路径">
          <el-input v-model="filters.path_keyword" placeholder="关键词搜索" clearable style="width:160px" />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filters.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width:220px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchHistory">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 批量操作 -->
      <div class="bulk-actions">
        <el-checkbox v-model="selectAll" :indeterminate="indeterminate" @change="toggleSelectAll">
          全选
        </el-checkbox>
        <el-button size="small" :disabled="selectedIds.length === 0" type="danger" @click="bulkDelete">
          批量删除 ({{ selectedIds.length }})
        </el-button>
        <el-button size="small" type="danger" plain @click="clearAll">一键清空</el-button>
      </div>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="hover">
      <el-table
        :data="historyList"
        stripe
        style="width:100%"
        @row-click="showDetail"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="40" />
        <el-table-column prop="path" label="接口路径" min-width="200">
          <template #default="scope">
            <span class="path-text">{{ scope.row.path }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="方法" width="90" align="center">
          <template #default="scope">
            <el-tag :type="methodTag(scope.row.method)" size="small">
              {{ scope.row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status_code" label="状态码" width="90" align="center">
          <template #default="scope">
            <el-tag :type="statusCodeTag(scope.row.status_code)" size="small">
              {{ scope.row.status_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="scope">{{ scope.row.duration }}ms</template>
        </el-table-column>
        <el-table-column prop="created_at" label="执行时间" width="170" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="scope">
            <el-button size="small" type="danger" link @click.stop="confirmDeleteSingle(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="historyList.length === 0" description="暂无请求历史" />

      <!-- 分页 -->
      <div class="pagination-wrap" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @change="fetchHistory"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="'请求详情'"
      width="800px"
      top="5vh"
    >
      <template v-if="detailData.id">
        <el-tabs v-model="detailTab">
          <el-tab-pane label="请求" name="request">
            <div class="detail-section">
              <div class="detail-row">
                <span class="label">接口路径：</span>
                <span class="value">{{ detailData.method }} {{ detailData.path }}</span>
              </div>
              <div class="detail-row">
                <span class="label">请求头：</span>
                <pre class="json-block">{{ formatJson(detailData.request?.headers) }}</pre>
              </div>
              <div class="detail-row">
                <span class="label">请求体：</span>
                <pre class="json-block">{{ formatJson(detailData.request?.body) }}</pre>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="响应" name="response">
            <div class="detail-section">
              <div class="detail-row">
                <span class="label">状态码：</span>
                <el-tag :type="statusCodeTag(detailData.status_code)" size="small">
                  {{ detailData.status_code }}
                </el-tag>
                <span style="margin-left:16px">
                  耗时：{{ detailData.duration }}ms
                </span>
              </div>
              <div class="detail-row">
                <span class="label">响应头：</span>
                <pre class="json-block">{{ formatJson(detailData.response?.headers) }}</pre>
              </div>
              <div class="detail-row">
                <span class="label">响应体：</span>
                <pre class="json-block">{{ formatJson(detailData.response?.body) }}</pre>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
      <el-empty v-else description="暂无详情数据" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

interface HistoryFilters {
  project_id: number | null
  methods: string[]
  status_code_min: number | null
  status_code_max: number | null
  date_range: [string, string] | null
  path_keyword: string
}

const filters = reactive<HistoryFilters>({
  project_id: null,
  methods: [],
  status_code_min: null,
  status_code_max: null,
  date_range: null,
  path_keyword: '',
})

const historyList = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const detailVisible = ref(false)
const detailData = ref<any>({})
const detailTab = ref('request')
const selectedIds = ref<number[]>([])
const selectAll = ref(false)
const indeterminate = ref(false)

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

function statusCodeTag(code: number): string {
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'warning'
  if (code >= 400) return 'danger'
  return 'info'
}

function formatJson(obj: any): string {
  if (!obj) return '-'
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

function onSelectionChange(rows: any[]) {
  selectedIds.value = rows.map((r) => r.id)
  indeterminate.value = rows.length > 0 && rows.length < historyList.value.length
}

function toggleSelectAll(_val: boolean) {
  // 实际全选逻辑由 el-table 的 selection-change 处理
}

async function fetchHistory() {
  try {
    const params = new URLSearchParams()
    params.set('page', String(page.value))
    params.set('page_size', String(pageSize.value))
    if (filters.methods.length) params.set('methods', filters.methods.join(','))
    if (filters.status_code_min) params.set('status_code_min', String(filters.status_code_min))
    if (filters.status_code_max) params.set('status_code_max', String(filters.status_code_max))
    if (filters.path_keyword) params.set('path_keyword', filters.path_keyword)
    if (filters.date_range) {
      params.set('start_date', filters.date_range[0])
      params.set('end_date', filters.date_range[1])
    }

    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/v1/api-testing/history?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json()
    if (json.code === 0 && json.data) {
      historyList.value = json.data.items || []
      total.value = json.data.total || 0
    }
  } catch {
    historyList.value = []
    total.value = 0
  }
}

function resetFilters() {
  filters.project_id = null
  filters.methods = []
  filters.status_code_min = null
  filters.status_code_max = null
  filters.date_range = null
  filters.path_keyword = ''
  page.value = 1
  fetchHistory()
}

async function showDetail(row: any) {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/v1/api-testing/history/${row.id}`, {
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

function confirmDeleteSingle(row: any) {
  ElMessageBox.confirm(`确定删除此请求记录？`, '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`/api/v1/api-testing/history/${row.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const json = await res.json()
      if (json.code === 0) {
        ElMessage.success('删除成功')
        fetchHistory()
      }
    } catch {
      ElMessage.error('删除失败')
    }
  })
}

async function bulkDelete() {
  if (selectedIds.value.length === 0) return
  ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条记录？`, '批量删除', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch('/api/v1/api-testing/history', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ ids: selectedIds.value }),
      })
      const json = await res.json()
      if (json.code === 0) {
        ElMessage.success('批量删除成功')
        selectedIds.value = []
        fetchHistory()
      }
    } catch {
      ElMessage.error('批量删除失败')
    }
  })
}

function clearAll() {
  ElMessageBox.confirm('确定清空所有请求历史记录？此操作不可恢复！', '清空确认', {
    confirmButtonText: '清空',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger',
  }).then(async () => {
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch('/api/v1/api-testing/history/clear', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const json = await res.json()
      if (json.code === 0) {
        ElMessage.success('已清空所有记录')
        fetchHistory()
      }
    } catch {
      ElMessage.error('清空失败')
    }
  })
}

onMounted(fetchHistory)
</script>

<style scoped>
.request-history {
  padding: 20px;
}
.filter-card {
  margin-bottom: 16px;
}
.range-sep {
  padding: 0 8px;
  color: #999;
}
.bulk-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  margin-top: 8px;
}
.path-text {
  font-family: monospace;
  font-size: 13px;
  color: #333;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.detail-section {
  padding: 8px 0;
}
.detail-row {
  margin-bottom: 12px;
}
.detail-row .label {
  font-weight: 600;
  color: #666;
  display: block;
  margin-bottom: 4px;
}
.detail-row .value {
  color: #333;
}
.json-block {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
}
</style>
