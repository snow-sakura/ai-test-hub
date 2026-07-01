<template>
  <!--
    生成行为配置管理页面

    精简设计的表单：启用 AI 评审和改进开关、默认输出模式选择、评审超时时间滑块。
  -->
  <div class="generation-config">
    <!-- 配置表单卡片 -->
    <el-card shadow="never" class="config-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-icon><SetUp /></el-icon>
          <span>生成行为配置</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        label-width="140px"
        label-position="left"
        class="gen-form"
        v-if="!loading"
      >
        <!-- 启用 AI 评审和改进 -->
        <el-form-item label="启用 AI 评审和改进">
          <div class="toggle-with-hint">
            <el-switch
              v-model="formData.enable_auto_review"
              active-text="启用"
              inactive-text="停用"
            />
            <span class="hint-text">
              开启后，AI 生成用例完成后将自动进行评审，并根据评审意见改进用例
            </span>
          </div>
        </el-form-item>

        <!-- 默认输出模式 -->
        <el-form-item label="默认输出模式">
          <el-radio-group v-model="formData.default_output_mode">
            <el-radio-button value="stream">
              <el-icon><RefreshRight /></el-icon>
              流式输出
            </el-radio-button>
            <el-radio-button value="complete">
              <el-icon><Finished /></el-icon>
              完整输出
            </el-radio-button>
          </el-radio-group>
          <span class="hint-text" style="display: block; margin-top: 6px;">
            流式输出实时显示生成进度，完整输出等待全部生成完毕后一次性显示
          </span>
        </el-form-item>

        <!-- 评审超时时间 -->
        <el-form-item label="评审超时时间（秒）">
          <div class="slider-with-hint">
            <el-slider
              v-model="formData.review_timeout"
              :min="30"
              :max="600"
              :step="10"
              show-input
              input-size="small"
              style="flex: 1"
            />
            <span class="slider-value">{{ formData.review_timeout }}s</span>
          </div>
          <span class="hint-text">
            超时后将跳过评审环节，直接返回已生成结果。范围 30 ~ 600 秒。
          </span>
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button type="warning" :loading="saving" @click="handleSave">
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 配置说明 -->
    <el-card shadow="never" class="info-card">
      <template #header>
        <div class="card-header">
          <el-icon><InfoFilled /></el-icon>
          <span>配置说明</span>
        </div>
      </template>
      <ul class="info-list">
        <li>
          <strong>启用 AI 评审和改进：</strong>开启后，生成的测试用例将自动经过 AI 评审并获得改进建议，提升用例质量。
        </li>
        <li>
          <strong>默认输出模式：</strong>流式输出适合长时间生成场景，可实时查看进度；完整输出适合快速生成场景。
        </li>
        <li>
          <strong>评审超时时间：</strong>评审过程超过设定时间后，系统将跳过评审，直接返回当前已生成的结果。
        </li>
      </ul>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { SetUp, Check, InfoFilled, RefreshRight, Finished } from '@element-plus/icons-vue'
import { configApi } from '@/api/configuration'
import type { GenerationConfigUpdate } from '@/types/ai'
import type { FormInstance } from 'element-plus'

// ====================================================================
// 状态管理
// ====================================================================

/** 加载状态 */
const loading = ref(false)
/** 保存中 */
const saving = ref(false)
/** 表单引用 */
const formRef = ref<FormInstance>()

/** 表单数据 */
const formData = reactive<GenerationConfigUpdate>({
  enable_auto_review: true,
  default_output_mode: 'stream',
  review_timeout: 120,
})

// ====================================================================
// 生命周期
// ====================================================================

onMounted(() => {
  loadConfig()
})

// ====================================================================
// 方法
// ====================================================================

/** 加载当前配置 */
async function loadConfig() {
  loading.value = true
  try {
    const res = await configApi.getGenerationConfig()
    const data = res.data
    if (data) {
      formData.enable_auto_review = data.enable_auto_review
      formData.default_output_mode = data.default_output_mode
      formData.review_timeout = data.review_timeout
    }
  } catch {
    // 首次使用可能没有配置，使用默认值
  } finally {
    loading.value = false
  }
}

/** 保存配置 */
async function handleSave() {
  saving.value = true
  try {
    await configApi.updateGenerationConfig(formData)
    ElMessage.success('配置已保存')
  } catch (err: any) {
    const msg = err?.response?.data?.message || '保存失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.generation-config {
  max-width: 800px;

  .config-card,
  .info-card {
    border: 1px solid rgba(180, 150, 120, 0.12);
    border-radius: 8px;
    background: #fffdf9;
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: #3d2e1f;
  }

  .gen-form {
    max-width: 600px;
  }

  .toggle-with-hint {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .hint-text {
    font-size: 12px;
    color: #8b7355;
    line-height: 1.6;
  }

  .slider-with-hint {
    display: flex;
    align-items: center;
    gap: 16px;
    width: 100%;

    .slider-value {
      font-size: 14px;
      font-weight: 600;
      color: #c67b5c;
      min-width: 48px;
      text-align: right;
    }
  }

  .info-list {
    padding-left: 16px;
    line-height: 1.8;

    li {
      font-size: 13px;
      color: #5c4a38;
      margin-bottom: 8px;

      strong {
        color: #3d2e1f;
      }
    }
  }
}
</style>
