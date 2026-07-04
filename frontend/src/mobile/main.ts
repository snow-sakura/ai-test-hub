/**
 * 移动端入口文件
 * 独立于桌面端，使用 Vant 4 组件库 + vue-i18n + Pinia
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import App from './App.vue'
import router from './router'

// Vant 4 按需引入（由 unplugin 自动注册组件，无需手动 import）
// 导入 Vant 基础样式
import 'vant/lib/index.css'

// 导入移动端全局样式
import './styles/index.scss'
import './styles/vant-overrides.scss'

// 导入国际化资源（复用桌面端翻译文件）
import zhCN from '@/locales/zh-cn'
import en from '@/locales/en'

// 创建 Vue I18n 实例
const i18n = createI18n({
  locale: 'zh-cn',
  fallbackLocale: 'en',
  messages: {
    'zh-cn': zhCN,
    en,
  },
})

const app = createApp(App)

// 安装插件
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(i18n)

// 初始化认证状态
import { useUserStore } from './stores/user'
const userStore = useUserStore()
userStore.initAuth()

// 挂载应用
app.mount('#app')
