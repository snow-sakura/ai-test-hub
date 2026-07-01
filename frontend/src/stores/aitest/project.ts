/**
 * 项目 Pinia Store
 * 统一管理项目 CRUD、成员管理、分页/搜索/筛选状态。
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TestProject, TestProjectCreate, TestProjectUpdate, ProjectStats, ProjectMember } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export const useProjectStore = defineStore('aitest-project', () => {
  // 项目列表
  const projects = ref<TestProject[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const totalPages = ref(0)
  const isLoading = ref(false)
  const searchKeyword = ref('')
  const statusFilter = ref<string | null>(null)

  // 项目统计（全量，独立于分页）
  const stats = ref<ProjectStats>({ total: 0, active: 0, completed: 0, archived: 0 })

  // 当前项目详情
  const currentProject = ref<TestProject | null>(null)

  // 成员管理
  const members = ref<ProjectMember[]>([])
  const membersLoading = ref(false)

  async function fetchProjects() {
    isLoading.value = true
    try {
      const params: Record<string, string | number> = { page: page.value, page_size: pageSize.value }
      if (statusFilter.value) params.status = statusFilter.value
      if (searchKeyword.value) params.search = searchKeyword.value
      const res = await aitestApi.listProjects(params)
      projects.value = res.data || []
      total.value = res.pagination?.total || 0
      totalPages.value = res.pagination?.total_pages || 0
    } catch (e) {
      console.error('获取项目列表失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  /** 获取项目全量统计（各状态项目数） */
  async function fetchProjectStats() {
    try {
      const res = await aitestApi.getProjectStats()
      stats.value = res.data || { total: 0, active: 0, completed: 0, archived: 0 }
    } catch (e) {
      console.error('获取项目统计失败:', e)
    }
  }

  /** 获取所有项目（不分页，用于下拉选择等） */
  async function fetchAllProjects() {
    try {
      const params: Record<string, string> = {}
      if (statusFilter.value) params.status = statusFilter.value
      if (searchKeyword.value) params.search = searchKeyword.value
      const res = await aitestApi.listProjects({ ...params, page_size: 999 })
      return res.data || []
    } catch (e) {
      console.error('获取全量项目列表失败:', e)
      return []
    }
  }

  async function fetchProject(id: number) {
    try {
      const res = await aitestApi.getProject(id)
      currentProject.value = res.data
    } catch (e) {
      console.error('获取项目详情失败:', e)
    }
  }

  async function createProject(data: TestProjectCreate): Promise<TestProject | null> {
    try {
      const res = await aitestApi.createProject(data)
      await fetchProjects()
      return res.data
    } catch (e) {
      console.error('创建项目失败:', e)
      return null
    }
  }

  async function updateProject(id: number, data: TestProjectUpdate): Promise<boolean> {
    try {
      await aitestApi.updateProject(id, data)
      if (currentProject.value?.id === id) {
        await fetchProject(id)
      }
      await fetchProjects()
      return true
    } catch (e) {
      console.error('更新项目失败:', e)
      return false
    }
  }

  async function deleteProject(id: number): Promise<boolean> {
    try {
      await aitestApi.deleteProject(id)
      await fetchProjects()
      return true
    } catch (e) {
      console.error('删除项目失败:', e)
      return false
    }
  }

  /** 批量删除项目 */
  async function batchDeleteProjects(ids: number[]): Promise<boolean> {
    try {
      await aitestApi.batchDeleteTestProjects(ids)
      await fetchProjects()
      return true
    } catch (e) {
      console.error('批量删除项目失败:', e)
      return false
    }
  }

  // ==================== 成员管理 ====================

  async function fetchMembers(projectId: number) {
    membersLoading.value = true
    try {
      const res = await aitestApi.listMembers(projectId)
      members.value = res.data || []
    } catch (e) {
      console.error('获取成员列表失败:', e)
    } finally {
      membersLoading.value = false
    }
  }

  async function addMember(projectId: number, userId: number, role: 'admin' | 'tester' | 'viewer'): Promise<void> {
    await aitestApi.addMember(projectId, { user_id: userId, role })
    await fetchMembers(projectId)
  }

  async function removeMember(projectId: number, userId: number): Promise<boolean> {
    try {
      await aitestApi.removeMember(projectId, userId)
      if (currentProject.value?.id === projectId) {
        await fetchMembers(projectId)
      }
      return true
    } catch (e) {
      console.error('移除成员失败:', e)
      return false
    }
  }

  async function updateMemberRole(projectId: number, userId: number, role: 'admin' | 'tester' | 'viewer'): Promise<boolean> {
    try {
      await aitestApi.updateMemberRole(projectId, userId, role)
      if (currentProject.value?.id === projectId) {
        await fetchMembers(projectId)
      }
      return true
    } catch (e) {
      console.error('更新成员角色失败:', e)
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
    page.value = 1
  }

  return {
    projects, total, page, pageSize, totalPages, isLoading,
    searchKeyword, statusFilter, stats, currentProject,
    members, membersLoading,
    fetchProjects, fetchProjectStats, fetchAllProjects, fetchProject,
    createProject, updateProject, deleteProject, batchDeleteProjects,
    fetchMembers, addMember, removeMember, updateMemberRole,
    setSearch, setStatusFilter, setPage, setPageSize, clearFilters,
  }
})
