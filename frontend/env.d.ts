/// <reference types="vite/client" />

/* 声明 .vue 文件的模块类型，使 TypeScript 能正确识别 SFC 组件 */
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
  export default component
}

/* 声明 element-plus 中文 locale 模块类型 */
declare module 'element-plus/dist/locale/zh-cn.mjs' {
  const zhCn: import('element-plus').Language
  export default zhCn
}
