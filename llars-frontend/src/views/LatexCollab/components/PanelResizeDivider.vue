<!--
  PanelResizeDivider.vue

  Horizontal resize divider between panels in the tree stack.
  Allows users to adjust panel heights by dragging.
-->
<template>
  <div
    class="panel-resize-divider"
    :class="{ resizing: isResizing }"
    @mousedown="startResize"
  >
    <div class="resize-handle">
      <div class="handle-dots">
        <span /><span /><span />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const emit = defineEmits(['resize-start', 'resize-move', 'resize-end'])

const isResizing = ref(false)
const startY = ref(0)

function startResize(e) {
  e.preventDefault()
  isResizing.value = true
  startY.value = e.clientY
  emit('resize-start', { y: e.clientY })

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  document.body.style.cursor = 'row-resize'
  document.body.style.userSelect = 'none'
}

function onMouseMove(e) {
  if (!isResizing.value) return
  const deltaY = e.clientY - startY.value
  emit('resize-move', { y: e.clientY, deltaY })
}

function onMouseUp(e) {
  if (!isResizing.value) return
  isResizing.value = false
  emit('resize-end', { y: e.clientY })

  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
})
</script>

<style scoped>
.panel-resize-divider {
  height: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: row-resize;
  position: relative;
  z-index: 10;
}

.panel-resize-divider:hover,
.panel-resize-divider.resizing {
  background: rgba(var(--v-theme-primary), 0.08);
}

.resize-handle {
  width: 40px;
  height: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.panel-resize-divider:hover .resize-handle,
.panel-resize-divider.resizing .resize-handle {
  opacity: 1;
}

.handle-dots {
  display: flex;
  gap: 3px;
}

.handle-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.3);
}

.panel-resize-divider:hover .handle-dots span,
.panel-resize-divider.resizing .handle-dots span {
  background: var(--llars-primary, #b0ca97);
}
</style>
