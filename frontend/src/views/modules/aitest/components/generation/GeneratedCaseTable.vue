<template>
  <div class="generated-case-table">
    <div v-if="cases.length > 0" class="batch-bar">
      <el-checkbox
        :model-value="allSelected"
        :indeterminate="indeterminate"
        @change="handleSelectAll"
      >
        全选 ({{ selectedIds.length }}/{{ cases.length }})
      </el-checkbox>
      <el-button size="small" type="success" @click="handleBatchAdopt" :disabled="selectedIds.length === 0">
        批量采纳
      </el-button>
      <el-button size="small" type="danger" @click="handleBatchDiscard" :disabled="selectedIds.length === 0">
        批量丢弃
      </el-button>
    </div>

    <el-table
      :data="cases"
      v-loading="loading"
      stripe
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="40" />
      <el-table-column prop="case_id" label="编号" width="80" />
      <el-table-column prop="title" label="用例标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="module" label="模块" width="120" />
      <el-table-column label="优先级" width="80">
        <template #default="{ row }">
          <PriorityBadge :priority="row.priority || 'P2'" />
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status || 'generated'" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="emit('preview', row)">预览</el-button>
          <el-button
            size="small"
            text
            :type="row.status === 'adopted' ? 'warning' : 'success'"
            @click="emit('toggle-status', row)"
          >
            {{ row.status === 'adopted' ? '取消采纳' : '采纳' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import PriorityBadge from '@/components/aitest/common/PriorityBadge.vue'
import StatusTag from '@/components/aitest/common/StatusTag.vue'

const props = defineProps<{
  cases: any[]
  loading: boolean
  selectedIds: number[]
  allSelected: boolean
}>()

const emit = defineEmits<{
  (e: 'select', ids: number[]): void
  (e: 'select-all', selected: boolean): void
  (e: 'batch-adopt'): void
  (e: 'batch-discard'): void
  (e: 'preview', item: any): void
  (e: 'toggle-status', item: any): void
}>()

const indeterminate = computed(() =>
  props.selectedIds.length > 0 && props.selectedIds.length < props.cases.length
)

function handleSelectionChange(selection: any[]) {
  const ids = selection.map((s: any) => s.id).filter(Boolean)
  emit('select', ids)
}

function handleSelectAll(val: boolean) {
  emit('select-all', val)
}

function handleBatchAdopt() {
  emit('batch-adopt')
}

function handleBatchDiscard() {
  emit('batch-discard')
}
</script>

<style scoped lang="scss">
.generated-case-table {
  .batch-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }
}
</style>
