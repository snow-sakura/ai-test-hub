/**
 * 用例评论 Pinia Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CaseComment, CaseCommentCreate, CaseCommentUpdate } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export const useCommentStore = defineStore('aitest-comment', () => {
  const comments = ref<CaseComment[]>([])
  const loading = ref(false)

  async function fetchComments(caseId: number) {
    loading.value = true
    try {
      const res = await aitestApi.listComments(caseId)
      comments.value = res.data || []
    } catch (e) {
      console.error('获取评论列表失败:', e)
      comments.value = []
    } finally {
      loading.value = false
    }
  }

  async function create(caseId: number, data: CaseCommentCreate) {
    const res = await aitestApi.createComment(caseId, data)
    if (res.data) {
      comments.value.push(res.data)
    }
    return res.data
  }

  async function update(commentId: number, data: CaseCommentUpdate) {
    const res = await aitestApi.updateComment(commentId, data)
    if (res.data) {
      const idx = comments.value.findIndex(c => c.id === commentId)
      if (idx !== -1) comments.value[idx] = res.data
    }
    return res.data
  }

  async function remove(commentId: number) {
    await aitestApi.deleteComment(commentId)
    comments.value = comments.value.filter(c => c.id !== commentId)
  }

  return {
    comments, loading,
    fetchComments, create, update, remove,
  }
})
