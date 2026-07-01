<template>
  <!--
    主布局组件
    固定侧边栏 + 顶部导航栏 + 主内容区
    响应式设计，小屏幕自动折叠侧边栏
  -->
  <div class="app-layout" :class="{ 'sidebar-collapsed': appStore.sidebarCollapsed }">
    <!-- 侧边栏 -->
    <Sidebar />

    <!-- 右侧区域 -->
    <div class="layout-right">
      <!-- 顶部导航栏 -->
      <Topbar />

      <!-- 主内容区 -->
      <MainContent />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'
import MainContent from './MainContent.vue'

const appStore = useAppStore()

/** 响应式：窗口宽度小于 768px 时自动折叠侧边栏 */
function handleResize() {
  if (window.innerWidth < 768) {
    if (!appStore.sidebarCollapsed) {
      appStore.sidebarCollapsed = true
    }
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
.app-layout {
  display: flex;
  min-height: 100vh;
}

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

// 小屏幕：侧边栏覆盖式（由 Sidebar 的 fixed 定位处理）
@media (max-width: 768px) {
  .layout-right {
    margin-left: 0 !important;
  }
}
</style>
