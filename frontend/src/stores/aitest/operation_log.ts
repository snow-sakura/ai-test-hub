/**
 * 操作日志 Pinia Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { OperationLog } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export const useOperationLogStore = defineStore('aitest-operation-log', () => {
  const logs = ref<OperationLog[]>([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchCaseLogs(caseId: number, params?: { page?: number; page_size?: number }) {
    loading.value = true
    try {
      const res = await aitestApi.listCaseLogs(caseId, params)
      const data = res.data || []
      logs.value = Array.isArray(data) ? data : []
      total.value = logs.value.length
    } catch (e) {
      console.error('获取操作日志失败:', e)
      logs.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchProjectLogs(projectId: number, params?: { page?: number; page_size?: number }) {
    loading.value = true
    try {
      const res = await aitestApi.listProjectLogs(projectId, params)
      const data = res.data || []
      logs.value = Array.isArray(data) ? data : []
      total.value = logs.value.length
    } catch (e) {
      console.error('获取项目操作日志失败:', e)
      logs.value = []
    } finally {
      loading.value = false
    }
  }

  return {
    logs, total, loading,
    fetchCaseLogs, fetchProjectLogs,
  }
})
