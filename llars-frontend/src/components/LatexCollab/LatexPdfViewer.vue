<template>
  <div ref="viewerEl" class="pdf-viewer">
    <div class="pdf-toolbar">
      <div class="d-flex align-center ga-2">
        <v-icon size="18">mdi-file-pdf-box</v-icon>
        <span class="text-body-2">PDF Preview</span>
      </div>
      <div v-if="props.isCompiling" class="pdf-compile-indicator">
        <span class="pdf-compile-dot"></span>
        Kompiliere...
      </div>
      <v-spacer />
      <div class="pdf-zoom-controls">
        <v-btn icon variant="text" size="x-small" title="Zoom out" @click="zoomOut">
          <v-icon size="16">mdi-minus</v-icon>
        </v-btn>
        <v-chip size="x-small" variant="tonal" class="pdf-zoom-chip">
          {{ zoomLabel }}
        </v-chip>
        <v-btn icon variant="text" size="x-small" title="Zoom in" @click="zoomIn">
          <v-icon size="16">mdi-plus</v-icon>
        </v-btn>
        <v-btn icon variant="text" size="x-small" title="Fit width" @click="resetZoom">
          <v-icon size="16">mdi-arrow-expand-horizontal</v-icon>
        </v-btn>
      </div>
      <v-chip v-if="pageCount" size="x-small" variant="tonal">
        {{ pageCount }} Seiten
      </v-chip>
    </div>

    <div v-if="error" class="px-3 pb-3">
      <v-alert type="error" variant="tonal" density="compact">
        {{ error }}
      </v-alert>
    </div>

    <div v-else class="pdf-body">
      <div v-if="!hasPdf && !showLoading" class="pdf-empty">
        <v-icon size="36" color="grey">mdi-file-pdf-box</v-icon>
        <div class="text-body-2 text-medium-emphasis mt-2">Noch kein PDF gerendert</div>
      </div>

      <div ref="pagesEl" class="pdf-pages" :class="{ 'pdf-pages--hidden': !hasPdf || showLoading }" />

      <div v-if="showLoading" class="pdf-loading">
        <LLoading size="lg" :label="loadingLabel" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist/build/pdf.mjs'
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

GlobalWorkerOptions.workerSrc = pdfWorker

const props = defineProps({
  workspaceId: { type: Number, required: true },
  jobId: { type: Number, default: null },
  refreshKey: { type: [Number, String], default: 0 },
  isCompiling: { type: Boolean, default: false }
})

