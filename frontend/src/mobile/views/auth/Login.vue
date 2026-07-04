<template>
  <!--
    移动端登录页
    简洁的全屏表单布局
  -->
  <div class="login-page">
    <div class="login-header">
      <div class="login-logo">
        <span class="logo-text">AI-HUB</span>
      </div>
      <h1 class="login-title">智能工作台</h1>
      <p class="login-subtitle">登录以继续使用</p>
    </div>

    <div class="login-form">
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="form.username"
            name="username"
            label="用户名"
            placeholder="请输入用户名"
            :rules="[{ required: true, message: '请输入用户名' }]"
          />
          <van-field
            v-model="form.password"
            type="password"
            name="password"
            label="密码"
            placeholder="请输入密码"
            :rules="[{ required: true, message: '请输入密码' }]"
          />
        </van-cell-group>

        <div class="login-actions">
          <van-button
            round
            block
            type="primary"
            native-type="submit"
            :loading="loading"
            size="large"
          >
            登录
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const form = ref({
  username: '',
  password: '',
})

async function onSubmit() {
  loading.value = true
  try {
    await userStore.login(form.value)
    showToast({ message: '登录成功', type: 'success' })
    router.replace('/m/home')
  } catch (err: any) {
    showToast({ message: err?.message || '登录失败', type: 'fail' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 32px 24px;
  background: var(--van-background);
}

.login-header {
  text-align: center;
  margin-bottom: 48px;
}

.login-logo {
  margin-bottom: 16px;
}

.logo-text {
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #C67B5C, #D49472);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--van-text-color);
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 14px;
  color: var(--van-text-color-3);
}

.login-actions {
  margin: 24px 16px 0;
}
</style>
