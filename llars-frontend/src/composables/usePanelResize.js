import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Composable für resizable Panels mit Drag-Divider.
 *
 * Supports both axes:
 *  - axis='horizontal' (default) — left ↔ right resize, e.g. context | options
 *  - axis='vertical' — top ↔ bottom resize, e.g. context above / options below
 *
 * `leftPanelWidth` keeps the name for backward-compatibility, but it
 * represents the size of the "first" panel along whichever axis is active.
 *
 * @param {Object} options - Konfiguration
 * @param {number} options.initialLeftPercent - Initial size of first panel (default: 50)
 * @param {number} options.minLeftPercent - Min size in % (default: 20)
 * @param {number} options.maxLeftPercent - Max size in % (default: 80)
 * @param {string} options.storageKey - LocalStorage key (optional)
 * @param {('horizontal'|'vertical')} options.axis - resize axis (default: 'horizontal')
 */
export function usePanelResize(options = {}) {
  const {
    initialLeftPercent = 50,
    minLeftPercent = 20,
    maxLeftPercent = 80,
    storageKey = null,
    axis = 'horizontal'
  } = options
  const isVertical = axis === 'vertical'

  const leftPanelWidth = ref(initialLeftPercent)
  const isResizing = ref(false)
  const containerRef = ref(null)

  onMounted(() => {
    if (storageKey) {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed = parseFloat(saved)
        if (!isNaN(parsed) && parsed >= minLeftPercent && parsed <= maxLeftPercent) {
          leftPanelWidth.value = parsed
        }
      }
    }
  })

  const startResize = (event) => {
    event.preventDefault()
    isResizing.value = true
    document.body.style.cursor = isVertical ? 'row-resize' : 'col-resize'
    document.body.style.userSelect = 'none'

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', stopResize)
  }

  const onMouseMove = (event) => {
    if (!isResizing.value || !containerRef.value) return

    const rect = containerRef.value.getBoundingClientRect()
    const span = isVertical ? rect.height : rect.width
    const cursorPos = isVertical
      ? event.clientY - rect.top
      : event.clientX - rect.left

    let percent = (cursorPos / span) * 100
    percent = Math.max(minLeftPercent, Math.min(maxLeftPercent, percent))
    leftPanelWidth.value = percent
  }

  const stopResize = () => {
    isResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''

    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', stopResize)

    if (storageKey) {
      localStorage.setItem(storageKey, leftPanelWidth.value.toString())
    }
  }

  onUnmounted(() => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', stopResize)
  })

  // Backward-compatible names. For horizontal axis they style the
  // left/right panels; for vertical axis they style the top/bottom
  // panels via height instead of width.
  const leftPanelStyle = () => isVertical
    ? { height: `calc(${leftPanelWidth.value}% - 3px)`, flexShrink: 0 }
    : { width: `calc(${leftPanelWidth.value}% - 3px)`, flexShrink: 0 }

  const rightPanelStyle = () => isVertical
    ? { height: `calc(${100 - leftPanelWidth.value}% - 3px)`, flexShrink: 0 }
    : { width: `calc(${100 - leftPanelWidth.value}% - 3px)`, flexShrink: 0 }

  return {
    leftPanelWidth,
    isResizing,
    containerRef,
    startResize,
    leftPanelStyle,
    rightPanelStyle
  }
}
