import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import Components from 'unplugin-vue-components/vite'
import AutoImport from 'unplugin-auto-import/vite'
import { VantResolver } from '@vant/auto-import-resolver'

export default defineConfig({
  plugins: [
    vue(),
    // Vant 组件按需自动引入
    Components({
      resolvers: [VantResolver()],
      dts: 'src/mobile/components.d.ts',
    }),
    // Vant 函数按需自动引入（如 showToast 等）
    AutoImport({
      resolvers: [VantResolver()],
      dts: 'src/mobile/auto-imports.d.ts',
    }),
  ],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },

  server: {
    port: Number(process.env.VITE_DEV_PORT || 5173),
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
        proxyTimeout: 300000,
        timeout: 300000,
      },
      '/ws': {
        target: (process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000').replace(/^http/, 'ws'),
        ws: true,
      },
    },
  },
})
