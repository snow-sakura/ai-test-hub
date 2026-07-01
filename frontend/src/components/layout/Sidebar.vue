<template>
  <!--
    侧边栏导航组件
    支持折叠/展开切换，导航高亮，响应式
  -->
  <aside
    class="sidebar"
    :class="{ collapsed: appStore.sidebarCollapsed }"
  >
    <!-- Logo 区域 -->
    <div class="sidebar-logo">
      <div class="logo-icon">AI</div>
      <transition name="fade">
        <span v-show="!appStore.sidebarCollapsed" class="logo-text">AI-HUB</span>
      </transition>
    </div>

    <!-- 导航菜单 -->
    <el-menu
      :default-active="route.path"
      :collapse="appStore.sidebarCollapsed"
      :collapse-transition="false"
      router
      class="sidebar-menu"
    >
      <!-- 普通菜单项 -->
      <el-menu-item
        v-for="item in flatMenuItems"
        :key="item.path"
        :index="item.path"
      >
        <el-icon>
          <component :is="item.icon" />
        </el-icon>
        <template #title>
          <span>{{ $t(item.i18nKey) }}</span>
        </template>
      </el-menu-item>

      <!-- 系统管理子菜单 -->
      <el-sub-menu index="/system-admin">
        <template #title>
          <el-icon><Tools /></el-icon>
          <span>{{ $t('nav.systemAdmin') }}</span>
        </template>
        <el-menu-item
          v-for="item in adminSubItems"
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
      </el-sub-menu>
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
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import {
  HomeFilled,
  MagicStick,
  Connection,
  Monitor,
  Iphone,
  Setting,
  Document,
  ChatDotSquare,
  Notebook,
  Tools,
  User,
  Lock,
  Fold,
  Expand,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'

/** 菜单项类型 */
interface MenuItem {
  /** 路由路径 */
  path: string
  /** 图标组件 */
  icon: Component
  /** 国际化 key */
  i18nKey: string
}

/** 系统管理子菜单项 */
interface AdminSubItem {
  path: string
  icon: Component
  title: string
}

const route = useRoute()
const appStore = useAppStore()

/** 普通导航菜单（不含系统管理子菜单） */
const flatMenuItems: MenuItem[] = [
  { path: '/home', icon: HomeFilled, i18nKey: 'nav.dashboard' },
  { path: '/modules/aitest/dashboard', icon: MagicStick, i18nKey: 'nav.aiTesting' },
  { path: '/modules/api-testing/dashboard', icon: Connection, i18nKey: 'nav.apiTesting' },
  { path: '/modules/ui-automation', icon: Monitor, i18nKey: 'nav.uiAutomation' },
  { path: '/modules/app-automation', icon: Iphone, i18nKey: 'nav.appAutomation' },
  { path: '/modules/configuration/ai-models', icon: Setting, i18nKey: 'nav.configuration' },
  { path: '/modules/ai-chat', icon: ChatDotSquare, i18nKey: 'nav.assistant' },
  { path: '/modules/knowledge-base', icon: Notebook, i18nKey: 'nav.knowledgeBase' },
]

/** 系统管理子菜单项 */
const adminSubItems: AdminSubItem[] = [
  { path: '/system-admin/users', icon: User, title: '用户管理' },
  { path: '/system-admin/roles', icon: Lock, title: '角色权限' },
  { path: '/system-admin/settings', icon: Setting, title: '系统设置' },
  { path: '/system-admin/audit-logs', icon: Document, title: '审计日志' },
]

/** 切换侧边栏折叠状态 */
function handleToggleCollapse() {
  appStore.toggleSidebar()
}
</script>

<style scoped lang="scss">
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

// Logo
.sidebar-logo {
  display: flex;
  align-items: center;
  height: 64px;
  padding: 0 16px;
  gap: 12px;
  flex-shrink: 0;
  overflow: hidden;
}

.logo-icon {
  width: 36px;
  height: 36px;
  min-width: 36px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 0.5px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 1px;
  white-space: nowrap;
}

// 菜单
.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: none !important;
  padding: 8px 0;
  background: transparent;

  // 菜单项样式
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

    // 菜单项悬浮
    &:hover {
      background-color: var(--el-menu-hover-bg-color) !important;
      color: var(--text);
    }

    // 激活状态
    &.is-active {
      background: linear-gradient(135deg, rgba(198, 123, 92, 0.12), rgba(212, 165, 116, 0.08)) !important;
      color: var(--primary) !important;
      font-weight: 500;
    }

    // 图标
    .el-icon {
      font-size: 18px;
      margin-right: 10px;
    }
  }

  // 子菜单标题样式
  :deep(.el-sub-menu__title) {
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

    .el-icon {
      font-size: 18px;
      margin-right: 10px;
    }
  }

  // 折叠时子菜单项样式
  .el-menu--collapse .el-sub-menu {
    .el-sub-menu__title {
      padding: 0 !important;
      margin: 2px 8px;
      justify-content: center;

      .el-icon {
        margin-right: 0;
      }
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
</style>
