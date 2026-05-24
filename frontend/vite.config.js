import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api/applications': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/api/ai': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/api/knowledge': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/mcp': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/check-completeness': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})