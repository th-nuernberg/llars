import { computed, onUnmounted, ref } from 'vue'

export function useSplitPaneResize({
  storageKey,
  viewMode,
  minRatio = 0.25,
  maxRatio = 0.75
} = {}) {
  const panesContainerRef = ref(null)
  const resizingPanes = ref(false)
  const editorPaneWidth = ref(0)

  if (typeof window !== 'undefined' && storageKey) {
    const stored = parseInt(localStorage.getItem(storageKey))
    editorPaneWidth.value = Number.isFinite(stored) ? stored : 0
  }

  const isSplitMode = computed(() => !viewMode || viewMode.value === 'split')

  const editorPaneStyle = computed(() => {
    if (!isSplitMode.value || editorPaneWidth.value <= 0) return {}
    const width = `${editorPaneWidth.value}px`
    return { width, flex: `0 0 ${width}` }
  })

  const previewPaneStyle = computed(() => {
    if (!isSplitMode.value || editorPaneWidth.value <= 0) return {}
    return { flex: '1 1 0' }
  })

  function startResize(event) {
    if (!isSplitMode.value) return
    event.preventDefault()
    resizingPanes.value = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', stopResize)
  }

  function onMouseMove(event) {
    if (!resizingPanes.value || !panesContainerRef.value) return
    const containerRect = panesContainerRef.value.getBoundingClientRect()
    const mouseX = event.clientX - containerRect.left
    const containerWidth = containerRect.width
    const minWidth = containerWidth * minRatio
    const maxWidth = containerWidth * maxRatio
    editorPaneWidth.value = Math.max(minWidth, Math.min(maxWidth, mouseX))
  }

  function stopResize() {
    resizingPanes.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', stopResize)
    if (storageKey) {
      localStorage.setItem(storageKey, editorPaneWidth.value.toString())
    }
  }

  onUnmounted(() => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', stopResize)
  })

  return {
    panesContainerRef,
    editorPaneWidth,
    editorPaneStyle,
    previewPaneStyle,
    resizingPanes,
    startResize
  }
}
