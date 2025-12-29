// Plugins
import Components from 'unplugin-vue-components/vite'
import Vue from '@vitejs/plugin-vue'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import { viteStaticCopy } from 'vite-plugin-static-copy'

// Utilities
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    Vue({
      template: { transformAssetUrls }
    }),
    // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
    Vuetify({ autoImport: true }),
    Components(),
    // Copy PDF.js worker to public folder at build time
    // This ensures the worker is always available at a fixed path (/pdf.worker.min.mjs)
    // and stays in sync with the pdfjs-dist version
    // See: https://medium.com/@prospercoded/how-i-fixed-the-it-works-on-my-machine-pdf-js-nightmare-in-vite-54adfe92e7f2
    viteStaticCopy({
      targets: [
        {
          src: 'node_modules/pdfjs-dist/build/pdf.worker.min.mjs',
          dest: '.'
        }
      ]
    }),
  ],
  define: { 'process.env': {} },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.ts',
      '.tsx',
      '.vue',
    ],
  },
  server: {
    port: 5173,
    allowedHosts: [
      'llars.e-beratungsinstitut.de',
      'llars.informatik.fh-nuernberg.de',
      'host.docker.internal',
      'localhost'
    ],
  },
  preview: {
    port: 5173,
    // Allow all hosts - the frontend runs in an internal Docker network
    // behind nginx reverse proxy which handles host validation
    allowedHosts: true,
  },
})
