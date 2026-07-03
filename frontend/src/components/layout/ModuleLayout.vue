<template>
  <!--
    模块布局（有侧边栏）
    动态侧边栏（按模块显示不同子菜单）+ Topbar + 主内容区
    响应式设计，小屏幕自动折叠侧边栏
  -->
  <div
    class="module-layout"
    :class="{ 'sidebar-collapsed': appStore.sidebarCollapsed }"
  >
    <!-- 侧边栏 -->
    <aside
      class="sidebar"
      :class="{ collapsed: appStore.sidebarCollapsed }"
    >
      <!-- 返回首页 + 模块名称 -->
      <div class="sidebar-header">
        <div class="back-home" @click="goHome">
          <el-icon :size="18"><ArrowLeft /></el-icon>
          <transition name="fade">
            <span v-show="!appStore.sidebarCollapsed" class="back-text">
              {{ $t('common.backToHome') }}
            </span>
          </transition>
        </div>
        <div class="module-title" v-show="!appStore.sidebarCollapsed">
          <el-icon :size="18" class="module-icon">
            <component :is="currentModuleConfig?.icon" />
          </el-icon>
          <span>{{ currentModuleConfig?.title }}</span>
        </div>
      </div>

      <!-- 子导航菜单 -->
      <el-menu
        :default-active="route.path"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item
          v-for="item in currentMenuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon>
            <component :is="item.icon" />
          </el-icon>
          <template #title>
            <span>{{ item.title }}</span>
          </template>
        </el-menu-item>
      </el-menu>

      <!-- 底部：收拢/展开按钮 -->
      <div class="sidebar-footer">
        <el-tooltip
          :content="appStore.sidebarCollapsed ? $t('layout.expand') : $t('layout.collapse')"
          placement="right"
          :show-after="500"
        >
          <div class="collapse-btn" @click="handleToggleCollapse">
            <el-icon :size="18">
              <Fold v-if="!appStore.sidebarCollapsed" />
              <Expand v-else />
            </el-icon>
            <transition name="fade">
              <span v-show="!appStore.sidebarCollapsed" class="collapse-text">
                {{ $t('layout.collapse') }}
              </span>
            </transition>
          </div>
        </el-tooltip>
      </div>
    </aside>

    <!-- 右侧区域 -->
    <div class="layout-right">
      <!-- 移动端遮罩层（侧边栏展开时） -->
      <div
        v-if="!appStore.sidebarCollapsed && isMobile"
        class="sidebar-mask"
        @click="appStore.toggleSidebar()"
      />

      <!-- 顶部导航栏 -->
      <Topbar />

      <!-- 主内容区 -->
      <MainContent />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import Topbar from './Topbar.vue'
import MainContent from './MainContent.vue'
import type { Component } from 'vue'
import {
  ArrowLeft,
  Fold,
  Expand,
  MagicStick,
  Edit,
  DataAnalysis,
  Document,
  Setting,
  Monitor,
  Tools,
  User,
  Lock,
  Folder,
  List,
  ChatSquare,
  Promotion,
  TrendCharts,
} from '@element-plus/icons-vue'

/** 菜单项类型 */
interface SidebarMenuItem {
  /** 路由路径 */
  path: string
  /** 图标组件 */
  icon: Component
  /** 显示标题 */
  title: string
}

/** 模块侧边栏配置 */
interface ModuleSidebarConfig {
  /** 模块显示名称 */
  title: string
  /** 模块图标 */
  icon: Component
  /** 子菜单项列表 */
  items: SidebarMenuItem[]
}

/**
 * 模块子菜单配置
 * 根据路由 meta.module 的值匹配对应的侧边栏菜单
 */
const moduleSidebarConfig: Record<string, ModuleSidebarConfig> = {
  'aitest': {
    title: 'AI智能测试',
    icon: MagicStick,
    items: [
      { path: '/modules/aitest/dashboard', icon: DataAnalysis, title: '测试总览' },
      { path: '/modules/aitest/projects', icon: Folder, title: '项目管理' },
      // 版本管理已整合到项目详情页 Tab 中，移除独立入口
      { path: '/modules/aitest/testcases', icon: Document, title: '用例列表' },
      { path: '/modules/aitest/review-cases', icon: Edit, title: '用例评审' },
      { path: '/modules/aitest/generate', icon: MagicStick, title: 'AI用例生成' },
      { path: '/modules/aitest/generate/records', icon: List, title: 'AI生成记录' },
      { path: '/modules/aitest/ai-tester', icon: ChatSquare, title: 'AI评测师' },
      { path: '/modules/aitest/reports', icon: TrendCharts, title: '测试报告' },
      { path: '/modules/aitest/config/model', icon: Setting, title: 'AI模型配置' },
      { path: '/modules/aitest/config/prompt', icon: Promotion, title: 'AI提示词配置' },
      { path: '/modules/aitest/config/generation', icon: Setting, title: '生成行为配置' },
      { path: '/modules/aitest/config/mode', icon: Monitor, title: '智能模式配置' },
    ],
  },
  'configuration': {
    title: '配置中心',
    icon: Setting,
    items: [
      { path: '/modules/configuration/ai-models', icon: Monitor, title: 'AI模型配置' },
      { path: '/modules/configuration/prompts', icon: Edit, title: '提示词配置' },
      { path: '/modules/configuration/generation', icon: Setting, title: '生成行为配置' },
    ],
  },
  'system-admin': {
    title: '系统管理',
    icon: Tools,
    items: [
      { path: '/modules/system-admin/users', icon: User, title: '用户管理' },
      { path: '/modules/system-admin/roles', icon: Lock, title: '角色权限' },
      { path: '/modules/system-admin/settings', icon: Setting, title: '系统设置' },
      { path: '/modules/system-admin/audit-logs', icon: Document, title: '审计日志' },
    ],
  },
}

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

