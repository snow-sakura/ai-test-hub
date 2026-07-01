import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import 'element-plus/dist/index.css'
import { createI18n } from 'vue-i18n'

import App from './App.vue'
import router from './router'

// 导入全局样式
import './styles/index.scss'

// 导入国际化资源
import zhCN from './locales/zh-cn'
import en from './locales/en'

// 创建 Vue I18n 实例
const i18n = createI18n({
  locale: 'zh-cn', // 默认中文
  fallbackLocale: 'en',
  messages: {
    'zh-cn': zhCN,
    en,
  },
})

const app = createApp(App)

// 按顺序安装插件
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.use(i18n)

// 应用启动时初始化认证状态（需在 pinia 安装之后）
import { useUserStore } from '@/stores/user'
const userStore = useUserStore()
userStore.initAuth()

// 挂载应用
app.mount('#app')
