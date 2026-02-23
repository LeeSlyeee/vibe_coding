import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/region/',
  server: {
    proxy: {
      '/api': {
        target: 'https://217.142.253.35.nip.io',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
