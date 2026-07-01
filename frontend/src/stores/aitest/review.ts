/**
 * 评审 Pinia Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TestReview, TestReviewCreate, TestReviewUpdate } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export interface ReviewCaseItem {
  id: string
  case_id: string
  case_title?: string
  case_priority?: string
  preconditions?: string
  steps?: string
  expected_results?: string
  status: string
  comment?: string
  latest_execution_status?: string | null
}

export interface ReviewStats {
  total: number
  pending: number
  passed: number
  rejected: number
}

export const useReviewStore = defineStore('aitest-review', () => {
  const reviews = ref<TestReview[]>([])
  const currentReview = ref<TestReview | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const isLoading = ref(false)
  const stats = ref<ReviewStats>({ total: 0, pending: 0, passed: 0, rejected: 0 })

  async function fetchReviews(params?: { project_id?: string; status?: string; keyword?: string; page?: number; page_size?: number }) {
    isLoading.value = true
    try {
      const res = await aitestApi.listReviews(params as any)
      reviews.value = res.data || []
      total.value = (res.data || []).length
    } catch (e) {
      console.error('获取评审列表失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchReview(id: number) {
    try {
      const res = await aitestApi.getReview(id)
      if (res.data) currentReview.value = res.data
    } catch (e) {
      console.error('获取评审详情失败:', e)
    }
  }

  async function fetchStats() {
    try {
      const res = await aitestApi.getReviewStats()
      if (res.data) stats.value = res.data as ReviewStats
    } catch (e) {
      console.error('获取评审统计失败:', e)
    }
  }

  async function createReview(data: TestReviewCreate) {
    const res = await aitestApi.createReview(data)
    return res.data
  }

  async function updateReview(id: number, data: TestReviewUpdate) {
    const res = await aitestApi.updateReview(id, data)
    if (res.data) currentReview.value = res.data
    return res.data
  }

  async function deleteReview(id: number) {
    const res = await aitestApi.deleteReview(id)
    if (res.data) {
      reviews.value = reviews.value.filter(r => r.id !== id)
    }
    return res.data
  }

  return {
    reviews, currentReview, total, page, pageSize, isLoading, stats,
    fetchReviews, fetchReview, fetchStats, createReview, updateReview, deleteReview,
  }
})
