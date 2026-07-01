<template>
  <!-- 路由占位页面：用于尚未实现的功能模块 -->
  <div class="placeholder-page">
    <el-result
      icon="info"
      :title="pageTitle"
      :sub-title="$t('common.comingSoon')"
    >
      <template #extra>
        <el-button type="primary" @click="$router.push('/home')">
          {{ $t('common.backToHome') }}
        </el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

/** 当前页面标题（从路由元数据获取） */
const pageTitle = computed(() => {
  return (route.meta?.title as string) || ''
})
</script>

<style scoped lang="scss">
.placeholder-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}
</style>
