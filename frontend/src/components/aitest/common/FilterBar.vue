<template>
  <div class="filter-bar">
    <el-input
      v-model="searchText"
      placeholder="搜索..."
      clearable
      style="width: 240px"
      :prefix-icon="Search"
      @update:model-value="$emit('search', $event)"
    />
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const searchText = ref('')

defineEmits<{
  search: [value: string]
}>()
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
