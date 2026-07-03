<template>
  <div class="notification-list">
    <!-- Tab 切换 -->
    <el-card shadow="hover" class="filter-card">
      <div class="notification-toolbar">
        <el-radio-group v-model="activeTab" @change="fetchNotifications">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="unread">未读</el-radio-button>
          <el-radio-button value="read">已读</el-radio-button>
        </el-radio-group>
        <el-button
          size="small"
          :disabled="unreadCount === 0"
          @click="markAllRead"
        >
          全部标为已读
        </el-button>
      </div>
    </el-card>

    <!-- 通知列表 -->
    <el-card shadow="hover">
      <div v-if="notifications.length > 0" class="notif-list">
        <div
          v-for="item in notifications"
          :key="item.id"
          :class="['notif-item', { unread: !item.is_read }]"
          @click="showDetail(item)"
        >
          <div class="notif-left">
            <el-checkbox
              v-model="item._checked"
              @change="onCheckChange"
              @click.stop
              class="notif-checkbox"
            />
            <div class="notif-icon" :class="notifTypeClass(item.type)">
              <el-icon><Bell /></el-icon>
            </div>
          </div>
          <div class="notif-content">
            <div class="notif-header">
              <span class="notif-title">{{ item.title }}</span>
              <span v-if="!item.is_read" class="unread-dot" />
            </div>
            <div class="notif-summary">{{ item.summary || item.content?.slice(0, 80) }}</div>
            <div class="notif-time">{{ formatTime(item.created_at) }}</div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="暂无通知">
        <el-icon :size="80" color="#d9d9d9"><Bell /></el-icon>
        <template #description>
          <p class="empty-text">暂无通知</p>
        </template>
      </el-empty>

      <!-- 批量操作 -->
      <div v-if="notifications.length > 0" class="notif-footer">
        <el-checkbox v-model="selectAll" :indeterminate="indeterminate" @change="toggleSelectAll">
          全选
        </el-checkbox>
        <el-button
          size="small"
          :disabled="checkedIds.length === 0"
          @click="markSelectedRead"
        >
          标记已读
        </el-button>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrap" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="fetchNotifications"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="detailData.title || '通知详情'"
      width="560px"
    >
      <template v-if="detailData.id">
        <div class="detail-meta">
          <span class="detail-type">
            <el-tag size="small">{{ detailData.type }}</el-tag>
          </span>
          <span class="detail-time">{{ formatTime(detailData.created_at) }}</span>
        </div>
        <div class="detail-body">{{ detailData.content }}</div>
      </template>
      <el-empty v-else description="暂无详情" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell } from '@element-plus/icons-vue'

interface Notification {
  id: number
  title: string
  summary?: string
  content?: string
  type: string
  is_read: boolean
  created_at: string
  _checked?: boolean
}

const activeTab = ref('all')
const notifications = ref<Notification[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const detailVisible = ref(false)
const detailData = ref<Notification>({} as Notification)

const checkedIds = computed(() =>
  notifications.value.filter((n) => n._checked).map((n) => n.id)
)
const selectAll = ref(false)
const indeterminate = ref(false)

const unreadCount = computed(() =>
  notifications.value.filter((n) => !n.is_read).length
)

function notifTypeClass(type: string): string {
  const map: Record<string, string> = {
    execution_complete: 'success',
    execution_failed: 'danger',
    schedule_trigger: 'warning',
    system: 'info',
  }
  return map[type] || 'info'
}

import { formatDateTime } from '@/utils'

function formatTime(timeStr: string): string {
  if (!timeStr) return '-'
  try {
    return formatDateTime(timeStr)
  } catch {
    return timeStr
  }
}

function onCheckChange() {
  const checked = notifications.value.filter((n) => n._checked)
  indeterminate.value = checked.length > 0 && checked.length < notifications.value.length
  selectAll.value = checked.length === notifications.value.length
}

function toggleSelectAll(val: boolean) {
  notifications.value.forEach((n) => {
    n._checked = val
  })
  indeterminate.value = false
}

async function fetchNotifications() {
  try {
    const params = new URLSearchParams()
    params.set('page', String(page.value))
    params.set('page_size', String(pageSize.value))
    if (activeTab.value !== 'all') {
      params.set('status', activeTab.value)
    }

    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/v1/api-testing/notifications?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const json = await res.json()
    if (json.code === 0 && json.data) {
      notifications.value = (json.data.items || []).map((n: Notification) => ({
        ...n,
        _checked: false,
      }))
      total.value = json.data.total || 0
    }
  } catch {
    notifications.value = []
    total.value = 0
  }
}

async function markAllRead() {
  const ids = notifications.value.filter((n) => !n.is_read).map((n) => n.id)
  if (ids.length === 0) return
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/v1/api-testing/notifications/read', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ ids }),
    })
    const json = await res.json()
    if (json.code === 0) {
      ElMessage.success('已全部标为已读')
      notifications.value.forEach((n) => { n.is_read = true; n._checked = false })
      selectAll.value = false
      indeterminate.value = false
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function markSelectedRead() {
  if (checkedIds.value.length === 0) return
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/v1/api-testing/notifications/read', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ ids: checkedIds.value }),
    })
    const json = await res.json()
    if (json.code === 0) {
      ElMessage.success(`已标记 ${checkedIds.value.length} 条为已读`)
      notifications.value.forEach((n) => {
        if (n._checked) n.is_read = true
        n._checked = false
      })
      selectAll.value = false
      indeterminate.value = false
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

function showDetail(item: Notification) {
  detailData.value = item
  detailVisible.value = true
}

onMounted(fetchNotifications)
</script>

<style scoped>
.notification-list {
  padding: 20px;
}
.filter-card {
  margin-bottom: 16px;
}
.notification-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.notif-list {
  max-height: 600px;
  overflow-y: auto;
}
.notif-item {
  display: flex;
  gap: 12px;
  padding: 14px 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}
.notif-item:hover {
  background: #fafafa;
}
.notif-item.unread {
  background: #f0f9ff;
}
.notif-item.unread:hover {
  background: #e6f7ff;
}
.notif-left {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding-top: 2px;
}
.notif-checkbox {
  margin-right: 4px;
}
.notif-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.notif-icon.success {
  background: #f6ffed;
  color: #52c41a;
}
.notif-icon.danger {
  background: #fff2f0;
  color: #ff4d4f;
}
.notif-icon.warning {
  background: #fff7e6;
  color: #fa8c16;
}
.notif-icon.info {
  background: #f0f5ff;
  color: #1890ff;
}
.notif-content {
  flex: 1;
  min-width: 0;
}
.notif-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.notif-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1890ff;
  flex-shrink: 0;
}
.notif-summary {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}
.notif-time {
  font-size: 12px;
  color: #bbb;
}
.notif-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.empty-text {
  color: #bbb;
  font-size: 14px;
  margin-top: 0;
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.detail-time {
  font-size: 13px;
  color: #999;
}
.detail-body {
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
}
</style>
