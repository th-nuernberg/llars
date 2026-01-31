/**
 * useAssistantState - Panel state management for FloatingAIAssistant
 *
 * Manages position, size, and minimized state with localStorage persistence.
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'

const STORAGE_KEY_POSITION = 'latex-ai-assistant-position'
const STORAGE_KEY_SIZE = 'latex-ai-assistant-size'
const STORAGE_KEY_MINIMIZED = 'latex-ai-assistant-minimized'

export function useAssistantState() {
  // State
  const position = ref({ x: 0, y: 100 })
  const size = ref({ width: 420, height: 520 })
  const isMinimized = ref(false)
  const isDragging = ref(false)
  const isResizing = ref(false)
  const dragOffset = ref({ x: 0, y: 0 })

  // Computed
  const panelStyle = computed(() => ({
    left: `${position.value.x}px`,
    top: `${position.value.y}px`,
    width: `${size.value.width}px`,
    height: `${size.value.height}px`
  }))

  // Load from localStorage
  function loadState() {
    try {
      const storedPos = localStorage.getItem(STORAGE_KEY_POSITION)
      if (storedPos) {
        const parsed = JSON.parse(storedPos)
        position.value = {
          x: Math.max(0, Math.min(window.innerWidth - 100, parsed.x || 0)),
          y: Math.max(0, Math.min(window.innerHeight - 100, parsed.y || 100))
        }
      } else {
        // Default position: right side of screen
        position.value = {
          x: window.innerWidth - 450,
          y: 100
        }
      }

      const storedSize = localStorage.getItem(STORAGE_KEY_SIZE)
      if (storedSize) {
        const parsed = JSON.parse(storedSize)
        size.value = {
          width: Math.max(350, Math.min(800, parsed.width || 420)),
          height: Math.max(400, Math.min(800, parsed.height || 520))
        }
      }

      const storedMinimized = localStorage.getItem(STORAGE_KEY_MINIMIZED)
      if (storedMinimized) {
        isMinimized.value = storedMinimized === 'true'
      }
    } catch (e) {
      console.warn('Failed to load assistant state:', e)
    }
  }

  // Save to localStorage
  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY_POSITION, JSON.stringify(position.value))
      localStorage.setItem(STORAGE_KEY_SIZE, JSON.stringify(size.value))
      localStorage.setItem(STORAGE_KEY_MINIMIZED, String(isMinimized.value))
    } catch (e) {
      console.warn('Failed to save assistant state:', e)
    }
  }

  // Drag handlers
  function startDrag(e) {
    if (e.target.closest('.header-actions') || e.target.closest('button')) return

    isDragging.value = true
    dragOffset.value = {
      x: e.clientX - position.value.x,
      y: e.clientY - position.value.y
    }

    document.addEventListener('mousemove', onDrag)
    document.addEventListener('mouseup', stopDrag)
  }

  function onDrag(e) {
    if (!isDragging.value) return

    const maxX = window.innerWidth - size.value.width
    const maxY = window.innerHeight - size.value.height

    position.value = {
      x: Math.max(0, Math.min(maxX, e.clientX - dragOffset.value.x)),
      y: Math.max(0, Math.min(maxY, e.clientY - dragOffset.value.y))
    }
  }

  function stopDrag() {
    isDragging.value = false
    document.removeEventListener('mousemove', onDrag)
    document.removeEventListener('mouseup', stopDrag)
    saveState()
  }

  // Resize handlers
  function startResize(e) {
    e.preventDefault()
    isResizing.value = true
    document.addEventListener('mousemove', onResize)
    document.addEventListener('mouseup', stopResize)
  }

  function onResize(e) {
    if (!isResizing.value) return

    const newWidth = Math.max(350, Math.min(800, e.clientX - position.value.x))
    const newHeight = Math.max(400, Math.min(800, e.clientY - position.value.y))

    size.value = { width: newWidth, height: newHeight }
  }

  function stopResize() {
    isResizing.value = false
    document.removeEventListener('mousemove', onResize)
    document.removeEventListener('mouseup', stopResize)
    saveState()
  }

  // Toggle minimize
  function toggleMinimize() {
    isMinimized.value = !isMinimized.value
    saveState()
  }

  function minimize() {
    isMinimized.value = true
    saveState()
  }

  function maximize() {
    isMinimized.value = false
    saveState()
  }

  // Cleanup
  function cleanup() {
    document.removeEventListener('mousemove', onDrag)
    document.removeEventListener('mouseup', stopDrag)
    document.removeEventListener('mousemove', onResize)
    document.removeEventListener('mouseup', stopResize)
  }

  onMounted(() => {
    loadState()
  })

  onUnmounted(() => {
    cleanup()
  })

  return {
    // State
    position,
    size,
    isMinimized,
    isDragging,
    isResizing,

    // Computed
    panelStyle,

    // Methods
    loadState,
    saveState,
    startDrag,
    startResize,
    toggleMinimize,
    minimize,
    maximize,
    cleanup
  }
}

export default useAssistantState
