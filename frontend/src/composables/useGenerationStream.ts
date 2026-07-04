/**
 * AI 生成流式输出 Composable
 *
 * 支持双模式 SSE：
 * - Legacy 模式：通过 onmessage 接收 {type, content} 事件
 * - LangGraph 模式：通过 addEventListener 接收 named events
 *
 * 提供阶段切换、流式内容累积、评审结果解析、进度跟踪等功能。
 */

import { ref, onUnmounted } from 'vue'

/** 生成阶段标签 */
export const STAGE_LABELS: Record<string, string> = {
  analyze: '需求分析',
  writing: '用例编写',
  review: 'AI 评审',
  revise: '修订完善',
  complete: '生成完成',
}

/** 阶段图标颜色 */
export const STAGE_COLORS: Record<string, string> = {
  analyze: '#1890FF',
  writing: '#52C41A',
  review: '#FAAD14',
  revise: '#FF7A00',
  complete: '#722ED1',
}

/** 评审结果 */
interface ReviewResult {
  overall_score?: number
  passed?: boolean
  issues?: Array<{ severity: string; title: string; description?: string }>
  suggestions?: string[]
  raw?: string
}

/** 生成完成结果 */
interface DoneResult {
  task_id: string
  generated_count: number
  review_passed: boolean
  overall_score?: number
}

/** 进度信息 */
interface ProgressInfo {
  current: number
  total: number
  message: string
}

/** SSE 事件类型 */
type SSEEvent =
  | { type: 'chunk'; content: string; stage?: string }
  | { type: 'stage'; stage: string; label: string }
  | { type: 'review'; result: ReviewResult }
  | { type: 'progress'; current: number; total: number; message: string }
  | { type: 'done'; task_id: string; generated_count: number; review_passed: boolean; overall_score?: number }
  | { type: 'error'; message: string }

export function useGenerationStream() {
  let eventSource: EventSource | null = null
  let isManuallyClosed = false

  const isConnecting = ref(false)
  const isDone = ref(false)
  const isError = ref(false)
  const errorMessage = ref('')
  const doneResult = ref<DoneResult | null>(null)
  const reviewResult = ref<ReviewResult | null>(null)
  const progress = ref<ProgressInfo>({ current: 0, total: 0, message: '' })
  const currentStage = ref('')
  const stageContents = ref<Record<string, string>>({
    analyze: '',
    writing: '',
    review: '',
    revise: '',
  })

  function handleEvent(event: SSEEvent) {
    switch (event.type) {
      case 'stage':
        currentStage.value = event.stage || event.stage
        break

      case 'chunk': {
        const stage = (event as any).stage || currentStage.value
        if (stage && stageContents.value[stage] !== undefined) {
          stageContents.value[stage] += event.content
        }
        break
      }

      case 'review':
        reviewResult.value = event.result
        break

      case 'progress':
        progress.value = {
          current: event.current,
          total: event.total,
          message: event.message,
        }
        break

      case 'done':
        isDone.value = true
        doneResult.value = {
          task_id: event.task_id,
          generated_count: event.generated_count,
          review_passed: event.review_passed,
          overall_score: event.overall_score,
        }
        close()
        break

      case 'error':
        isError.value = true
        errorMessage.value = event.message
        close()
        break
    }
  }

  function start(taskId: string, baseUrl: string) {
    const url = `${baseUrl}/v1/ai/generate/${taskId}/stream`
    isConnecting.value = true
    isDone.value = false
    isError.value = false
    errorMessage.value = ''
    doneResult.value = null
    reviewResult.value = null
    currentStage.value = ''
    stageContents.value = { analyze: '', writing: '', review: '', revise: '' }
    progress.value = { current: 0, total: 0, message: '' }

    isManuallyClosed = false
    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      isConnecting.value = false
    }

    // Legacy 模式：通用 onmessage
    eventSource.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as SSEEvent
        handleEvent(data)
      } catch { /* ignore parse errors */ }
    }

    // LangGraph 模式：命名事件
    const namedEvents = ['testing_stage', 'testing_token', 'testing_review', 'testing_progress', 'testing_done', 'testing_error']
    namedEvents.forEach((eventName) => {
      eventSource?.addEventListener(eventName, (event: Event) => {
        try {
          const data = JSON.parse((event as MessageEvent).data)
          // Map named events to internal format
          switch (eventName) {
            case 'testing_stage':
              handleEvent({ type: 'stage', stage: data.stage, label: data.label || '' })
              break
            case 'testing_token':
              handleEvent({ type: 'chunk', content: data.content, stage: data.stage })
              break
            case 'testing_review':
              handleEvent({ type: 'review', result: data })
              break
            case 'testing_progress':
              handleEvent({ type: 'progress', current: data.current, total: data.total, message: data.message })
              break
            case 'testing_done':
              handleEvent({ type: 'done', ...data })
              break
            case 'testing_error':
              handleEvent({ type: 'error', message: data.message || '生成失败' })
              break
          }
        } catch { /* ignore */ }
      })
    })

    eventSource.onerror = () => {
      isConnecting.value = false
      if (!isManuallyClosed && !isDone.value) {
        isError.value = true
        errorMessage.value = '连接中断'
      }
    }
  }

  /** 从已有数据加载（回放模式） */
  function loadFromExisting(task: any, results: any[]) {
    if (task) {
      currentStage.value = task.status === 'completed' ? 'complete' : task.status
    }
    if (results && results.length > 0) {
      for (const r of results) {
        if (r.stage && stageContents.value[r.stage] !== undefined) {
          stageContents.value[r.stage] = r.content || ''
        }
      }
    }
  }

  function close() {
    isManuallyClosed = true
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isConnecting.value = false
  }

  function reset() {
    close()
    isDone.value = false
    isError.value = false
    errorMessage.value = ''
    doneResult.value = null
    reviewResult.value = null
    currentStage.value = ''
    stageContents.value = { analyze: '', writing: '', review: '', revise: '' }
    progress.value = { current: 0, total: 0, message: '' }
  }

  onUnmounted(() => {
    close()
  })

  return {
    isConnecting, isDone, isError, errorMessage,
    doneResult, reviewResult, progress, currentStage, stageContents,
    start, loadFromExisting, close, reset,
  }
}
