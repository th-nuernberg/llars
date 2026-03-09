// Plugins
import Components from 'unplugin-vue-components/vite'
import Vue from '@vitejs/plugin-vue'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import { viteStaticCopy } from 'vite-plugin-static-copy'

// Utilities
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'
import { execSync } from 'node:child_process'

// Build-time semantic version derived from git tags.
// Tag a release (e.g. `git tag v3.1.0`), then versions auto-increment:
//   dev branch:  patch bumps → v3.1.1, v3.1.2, ...
//   main branch: minor bumps → v3.2.0, v3.3.0, ...
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
    // git describe: "v3.1.0-42-g66818a6f" → 42 commits since tag v3.1.0
    const describe = run('git describe --tags --long --match "v*" 2>/dev/null || echo ""')

    let version
    const match = describe.match(/^v(\d+)\.(\d+)\.(\d+)-(\d+)-g/)
    if (match) {
      const [, major, minor, patch, commits] = match
      if (branch === 'main') {
        // Main: bump minor per commit, reset patch → v3.2.0, v3.3.0, ...
        version = `${major}.${Number(minor) + Number(commits)}.0`
      } else {
        // Dev/feature branches: bump patch per commit → v3.1.1, v3.1.2, ...
        version = `${major}.${minor}.${Number(patch) + Number(commits)}`
      }
    } else {
      // No tags yet — use commit count as patch
      const count = run('git rev-list --count HEAD')
      version = `0.0.${count}`
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
  define: {
    'process.env': {},
    __APP_VERSION__: JSON.stringify(versionInfo),
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
  },
  preview: {
    port: 5173,
    // Allow all hosts - the frontend runs in an internal Docker network
    // behind nginx reverse proxy which handles host validation
    allowedHosts: true,
  },
})
