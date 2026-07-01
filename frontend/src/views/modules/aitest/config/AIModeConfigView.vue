<template>
  <!--
    AI 智能模式配置页面

    三个 Tab 标签页：
    1. 基础配置：开关控制 AI 模式、自动触发、报告生成、失败重测、通知设置
    2. 模型配置：跳转到配置中心的 AI 模型配置页面
    3. 高级配置：Token 数、重试、超时、并发等参数调整
  -->
  <div class="ai-mode-config-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>AI 智能模式配置</h2>
      <p class="page-desc">配置 AI 智能测试模式的全局参数和行为</p>
    </div>

    <!-- Tab 标签页切换 -->
    <el-tabs v-model="activeTab" type="border-card" class="config-tabs">
      <!-- Tab 1: 基础配置 -->
      <el-tab-pane label="基础配置" name="basic">
        <div class="tab-content">
          <!-- AI 模式开关 -->
          <div class="config-section">
            <h4 class="section-title">AI 模式开关</h4>
            <div class="config-item">
              <div class="config-info">
                <span class="config-label">启用 AI 模式</span>
                <span class="config-desc">启用后系统将使用 AI 辅助生成和管理测试用例</span>
              </div>
              <el-switch v-model="settings.ai_mode_enabled" />
            </div>
          </div>

          <!-- 自动触发策略 -->
          <div class="config-section">
            <h4 class="section-title">自动触发策略</h4>
            <div class="config-item">
              <div class="config-info">
                <span class="config-label">需求变更自动触发</span>
                <span class="config-desc">当需求文档发生变更时，自动触发 AI 重新生成测试用例</span>
              </div>
              <el-switch v-model="settings.auto_trigger_on_requirement_change" />
            </div>
            <div class="config-item">
              <div class="config-info">
                <span class="config-label">自动生成报告</span>
                <span class="config-desc">用例生成完成后自动生成测试报告</span>
              </div>
              <el-switch v-model="settings.auto_generate_report" />
            </div>
            <div class="config-item">
              <div class="config-info">
                <span class="config-label">失败自动重测</span>
                <span class="config-desc">当测试用例执行失败时自动触发重测</span>
              </div>
              <el-switch v-model="settings.auto_retest_on_failure" />
            </div>
          </div>

          <!-- 通知设置 -->
          <div class="config-section">
            <h4 class="section-title">通知设置</h4>
            <div class="config-item">
              <div class="config-info">
                <span class="config-label">通知方式</span>
                <span class="config-desc">选择需要接收通知的渠道</span>
              </div>
              <div class="config-controls">
                <el-checkbox-group v-model="notificationChannels" class="notify-checks">
                  <el-checkbox label="email" value="email">邮件通知</el-checkbox>
                  <el-checkbox label="dingtalk" value="dingtalk">钉钉通知</el-checkbox>
                  <el-checkbox label="wechat" value="wechat">企业微信</el-checkbox>
                </el-checkbox-group>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 2: 模型配置 -->
      <el-tab-pane label="模型配置" name="model">
        <div class="tab-content model-redirect-content">
          <el-empty description="模型配置管理已移至独立页面">
            <template #extra>
              <el-button type="primary" @click="goToModelConfig">
                前往 AI 模型配置
              </el-button>
            </template>
          </el-empty>
          <p class="redirect-hint">
            当前配置：{{ settings.provider || '未配置' }} /
            {{ settings.model_name || '未选择' }} /
            Temperature: {{ settings.temperature }} /
            上下文: {{ settings.context_window }}
          </p>
          <el-divider />
          <div class="model-overview">
            <el-descriptions :column="2" border size="small" title="当前模型配置概览">
              <el-descriptions-item label="AI 提供商">{{ settings.provider || '-' }}</el-descriptions-item>
              <el-descriptions-item label="API Key">
                <span v-if="settings.api_key">{{ maskApiKey(settings.api_key) }}</span>
                <span v-else style="color: #f56c6c">未配置</span>
              </el-descriptions-item>
              <el-descriptions-item label="模型名称">{{ settings.model_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="Temperature">{{ settings.temperature }}</el-descriptions-item>
              <el-descriptions-item label="上下文窗口大小">{{ settings.context_window }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 3: 高级配置 -->
      <el-tab-pane label="高级配置" name="advanced">
        <div class="tab-content">
          <div class="config-section">
            <h4 class="section-title">Token 限制</h4>

            <div class="config-item">
              <div class="config-info">
                <span class="config-label">最大输入 Token（{{ settings.max_input_tokens }}）</span>
                <span class="config-desc">AI 模型单次请求的最大输入 Token 数量</span>
              </div>
              <div class="config-slider">
                <el-slider
                  v-model="settings.max_input_tokens"
                  :min="4096"
                  :max="512000"
                  :step="1024"
                  show-input
                  input-size="small"
                  style="width: 360px"
                />
              </div>
            </div>

            <div class="config-item">
              <div class="config-info">
                <span class="config-label">最大输出 Token（{{ settings.max_output_tokens }}）</span>
                <span class="config-desc">AI 模型单次响应的最大输出 Token 数量</span>
              </div>
              <div class="config-slider">
                <el-slider
                  v-model="settings.max_output_tokens"
                  :min="512"
                  :max="32768"
                  :step="512"
                  show-input
                  input-size="small"
                  style="width: 360px"
                />
              </div>
            </div>
          </div>

          <div class="config-section">
            <h4 class="section-title">执行策略</h4>

            <div class="config-item">
              <div class="config-info">
                <span class="config-label">重试次数（{{ settings.retry_count }}）</span>
                <span class="config-desc">AI 请求失败后自动重试的次数</span>
              </div>
              <div class="config-slider">
                <el-slider
                  v-model="settings.retry_count"
                  :min="0"
                  :max="10"
                  show-input
                  input-size="small"
                  style="width: 360px"
                />
              </div>
            </div>

            <div class="config-item">
              <div class="config-info">
                <span class="config-label">超时时间（{{ settings.timeout_seconds }} 秒）</span>
                <span class="config-desc">AI 请求的超时时间，超过将自动终止</span>
              </div>
              <div class="config-slider">
                <el-slider
                  v-model="settings.timeout_seconds"
                  :min="30"
                  :max="600"
                  :step="10"
                  show-input
                  input-size="small"
                  style="width: 360px"
                />
              </div>
            </div>

            <div class="config-item">
              <div class="config-info">
                <span class="config-label">并发数（{{ settings.concurrency }}）</span>
                <span class="config-desc">同时发起的最大 AI 请求数量</span>
              </div>
              <div class="config-slider">
                <el-slider
                  v-model="settings.concurrency"
                  :min="1"
                  :max="20"
                  show-input
                  input-size="small"
                  style="width: 360px"
                />
              </div>
            </div>

            <div class="config-item">
              <div class="config-info">
                <span class="config-label">速率限制 RPM（{{ settings.rate_limit_rpm }}）</span>
                <span class="config-desc">每分钟最大请求次数（Requests Per Minute）</span>
              </div>
              <div class="config-slider">
                <el-slider
                  v-model="settings.rate_limit_rpm"
                  :min="1"
                  :max="1000"
                  :step="1"
                  show-input
                  input-size="small"
                  style="width: 360px"
                />
              </div>
            </div>
          </div>

          <!-- 自定义 Prompt 模板 -->
          <div class="config-section">
            <h4 class="section-title">自定义 Prompt 模板</h4>
            <div class="config-item">
              <div class="config-info">
                <span class="config-label">Prompt 模板</span>
                <span class="config-desc">自定义 AI 生成的提示词模板，留空则使用系统默认模板</span>
              </div>
            </div>
            <el-input
              v-model="settings.custom_prompt_template"
              type="textarea"
              :rows="8"
              placeholder="输入自定义 Prompt 模板（可选）..."
              class="prompt-editor"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 底部操作按钮 -->
    <div class="footer-actions">
      <el-button type="primary" :loading="saving" @click="handleSave">
        {{ saving ? '保存中...' : '保存配置' }}
      </el-button>
      <el-button @click="handleResetConfig">重置</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { aitestApi } from '@/api/aitest'
import type { AISettings, AISettingsUpdate } from '@/types/aitest'

const router = useRouter()

// ======================================================================
// 状态
// ======================================================================

/** 当前激活的 Tab */
const activeTab = ref('basic')

/** 保存状态 */
const saving = ref(false)

/** 配置数据（本地编辑） */
const settings = reactive<AISettings>({
  ai_mode_enabled: true,
  auto_trigger_on_requirement_change: false,
  auto_generate_report: false,
  auto_retest_on_failure: false,
  notification_config: null,
  provider: '',
  api_key: '',
  model_name: '',
  temperature: 0.7,
  context_window: 128000,
  max_input_tokens: 128000,
  max_output_tokens: 4096,
  retry_count: 3,
  timeout_seconds: 120,
  concurrency: 1,
  rate_limit_rpm: 60,
  custom_prompt_template: null,
  id: 0,
  created_by: 0,
  created_at: '',
  updated_at: '',
})

/** 通知渠道绑定 */
const notificationChannels = ref<string[]>([])

// 完整的初始快照（用于"重置"功能）
const initialSnapshot = ref<string>('')

// ======================================================================
// 方法
// ======================================================================

/**
 * 脱敏显示 API Key
 */
function maskApiKey(key: string): string {
  if (!key) return ''
  if (key.length <= 8) return '****'
  return key.slice(0, 4) + '****' + key.slice(-4)
}

/**
 * 跳转到 AI 模型配置页面
 */
function goToModelConfig() {
  router.push('/modules/configuration/ai-models')
}

/**
 * 加载配置数据
 */
async function loadSettings() {
  try {
    const res = await aitestApi.getSettings()
    if (res.code === 0 && res.data) {
      const data = res.data
      // 逐个赋值到 reactive 对象
      Object.assign(settings, data)
      // 保存初始快照
      initialSnapshot.value = JSON.stringify(data)
    }
  } catch (e) {
    ElMessage.error('加载配置失败')
    console.error(e)
  }
}

/**
 * 保存配置
 */
async function handleSave() {
  saving.value = true
  try {
    // 构建更新数据（只传需要修改的字段）
    const updateData: AISettingsUpdate = {
      ai_mode_enabled: settings.ai_mode_enabled,
      auto_trigger_on_requirement_change: settings.auto_trigger_on_requirement_change,
      auto_generate_report: settings.auto_generate_report,
      auto_retest_on_failure: settings.auto_retest_on_failure,
      notification_config: { channels: notificationChannels.value },
      max_input_tokens: settings.max_input_tokens,
      max_output_tokens: settings.max_output_tokens,
      retry_count: settings.retry_count,
      timeout_seconds: settings.timeout_seconds,
      concurrency: settings.concurrency,
      rate_limit_rpm: settings.rate_limit_rpm,
      custom_prompt_template: settings.custom_prompt_template,
    }

    const res = await aitestApi.updateSettings(updateData)
    if (res.code === 0) {
      ElMessage.success('配置保存成功')
      // 更新初始快照
      initialSnapshot.value = JSON.stringify(settings)
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存配置失败')
    console.error(e)
  } finally {
    saving.value = false
  }
}

/**
 * 重置配置到上一次保存的状态
 */
function handleResetConfig() {
  if (initialSnapshot.value) {
    try {
      const saved = JSON.parse(initialSnapshot.value) as AISettings
      Object.assign(settings, saved)
      ElMessage.info('已重置为上次保存的配置')
    } catch {
      ElMessage.warning('重置失败，请重新加载页面')
    }
  } else {
    loadSettings()
    ElMessage.info('已重置为默认配置')
  }
}

// ======================================================================
// 初始化
// ======================================================================

onMounted(() => {
  loadSettings()
})
</script>

<style scoped lang="scss">
/* 暖色主题变量 */
$warm-bg: #fdf6ec;
$warm-border: #f5d9b0;

.ai-mode-config-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 6px;
    font-size: 22px;
    color: var(--el-text-color-primary);
  }

  .page-desc {
    margin: 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

/* Tab 容器 */
.config-tabs {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);

  :deep(.el-tabs__content) {
    padding: 0;
  }
}

.tab-content {
  padding: 24px;
}

/* 配置区块 */
.config-section {
  margin-bottom: 28px;

  .section-title {
    margin: 0 0 16px;
    font-size: 15px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    position: relative;
    padding-left: 12px;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 3px;
      bottom: 3px;
      width: 3px;
      border-radius: 2px;
      background: var(--el-color-primary);
    }
  }
}

/* 配置项行 */
.config-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  margin-bottom: 8px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  transition: background 0.2s;

  &:hover {
    background: $warm-bg;
    border-color: $warm-border;
  }

  .config-info {
    flex: 1;

    .config-label {
      display: block;
      font-size: 14px;
      font-weight: 500;
      color: var(--el-text-color-primary);
      margin-bottom: 4px;
    }

    .config-desc {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }

  .config-controls {
    flex-shrink: 0;
  }

  .config-slider {
    flex-shrink: 0;
  }
}

/* 通知渠道复选框组 */
.notify-checks {
  display: flex;
  gap: 16px;
}

/* 模型配置 - 跳转页 */
.model-redirect-content {
  text-align: center;

  .redirect-hint {
    margin-top: 16px;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }

  .model-overview {
    margin-top: 16px;
    text-align: left;
  }
}

/* Prompt 编辑器 */
.prompt-editor {
  margin-top: 8px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
}

/* 底部按钮 */
.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
</style>
