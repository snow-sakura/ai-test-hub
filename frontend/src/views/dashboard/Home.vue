<template>
  <div class="dashboard">
    <!-- 欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-text">
        <h1>早上好，{{ username }}</h1>
        <p>这是您的 AI 智能测试工作台，今天也要高效工作哦</p>
      </div>
      <div class="welcome-date">
        <span class="date-text">{{ currentDate }}</span>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div
        v-for="card in statCards"
        :key="card.label"
        class="stat-card"
      >
        <div class="stat-card-header">
          <div
            class="stat-icon"
            :style="{ background: card.iconBg, color: card.iconColor }"
          >
            <el-icon :size="20">
              <component :is="card.icon" />
            </el-icon>
          </div>
          <span class="stat-label">{{ card.label }}</span>
        </div>
        <div class="stat-card-body">
          <span class="stat-value">{{ card.value }}</span>
          <span v-if="card.trend" class="stat-trend" :class="card.trendDir">
            {{ card.trend }}
          </span>
        </div>
      </div>
    </div>

    <!-- 功能模块 -->
    <div class="section-header">
      <h2>功能模块</h2>
      <span class="section-desc">快速访问常用功能</span>
    </div>

    <div class="module-grid">
      <div
        v-for="mod in modules"
        :key="mod.key"
        class="module-card"
        @click="handleModuleClick(mod.path)"
      >
        <div
          class="module-icon"
          :style="{ background: mod.color + '15', color: mod.color }"
        >
          <el-icon :size="22">
            <component :is="getIconComponent(mod.icon)" />
          </el-icon>
        </div>
        <div class="module-info">
          <h3>{{ mod.name }}</h3>
          <p>{{ mod.description }}</p>
        </div>
        <div class="module-arrow">
          <el-icon :size="16"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { dashboardApi } from '@/api/dashboard'
import type { DashboardStats, ModuleInfo } from '@/types/dashboard'
import type { Component } from 'vue'

import {
  FolderOpened,
  DocumentChecked,
  VideoPlay,
  CircleCheckFilled,
} from '@element-plus/icons-vue'

import {
  MagicStick,
  Connection,
  Monitor,
  Iphone,
  Setting,
  ChatDotSquare,
  Notebook,
  Tools,
} from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()

const username = computed(() => userStore.username || '用户')
const loading = ref(true)
const error = ref('')
const stats = ref<DashboardStats | null>(null)

const modules = ref<ModuleInfo[]>([
  {
    key: 'aitest',
    name: 'AI 智能测试',
    description: 'AI 生成用例、评审、管理全流程',
    icon: 'MagicStick',
    color: '#C67B5C',
    path: '/modules/aitest/dashboard',
    meta: '12 个子模块',
  },
  {
    key: 'api-testing',
    name: 'API 接口测试',
    description: '接口管理与自动化测试套件',
    icon: 'Connection',
    color: '#5B8DEF',
    path: '/modules/api-testing/dashboard',
    meta: '9 个子模块',
  },
  {
    key: 'ui-automation',
    name: 'UI 自动化测试',
    description: 'Web UI 自动化脚本录制与执行',
    icon: 'Monitor',
    color: '#52C41A',
    path: '/modules/ui-automation',
    meta: '即将上线',
  },
  {
    key: 'app-automation',
    name: 'APP 自动化测试',
    description: '移动端 APP 自动化测试',
    icon: 'Iphone',
    color: '#FAAD14',
    path: '/modules/app-automation',
    meta: '即将上线',
  },
  {
    key: 'ai-chat',
    name: 'AI 聊天室',
    description: 'AI 智能对话，获取测试建议',
    icon: 'ChatDotSquare',
    color: '#722ED1',
    path: '/modules/ai-chat',
  },
  {
    key: 'knowledge-base',
    name: '知识库',
    description: '测试知识沉淀与智能检索',
    icon: 'Notebook',
    color: '#13C2C2',
    path: '/modules/knowledge-base',
    meta: '4 个子模块',
  },
  {
    key: 'configuration',
    name: '配置中心',
    description: 'AI 模型、提示词统一配置',
    icon: 'Setting',
    color: '#EB2F96',
    path: '/modules/configuration/ai-models',
    meta: '3 个子模块',
  },
  {
    key: 'system-admin',
    name: '系统管理',
    description: '用户、角色、权限管理',
    icon: 'Tools',
    color: '#8C8C8C',
    path: '/modules/system-admin/users',
    meta: '4 个子模块',
  },
])

interface StatCardConfig {
  icon: Component
  iconBg: string
  iconColor: string
  label: string
  value: string
  trend?: string
  trendDir?: string
}

