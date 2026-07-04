import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 移动端全局应用状态
 */
export const useAppStore = defineStore('mobile-app', () => {
  /** 侧边抽屉是否展开 */
  const drawerVisible = ref(false)
  /** 当前语言 */
  const locale = ref<'zh-cn' | 'en'>('zh-cn')

  function toggleDrawer() {
    drawerVisible.value = !drawerVisible.value
  }

  function openDrawer() {
    drawerVisible.value = true
  }

  function closeDrawer() {
    drawerVisible.value = false
  }

  function setLocale(lang: 'zh-cn' | 'en') {
    locale.value = lang
  }

  return {
    drawerVisible,
    locale,
    toggleDrawer,
    openDrawer,
    closeDrawer,
    setLocale,
  }
})
