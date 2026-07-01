/**
 * 测试用例 Pinia Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TestCase, TestCaseCreate } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export const useTestCaseStore = defineStore('aitest-testcase', () => {
  const cases = ref<TestCase[]>([])
  const currentCase = ref<TestCase | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const isLoading = ref(false)
  const selectedIds = ref<number[]>([])

  const filters = ref<{
    project_id: number | null
    priority: string | null
    status: string | null
    search: string | null
  }>({ project_id: null, priority: null, status: null, search: null })

  const stats = ref<{ total: number; by_priority: Record<string, number> }>({ total: 0, by_priority: {} })

  async function fetchCases() {
    isLoading.value = true
    try {
      const params: Record<string, string> = {}
      if (filters.value.project_id) params.project_id = String(filters.value.project_id)
      if (filters.value.priority) params.priority = filters.value.priority
      if (filters.value.status) params.status = filters.value.status
      if (filters.value.search) params.search = filters.value.search
      const res = await aitestApi.listTestCases(params)
      cases.value = res.data || []
      total.value = (res.data || []).length
    } catch (e) {
      console.error('获取用例列表失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCase(id: number) {
    try {
      const res = await aitestApi.getTestCase(id)
      currentCase.value = res.data
    } catch (e) {
      console.error('获取用例详情失败:', e)
    }
  }

  async function createCase(data: TestCaseCreate): Promise<TestCase | null> {
    try {
      const res = await aitestApi.createTestCase(data)
      await fetchCases()
      return res.data
    } catch (e) {
      console.error('创建用例失败:', e)
      return null
    }
  }

  async function updateCase(id: number, data: Partial<TestCaseCreate>): Promise<boolean> {
    try {
      await aitestApi.updateTestCase(id, data)
      await fetchCases()
      return true
    } catch (e) {
      console.error('更新用例失败:', e)
      return false
    }
  }

  async function deleteCase(id: number): Promise<boolean> {
    try {
      await aitestApi.deleteTestCase(id)
      await fetchCases()
      return true
    } catch (e) {
      console.error('删除用例失败:', e)
      return false
    }
  }

  function setFilter(key: string, value: unknown) {
    (filters.value as Record<string, unknown>)[key] = value
    page.value = 1
  }

  function clearSelection() { selectedIds.value = [] }

  return {
    cases, currentCase, total, page, pageSize, isLoading, selectedIds, filters, stats,
    fetchCases, fetchCase, createCase, updateCase, deleteCase, setFilter, clearSelection,
  }
})
