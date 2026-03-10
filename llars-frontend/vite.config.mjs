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
//
// Uses --first-parent commit counting to avoid merge commit inflation:
//   git rev-list --first-parent --count v1.0.0..HEAD
// Without --first-parent, main has MORE commits than dev (each merge adds N+1 commits),
// making main appear as a higher version even though dev is always ahead.
//
// Both branches use the same formula: v{major}.{minor + first_parent_commits}.{patch}
// The branch name is shown separately in the UI (e.g. "DEV v1.22.0 · dev@abc123").
//
// Example with base tag v1.0.0:
//   dev (22 direct commits)  → v1.22.0
//   main (8 merge commits)   → v1.8.0
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

    // Find the latest version tag reachable from HEAD
    const tagDescribe = run('git describe --tags --long --match "v*" 2>/dev/null || echo ""')
    const match = tagDescribe.match(/^v(\d+)\.(\d+)\.(\d+)-\d+-g/)

    let version
    if (match) {
      const [, major, minor, patch] = match
      const tag = `v${major}.${minor}.${patch}`
      // Count only first-parent commits since the tag.
      // This gives dev=22, main=8 instead of dev=22, main=32.
      const commits = Number(run(`git rev-list --first-parent --count ${tag}..HEAD`))
      version = `${major}.${Number(minor) + commits}.${patch}`
    } else {
      // No tags yet — use first-parent commit count as minor
      const count = run('git rev-list --first-parent --count HEAD')
      version = `0.${count}.0`
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
