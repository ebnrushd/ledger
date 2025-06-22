import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path' // Import path module for resolving aliases

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'happy-dom', // or 'jsdom'
    setupFiles: ['./tests/setup.ts'], // Optional setup file for global test configurations
    coverage: {
      provider: 'istanbul', // or 'v8'
      reporter: ['text', 'json', 'html'],
    },
  },
})
```
