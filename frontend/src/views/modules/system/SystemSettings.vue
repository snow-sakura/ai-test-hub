<template>
  <!--
    系统设置页面

    包含基本设置、安全设置等系统级参数配置表单。
  -->
  <div class="system-settings">
    <!-- 基本设置 -->
    <el-card shadow="never" class="settings-card">
      <div class="card-title">基本设置</div>
      <el-form :model="formData" label-width="100px" label-position="top" size="default">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="系统名称">
              <el-input v-model="formData.site_name" placeholder="系统名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备案号">
              <el-input v-model="formData.icp_beian" placeholder="如: 京ICP备XXXXXXXX号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="系统描述">
          <el-input v-model="formData.site_description" placeholder="系统简短描述" />
        </el-form-item>
        <el-form-item label="Logo URL">
          <el-input v-model="formData.logo_url" placeholder="Logo 图片 URL 地址" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 安全设置 -->
    <el-card shadow="never" class="settings-card">
      <div class="card-title">安全设置</div>
      <el-form :model="formData" label-width="130px" label-position="top" size="default">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="密码最小长度">
              <el-input-number
                v-model="formData.password_min_length"
                :min="4"
                :max="32"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码复杂度要求">
              <el-select v-model="formData.password_complexity" style="width: 100%">
                <el-option label="无要求" value="none" />
                <el-option label="字母 + 数字" value="letter_digit" />
                <el-option label="字母 + 数字 + 特殊字符" value="letter_digit_symbol" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大登录尝试次数">
              <el-input-number
                v-model="formData.max_login_attempts"
                :min="1"
                :max="20"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="登录锁定时间 (分钟)">
              <el-input-number
                v-model="formData.login_lock_minutes"
                :min="1"
                :max="1440"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="会话超时时间 (分钟)">
              <el-input-number
                v-model="formData.session_timeout_minutes"
                :min="5"
                :max="1440"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码过期天数">
              <el-input-number
                v-model="formData.password_expire_days"
                :min="0"
                :max="365"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 存储设置 -->
    <el-card shadow="never" class="settings-card">
      <div class="card-title">存储设置</div>
      <el-form :model="formData" label-width="130px" label-position="top" size="default">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大上传大小 (MB)">
              <el-input-number
                v-model="formData.upload_max_size_mb"
                :min="1"
                :max="1024"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="允许的文件类型">
              <el-input v-model="formData.allowed_file_types" placeholder="逗号分隔" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 操作按钮 -->
    <div class="btn-group">
      <el-button plain @click="loadSettings">恢复默认</el-button>
      <el-button type="warning" :loading="saving" @click="handleSave">保存设置</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/api/admin'
import type { SystemSettings } from '@/types/admin'

// ====================================================================
// 状态管理
// ====================================================================

const loading = ref(false)
const saving = ref(false)

const formData = reactive<SystemSettings>({
  site_name: 'AI-HUB',
  site_description: '基于AI技术的一站式智能软件测试平台',
  logo_url: '',
  icp_beian: '',
  password_min_length: 6,
  password_complexity: 'letter_digit',
  max_login_attempts: 5,
  login_lock_minutes: 30,
  session_timeout_minutes: 60,
  password_expire_days: 90,
  upload_max_size_mb: 100,
  allowed_file_types: 'pdf,doc,docx,md',
})

// ====================================================================
// 生命周期
// ====================================================================

onMounted(() => {
  loadSettings()
})

// ====================================================================
// 方法
// ====================================================================

/** 加载系统设置 */
async function loadSettings() {
  loading.value = true
  try {
    const res = await adminApi.getSettings()
    if (res.data) {
      Object.assign(formData, res.data)
    }
  } catch {
    ElMessage.error('加载系统设置失败')
  } finally {
    loading.value = false
  }
}

/** 保存设置 */
async function handleSave() {
  saving.value = true
  try {
    await adminApi.updateSettings({ ...formData })
    ElMessage.success('系统设置已保存')
  } catch (err: any) {
    const msg = err?.response?.data?.message || '保存失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.system-settings {
  .settings-card {
    border: 1px solid rgba(180, 150, 120, 0.12);
    border-radius: 8px;
    background: #fffdf9;
    margin-bottom: 16px;
  }

  .card-title {
    font-size: 15px;
    font-weight: 600;
    color: #3d2e1f;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(180, 150, 120, 0.12);
  }

  .btn-group {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 8px;
  }
}
</style>
