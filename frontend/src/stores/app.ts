import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 全局应用状态管理
 * 预留：后续可扩展主题切换、侧边栏折叠、语言切换等
 */
export const useAppStore = defineStore('app', () => {
  /** 侧边栏是否折叠 */
  const sidebarCollapsed = ref(false)
  /** 当前语言 */
  const locale = ref<'zh-cn' | 'en'>('zh-cn')

  /** 切换侧边栏折叠状态 */
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /** 设置语言 */
  function setLocale(lang: 'zh-cn' | 'en') {
    locale.value = lang
  }

  return {
    sidebarCollapsed,
    locale,
    toggleSidebar,
    setLocale,
  }
})
