/**
 * useLatexCompile.js
 *
 * Composable for LaTeX compilation functionality.
 * Handles compile jobs, polling, status tracking, and log parsing.
 */

import { ref, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const AUTO_COMPILE_KEY = 'latex-collab-auto-compile'
const AUTO_COMPILE_DELAY_KEY = 'latex-collab-auto-compile-delay'

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Parse LaTeX compile log for errors, warnings, and overfull boxes.
 * @param {string} logText - Raw log text from pdflatex
 * @returns {Array} Array of issue objects
 */
export function parseLatexLog(logText) {
  const issues = []
  const lines = String(logText || '').split(/\r?\n/)
  const fileStack = []

  const pushFile = (file) => {
    if (!file) return
    const cleaned = file.replace(/[()]/g, '').trim()
    if (!cleaned) return
    fileStack.push(cleaned)
  }

  const currentFile = () => fileStack[fileStack.length - 1] || null

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i] || ''

    const fileMatches = Array.from(line.matchAll(/\(([^()\s]+?\.(?:tex|bib|sty|cls|ltx|bst))\b/g))
    fileMatches.forEach((match) => pushFile(match[1]))

    const closeCount = (line.match(/\)/g) || []).length
    for (let c = 0; c < closeCount && fileStack.length > 0; c += 1) {
      fileStack.pop()
    }

    if (line.startsWith('! ')) {
      let lineNo = null
      for (let j = i + 1; j < Math.min(i + 6, lines.length); j += 1) {
        const ln = lines[j]
        const match = ln.match(/^l\.(\d+)/) || ln.match(/line\s+(\d+)/i)
        if (match) {
          lineNo = Number(match[1])
          break
        }
      }
      issues.push({
        type: 'error',
        message: line.replace(/^!\s*/, '').trim(),
        file: currentFile(),
        line: lineNo
      })
      continue
    }

    if (/warning/i.test(line)) {
      const match = line.match(/line\s+(\d+)/i)
      issues.push({
        type: 'warning',
        message: line.trim(),
        file: currentFile(),
        line: match ? Number(match[1]) : null
      })
      continue
    }

    if (line.includes('Overfull \\hbox')) {
      const match = line.match(/lines?\s+(\d+)/i)
      issues.push({
        type: 'overfull',
        message: line.trim(),
        file: currentFile(),
        line: match ? Number(match[1]) : null
      })
    }
  }

  return issues
}

/**
 * Create LaTeX compile composable
 * @param {Object} options - Configuration options
 * @param {Ref<number>} options.workspaceId - Workspace ID ref
 * @param {Ref<Object>} options.selectedNode - Currently selected document node
 * @param {Ref<Object>} options.editorRef - Editor component ref
 * @param {Function} options.resolveDocumentIdFromPath - Function to resolve document ID from file path
 * @param {Function} options.normalizePath - Function to normalize file paths
 * @param {Ref<boolean>} options.reviewMode - Review mode state
 * @param {Function} options.hasPermission - Permission check function
 * @returns {Object} Composable state and methods
 */
