<template>
  <div class="pdf-viewer">
    <div class="pdf-toolbar">
      <div class="d-flex align-center ga-2">
        <v-icon size="18">mdi-file-pdf-box</v-icon>
        <span class="text-body-2">PDF Preview</span>
      </div>
      <v-spacer />
      <v-chip v-if="pageCount" size="x-small" variant="tonal">
        {{ pageCount }} Seiten
      </v-chip>
    </div>

    <div v-if="error" class="px-3 pb-3">
      <v-alert type="error" variant="tonal" density="compact">
        {{ error }}
      </v-alert>
    </div>

    <div v-else-if="loading" class="pdf-loading">
      <v-skeleton-loader type="image" height="260" />
    </div>

    <div v-else-if="!hasPdf" class="pdf-empty">
      <v-icon size="36" color="grey">mdi-file-pdf-box</v-icon>
      <div class="text-body-2 text-medium-emphasis mt-2">Noch kein PDF gerendert</div>
    </div>

    <div v-else ref="pagesEl" class="pdf-pages" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist/build/pdf.mjs'
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

GlobalWorkerOptions.workerSrc = pdfWorker

const props = defineProps({
  workspaceId: { type: Number, required: true },
  jobId: { type: Number, default: null },
  refreshKey: { type: [Number, String], default: 0 }
})

const emit = defineEmits(['pdf-click'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'

const loading = ref(false)
const error = ref('')
const pageCount = ref(0)
const hasPdf = ref(false)
const pagesEl = ref(null)
let currentPdf = null
const pageMeta = new Map()

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function clearPages() {
  if (!pagesEl.value) return
  pagesEl.value.innerHTML = ''
  pageMeta.clear()
}

function handleCanvasClick(event, pageNum) {
  const meta = pageMeta.get(pageNum)
  if (!meta || !meta.canvas || !meta.scale) return
  const rect = meta.canvas.getBoundingClientRect()
  const offsetX = (event.clientX - rect.left) * (meta.canvas.width / rect.width)
  const offsetY = (event.clientY - rect.top) * (meta.canvas.height / rect.height)

  const x = offsetX / meta.scale
  const y = (meta.canvas.height - offsetY) / meta.scale

  emit('pdf-click', { page: pageNum, x, y })
}

function highlightLocation(meta, xPx, yPx, widthPx, heightPx) {
  if (!meta?.wrapper) return
  if (meta.highlightEl) {
    try {
      meta.highlightEl.remove()
    } catch {}
    meta.highlightEl = null
  }
  const highlight = document.createElement('div')
  highlight.className = 'pdf-highlight'
  highlight.style.left = `${Math.max(0, xPx)}px`
  highlight.style.top = `${Math.max(0, yPx)}px`
  highlight.style.width = `${Math.max(18, widthPx || 24)}px`
  highlight.style.height = `${Math.max(12, heightPx || 16)}px`
  meta.wrapper.appendChild(highlight)
  meta.highlightEl = highlight
  setTimeout(() => {
    try {
      highlight.remove()
    } catch {}
    if (meta.highlightEl === highlight) {
      meta.highlightEl = null
    }
  }, 1400)
}

function scrollToLocation(location) {
  if (!location || !pagesEl.value) return
  const pageNum = Number(location.page)
  const meta = pageMeta.get(pageNum)
  if (!meta || !meta.canvas) return

  const scale = meta.scale || 1
  const canvasHeight = meta.canvas.height
  const canvasWidth = meta.canvas.width

  const xPx = (location.x || 0) * scale
  const yPx = canvasHeight - (location.y || 0) * scale
  const widthPx = (location.width || 0) * scale
  const heightPx = (location.height || 0) * scale

  const container = pagesEl.value
  const targetTop = meta.wrapper.offsetTop + Math.max(0, yPx - container.clientHeight * 0.35)
  const targetLeft = Math.max(0, xPx - container.clientWidth * 0.4)

  container.scrollTo({
    top: targetTop,
    left: targetLeft,
    behavior: 'smooth'
  })

  highlightLocation(meta, Math.min(xPx, canvasWidth - 1), Math.min(yPx, canvasHeight - 1), widthPx, heightPx)
}

async function renderPdf(data) {
  if (!pagesEl.value) return
  clearPages()

  if (currentPdf?.destroy) {
    try {
      currentPdf.destroy()
    } catch {}
  }

  const pdf = await getDocument({ data }).promise
  currentPdf = pdf
  pageCount.value = pdf.numPages || 0

  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
    const page = await pdf.getPage(pageNum)
    const viewport = page.getViewport({ scale: 1 })
    const containerWidth = pagesEl.value?.clientWidth || viewport.width
    const scale = containerWidth / viewport.width
    const scaledViewport = page.getViewport({ scale })

    const wrapper = document.createElement('div')
    wrapper.className = 'pdf-page'
    wrapper.style.position = 'relative'

    const canvas = document.createElement('canvas')
    canvas.width = scaledViewport.width
    canvas.height = scaledViewport.height
    canvas.className = 'pdf-canvas'
    canvas.addEventListener('click', (event) => handleCanvasClick(event, pageNum))
    const ctx = canvas.getContext('2d')

    await page.render({ canvasContext: ctx, viewport: scaledViewport }).promise
    wrapper.appendChild(canvas)
    pagesEl.value.appendChild(wrapper)
    pageMeta.set(pageNum, { canvas, wrapper, scale, highlightEl: null })
  }
}

async function loadPdf() {
  if (!props.workspaceId) return
  loading.value = true
  error.value = ''
  pageCount.value = 0
  hasPdf.value = false
  clearPages()

  try {
    const params = props.jobId ? `?job_id=${props.jobId}` : ''
    const res = await axios.get(
      `${API_BASE}/api/latex-collab/workspaces/${props.workspaceId}/pdf${params}`,
      { headers: authHeaders(), responseType: 'arraybuffer' }
    )
    hasPdf.value = true
    await renderPdf(res.data)
  } catch (err) {
    const status = err?.response?.status
    if (status === 404) {
      hasPdf.value = false
      error.value = ''
    } else {
      error.value = err?.response?.data?.error || err?.message || 'PDF konnte nicht geladen werden'
    }
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.workspaceId, props.jobId, props.refreshKey],
  () => {
    loadPdf()
  }
)

onMounted(() => {
  loadPdf()
})

onUnmounted(() => {
  if (currentPdf?.destroy) {
    try {
      currentPdf.destroy()
    } catch {}
  }
})

defineExpose({ scrollToLocation })
</script>

<style scoped>
.pdf-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  background: rgba(var(--v-theme-surface), 0.9);
  overflow: hidden;
}

.pdf-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.pdf-loading,
.pdf-empty {
  padding: 16px;
}

.pdf-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.pdf-pages {
  padding: 12px;
  overflow: auto;
  background: rgba(var(--v-theme-surface-variant), 0.25);
  color: rgb(var(--v-theme-on-surface));
}

.pdf-page {
  position: relative;
}

.pdf-pages :deep(.pdf-canvas) {
  width: 100%;
  height: auto;
  margin-bottom: 12px;
  border-radius: 8px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
  background: white;
}

.pdf-pages :deep(.pdf-highlight) {
  position: absolute;
  border: 2px solid rgba(255, 193, 7, 0.85);
  background: rgba(255, 193, 7, 0.18);
  border-radius: 4px;
  pointer-events: none;
  box-shadow: 0 0 0 1px rgba(255, 193, 7, 0.35);
}
</style>
