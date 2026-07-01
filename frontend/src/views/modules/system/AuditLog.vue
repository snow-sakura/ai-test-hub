<template>
  <!--
    审计日志页面

    筛选栏支持操作类型/模块/用户/时间范围搜索，el-table 展示日志列表，支持查看详情。
  -->
  <div class="page-wrap">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">审计日志</h1>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
        <el-select v-model="filterAction" placeholder="全部操作类型" clearable style="width: 140px">
          <el-option label="全部操作类型" value="" />
          <el-option label="创建" value="create" />
          <el-option label="更新" value="update" />
          <el-option label="删除" value="delete" />
          <el-option label="登录" value="login" />
          <el-option label="登出" value="logout" />
        </el-select>
        <el-select v-model="filterModule" placeholder="全部模块" clearable style="width: 140px">
          <el-option label="全部模块" value="" />
          <el-option label="用户管理" value="user_management" />
          <el-option label="角色权限" value="role_permission" />
          <el-option label="系统设置" value="system_settings" />
          <el-option label="AI智能测试" value="ai_testing" />
          <el-option label="配置中心" value="configuration" />
        </el-select>
        <el-input
          v-model="filterUser"
          placeholder="操作用户"
          clearable
          style="width: 140px"
        />
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="~"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 260px"
        />
        <el-input
          v-model="filterKeyword"
          placeholder="搜索详情..."
          clearable
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="warning" plain @click="handleSearch">搜索</el-button>
        <el-button plain @click="resetFilter">重置</el-button>
      </div>

    <!-- 日志表格 -->
    <el-card shadow="never" class="config-table-card">

      <el-table
        :data="logList"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无日志数据"
      >
        <el-table-column label="时间" min-width="170" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" min-width="100" align="center" show-overflow-tooltip />
        <el-table-column label="模块" min-width="120" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            {{ moduleLabel(row.module) }}
          </template>
        </el-table-column>
        <el-table-column label="操作类型" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small" effect="plain">
              {{ actionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="详情" min-width="300" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="log-detail">{{ row.detail || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" min-width="140" align="center" show-overflow-tooltip />
        <el-table-column label="状态" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'success' ? 'success' : 'danger'"
              size="small"
              effect="plain"
            >
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="70" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @change="loadLogs"
        />
      </div>
    </el-card>
    <!-- 日志详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="日志详情"
      width="580px"
      :close-on-click-modal="false"
    >
      <div v-if="detailData" class="detail-grid">
        <div class="detail-row">
          <span class="label">时间</span>
          <span class="value">{{ formatTime(detailData.created_at) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">操作用户</span>
          <span class="value">{{ detailData.username }}</span>
        </div>
        <div class="detail-row">
          <span class="label">所属模块</span>
          <span class="value">{{ moduleLabel(detailData.module) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">操作类型</span>
          <span class="value">
            <el-tag :type="actionTagType(detailData.action)" size="small" effect="plain">
              {{ actionLabel(detailData.action) }}
            </el-tag>
          </span>
        </div>
        <div class="detail-row">
          <span class="label">操作详情</span>
          <span class="value">{{ detailData.detail || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="label">IP 地址</span>
          <span class="value">{{ detailData.ip_address || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="label">操作状态</span>
          <span class="value">
            <el-tag
              :type="detailData.status === 'success' ? 'success' : 'danger'"
              size="small"
              effect="plain"
            >
              {{ detailData.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </span>
        </div>
        <div class="detail-row">
          <span class="label">对象类型</span>
          <span class="value">{{ detailData.target_type || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="label">对象 ID</span>
          <span class="value">{{ detailData.target_id ?? '-' }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import type { AuditLog } from '@/types/admin'

// ====================================================================
// 状态管理
// ====================================================================

const logList = ref<AuditLog[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filterAction = ref('')
const filterModule = ref('')
const filterUser = ref('')
const filterKeyword = ref('')
const dateRange = ref<[string, string] | null>(null)

const detailVisible = ref(false)
const detailData = ref<AuditLog | null>(null)

// ====================================================================
// 生命周期
// ====================================================================

onMounted(() => {
  loadLogs()
})

// ====================================================================
// 方法
// ====================================================================

/** 加载日志列表 */
async function loadLogs() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (filterAction.value) params.action = filterAction.value
    if (filterModule.value) params.module = filterModule.value
    if (filterUser.value) params.username = filterUser.value
    if (filterKeyword.value) params.keyword = filterKeyword.value
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const res = await adminApi.getAuditLogs(params)
    logList.value = res.data || []
    total.value = res.pagination?.total || 0
  } catch {
    ElMessage.error('加载审计日志失败')
  } finally {
    loading.value = false
  }
}

/** 搜索 */
function handleSearch() {
  currentPage.value = 1
  loadLogs()
}

/** 重置筛选条件 */
function resetFilter() {
  filterAction.value = ''
  filterModule.value = ''
  filterUser.value = ''
  filterKeyword.value = ''
  dateRange.value = null
  currentPage.value = 1
  loadLogs()
}

/** 格式化时间 */
function formatTime(time?: string): string {
  if (!time) return '-'
  return time.replace('T', ' ').substring(0, 19)
}

/** 操作类型映射为中文 */
function actionLabel(action: string): string {
  const map: Record<string, string> = {
    create: '创建',
    update: '更新',
    delete: '删除',
    login: '登录',
    logout: '登出',
  }
  return map[action] || action
}

/** 操作类型标签颜色 */
function actionTagType(action: string): string {
  const map: Record<string, string> = {
    create: 'success',
    update: 'primary',
    delete: 'danger',
    login: 'warning',
    logout: 'info',
  }
  return map[action] || 'info'
}

/** 模块名映射为中文 */
function moduleLabel(module: string): string {
  const map: Record<string, string> = {
    user_management: '用户管理',
    role_permission: '角色权限',
    system_settings: '系统设置',
    ai_testing: 'AI智能测试',
    configuration: '配置中心',
  }
  return map[module] || module
}

/** 打开日志详情弹窗 */
function openDetail(row: AuditLog) {
  detailData.value = row
  detailVisible.value = true
}
</script>

<style scoped lang="scss">
.page-wrap {
  padding: 24px 16px;

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    .page-title {
      font-size: 22px;
      font-weight: 700;
      color: #3d2e1f;
      margin: 0;
    }
  }

  .filter-bar {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 16px;

    .search-input {
      flex: 1;
      min-width: 200px;
      max-width: 420px;
    }
  }

  .config-table-card {
    border: 1px solid rgba(180, 150, 120, 0.12);
    border-radius: 8px;
    background: #fffdf9;

    :deep(.el-card__body) {
      padding: 16px;
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      padding: 16px 0 4px;
    }

    .time-text {
      font-size: 13px;
      color: #8b7355;
      white-space: nowrap;
    }

    .log-detail {
      font-size: 13px;
      color: #8b7355;
    }
  }

  .detail-grid {
    .detail-row {
      display: grid;
      grid-template-columns: 100px 1fr;
      gap: 8px 16px;
      padding: 8px 0;
      font-size: 14px;
      border-bottom: 1px solid rgba(180, 150, 120, 0.08);

      .label {
        color: #8b7355;
        font-weight: 500;
      }

      .value {
        color: #5c4a38;
        word-break: break-all;
      }
    }
  }
}
</style>