const emit = defineEmits(['pdf-click'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'

const loading = ref(false)
const pendingPdf = ref(false)
const error = ref('')
const pageCount = ref(0)
const hasPdf = ref(false)
const viewerEl = ref(null)
const pagesEl = ref(null)
let currentPdf = null
const pageMeta = new Map()
const zoom = ref(1)
const minZoom = 0.6
const maxZoom = 3
const zoomStep = 0.1
const zoomLabel = computed(() => `${Math.round(zoom.value * 100)}%`)
let renderToken = 0
let renderFrame = null
let resizeObserver = null
let lastContainerWidth = 0
let retryTimer = null
let retryCount = 0
let retryBackoff = 0
const maxRetries = 10
const retryDelays = [400, 600, 800, 1000, 1200, 1500, 1800, 2200, 2600, 3000]
const showLoading = computed(() => loading.value || pendingPdf.value || props.isCompiling)
const loadingLabel = computed(() => {
  if (loading.value) return 'PDF wird geladen...'
  if (props.isCompiling) return 'PDF wird kompiliert...'
  if (pendingPdf.value) return 'PDF wird bereitgestellt...'
  return ''
})

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function clearPages() {
  if (!pagesEl.value) return
  pagesEl.value.innerHTML = ''
  pageMeta.clear()
}

function clearRetry() {
  if (retryTimer) {
    clearTimeout(retryTimer)
    retryTimer = null
  }
  retryCount = 0
  retryBackoff = 0
  pendingPdf.value = false
}

function scheduleRetry() {
  if (retryTimer || retryCount >= maxRetries) return
  pendingPdf.value = true
  const delay = retryDelays[Math.min(retryCount, retryDelays.length - 1)] + retryBackoff
  retryTimer = setTimeout(() => {
    retryTimer = null
    retryCount += 1
    loadPdf({ isRetry: true })
  }, delay)
}

function getPageDims(viewport) {
  if (!viewport) {
    return { pageX: 0, pageY: 0, pageWidth: 0, pageHeight: 0 }
  }
  const raw = viewport.rawDims
  if (raw) {
    return {
      pageX: Number(raw.pageX || 0),
      pageY: Number(raw.pageY || 0),
      pageWidth: Number(raw.pageWidth || 0),
      pageHeight: Number(raw.pageHeight || 0)
    }
  }
  const viewBox = viewport.viewBox
  if (Array.isArray(viewBox) && viewBox.length >= 4) {
    const [xMin, yMin, xMax, yMax] = viewBox
    return {
      pageX: Number(xMin || 0),
      pageY: Number(yMin || 0),
      pageWidth: Number(xMax - xMin || 0),
      pageHeight: Number(yMax - yMin || 0)
    }
  }
  return {
    pageX: 0,
    pageY: 0,
    pageWidth: Number(viewport.width || 0),
    pageHeight: Number(viewport.height || 0)
  }
}

function handleCanvasClick(event, pageNum) {
  const meta = pageMeta.get(pageNum)
  if (!meta || !meta.canvas || !meta.viewport) return
  const rect = meta.canvas.getBoundingClientRect()
  const offsetX = event.clientX - rect.left
  const offsetY = event.clientY - rect.top
  const [xPdf, yPdf] = meta.viewport.convertToPdfPoint(offsetX, offsetY)
  const { pageX, pageY, pageHeight } = getPageDims(meta.viewport)
  const x = xPdf - pageX
  const topOrigin = pageHeight + pageY
  const y = pageHeight ? topOrigin - yPdf : yPdf
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
  if (!meta || !meta.canvas || !meta.viewport) return

  const width = Number(location.width || 0)
  const height = Number(location.height || 0)
  const xRaw = Number(location.h ?? location.x ?? 0)
  const yRaw = Number(location.v ?? location.y ?? 0)
  const canvasHeight = meta.cssHeight || meta.canvas.getBoundingClientRect().height
  const canvasWidth = meta.cssWidth || meta.canvas.getBoundingClientRect().width
  const { pageX, pageY, pageHeight } = getPageDims(meta.viewport)
  const topOrigin = pageHeight + pageY

  let left = 0
  let top = 0
  let widthPx = 0
  let heightPx = 0

  if (width > 0 && height > 0) {
    const yBottom = pageHeight ? topOrigin - yRaw : yRaw
    const xPdf = pageX + xRaw
    const rect = meta.viewport.convertToViewportRectangle([
      xPdf,
      yBottom,
      xPdf + width,
      yBottom + height
    ])
    left = Math.min(rect[0], rect[2])
    top = Math.min(rect[1], rect[3])
    widthPx = Math.abs(rect[2] - rect[0])
    heightPx = Math.abs(rect[3] - rect[1])
  } else {
    const yBottom = pageHeight ? topOrigin - yRaw : yRaw
    const point = meta.viewport.convertToViewportPoint(pageX + xRaw, yBottom)
    left = point[0]
    top = point[1]
    widthPx = 24
    heightPx = 16
  }

  const container = pagesEl.value
  const targetTop = meta.wrapper.offsetTop + Math.max(0, top - container.clientHeight * 0.35)
  const targetLeft = meta.wrapper.offsetLeft + Math.max(0, left - container.clientWidth * 0.4)

  container.scrollTo({
    top: targetTop,
    left: targetLeft,
    behavior: 'smooth'
  })

  highlightLocation(
    meta,
    Math.min(left, canvasWidth - 1),
    Math.min(top, canvasHeight - 1),
    widthPx,
    heightPx
  )
}

function getContainerWidth() {
  if (!pagesEl.value) return 0
  const styles = window.getComputedStyle(pagesEl.value)
  const paddingLeft = parseFloat(styles.paddingLeft) || 0
  const paddingRight = parseFloat(styles.paddingRight) || 0
  const rect = pagesEl.value.getBoundingClientRect()
  const width = rect.width - paddingLeft - paddingRight
  return Math.max(0, width)
}

function scheduleRender() {
  if (!currentPdf) return
  if (renderFrame) cancelAnimationFrame(renderFrame)
  renderFrame = requestAnimationFrame(() => {
    renderFrame = null
    renderCurrentPdf()
  })
}

async function renderCurrentPdf() {
  if (!pagesEl.value || !currentPdf) return
  const containerWidth = getContainerWidth()
  if (!containerWidth) return
  clearPages()
  const pdf = currentPdf
  pageCount.value = pdf.numPages || 0
  const generation = ++renderToken
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  lastContainerWidth = containerWidth

  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
    if (generation !== renderToken) return
    const page = await pdf.getPage(pageNum)
    const baseViewport = page.getViewport({ scale: 1 })
    const targetScale = (containerWidth / baseViewport.width) * zoom.value
    const renderViewport = page.getViewport({ scale: targetScale * dpr })
    const renderWidth = Math.round(renderViewport.width)
    const renderHeight = Math.round(renderViewport.height)
    const cssWidth = Math.max(1, renderWidth / dpr)
    const cssHeight = Math.max(1, renderHeight / dpr)
    const effectiveScale = cssWidth / baseViewport.width
    const cssViewport = page.getViewport({ scale: effectiveScale })

    const wrapper = document.createElement('div')
    wrapper.className = 'pdf-page'
    wrapper.style.position = 'relative'
    wrapper.style.width = `${cssWidth}px`
    wrapper.style.height = `${cssHeight}px`

    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, renderWidth)
    canvas.height = Math.max(1, renderHeight)
    canvas.className = 'pdf-canvas'
    canvas.style.width = `${cssWidth}px`
    canvas.style.height = `${cssHeight}px`
    canvas.addEventListener('click', (event) => handleCanvasClick(event, pageNum))
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
    }

    await page.render({ canvasContext: ctx, viewport: renderViewport }).promise
    wrapper.appendChild(canvas)
    pagesEl.value.appendChild(wrapper)
    pageMeta.set(pageNum, {
      canvas,
      wrapper,
      viewport: cssViewport,
      cssWidth,
      cssHeight,
      highlightEl: null
    })
  }
}

