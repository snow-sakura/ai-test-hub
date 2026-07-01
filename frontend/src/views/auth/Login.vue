<template>
  <!-- 登录/注册页面 —— 暖色主题居中卡片布局 -->
  <div class="auth-page">
    <div class="auth-card">
      <!-- logo 和标题 -->
      <div class="auth-header">
        <div class="auth-logo">AI</div>
        <h2>{{ isRegister ? $t('auth.register') : $t('auth.loginTitle') }}</h2>
        <p class="auth-subtitle">{{ $t('auth.loginSubtitle') }}</p>
      </div>

      <!-- 登录表单 -->
      <el-form
        v-if="!isRegister"
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="0"
        size="large"
        class="auth-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            :placeholder="$t('auth.username')"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            :placeholder="$t('auth.password')"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <!-- 记住我 -->
        <el-form-item class="remember-row">
          <el-checkbox v-model="loginForm.rememberMe">
            {{ $t('auth.rememberMe') }}
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="auth-btn"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? $t('auth.logging') : $t('auth.loginButton') }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 注册表单 -->
      <el-form
        v-else
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="0"
        size="large"
        class="auth-form"
        @keyup.enter="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            :placeholder="$t('auth.username')"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            :placeholder="$t('auth.password')"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            :placeholder="$t('auth.confirmPassword')"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="auth-btn"
            :loading="loading"
            @click="handleRegister"
          >
            {{ loading ? $t('common.loading') : $t('auth.registerButton') }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 底部切换链接 -->
      <div class="auth-footer">
        <el-button link type="primary" @click="toggleMode">
          {{ isRegister ? $t('auth.goLogin') : $t('auth.goRegister') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()
const loading = ref(false)
const isRegister = ref(false)

// ========== 登录表单 ==========

/** 登录表单数据 */
const loginForm = reactive({
  username: localStorage.getItem('remembered_username') || '',
  password: '',
  rememberMe: !!localStorage.getItem('remembered_username'),
})

/** 登录表单校验规则 */
const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' },
  ],
}

// ========== 注册表单 ==========

/** 注册表单数据 */
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

/** 确认密码校验 */
const validateConfirmPassword = (_rule: unknown, value: string, callback: (e?: Error) => void) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

/** 注册表单校验规则 */
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度 2-50 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// ========== 方法 ==========

/** 切换登录/注册模式 */
function toggleMode(): void {
  isRegister.value = !isRegister.value
  loading.value = false
}

/** 处理登录 */
async function handleLogin(): Promise<void> {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await userStore.login({
      username: loginForm.username,
      password: loginForm.password,
    })

    // 记忆用户名
    if (loginForm.rememberMe) {
      localStorage.setItem('remembered_username', loginForm.username)
    } else {
      localStorage.removeItem('remembered_username')
    }

    ElMessage.success('登录成功')
    router.push('/home')
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    ElMessage.error(detail || '登录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

/** 处理注册 */
async function handleRegister(): Promise<void> {
  if (!registerFormRef.value) return
  try {
    await registerFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await userStore.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
    })

    ElMessage.success('注册成功，请登录')
    // 切换到登录模式并填入用户名
    isRegister.value = false
    loginForm.username = registerForm.username
    loginForm.password = ''
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    ElMessage.error(detail || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 已登录则直接跳转首页
onMounted(() => {
  if (userStore.isLoggedIn) {
    router.push('/home')
  }
  // 根据路由自动切换注册模式
  if (route.name === 'Register') {
    isRegister.value = true
  }
})

// 监听路由变化以切换模式
watch(
  () => route.name,
  (name) => {
    isRegister.value = name === 'Register'
  },
)
</script>

<style scoped lang="scss">
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg);
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  border: var(--border);
  padding: 40px 32px;
  box-shadow: 0 8px 32px rgba(60, 45, 30, 0.08);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;

  .auth-logo {
    width: 56px;
    height: 56px;
    margin: 0 auto 16px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 24px;
    font-weight: 700;
  }

  h2 {
    font-size: 24px;
    font-weight: 700;
    color: var(--text);
    margin: 0 0 8px;
  }

  .auth-subtitle {
    font-size: 14px;
    color: var(--text-muted);
    margin: 0;
  }
}

.auth-form {
  :deep(.el-input__wrapper) {
    background: var(--bg);
    border-radius: var(--radius);
    box-shadow: none;
    border: var(--border);
  }

  :deep(.el-input__wrapper:hover) {
    border-color: var(--primary);
  }
}

.remember-row {
  margin-bottom: 0;

  :deep(.el-form-item__content) {
    justify-content: flex-start;
  }
}

.auth-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: var(--radius);
}

.auth-footer {
  text-align: center;
  margin-top: 20px;

  :deep(.el-button) {
    font-size: 14px;
  }
}
</style>
