// Plugins
import Components from 'unplugin-vue-components/vite'
import Vue from '@vitejs/plugin-vue'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

// Utilities
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'
import { execSync } from 'node:child_process'

// Build-time semantic version derived from git tags using `git describe`.
//
// Formula: `git describe --tags --match "v*" --first-parent` → `v1.5.0-N-gabcdef`
//   - N=0: version = tag exactly (e.g. 1.5.0) — happens at tagged merge points
//   - N>0: version = major.minor.(patch + N) — increments patch per commit since tag
//
// Both branches show the SAME version at merge points (where the tag lives).
// After merge dev→main, create tag v1.{minor+1}.0 on main. Dev then auto-increments
// patch from that tag as new commits land.
//
// Example:
//   Tag v1.5.0 on main (after merge)  → both show v1.5.0
//   dev gets 3 more commits           → dev shows v1.5.3
//   Merge dev→main, tag v1.6.0        → both show v1.6.0
//   dev gets 2 more commits           → dev shows v1.6.2
function getVersionInfo() {
  // Docker builds pass version as env vars (no .git in container)
  if (process.env.APP_VERSION) {
    return {
      version: process.env.APP_VERSION,
      commitHash: process.env.APP_COMMIT_HASH || 'unknown',
      branch: process.env.APP_BRANCH || 'unknown',
    }
  }

  const run = (cmd) => execSync(cmd, { encoding: 'utf-8', cwd: '..' }).trim()
  try {
    const commitHash = run('git rev-parse --short HEAD')
    const branch = run('git rev-parse --abbrev-ref HEAD')

    // Try --first-parent first (works on dev), fall back to normal describe (works on main after merge)
    let describe = ''
    try { describe = run('git describe --tags --match "v*" --first-parent 2>/dev/null') } catch {}
    if (!describe) {
      try { describe = run('git describe --tags --match "v*" 2>/dev/null') } catch {}
    }

    const match = describe.match(/^v(\d+)\.(\d+)\.(\d+)(?:-(\d+)-g[0-9a-f]+)?$/)
    let version
    if (match) {
      const [, major, minor, patch, commits] = match
      const n = Number(commits || 0)
      version = n === 0
        ? `${major}.${minor}.${patch}`
        : `${major}.${minor}.${Number(patch) + n}`
    } else {
      version = '0.0.0'
    }

    return { version, commitHash, branch }
  } catch {
    return { version: '0.0.0', commitHash: 'unknown', branch: 'unknown' }
  }
}

const versionInfo = getVersionInfo()

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    Vue({
      template: { transformAssetUrls }
    }),
    // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
    Vuetify({ autoImport: true }),
    Components(),
  ],
  define: {
    'process.env': {},
    __APP_VERSION__: JSON.stringify(versionInfo),
  },
  build: {
    // Warnschwelle etwas anheben — die großen Vendor-Chunks (Vuetify etc.)
    // sind bewusst getrennt und werden gecacht.
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        // Große, selten wechselnde Bibliotheken in eigene, langfristig
        // cachebare Chunks aufteilen. Verkleinert den Haupt-Bundle und
        // verbessert Ladezeit/Core-Web-Vitals (Landing Page = SEO-relevant).
        // Konservativ gehalten: nur node_modules, nach Paket gruppiert.
        // Nur nachweislich ZYKLUSFREIE, große und lazy-geladene Libs in eigene
        // Chunks. Der Framework-Kern (Vue/Vuetify-Runtime, vue-router, i18n)
        // und der App-Code bleiben im Haupt-Bundle — ein separater 'vue'- oder
        // 'realtime'-Chunk erzeugte zirkuläre Abhängigkeiten (Init-Reihenfolge-
        // Risiko). Diese vier Libs sind reine Blätter im Import-Graph.
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('jspdf') || id.includes('html2canvas')) return 'pdf-export'
          if (id.includes('leaflet')) return 'leaflet'
          if (id.includes('vuetify')) return 'vuetify'
        },
      },
    },
  },
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
    // Local preview: when VITE_PROXY_TARGET is set, forward /api, /auth,
    // /health, /healthz to that URL. Used by `npm run dev` from a dev
    // machine to render the frontend locally while talking to the
    // production (or staging) backend — no need to spin up the full
    // docker stack just to eyeball a UI tweak.
    proxy: process.env.VITE_PROXY_TARGET
      ? {
          '/api':     { target: process.env.VITE_PROXY_TARGET, changeOrigin: true, secure: true },
          '/auth':    { target: process.env.VITE_PROXY_TARGET, changeOrigin: true, secure: true },
          '/health':  { target: process.env.VITE_PROXY_TARGET, changeOrigin: true, secure: true },
          '/healthz': { target: process.env.VITE_PROXY_TARGET, changeOrigin: true, secure: true },
          '/socket.io': {
            target: process.env.VITE_PROXY_TARGET,
            changeOrigin: true,
            secure: true,
            ws: true,
          },
        }
      : undefined,
  },
  preview: {
    port: 5173,
    // Allow all hosts - the frontend runs in an internal Docker network
    // behind nginx reverse proxy which handles host validation
    allowedHosts: true,
  },
})