async function loadPdf({ isRetry = false } = {}) {
  if (!props.workspaceId) return
  if (!isRetry) clearRetry()
  const hadPdf = hasPdf.value
  loading.value = true
  error.value = ''
  if (!hadPdf) {
    pageCount.value = 0
    hasPdf.value = false
    clearPages()
  }

  try {
    const params = props.jobId ? `?job_id=${props.jobId}` : ''
    const res = await axios.get(
      `${API_BASE}/api/latex-collab/workspaces/${props.workspaceId}/pdf${params}`,
      { headers: authHeaders(), responseType: 'arraybuffer' }
    )
    hasPdf.value = true
    pendingPdf.value = false
    retryCount = 0
    if (currentPdf?.destroy) {
      try {
        currentPdf.destroy()
      } catch {}
    }
    currentPdf = await getDocument({ data: res.data }).promise
    await renderCurrentPdf()
  } catch (err) {
    const status = err?.response?.status
    if (status === 404) {
      error.value = ''
      if (!hadPdf) {
        hasPdf.value = false
      }
      if (props.jobId) {
        scheduleRetry()
      } else {
        pendingPdf.value = false
      }
    } else if (status === 429) {
      retryBackoff = Math.min(8000, Math.max(retryBackoff, 1200) * 1.6 || 1200)
      if (props.jobId) {
        scheduleRetry()
      } else {
        pendingPdf.value = false
      }
    } else {
      pendingPdf.value = false
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

watch(zoom, () => {
  scheduleRender()
})

watch(viewerEl, (el) => {
  if (!el || typeof ResizeObserver === 'undefined') return
  if (resizeObserver) resizeObserver.disconnect()
  resizeObserver = new ResizeObserver((entries) => {
    const nextWidth = getContainerWidth()
    if (!nextWidth) return
    if (Math.abs(nextWidth - lastContainerWidth) < 2) return
    scheduleRender()
  })
  resizeObserver.observe(el)
})

onMounted(() => {
  loadPdf()
})

onUnmounted(() => {
  if (currentPdf?.destroy) {
    try {
      currentPdf.destroy()
    } catch {}
  }
  clearRetry()
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})

defineExpose({ scrollToLocation })

function zoomIn() {
  zoom.value = Math.min(maxZoom, Math.round((zoom.value + zoomStep) * 100) / 100)
}

function zoomOut() {
  zoom.value = Math.max(minZoom, Math.round((zoom.value - zoomStep) * 100) / 100)
}

function resetZoom() {
  zoom.value = 1
}
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

.pdf-body {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.pdf-loading,
.pdf-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
}

.pdf-loading {
  background: rgba(var(--v-theme-surface), 0.65);
}

.pdf-empty {
  background: transparent;
}

.pdf-pages {
  flex: 1;
  min-height: 0;
  padding: 12px;
  overflow: auto;
  background: rgba(var(--v-theme-surface-variant), 0.25);
  color: rgb(var(--v-theme-on-surface));
  display: flex;
  flex-direction: column;
  align-items: center;
  scrollbar-gutter: stable both-edges;
}

.pdf-pages--hidden {
  visibility: hidden;
  pointer-events: none;
}

.pdf-page {
  position: relative;
  margin-bottom: 12px;
}

.pdf-pages :deep(.pdf-canvas) {
  display: block;
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

.pdf-zoom-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pdf-zoom-chip {
  min-width: 54px;
  justify-content: center;
}

.pdf-compile-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.14);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.pdf-compile-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgb(var(--v-theme-warning));
  box-shadow: 0 0 0 0 rgba(var(--v-theme-warning), 0.45);
  animation: pdf-compile-pulse 1.2s ease-in-out infinite;
}

@keyframes pdf-compile-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(var(--v-theme-warning), 0.45);
    transform: scale(0.9);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(var(--v-theme-warning), 0);
    transform: scale(1);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(var(--v-theme-warning), 0);
    transform: scale(0.9);
  }
}

@media (prefers-reduced-motion: reduce) {
  .pdf-compile-dot {
    animation: none;
  }
}
</style>
