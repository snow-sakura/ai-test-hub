<template>
  <!--
    顶部导航栏组件
    左侧显示当前页面标题，右侧提供语言切换和用户下拉菜单
  -->
  <header class="topbar">
    <!-- 左侧：返回首页 + 侧边栏展开按钮（小屏幕用）+ 页面标题 -->
    <div class="topbar-left">
      <!-- 返回首页 -->
      <router-link to="/home" class="back-home-btn" title="返回首页">
        <el-icon :size="16"><HomeFilled /></el-icon>
        <span class="back-home-text">首页</span>
      </router-link>

      <!-- 移动端菜单展开按钮 -->
      <el-button
        class="menu-toggle-btn"
        text
        @click="appStore.toggleSidebar()"
      >
        <el-icon :size="20">
          <Fold v-if="!appStore.sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
      </el-button>

      <!-- 页面标题/面包屑 -->
      <div class="page-title">
        <el-icon :size="18" class="title-icon">
          <component :is="currentIcon" />
        </el-icon>
        <span>{{ pageTitle }}</span>
      </div>
    </div>

    <!-- 右侧：语言切换 + 用户信息 -->
    <div class="topbar-right">
      <!-- 语言切换 -->
      <div class="lang-switch">
        <button
          class="lang-btn"
          :class="{ active: currentLang === 'zh-cn' }"
          @click="switchLang('zh-cn')"
        >
          中文
        </button>
        <button
          class="lang-btn"
          :class="{ active: currentLang === 'en' }"
          @click="switchLang('en')"
        >
          English
        </button>
      </div>

      <!-- 用户下拉菜单 -->
      <el-dropdown trigger="click" @command="handleUserCommand">
        <span class="user-trigger">
          <span class="user-avatar">{{ userStore.avatar }}</span>
          <span class="user-name">{{ userStore.username || '用户' }}</span>
          <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              {{ $t('layout.profile') }}
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              {{ $t('layout.settings') }}
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              {{ $t('layout.logout') }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import {
  ArrowDown,
  Fold,
  Expand,
  User,
  Setting,
  SwitchButton,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'
import {
  HomeFilled,
  MagicStick,
  Connection,
  Monitor,
  Iphone,
  ChatDotSquare,
  Notebook,
  Tools,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const { locale } = useI18n()
const appStore = useAppStore()
const userStore = useUserStore()

/** 模块图标映射（根据路由 meta.module 匹配） */
const moduleIconMap: Record<string, Component> = {
  'aitest': MagicStick,
  'api-testing': Connection,
  'ui-automation': Monitor,
  'app-automation': Iphone,
  'configuration': Setting,
  'ai-chat': ChatDotSquare,
  'knowledge-base': Notebook,
  'system-admin': Tools,
}

/** 当前页面图标 */
const currentIcon = computed<Component>(() => {
  // 模块页面：根据 meta.module 取图标
  const mod = route.meta?.module as string | undefined
  if (mod && moduleIconMap[mod]) {
    return moduleIconMap[mod]
  }
  // 首页
  if (route.path === '/home') {
    return HomeFilled
  }
  return HomeFilled
})

/** 当前页面标题 */
const pageTitle = computed(() => {
  return (route.meta?.title as string) || (route.name as string) || ''
})

/** 当前语言 */
const currentLang = computed(() => appStore.locale)

/** 切换语言 */
function switchLang(lang: 'zh-cn' | 'en') {
  appStore.setLocale(lang)
  locale.value = lang
}

/** 用户下拉菜单命令处理 */
async function handleUserCommand(command: string) {
  switch (command) {
    case 'profile':
      // TODO: 跳转到个人信息页
      break
    case 'settings':
      // TODO: 跳转到设置页
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        })
        await userStore.logout()
        router.push('/login')
      } catch {
        // 取消退出，不做处理
      }
      break
  }
}
</script>

<style scoped lang="scss">
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--topbar-height);
  padding: 0 24px;
  background: var(--card-bg);
  border-bottom: var(--border);
  flex-shrink: 0;
}

// 左侧
.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-toggle-btn {
  display: none; // 默认隐藏，小屏幕显示
  color: var(--text-secondary);

  @media (max-width: 768px) {
    display: flex;
  }
}

.back-home-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 8px;
  color: var(--text-muted);
  text-decoration: none;
  transition: all 0.2s;
  font-size: 14px;
}

.back-home-btn:hover {
  background: rgba(198, 123, 92, 0.1);
  color: var(--primary);
}

.back-home-text {
  font-size: 14px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.title-icon {
  color: var(--primary);
}

// 右侧
.topbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

// 语言切换
.lang-switch {
  display: flex;
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 2px;
  border: var(--border);
}

.lang-btn {
  padding: 4px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  border-radius: 4px;
  color: var(--text-muted);
  transition: all 0.2s;
  font-family: var(--font);

  &.active {
    background: var(--primary);
    color: #fff;
  }

  &:hover:not(.active) {
    color: var(--text);
  }
}

// 用户触发按钮
.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius);
  transition: background 0.2s;

  &:hover {
    background: var(--bg);
  }
}

.user-avatar {
  width: 32px;
  height: 32px;
  min-width: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-light), var(--accent));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.dropdown-arrow {
  color: var(--text-muted);
  font-size: 14px;
}
</style>
