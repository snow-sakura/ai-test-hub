<template>
  <!--
    首页布局（无侧边栏）
    仅包含 Topbar + 主内容区，用于首页仪表盘
  -->
  <div class="home-layout">
    <!-- 顶部导航栏 -->
    <Topbar />

    <!-- 主内容区 -->
    <MainContent />
  </div>
</template>

<script setup lang="ts">
import Topbar from './Topbar.vue'
import MainContent from './MainContent.vue'
</script>

<style scoped lang="scss">
.home-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
</style>
