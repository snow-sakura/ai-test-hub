<template>
  <!--
    移动端主布局
    顶部 NavBar（汉堡菜单 + 标题）+ 中间路由视图 + 底部 TabBar
  -->
  <van-nav-bar
    :title="currentTitle"
    :left-arrow="showBack"
    :fixed="true"
    :placeholder="true"
    @click-left="onBack"
  >
    <template #left v-if="!showBack">
      <van-icon name="bars" size="20" @click.stop="showSidebar = true" />
    </template>
    <template #right>
      <van-icon name="search" size="20" v-if="showSearch" />
    </template>
  </van-nav-bar>

  <!-- 主内容区 -->
  <div class="mobile-layout-content">
    <router-view v-slot="{ Component }">
      <keep-alive :include="cachedViews">
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </div>

  <!-- 底部安全区域 -->
  <div class="safe-area-bottom" />

  <!-- 底部 TabBar -->
  <van-tabbar v-model="activeTab" :fixed="true" :placeholder="true" route>
    <van-tabbar-item icon="home-o" to="/m/home">首页</van-tabbar-item>
    <van-tabbar-item icon="chat-o" to="/m/ai-chat">聊天</van-tabbar-item>
    <van-tabbar-item icon="label-o" to="/m/aitest">测试</van-tabbar-item>
    <van-tabbar-item icon="user-o" to="/m/profile">我的</van-tabbar-item>
  </van-tabbar>

  <!-- 侧边栏抽屉 -->
  <van-popup
    v-model:show="showSidebar"
    position="left"
    :style="{ width: '70%', height: '100%' }"
  >
    <div class="sidebar-drawer">
      <!-- 用户信息区 -->
      <div class="sidebar-user">
        <div class="user-avatar">
          <van-icon name="manager-o" size="32" color="#fff" />
        </div>
        <div class="user-info">
          <span class="user-name">{{ username }}</span>
          <span class="user-role">测试工程师</span>
        </div>
      </div>

      <!-- 模块导航 -->
      <div class="sidebar-nav">
        <div
          v-for="item in navItems"
          :key="item.path"
          class="nav-item"
          @click="navigateTo(item.path)"
        >
          <van-icon :name="item.icon" size="20" :color="item.color" />
          <span class="nav-label">{{ item.label }}</span>
          <van-icon name="arrow" size="14" color="#ccc" />
        </div>
      </div>

      <!-- 底部信息 -->
      <div class="sidebar-footer">
        <div class="sidebar-version">AI-HUB v1.0</div>
      </div>
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const showSidebar = ref(false)
const activeTab = ref(0)

const username = computed(() => userStore.username || '用户')

// 缓存的视图组件名
const cachedViews = ['m-home', 'm-ai-chat', 'm-aitest', 'm-profile']

// 当前页面标题
const currentTitle = computed(() => {
  return (route.meta?.title as string) || 'AI-HUB'
})

// 是否显示返回按钮（非 TabBar 主页面）
const showBack = computed(() => {
  const tabPaths = ['/m/home', '/m/ai-chat', '/m/aitest', '/m/profile']
  return !tabPaths.includes(route.path)
})

// 是否显示搜索图标
const showSearch = computed(() => false)

// 侧边栏导航项
const navItems = [
  { label: '首页', icon: 'home-o', color: '#C67B5C', path: '/m/home' },
  { label: 'AI 聊天', icon: 'chat-o', color: '#D49472', path: '/m/ai-chat' },
  { label: 'API 接口测试', icon: 'wap-o', color: '#C67B5C', path: '/m/api-testing' },
  { label: '知识库', icon: 'records-o', color: '#D4A574', path: '/m/knowledge-base' },
  { label: '系统管理', icon: 'setting-o', color: '#8B7355', path: '/m/profile' },
]

function onBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/m/home')
  }
}

function navigateTo(path: string) {
  showSidebar.value = false
  router.push(path)
}
</script>

<style scoped lang="scss">
.mobile-layout-content {
  min-height: calc(100vh - 46px - 50px);
  background: var(--van-background);
}

.sidebar-drawer {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--van-background);
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 20px;
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 100%);
}

.user-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 17px;
  font-weight: 700;
  color: #fff;
}

.user-role {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 2px;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 0.2s;

  &:active {
    background: rgba(198, 123, 92, 0.06);
  }
}

.nav-label {
  flex: 1;
  font-size: 15px;
  color: var(--van-text-color);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--van-border-color);
}

.sidebar-version {
  font-size: 12px;
  color: var(--van-text-color-3);
  text-align: center;
}
</style>
