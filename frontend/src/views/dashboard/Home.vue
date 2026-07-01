<template>
  <!--
    首页仪表盘组件
    欢迎区 + 统计卡片 + 功能模块网格
  -->
  <div class="dashboard">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-else-if="error"
      :title="error"
      type="error"
      show-icon
      closable
      @close="error = ''"
    />

    <!-- 仪表盘内容 -->
    <template v-else>
      <!-- ====== 欢迎区 ====== -->
      <div class="welcome">
        <h1><span>AI-HUB</span> 智能工作台</h1>
        <p>欢迎回来，{{ username }}！这是您的测试工作台概览。</p>
      </div>

      <!-- ====== 统计卡片（4 个） ====== -->
      <div class="stats">
        <div
          v-for="card in statCards"
          :key="card.label"
          class="stat-card"
        >
          <div
            class="stat-icon"
            :style="{ background: card.iconBg, color: card.iconColor }"
          >
            <el-icon :size="24">
              <component :is="card.icon" />
            </el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-number">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
            <div
              v-if="card.trend"
              class="stat-trend"
              :class="card.trendDir"
            >
              {{ card.trend }}
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 功能模块网格 ====== -->
      <div class="module-grid">
        <div
          v-for="mod in modules"
          :key="mod.key"
          class="module-card"
          :style="{ '--card-color': mod.color }"
          @click="handleModuleClick(mod.path)"
        >
          <!-- 顶部 hover 彩色条 -->
          <div class="module-card-bar" :style="{ background: mod.color }" />
          <!-- 图标 -->
          <div
            class="module-card-icon"
            :style="{ background: mod.color + '18', color: mod.color }"
          >
            <el-icon :size="22">
              <component :is="getIconComponent(mod.icon)" />
            </el-icon>
          </div>
          <!-- 名称和描述 -->
          <h3>{{ mod.name }}</h3>
          <p>{{ mod.description }}</p>
          <!-- 元信息 -->
          <div v-if="mod.meta" class="module-card-meta">
            <span>{{ mod.meta }}</span>
          </div>
          <div v-else class="module-card-meta">
            <span>实时对话</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { dashboardApi } from '@/api/dashboard'
import type { DashboardStats, ModuleInfo } from '@/types/dashboard'
import type { Component } from 'vue'

// Element Plus 统计卡片图标
import {
  FolderOpened,
  DocumentChecked,
  VideoPlay,
  CircleCheckFilled,
} from '@element-plus/icons-vue'

// Element Plus 功能模块图标（动态加载用）
import {
  MagicStick,
  Connection,
  Monitor,
  Iphone,
  List,
  Setting,
  ChatDotSquare,
  Notebook,
  Tools,
} from '@element-plus/icons-vue'

/** 用户状态 */
const userStore = useUserStore()
const router = useRouter()

/** 当前用户名 */
const username = computed(() => userStore.username || '用户')

// ========== 数据状态 ==========

/** 加载中 */
const loading = ref(true)
/** 错误信息 */
const error = ref('')
/** 统计数据 */
const stats = ref<DashboardStats | null>(null)

/** 内联功能模块定义（确保卡片始终展示，后端 API 仅做增强） */
const modules = ref<ModuleInfo[]>([
  {
    key: 'aitest',
    name: 'AI智能测试',
    description: '项目、版本、用例、评审、AI生成、评测全流程管理',
    icon: 'MagicStick',
    color: '#C67B5C',
    path: '/modules/aitest/dashboard',
    meta: '12个子模块',
  },
  {
    key: 'api-testing',
    name: 'API接口测试',
    description: 'HTTP/WebSocket接口测试与自动化',
    icon: 'Connection',
    color: '#D4A574',
    path: '/modules/api-testing/dashboard',
    meta: '9个子模块',
  },
  {
    key: 'ui-automation',
    name: 'UI自动化测试',
    description: 'Web端UI自动化测试脚本录制与执行',
    icon: 'Monitor',
    color: '#C67B5C',
    path: '/modules/ui-automation',
    meta: '5个子模块',
  },
  {
    key: 'app-automation',
    name: 'APP自动化测试',
    description: '移动端APP自动化测试',
    icon: 'Iphone',
    color: '#D4A574',
    path: '/modules/app-automation',
    meta: '4个子模块',
  },
  {
    key: 'configuration',
    name: '配置中心',
    description: 'AI模型、提示词、环境统一配置',
    icon: 'Setting',
    color: '#D4A574',
    path: '/modules/configuration/ai-models',
    meta: '3个子模块',
  },
  {
    key: 'ai-chat',
    name: 'AI聊天室',
    description: 'AI智能对话助手，随时获取测试建议',
    icon: 'ChatDotSquare',
    color: '#C67B5C',
    path: '/modules/ai-chat',
  },
  {
    key: 'knowledge-base',
    name: '知识库',
    description: '测试知识沉淀与共享',
    icon: 'Notebook',
    color: '#D4A574',
    path: '/modules/knowledge-base',
    meta: '4个子模块',
  },
  {
    key: 'system-admin',
    name: '系统管理',
    description: '用户、角色、权限、审计管理',
    icon: 'Tools',
    color: '#C67B5C',
    path: '/modules/system-admin/users',
    meta: '4个子模块',
  },
])

// ========== 统计卡片配置 ==========

/** 统计卡片定义 */
interface StatCardConfig {
  /** Element Plus 图标组件 */
  icon: Component
  /** 图标背景色 */
  iconBg: string
  /** 图标颜色 */
  iconColor: string
  /** 显示标签 */
  label: string
  /** 数值 */
  value: string
  /** 趋势文字 */
  trend?: string
  /** 趋势方向（up / down） */
  trendDir?: string
}

