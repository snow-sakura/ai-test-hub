/**
 * 版本 Pinia Store
 * 统一管理版本 CRUD、分页/搜索/筛选状态。
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TestVersion, TestVersionCreate, TestVersionUpdate } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export const useVersionStore = defineStore('aitest-version', () => {
  const versions = ref<TestVersion[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const totalPages = ref(0)
  const isLoading = ref(false)
  const searchKeyword = ref('')
  const statusFilter = ref<string | null>(null)
  const projectFilter = ref<number | null>(null)

  async function fetchVersions() {
    isLoading.value = true
    try {
      const params: Record<string, string | number> = { page: page.value, page_size: pageSize.value }
      if (statusFilter.value) params.status = statusFilter.value
      if (searchKeyword.value) params.search = searchKeyword.value
      if (projectFilter.value !== null) params.project_id = projectFilter.value
      const res = await aitestApi.listVersions(params)
      versions.value = res.data || []
      total.value = res.pagination?.total || 0
      totalPages.value = res.pagination?.total_pages || 0
    } catch (e) {
      console.error('获取版本列表失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function createVersion(data: TestVersionCreate): Promise<TestVersion | null> {
    try {
      const res = await aitestApi.createVersion(data)
      await fetchVersions()
      return res.data
    } catch (e) {
      console.error('创建版本失败:', e)
      return null
    }
  }

  async function updateVersion(id: number, data: TestVersionUpdate): Promise<boolean> {
    try {
      await aitestApi.updateVersion(id, data)
      await fetchVersions()
      return true
    } catch (e) {
      console.error('更新版本失败:', e)
      return false
    }
  }

  async function deleteVersion(id: number): Promise<boolean> {
    try {
      await aitestApi.deleteVersion(id)
      await fetchVersions()
      return true
    } catch (e) {
      console.error('删除版本失败:', e)
      return false
    }
  }

  // ==================== 筛选 & 分页 ====================

  function setSearch(keyword: string) {
    searchKeyword.value = keyword
    page.value = 1
  }

  function setStatusFilter(status: string | null) {
    statusFilter.value = status
    page.value = 1
  }

  function setProjectFilter(projectId: number | null) {
    projectFilter.value = projectId
    page.value = 1
  }

  function setPage(p: number) {
    page.value = p
  }

  function setPageSize(ps: number) {
    pageSize.value = ps
    page.value = 1
  }

  function clearFilters() {
    searchKeyword.value = ''
    statusFilter.value = null
    projectFilter.value = null
    page.value = 1
  }

  return {
    versions, total, page, pageSize, totalPages, isLoading,
    searchKeyword, statusFilter, projectFilter,
    fetchVersions, createVersion, updateVersion, deleteVersion,
    setSearch, setStatusFilter, setProjectFilter, setPage, setPageSize, clearFilters,
  }
})