export function useLatexCompile({
  workspaceId,
  selectedNode,
  editorRef,
  resolveDocumentIdFromPath,
  normalizePath,
  reviewMode,
  hasPermission
}) {
  // State
  const compileJobId = ref(null)
  const compileStatus = ref('idle')
  const compileError = ref('')
  const compileLog = ref('')
  const compileHasPdf = ref(false)
  const compileHasSynctex = ref(false)
  const compileLogDialog = ref(false)
  const pdfRefreshKey = ref(0)
  const pdfRefreshJobId = ref(null)
  const compileCommitId = ref(null)
  const compileCommitOptions = ref([{ title: 'Aktuell', value: null }])
  const compileIssues = ref([])

  // Auto-compile settings
  const autoCompileEnabled = ref(localStorage.getItem(AUTO_COMPILE_KEY) === 'true')
  const autoCompileDelay = ref(parseInt(localStorage.getItem(AUTO_COMPILE_DELAY_KEY)) || 2000)

  // Timers
  let autoCompileTimer = null
  let compilePollTimer = null

  // Computed
  const canCompile = computed(() => {
    return !!(
      selectedNode.value &&
      selectedNode.value.type === 'file' &&
      !selectedNode.value.asset_id &&
      hasPermission('feature:latex_collab:edit')
    )
  })

  const isCompiling = computed(() => ['queued', 'running'].includes(compileStatus.value))

  const compileStatusLabel = computed(() => {
    if (compileStatus.value === 'queued') return 'Queued'
    if (compileStatus.value === 'running') return 'Kompiliert'
    if (compileStatus.value === 'success') return 'Fertig'
    if (compileStatus.value === 'failed') return 'Fehler'
    return 'Idle'
  })

  const compileStatusColor = computed(() => {
    if (compileStatus.value === 'success') return 'success'
    if (compileStatus.value === 'failed') return 'error'
    if (compileStatus.value === 'running') return 'info'
    if (compileStatus.value === 'queued') return 'warning'
    return undefined
  })

  const canSync = computed(() => (
    compileStatus.value === 'success' &&
    !!compileJobId.value &&
    compileHasSynctex.value
  ))

  const pdfJobId = computed(() => (
    compileStatus.value === 'success' && compileJobId.value ? compileJobId.value : null
  ))

  // Watchers
  watch(autoCompileEnabled, (val) => {
    localStorage.setItem(AUTO_COMPILE_KEY, val ? 'true' : 'false')
  })

  watch(autoCompileDelay, (val) => {
    const normalized = Number.isFinite(Number(val)) ? Math.max(250, Number(val)) : 2000
    if (normalized !== Number(val)) {
      autoCompileDelay.value = normalized
      return
    }
    localStorage.setItem(AUTO_COMPILE_DELAY_KEY, normalized.toString())
  })

  // Decorate issues with UI metadata
  function decorateIssues(issues) {
    return issues.map((issue, index) => {
      const filePath = issue.file ? normalizePath(issue.file) : ''
      const fileName = filePath ? filePath.split('/').pop() : ''
      const documentId = filePath ? resolveDocumentIdFromPath(filePath) : null
      const location = fileName
        ? `${fileName}${issue.line ? `:${issue.line}` : ''}`
        : (issue.line ? `Zeile ${issue.line}` : '—')
      const type = issue.type || 'warning'
      const color = type === 'error' ? 'error' : (type === 'overfull' ? 'info' : 'warning')
      const label = type === 'error' ? 'Error' : (type === 'overfull' ? 'Overfull' : 'Warning')
      return {
        ...issue,
        id: `${type}-${index}-${issue.line || 0}`,
        document_id: documentId,
        location,
        color,
        label
      }
    })
  }

  // Update issues when log changes
  watch(compileLog, () => {
    compileIssues.value = decorateIssues(parseLatexLog(compileLog.value))
  }, { immediate: true })

  // Methods
  async function loadCompileStatus(jobId) {
    if (!jobId) {
      compileStatus.value = 'idle'
      compileJobId.value = null
      compileError.value = ''
      compileLog.value = ''
      compileHasPdf.value = false
      compileHasSynctex.value = false
      return
    }
    try {
      const res = await axios.get(`${API_BASE}/api/latex-collab/compile/${jobId}`, {
        headers: authHeaders()
      })
      const job = res.data?.job
      if (job) {
        compileJobId.value = job.id
        compileStatus.value = job.status || 'idle'
        compileError.value = job.error_message || ''
        compileLog.value = job.log_text || ''
        compileHasPdf.value = !!job.has_pdf
        compileHasSynctex.value = !!job.has_synctex
        if (['queued', 'running'].includes(job.status)) {
          pollCompileJob(job.id)
        }
      }
    } catch (e) {
      console.error('Failed to load compile status:', e)
    }
  }

  async function loadCommitOptions(documentId) {
    if (!documentId) {
      compileCommitOptions.value = [{ title: 'Aktuell', value: null }]
      compileCommitId.value = null
      return
    }
    try {
      const res = await axios.get(
        `${API_BASE}/api/latex-collab/documents/${documentId}/commits`,
        { headers: authHeaders() }
      )
      const items = (res.data?.commits || []).map((c) => ({
        title: `#${c.id} · ${c.message}`,
        value: c.id
      }))
      const options = [{ title: 'Aktuell', value: null }, ...items]
      compileCommitOptions.value = options
      const optionValues = new Set(options.map((opt) => opt.value))
      if (!optionValues.has(compileCommitId.value)) {
        compileCommitId.value = null
      }
    } catch (e) {
      compileCommitOptions.value = [{ title: 'Aktuell', value: null }]
      compileCommitId.value = null
    }
  }

  function scheduleAutoCompile() {
    if (!autoCompileEnabled.value || !canCompile.value || reviewMode.value || isCompiling.value) return
    if (autoCompileTimer) clearTimeout(autoCompileTimer)
    autoCompileTimer = setTimeout(() => {
      triggerCompile()
    }, autoCompileDelay.value)
  }

  async function triggerCompile() {
    if (!canCompile.value) return
    compileError.value = ''
    compileLog.value = ''
    compileHasPdf.value = false
    compileHasSynctex.value = false
    pdfRefreshJobId.value = null
    if (autoCompileTimer) clearTimeout(autoCompileTimer)
    try {
      if (!compileCommitId.value) {
        await editorRef.value?.flushDocumentState?.()
      }
      const payload = {}
      if (compileCommitId.value) payload.commit_id = compileCommitId.value
      const res = await axios.post(
        `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/compile`,
        payload,
        { headers: authHeaders() }
      )
      const job = res.data?.job
      if (job) {
        compileJobId.value = job.id
        compileStatus.value = job.status || 'queued'
        compileHasPdf.value = !!job.has_pdf
        compileHasSynctex.value = !!job.has_synctex
        pollCompileJob(job.id)
      }
    } catch (e) {
      compileStatus.value = 'failed'
      compileError.value = e?.response?.data?.error || e?.message || 'Kompilierung fehlgeschlagen'
      compileHasPdf.value = false
      compileHasSynctex.value = false
    }
  }

  async function pollCompileJob(jobId) {
    if (!jobId) return
    if (compilePollTimer) clearTimeout(compilePollTimer)
    let pdfWaitAttempts = 0
    const maxPdfWaitAttempts = 12
    let rateLimitedCount = 0

    const poll = async () => {
      let nextDelay = 1500
      try {
        const res = await axios.get(`${API_BASE}/api/latex-collab/compile/${jobId}`, {
          headers: authHeaders()
        })
        const job = res.data?.job
        if (job) {
          compileJobId.value = job.id
          compileStatus.value = job.status || compileStatus.value
          compileError.value = job.error_message || ''
          compileLog.value = job.log_text || ''
          compileHasPdf.value = !!job.has_pdf
          compileHasSynctex.value = !!job.has_synctex
          rateLimitedCount = 0
          if (job.status === 'success') {
            compileError.value = ''
            if (pdfRefreshJobId.value !== job.id) {
              pdfRefreshJobId.value = job.id
              pdfRefreshKey.value += 1
            }
            if (job.has_pdf && job.has_synctex) {
              compilePollTimer = null
              return
            }
            pdfWaitAttempts += 1
            nextDelay = 800
            if (pdfWaitAttempts > maxPdfWaitAttempts) {
              compilePollTimer = null
              return
            }
          }
          if (job.status === 'failed') {
            compilePollTimer = null
            return
          }
        }
      } catch (e) {
        const status = e?.response?.status
        if (status === 429) {
          rateLimitedCount += 1
          nextDelay = Math.min(12000, 1200 * Math.pow(1.7, rateLimitedCount))
        } else {
          console.error('Compile polling failed:', e)
        }
      }
      compilePollTimer = setTimeout(poll, nextDelay)
    }

    compilePollTimer = setTimeout(poll, 800)
  }

  // Cleanup
  onUnmounted(() => {
    if (autoCompileTimer) clearTimeout(autoCompileTimer)
    if (compilePollTimer) clearTimeout(compilePollTimer)
  })

  return {
    // State
    compileJobId,
    compileStatus,
    compileError,
    compileLog,
    compileHasPdf,
    compileHasSynctex,
    compileLogDialog,
    pdfRefreshKey,
    pdfRefreshJobId,
    compileCommitId,
    compileCommitOptions,
    compileIssues,
    autoCompileEnabled,
    autoCompileDelay,

    // Computed
    canCompile,
    isCompiling,
    compileStatusLabel,
    compileStatusColor,
    canSync,
    pdfJobId,

    // Methods
    loadCompileStatus,
    loadCommitOptions,
    scheduleAutoCompile,
    triggerCompile,
    pollCompileJob
  }
}
