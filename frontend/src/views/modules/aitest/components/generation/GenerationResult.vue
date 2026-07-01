<template>
  <div class="generation-result">
    <el-card shadow="never" class="result-card">
      <template #header>
        <div class="result-header">
          <span style="font-weight: 600; color: #6b5a4a;">生成结果</span>
          <div class="result-actions">
            <el-button size="small" type="primary" @click="emit('save')" :disabled="!hasCases">
              保存到用例库
            </el-button>
            <el-button size="small" @click="emit('export')" :disabled="!hasCases">
              导出 Excel
            </el-button>
            <el-button size="small" type="warning" @click="emit('revise')">
              重新修订
            </el-button>
          </div>
        </div>
      </template>

      <GeneratedCaseTable
        :cases="cases"
        :loading="loading"
        :selected-ids="selectedIds"
        :all-selected="allSelected"
        @select="emit('select', $event)"
        @select-all="emit('select-all', $event)"
        @batch-adopt="emit('batch-adopt')"
        @batch-discard="emit('batch-discard')"
        @preview="emit('preview', $event)"
        @toggle-status="emit('toggle-status', $event)"
      />

      <div v-if="cases.length === 0 && !loading" class="empty-result">
        <el-empty description="暂无生成结果" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import GeneratedCaseTable from './GeneratedCaseTable.vue'

const props = defineProps<{
  cases: any[]
  loading: boolean
  selectedIds: number[]
  allSelected: boolean
}>()

const emit = defineEmits<{
  (e: 'save'): void
  (e: 'export'): void
  (e: 'revise'): void
  (e: 'select', ids: number[]): void
  (e: 'select-all', selected: boolean): void
  (e: 'batch-adopt'): void
  (e: 'batch-discard'): void
  (e: 'preview', item: any): void
  (e: 'toggle-status', item: any): void
}>()

const hasCases = computed(() => props.cases.length > 0)
</script>

<style scoped lang="scss">
.result-card {
  margin-top: 16px;
  border: 1px solid rgba(180, 150, 120, 0.12);
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.empty-result {
  padding: 40px 0;
}
</style>
