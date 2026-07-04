<template>
  <!--
    移动端首页仪表盘
    欢迎区 + 统计卡片 + 模块入口网格
  -->
  <div class="mobile-home">
    <!-- 欢迎区 -->
    <div class="welcome-section">
      <h1 class="welcome-title">
        <span class="brand">AI-HUB</span> 智能工作台
      </h1>
      <p class="welcome-sub">欢迎回来，{{ username }}！</p>
    </div>

    <!-- 统计卡片 2 列网格 -->
    <div class="stats-grid">
      <div v-for="card in statCards" :key="card.label" class="stat-card">
        <div class="stat-value">{{ card.value }}</div>
        <div class="stat-label">{{ card.label }}</div>
      </div>
    </div>

    <!-- 模块入口网格 -->
    <div class="module-grid">
      <div
        v-for="mod in modules"
        :key="mod.key"
        class="module-card"
        @click="router.push(mod.path)"
      >
        <div class="module-icon" :style="{ background: mod.color + '18', color: mod.color }">
          <van-icon :name="mod.icon" size="24" />
        </div>
        <div class="module-name">{{ mod.name }}</div>
        <div class="module-desc">{{ mod.description }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import client from '../../api/client'

const router = useRouter()
const userStore = useUserStore()
const username = computed(() => userStore.username || '用户')

interface Stats {
  total_projects: number
  total_test_cases: number
  today_executions: number
  pass_rate: number
}

const stats = ref<Stats | null>(null)

const statCards = computed(() => [
  { label: '项目总数', value: stats.value?.total_projects?.toLocaleString() ?? '0' },
  { label: '测试用例', value: stats.value?.total_test_cases?.toLocaleString() ?? '0' },
  { label: '今日执行', value: stats.value?.today_executions?.toLocaleString() ?? '0' },
  { label: '通过率', value: stats.value ? `${stats.value.pass_rate ?? 0}%` : '0%' },
])

const modules = [
  { key: 'ai-chat', name: 'AI 聊天', description: '智能对话助手', icon: 'chat-o', color: '#C67B5C', path: '/m/ai-chat' },
  { key: 'aitest', name: 'AI 智能测试', description: '测试全流程管理', icon: 'label-o', color: '#D4A574', path: '/m/aitest' },
  { key: 'api-testing', name: 'API 接口测试', description: '接口测试与自动化', icon: 'wap-o', color: '#C67B5C', path: '/m/api-testing' },
  { key: 'knowledge-base', name: '知识库', description: '测试知识沉淀', icon: 'records-o', color: '#D4A574', path: '/m/knowledge-base' },
]

onMounted(async () => {
  try {
    const res = await client.get<{ data: Stats }>('/v1/dashboard/stats')
    stats.value = res.data.data
  } catch {
    // 加载失败不阻塞页面
  }
})
</script>

<style scoped lang="scss">
.mobile-home {
  padding: 16px;
}

.welcome-section {
  margin-bottom: 20px;
}

.welcome-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--van-text-color);
  margin-bottom: 4px;
}

.brand {
  background: linear-gradient(135deg, #C67B5C, #D49472);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-sub {
  font-size: 14px;
  color: var(--van-text-color-3);
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--van-background-2);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--van-border-color);
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--van-text-color);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--van-text-color-3);
}

.module-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.module-card {
  background: var(--van-background-2);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--van-border-color);
  cursor: pointer;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.97);
  }
}

.module-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.module-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--van-text-color);
  margin-bottom: 4px;
}

.module-desc {
  font-size: 12px;
  color: var(--van-text-color-3);
}
</style>
