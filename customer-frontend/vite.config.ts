import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'url'; // For new alias style
// Removed 'path' import as fileURLToPath/URL is more standard with import.meta.url

/// <reference types="vitest" />

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@customer': fileURLToPath(new URL('./src/modules/customer', import.meta.url)),
      '@admin': fileURLToPath(new URL('./src/modules/admin', import.meta.url)),
      '@shared': fileURLToPath(new URL('./src/shared', import.meta.url))
    }
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
