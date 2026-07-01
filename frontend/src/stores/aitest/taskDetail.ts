/**
 * 生成任务详情 Pinia Store（含候选用例管理）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AIGenerationTask, GeneratedCaseItem, BatchUpdateCasesRequest } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export const useTaskDetailStore = defineStore('aitest-task-detail', () => {
  const task = ref<AIGenerationTask | null>(null)
  const results = ref<any[]>([])
  const generatedCases = ref<GeneratedCaseItem[]>([])
  const casesTotal = ref(0)
  const casesPage = ref(1)
  const casesPageSize = ref(20)
  const selectedIds = ref<number[]>([])
  const currentPreviewCase = ref<GeneratedCaseItem | null>(null)
  const showPreviewModal = ref(false)
  const loading = ref(false)

  const totalPages = computed(() => Math.ceil(casesTotal.value / casesPageSize.value))
  const selectedCount = computed(() => selectedIds.value.length)
  const allSelected = computed(() =>
    generatedCases.value.length > 0 && selectedIds.value.length === generatedCases.value.length
  )

  async function fetchTask(taskId: string) {
    loading.value = true
    try {
      const res = await aitestApi.getTaskDetail(taskId)
      task.value = res.data || null
    } catch (e) {
      console.error('获取任务详情失败:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchGeneratedCases(taskId: string) {
    loading.value = true
    try {
      const res = await aitestApi.listGeneratedCaseItems(taskId, {
        page: casesPage.value,
        page_size: casesPageSize.value,
      })
      const resp = res as any
      const data = resp.data || []
      generatedCases.value = Array.isArray(data) ? data : []
      casesTotal.value = resp.pagination?.total || generatedCases.value.length
    } catch (e) {
      console.error('获取候选用例失败:', e)
      generatedCases.value = []
    } finally {
      loading.value = false
    }
  }

  async function batchUpdateCases(taskId: string, data: BatchUpdateCasesRequest) {
    await aitestApi.batchUpdateCaseItems(taskId, data)
    await fetchGeneratedCases(taskId)
    selectedIds.value = []
  }

  function toggleSelect(id: number) {
    const idx = selectedIds.value.indexOf(id)
    if (idx === -1) selectedIds.value.push(id)
    else selectedIds.value.splice(idx, 1)
  }

  function toggleSelectAll() {
    if (allSelected.value) {
      selectedIds.value = []
    } else {
      selectedIds.value = generatedCases.value.map(c => c.id!)
    }
  }

  function reset() {
    task.value = null
    results.value = []
    generatedCases.value = []
    casesTotal.value = 0
    casesPage.value = 1
    selectedIds.value = []
    currentPreviewCase.value = null
    showPreviewModal.value = false
  }

  return {
    task, results, generatedCases, casesTotal,
    casesPage, casesPageSize, selectedIds,
    currentPreviewCase, showPreviewModal, loading,
    totalPages, selectedCount, allSelected,
    fetchTask, fetchGeneratedCases, batchUpdateCases,
    toggleSelect, toggleSelectAll, reset,
  }
})