const statCards = computed<StatCardConfig[]>(() => {
  const s = stats.value
  return [
    {
      icon: FolderOpened,
      iconBg: 'rgba(198, 123, 92, 0.1)',
      iconColor: '#C67B5C',
      label: '项目总数',
      value: s?.total_projects?.toLocaleString() ?? '0',
      trend: '较上月 +0',
      trendDir: 'up',
    },
    {
      icon: DocumentChecked,
      iconBg: 'rgba(91, 141, 239, 0.1)',
      iconColor: '#5B8DEF',
      label: '测试用例',
      value: s?.total_test_cases?.toLocaleString() ?? '0',
      trend: '较上月 +0',
      trendDir: 'up',
    },
    {
      icon: VideoPlay,
      iconBg: 'rgba(82, 196, 26, 0.1)',
      iconColor: '#52C41A',
      label: '今日执行',
      value: s?.today_executions?.toLocaleString() ?? '0',
      trend: '较昨日 +0',
      trendDir: 'up',
    },
    {
      icon: CircleCheckFilled,
      iconBg: 'rgba(250, 173, 20, 0.1)',
      iconColor: '#FAAD14',
      label: '通过率',
      value: s ? (s.pass_rate ?? 0) + '%' : '0%',
      trend: '较上周 +0%',
      trendDir: 'up',
    },
  ]
})

const iconComponentMap: Record<string, Component> = {
  MagicStick,
  Connection,
  Monitor,
  Iphone,
  Setting,
  ChatDotSquare,
  Notebook,
  Tools,
}

function getIconComponent(name: string): Component {
  return iconComponentMap[name] || MagicStick
}

const currentDate = computed(() => {
  const now = new Date()
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 星期${weekDays[now.getDay()]}`
})

const pathMap: Record<string, string> = {
  '/home': '/home',
  '/aitest': '/modules/aitest/dashboard',
  '/api-testing': '/modules/api-testing/dashboard',
  '/ui-automation': '/modules/ui-automation',
  '/app-automation': '/modules/app-automation',
  '/configuration': '/modules/configuration/ai-models',
  '/ai-chat': '/modules/ai-chat',
  '/knowledge-base': '/modules/knowledge-base',
  '/system-admin': '/modules/system-admin/users',
}

function handleModuleClick(path: string) {
  const newPath = pathMap[path] || path
  router.push(newPath)
}

onMounted(async () => {
  loading.value = true
  error.value = ''

  try {
    const [statsRes, modulesRes] = await Promise.all([
      dashboardApi.getStats(),
      dashboardApi.getModules(),
    ])
    stats.value = statsRes.data

    if (modulesRes.data && modulesRes.data.length > 0) {
      modules.value = modulesRes.data
    }
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || ''
    if (msg) {
      console.warn('仪表盘数据加载失败，使用默认配置:', msg)
    }
    try {
      const modulesRes = await dashboardApi.getModules()
      if (modulesRes.data && modulesRes.data.length > 0) {
        modules.value = modulesRes.data
      }
    } catch {
      // 使用内联定义
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.dashboard {
  max-width: 1120px;
  margin: 0 auto;
  padding: 8px 0 40px;
}

/* ====== 欢迎区 ====== */
.welcome-section {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 32px;
}

.welcome-text h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}

.welcome-text p {
  font-size: 14px;
  color: var(--text-muted);
}

.welcome-date .date-text {
  font-size: 13px;
  color: var(--text-muted);
  background: var(--card-bg);
  padding: 6px 14px;
  border-radius: 20px;
  border: var(--border);
}

/* ====== 统计卡片 ====== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;

  @media (max-width: 900px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 20px;
  border: var(--border);
  transition: all 0.25s ease;

  &:hover {
    box-shadow: 0 4px 16px rgba(60, 45, 30, 0.06);
    transform: translateY(-1px);
  }
}

.stat-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

.stat-card-body {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  line-height: 1;
}

.stat-trend {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;

  &.up {
    background: rgba(82, 196, 26, 0.08);
    color: #52C41A;
  }

  &.down {
    background: rgba(180, 150, 120, 0.1);
    color: var(--text-muted);
  }
}

/* ====== 模块区域 ====== */
.section-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;

  h2 {
    font-size: 18px;
    font-weight: 700;
    color: var(--text);
  }

  .section-desc {
    font-size: 13px;
    color: var(--text-muted);
  }
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;

  @media (max-width: 900px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.module-card {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 20px;
  border: var(--border);
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: flex-start;
  gap: 14px;

  &:hover {
    box-shadow: 0 4px 16px rgba(60, 45, 30, 0.08);
    transform: translateY(-2px);
    border-color: rgba(198, 123, 92, 0.2);
  }
}

.module-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.module-info {
  flex: 1;
  min-width: 0;

  h3 {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
  }

  p {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.module-arrow {
  color: var(--text-muted);
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
  margin-top: 10px;

  .module-card:hover & {
    opacity: 1;
  }
}
</style>
