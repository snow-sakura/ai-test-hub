import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },

  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:7861',
        changeOrigin: true,
        ws: true,
        proxyTimeout: 300000,
        timeout: 300000,
      },
      '/ws': {
        target: 'ws://127.0.0.1:7861',
        ws: true,
      },
    },
  },
})
