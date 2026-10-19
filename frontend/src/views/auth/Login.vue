<template>
  <div class="auth-page">
    <!-- 左侧品牌展示区 -->
    <div class="auth-brand">
      <div class="brand-content">
        <div class="brand-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="40" height="40" rx="10" fill="white" fill-opacity="0.2"/>
              <text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" fill="white" font-size="16" font-weight="700" font-family="system-ui">AI</text>
            </svg>
          </div>
          <span class="logo-text">AI-HUB</span>
        </div>

        <h1 class="brand-title">智能测试工作台</h1>
        <p class="brand-desc">AI 驱动的一站式软件测试平台<br/>让测试更高效、更智能</p>

        <div class="brand-features">
          <div class="feature-item">
            <div class="feature-dot"></div>
            <span>AI 自动生成测试用例</span>
          </div>
          <div class="feature-item">
            <div class="feature-dot"></div>
            <span>智能评审与持续改进</span>
          </div>
          <div class="feature-item">
            <div class="feature-dot"></div>
            <span>全流程测试管理</span>
          </div>
        </div>
      </div>

      <!-- 装饰元素 -->
      <div class="brand-decoration">
        <div class="deco-circle deco-1"></div>
        <div class="deco-circle deco-2"></div>
        <div class="deco-circle deco-3"></div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="auth-form-side">
      <div class="form-container">
        <!-- 头部 -->
        <div class="form-header">
          <h2>{{ isRegister ? '创建账号' : '欢迎回来' }}</h2>
          <p>{{ isRegister ? '填写以下信息完成注册' : '登录以继续使用 AI-HUB' }}</p>
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
              placeholder="用户名或邮箱"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <div class="form-options">
            <el-checkbox v-model="loginForm.rememberMe">记住我</el-checkbox>
          </div>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="auth-btn"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
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
              placeholder="用户名"
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
              placeholder="密码"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="确认密码"
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
              {{ loading ? '注册中...' : '注 册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部切换 -->
        <div class="form-footer">
          <span>{{ isRegister ? '已有账号？' : '还没有账号？' }}</span>
          <el-button link type="primary" @click="toggleMode">
            {{ isRegister ? '去登录' : '立即注册' }}
          </el-button>
        </div>
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

const loginForm = reactive({
  username: localStorage.getItem('remembered_username') || '',
  password: '',
  rememberMe: !!localStorage.getItem('remembered_username'),
})

const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' },
  ],
}

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_rule: unknown, value: string, callback: (e?: Error) => void) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

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

function toggleMode(): void {
  isRegister.value = !isRegister.value
  loading.value = false
}

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

    if (loginForm.rememberMe) {
      localStorage.setItem('remembered_username', loginForm.username)
    } else {
      localStorage.removeItem('remembered_username')
    }

    ElMessage.success('登录成功')
    router.push('/home')
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    console.error('[登录失败]', detail || err.message || err)
    ElMessage.error(detail || '登录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

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
    isRegister.value = false
    loginForm.username = registerForm.username
    loginForm.password = ''
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    console.error('[注册失败]', detail || err.message || err)
    ElMessage.error(detail || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    router.push('/home')
  }
  if (route.name === 'Register') {
    isRegister.value = true
  }
})

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
  min-height: 100vh;
  background: var(--bg);
}

/* ====== 左侧品牌区 ====== */
.auth-brand {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 50%, #D4A574 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  overflow: hidden;

  @media (max-width: 900px) {
    display: none;
  }
}

.brand-content {
  position: relative;
  z-index: 2;
  max-width: 420px;
  color: #fff;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 48px;

  .logo-icon {
    width: 44px;
    height: 44px;

    svg {
      width: 100%;
      height: 100%;
    }
  }

  .logo-text {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 1px;
  }
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.3;
  margin-bottom: 16px;
  letter-spacing: 1px;
}

.brand-desc {
  font-size: 16px;
  line-height: 1.7;
  opacity: 0.9;
  margin-bottom: 48px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  opacity: 0.9;

  .feature-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.8);
    flex-shrink: 0;
  }
}

/* 装饰圆形 */
.brand-decoration {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.deco-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
}

.deco-1 {
  width: 300px;
  height: 300px;
  top: -80px;
  right: -60px;
}

.deco-2 {
  width: 200px;
  height: 200px;
  bottom: -40px;
  left: -40px;
}

.deco-3 {
  width: 120px;
  height: 120px;
  top: 50%;
  right: 20%;
  background: rgba(255, 255, 255, 0.04);
}

/* ====== 右侧表单区 ====== */
.auth-form-side {
  width: 520px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;

  @media (max-width: 900px) {
    width: 100%;
  }
}

.form-container {
  width: 100%;
  max-width: 380px;
}

.form-header {
  margin-bottom: 36px;

  h2 {
    font-size: 26px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 8px;
  }

  p {
    font-size: 14px;
    color: var(--text-muted);
  }
}

.auth-form {
  :deep(.el-input__wrapper) {
    background: var(--bg);
    border-radius: 8px;
    box-shadow: none;
    border: 1px solid rgba(180, 150, 120, 0.15);
    padding: 4px 12px;
    height: 44px;
    transition: border-color 0.2s;
  }

  :deep(.el-input__wrapper:hover) {
    border-color: var(--primary);
  }

  :deep(.el-input__wrapper.is-focus) {
    border-color: var(--primary);
    box-shadow: 0 0 0 2px rgba(198, 123, 92, 0.1);
  }

  :deep(.el-form-item) {
    margin-bottom: 20px;
  }
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  font-size: 14px;
}

.auth-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 8px;
  letter-spacing: 2px;
}

.form-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: var(--text-muted);

  :deep(.el-button) {
    font-size: 14px;
    font-weight: 500;
  }
}
</style>
