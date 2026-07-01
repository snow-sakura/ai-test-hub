/**
 * AI 用例生成 Pinia Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AIGenerationTask } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

export type GenerationStage = 'analyze' | 'writing' | 'review' | 'revise'

export const useGenerationStore = defineStore('aitest-generation', () => {
  const currentTask = ref<AIGenerationTask | null>(null)
  const isLoading = ref(false)
  const isStreaming = ref(false)

  // 任务列表
  const tasks = ref<AIGenerationTask[]>([])
  const tasksTotal = ref(0)
  const tasksPage = ref(1)
  const tasksPageSize = ref(10)
  const tasksLoading = ref(false)

  // 流式状态
  const currentStage = ref<GenerationStage | null>(null)
  const streamingContent = ref('')
  const streamError = ref<string | null>(null)

  async function createTask(params: {
    project_id?: string | null
    requirement_title?: string
    input_text?: string
    model?: string
  }): Promise<AIGenerationTask | null> {
    isLoading.value = true
    try {
      const res = await aitestApi.createGenerationTask(params as any)
      currentTask.value = res.data
      currentStage.value = null
      streamingContent.value = ''
      streamError.value = null
      return res.data
    } catch (e) {
      console.error('创建生成任务失败:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTask(taskId: string) {
    try {
      const res = await aitestApi.getTaskDetail(taskId)
      currentTask.value = res.data
    } catch (e) {
      console.error('获取任务状态失败:', e)
    }
  }

  async function fetchTasks() {
    tasksLoading.value = true
    try {
      const res = await aitestApi.getTaskList(tasksPage.value, tasksPageSize.value)
      tasks.value = res.data || []
      tasksTotal.value = (res.data || []).length
    } catch (e) {
      console.error('获取任务列表失败:', e)
    } finally {
      tasksLoading.value = false
    }
  }

  async function removeTask(taskId: string): Promise<boolean> {
    try {
      await aitestApi.deleteGenerationTask(taskId)
      await fetchTasks()
      return true
    } catch (e) {
      console.error('删除任务失败:', e)
      return false
    }
  }

  function setCurrentStage(stage: GenerationStage) {
    currentStage.value = stage
  }

  function appendStreamContent(text: string) {
    streamingContent.value += text
  }

  function resetStreamState() {
    currentStage.value = null
    streamingContent.value = ''
    streamError.value = null
    isStreaming.value = false
  }

  function reset() {
    currentTask.value = null
    resetStreamState()
  }

  return {
    currentTask, isLoading, isStreaming, tasks, tasksTotal, tasksPage, tasksPageSize, tasksLoading,
    currentStage, streamingContent, streamError,
    createTask, fetchTask, fetchTasks, removeTask,
    setCurrentStage, appendStreamContent, resetStreamState, reset,
  }
})