/** 根据统计数据组装卡片列表 */
const statCards = computed<StatCardConfig[]>(() => {
  const s = stats.value
  return [
    {
      icon: FolderOpened,
      iconBg: 'rgba(198, 123, 92, 0.12)',
      iconColor: 'var(--primary)',
      label: '项目总数',
      value: s?.total_projects?.toLocaleString() ?? '0',
      trend: '较上月 +0',
      trendDir: 'up',
    },
    {
      icon: DocumentChecked,
      iconBg: 'rgba(74, 144, 217, 0.12)',
      iconColor: '#4A90D9',
      label: '测试用例总数',
      value: s?.total_test_cases?.toLocaleString() ?? '0',
      trend: '较上月 +0',
      trendDir: 'up',
    },
    {
      icon: VideoPlay,
      iconBg: 'rgba(82, 196, 26, 0.12)',
      iconColor: '#52C41A',
      label: '今日执行',
      value: s?.today_executions?.toLocaleString() ?? '0',
      trend: '较昨日 +0',
      trendDir: 'up',
    },
    {
      icon: CircleCheckFilled,
      iconBg: 'rgba(250, 173, 20, 0.12)',
      iconColor: '#FAAD14',
      label: '通过率',
      value: s ? (s.pass_rate ?? 0) + '%' : '0%',
      trend: '较上周 +0%',
      trendDir: 'up',
    },
  ]
})

/** 模块图标名称到 Element Plus 组件的映射 */
const iconComponentMap: Record<string, Component> = {
  MagicStick,
  Connection,
  Monitor,
  Iphone,
  List,
  Setting,
  ChatDotSquare,
  Notebook,
  Tools,
}

/** 根据图标名称获取对应的 EP 图标组件 */
function getIconComponent(name: string): Component {
  return iconComponentMap[name] || MagicStick
}

// ========== 生命周期 ==========

onMounted(async () => {
  await fetchDashboardData()
})

// ========== 数据加载 ==========

/** 获取仪表盘数据（统计 + 可选模块列表增强） */
async function fetchDashboardData() {
  loading.value = true
  error.value = ''

  try {
    // 并行请求统计数据与模块列表
    const [statsRes, modulesRes] = await Promise.all([
      dashboardApi.getStats(),
      dashboardApi.getModules(),
    ])
    stats.value = statsRes.data

    // 后端返回模块数据时，用后端数据覆盖内联默认值
    if (modulesRes.data && modulesRes.data.length > 0) {
      modules.value = modulesRes.data
    }
  } catch (err: any) {
    // API 失败时仍使用内联模块定义，仅显示警告
    const msg = err?.response?.data?.message || err?.message || ''
    if (msg) {
      console.warn('仪表盘数据加载失败，使用默认配置:', msg)
    }
    // 仅加载统计数据失败时尝试单独加载模块
    try {
      const modulesRes = await dashboardApi.getModules()
      if (modulesRes.data && modulesRes.data.length > 0) {
        modules.value = modulesRes.data
      }
    } catch {
      // 模块也加载失败，使用内联定义
    }
  } finally {
    loading.value = false
  }
}

// ========== 交互 ==========

/**
 * 路径映射（兼容旧路径）
 * 内联模块定义已使用正确路径，此处仅处理后端可能返回的旧路径。
 */
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

/** 点击功能模块卡片，导航到对应路由 */
function handleModuleClick(path: string) {
  const newPath = pathMap[path] || path
  router.push(newPath)
}
</script>

<style scoped lang="scss">
/*
 * 仪表盘样式
 * 参考原型页面 aihub-pic/00-首页仪表盘/首页仪表盘.html
 */

.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

// ====== 加载状态 ======

.loading-state {
  padding: 24px;
}

// ====== 欢迎区 ======

.welcome {
  text-align: center;
  margin-bottom: 24px;

  h1 {
    font-size: 28px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 6px;

    span {
      background: linear-gradient(135deg, var(--primary), var(--accent));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }

  p {
    color: var(--text-muted);
    font-size: 15px;
  }
}

// ====== 统计卡片网格 ======

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  @media (max-width: 900px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

/** 统计卡片 */
.stat-card {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: 20px;
  border: var(--border);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.25s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(180, 150, 120, 0.1);
  }
}

/** 统计图标容器 */
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/** 数值+标签区域 */
.stat-body {
  flex: 1;
  min-width: 0;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 2px;
}

.stat-trend {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-top: 4px;
  display: inline-block;

  &.up {
    background: rgba(198, 123, 92, 0.1);
    color: var(--primary);
  }

  &.down {
    background: rgba(180, 150, 120, 0.1);
    color: var(--text-muted);
  }
}

// ====== 功能模块区域标题 ======

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;

  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }
}

// ====== 功能模块网格 ======

.module-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;

  @media (max-width: 900px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

/** 模块卡片 */
.module-card {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: 24px;
  border: var(--border);
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(180, 150, 120, 0.12);

    .module-card-bar {
      opacity: 1;
    }
  }
}

/** 顶部 hover 渐变色条 */
.module-card-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  opacity: 0;
  transition: opacity 0.3s;
}

/** 模块图标 */
.module-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}

/** 模块名称 */
.module-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text);
}

/** 模块描述 */
.module-card p {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 12px;
}

/** 模块元信息 */
.module-card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);

  span {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}
</style>
