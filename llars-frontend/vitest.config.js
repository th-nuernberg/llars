import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
  ],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.js'],
    include: ['tests/**/*.{test,spec}.{js,ts,vue}'],
    exclude: ['node_modules', 'dist'],
    // CSS handling for Vuetify
    css: true,
    deps: {
      inline: ['vuetify'],
    },
    server: {
      deps: {
        inline: ['vuetify'],
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{js,vue}'],
      exclude: [
        'src/main.js',
        'src/plugins/**',
        '**/*.d.ts',
      ],
    },
    // Mock environment variables
    env: {
      VITE_API_BASE_URL: 'http://localhost:55080',
      VITE_AUTHENTIK_URL: 'http://localhost:55095',
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
