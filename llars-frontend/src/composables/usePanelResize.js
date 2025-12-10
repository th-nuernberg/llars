import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Composable für resizable Panels mit Drag-Divider
 *
 * @param {Object} options - Konfiguration
 * @param {number} options.initialLeftPercent - Initiale Breite des linken Panels in Prozent (default: 50)
 * @param {number} options.minLeftPercent - Minimale Breite links in Prozent (default: 20)
 * @param {number} options.maxLeftPercent - Maximale Breite links in Prozent (default: 80)
 * @param {string} options.storageKey - LocalStorage Key zum Speichern der Position (optional)
 */
export function usePanelResize(options = {}) {
  const {
    initialLeftPercent = 50,
    minLeftPercent = 20,
    maxLeftPercent = 80,
    storageKey = null
  } = options

  const leftPanelWidth = ref(initialLeftPercent)
  const isResizing = ref(false)
  const containerRef = ref(null)

  // Lade gespeicherte Position
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
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', stopResize)
  }

  const onMouseMove = (event) => {
    if (!isResizing.value || !containerRef.value) return

    const containerRect = containerRef.value.getBoundingClientRect()
    const containerWidth = containerRect.width
    const mouseX = event.clientX - containerRect.left

    // Berechne Prozent
    let percent = (mouseX / containerWidth) * 100

    // Clamp zwischen min und max
    percent = Math.max(minLeftPercent, Math.min(maxLeftPercent, percent))

    leftPanelWidth.value = percent
  }

  const stopResize = () => {
    isResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''

    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', stopResize)

    // Speichere Position
    if (storageKey) {
      localStorage.setItem(storageKey, leftPanelWidth.value.toString())
    }
  }

  // Cleanup bei Unmount
  onUnmounted(() => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', stopResize)
  })

  // CSS Styles für die Panels
  const leftPanelStyle = () => ({
    width: `calc(${leftPanelWidth.value}% - 3px)`,
    flexShrink: 0
  })

  const rightPanelStyle = () => ({
    width: `calc(${100 - leftPanelWidth.value}% - 3px)`,
    flexShrink: 0
  })

  return {
    leftPanelWidth,
    isResizing,
    containerRef,
    startResize,
    leftPanelStyle,
    rightPanelStyle
  }
}
