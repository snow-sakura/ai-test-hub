<template>
  <!-- 主内容区域：包裹路由视图 -->
  <main class="main-content">
    <router-view />
  </main>
</template>

<script setup lang="ts">
// 主内容区：仅作为 router-view 的容器
</script>

<style scoped lang="scss">
.main-content {
  padding: 24px;
  min-height: calc(100vh - var(--topbar-height));
  overflow-y: auto;
  background: var(--bg);

  @media (max-width: 768px) {
    padding: 16px;
  }
}
</style>
