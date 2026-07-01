/**
 * 用例附件 Pinia Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CaseAttachment } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export const useAttachmentStore = defineStore('aitest-attachment', () => {
  const attachments = ref<CaseAttachment[]>([])
  const loading = ref(false)

  async function fetchAttachments(caseId: number) {
    loading.value = true
    try {
      const res = await aitestApi.listAttachments(caseId)
      attachments.value = res.data || []
    } catch (e) {
      console.error('获取附件列表失败:', e)
      attachments.value = []
    } finally {
      loading.value = false
    }
  }

  async function upload(caseId: number, file: File) {
    const res = await aitestApi.uploadAttachment(caseId, file)
    if (res.data) {
      attachments.value.push(res.data)
    }
    return res.data
  }

  async function remove(attachmentId: number) {
    await aitestApi.deleteAttachment(attachmentId)
    attachments.value = attachments.value.filter(a => a.id !== attachmentId)
  }

  function getDownloadUrl(attachmentId: number): string {
    return aitestApi.getAttachmentDownloadUrl(attachmentId)
  }

  return {
    attachments, loading,
    fetchAttachments, upload, remove, getDownloadUrl,
  }
})