/** 当前是否为移动端 */
const isMobile = ref(false)

/** 当前模块标识（从路由 meta 获取） */
const currentModule = computed(() => {
  return route.meta?.module as string | undefined
})

/** 当前模块的侧边栏配置 */
const currentModuleConfig = computed<ModuleSidebarConfig | undefined>(() => {
  const mod = currentModule.value
  return mod ? moduleSidebarConfig[mod] : undefined
})

/** 当前模块的子菜单项 */
const currentMenuItems = computed<SidebarMenuItem[]>(() => {
  return currentModuleConfig.value?.items ?? []
})

/** 返回首页 */
function goHome() {
  router.push('/home')
}

/** 切换侧边栏折叠状态 */
function handleToggleCollapse() {
  appStore.toggleSidebar()
}

/** 响应式：窗口宽度小于 768px 时标记为移动端 */
function handleResize() {
  const wasMobile = isMobile.value
  isMobile.value = window.innerWidth < 768
  
  // 仅在首次进入移动端时自动折叠，不强制阻止展开
  if (isMobile.value && !wasMobile) {
    appStore.sidebarCollapsed = true
  }
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
.module-layout {
  display: flex;
  min-height: 100vh;
}

// ====== 侧边栏 ======

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  border-right: var(--border);

  &.collapsed {
    width: var(--sidebar-collapsed-width);
  }
}

// 侧边栏头部（返回首页 + 模块名称）
.sidebar-header {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-bottom: var(--border);
  padding: 12px 0;
}

.back-home {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  margin: 0 8px;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 13px;
  border-radius: var(--radius-sm);
  transition: all 0.2s;

  &:hover {
    color: var(--primary);
    background-color: var(--el-menu-hover-bg-color);
  }

  .el-icon {
    flex-shrink: 0;
  }
}

.back-text {
  white-space: nowrap;
}

.module-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 16px;
  margin: 4px 8px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
}

.module-icon {
  color: var(--primary);
}

// 菜单
.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: none !important;
  padding: 8px 0;
  background: transparent;

  .el-menu-item {
    display: flex;
    align-items: center;
    height: 44px;
    line-height: 44px;
    padding: 0 16px !important;
    margin: 2px 8px;
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 14px;
    transition: all 0.2s;

    &:hover {
      background-color: var(--el-menu-hover-bg-color) !important;
      color: var(--text);
    }

    &.is-active {
      background: linear-gradient(135deg, rgba(198, 123, 92, 0.12), rgba(212, 165, 116, 0.08)) !important;
      color: var(--primary) !important;
      font-weight: 500;
    }

    .el-icon {
      font-size: 18px;
      margin-right: 10px;
    }
  }

  // 折叠时菜单项样式
  .el-menu--collapse & .el-menu-item {
    padding: 0 0 !important;
    margin: 2px 8px;
    justify-content: center;

    .el-icon {
      margin-right: 0;
    }
  }
}

// 底部按钮
.sidebar-footer {
  flex-shrink: 0;
  border-top: var(--border);
  padding: 8px 0;
}

.collapse-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  height: 40px;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.2s;
  border-radius: 0;
  margin: 0 8px;

  &:hover {
    color: var(--text);
    background-color: var(--el-menu-hover-bg-color);
  }

  .el-icon {
    font-size: 18px;
    flex-shrink: 0;
  }
}

.collapse-text {
  font-size: 13px;
  white-space: nowrap;
}

// ====== 右侧区域 ======

.layout-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

// 折叠状态时调整
.sidebar-collapsed .layout-right {
  margin-left: var(--sidebar-collapsed-width);
}

// 移动端遮罩层
.sidebar-mask {
  display: none;

  @media (max-width: 768px) {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.3);
    z-index: 999;
  }
}

// 小屏幕：侧边栏覆盖式
@media (max-width: 768px) {
  .layout-right {
    margin-left: 0 !important;
  }
}
</style>
