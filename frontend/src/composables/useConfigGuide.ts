/**
 * AI 配置检查引导 Composable
 *
 * 提供 AI 配置完整性检查、引导弹窗状态管理。
 */
import { ref, computed } from 'vue'
import { aitestApi } from '@/api/aitest'

export interface ConfigCheckItem {
  key: string
  label: string
  ok: boolean
  message: string
}

export function useConfigGuide() {
  const showGuide = ref(false)
  const configStatus = ref<ConfigCheckItem[]>([])
  const loading = ref(false)

  const allPassed = computed(() =>
    configStatus.value.length > 0 && configStatus.value.every(c => c.ok)
  )

  const failedCount = computed(() =>
    configStatus.value.filter(c => !c.ok).length
  )

  async function check() {
    loading.value = true
    try {
      const res = await aitestApi.checkAIConfig()
      const data: Record<string, any> = res.data || {}
      configStatus.value = [
        {
          key: 'model',
          label: 'AI 模型配置',
          ok: !!(data.models_configured || data.has_model_config),
          message: data.models_configured || data.has_model_config ? '已配置' : '未配置模型',
        },
        {
          key: 'analyze_prompt',
          label: '分析提示词',
          ok: !!(data.has_analyze_prompt),
          message: data.has_analyze_prompt ? '已配置' : '未配置',
        },
        {
          key: 'write_prompt',
          label: '编写提示词',
          ok: !!(data.has_write_prompt),
          message: data.has_write_prompt ? '已配置' : '未配置',
        },
        {
          key: 'review_prompt',
          label: '评审提示词',
          ok: !!(data.has_review_prompt),
          message: data.has_review_prompt ? '已配置' : '未配置',
        },
        {
          key: 'env_key',
          label: '环境变量 API Key',
          ok: !!(data.has_env_api_key || data.status === 'configured'),
          message: data.has_env_api_key ? '已配置' : '未配置（可使用数据库 Key）',
        },
      ]
    } catch {
      configStatus.value = []
    } finally {
      loading.value = false
    }
  }

  async function open() {
    showGuide.value = true
    await check()
  }

  function close() {
    showGuide.value = false
  }

  return {
    showGuide, configStatus, loading, allPassed, failedCount,
    check, open, close,
  }
}
