<!--
  LFloatingWindow.vue

  Global LLARS Design System floating window component.
  Features:
  - Draggable header
  - Resizable (with resize handle)
  - Persists position/size to localStorage
  - Customizable header with icon, title, tags, and action buttons
  - Content slot
  - Optional footer slot
  - LLARS asymmetric border-radius design
  - Multiple color themes
-->
<template>
  <Teleport to="body">
    <Transition name="floating-window">
      <div
        v-if="modelValue"
        ref="windowRef"
        class="l-floating-window"
        :class="[
          `theme-${color}`,
          { dragging: isDragging, resizing: isResizing }
        ]"
        :style="windowStyle"
      >
        <!-- Header -->
        <div
          class="floating-window-header"
          @mousedown="startDrag"
        >
          <div class="header-left">
            <div v-if="icon" class="header-icon" :class="`icon-${color}`">
              <LIcon :size="iconSize">{{ icon }}</LIcon>
            </div>
            <span class="header-title">{{ title }}</span>
          </div>

          <!-- Tags Slot (between title and actions) -->
          <div v-if="$slots.tags" class="header-tags">
            <slot name="tags" />
          </div>

          <v-spacer />

          <!-- Header Actions Slot -->
          <div class="header-actions">
            <slot name="header-actions" />

            <!-- Built-in action buttons -->
            <LIconBtn
              v-if="showRefresh"
              icon="mdi-refresh"
              size="small"
              :tooltip="refreshTooltip || $t('common.refresh')"
              :loading="refreshLoading"
              @click="$emit('refresh')"
            />
            <LIconBtn
              v-if="showMinimize"
              icon="mdi-window-minimize"
              size="small"
              :tooltip="$t('common.minimize')"
              @click="$emit('minimize')"
            />
            <LIconBtn
              v-if="showMaximize"
              :icon="isMaximized ? 'mdi-window-restore' : 'mdi-window-maximize'"
              size="small"
              :tooltip="isMaximized ? $t('common.restore') : $t('common.maximize')"
              @click="toggleMaximize"
            />
            <LIconBtn
              v-if="showClose"
              icon="mdi-close"
              size="small"
              :tooltip="$t('common.close')"
              @click="close"
            />
          </div>
        </div>

        <!-- Content -->
        <div class="floating-window-content">
          <slot />
        </div>

        <!-- Footer (optional) -->
        <div v-if="$slots.footer" class="floating-window-footer">
          <slot name="footer" />
        </div>

        <!-- Resize Handle -->
        <div
          v-if="resizable && !isMaximized"
          class="resize-handle"
          @mousedown="startResize"
        />
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
/**
 * LFloatingWindow - Global LLARS Design System Floating Window Component
 *
 * A reusable, draggable, resizable floating window that follows the LLARS design system.
 * Use this component whenever you need a floating panel, dialog, or tool window.
 *
 * @component
 *
 * @example Basic usage
 * ```vue
 * <LFloatingWindow
 *   v-model="showWindow"
 *   title="My Window"
 *   icon="mdi-cog"
 *   color="primary"
 * >
 *   <p>Window content here</p>
 * </LFloatingWindow>
 * ```
 *
 * @example With tags, footer, and persistence
 * ```vue
 * <LFloatingWindow
 *   v-model="showWindow"
 *   title="Git Panel"
 *   icon="mdi-source-branch"
 *   color="primary"
 *   storage-key="my-git-panel"
 *   :show-refresh="true"
 *   @refresh="handleRefresh"
 * >
 *   <template #tags>
 *     <LTag variant="warning">3 changes</LTag>
 *   </template>
 *
 *   <div>Main content</div>
 *
 *   <template #footer>
 *     <v-text-field v-model="message" />
 *     <LBtn variant="primary">Commit</LBtn>
 *   </template>
 * </LFloatingWindow>
 * ```
 *
 * @slot default - Main window content
 * @slot tags - Status tags displayed in header between title and actions
 * @slot header-actions - Custom action buttons before built-in buttons
 * @slot footer - Optional footer area (e.g., for input fields and submit buttons)
 *
 * @emits update:modelValue - When visibility changes
 * @emits refresh - When refresh button is clicked
 * @emits minimize - When minimize button is clicked
 * @emits maximize - When window is maximized
 * @emits restore - When window is restored from maximized state
 * @emits close - When window is closed
 * @emits drag-start - When dragging starts
 * @emits drag-end - When dragging ends
 * @emits resize-start - When resizing starts
 * @emits resize-end - When resizing ends
 *
 * Color Themes:
 * - primary: LLARS green (#b0ca97) - Default, for main features
 * - secondary: LLARS gold (#D1BC8A) - Secondary features
 * - accent: LLARS teal (#88c4c8) - Highlighted features
 * - success: Green (#98d4bb) - Success states
 * - warning: Yellow (#f0c674) - Warning states
 * - danger: Red (#e8a087) - Danger/delete actions
 * - ai: Purple (#9B59B6) - AI-related features
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  /** v-model for visibility */
  modelValue: {
    type: Boolean,
    default: false
  },
  /** Window title */
  title: {
    type: String,
    required: true
  },
  /** Header icon (mdi icon name) */
  icon: {
    type: String,
    default: null
  },
  /** Icon size */
  iconSize: {
    type: [Number, String],
    default: 18
  },
  /** Color theme: primary, secondary, accent, success, warning, danger */
  color: {
    type: String,
    default: 'primary',
    validator: v => ['primary', 'secondary', 'accent', 'success', 'warning', 'danger', 'ai'].includes(v)
  },
  /** Initial width */
  width: {
    type: [Number, String],
    default: 400
  },
  /** Initial height */
  height: {
    type: [Number, String],
    default: 300
  },
  /** Minimum width */
  minWidth: {
    type: Number,
    default: 300
  },
  /** Minimum height */
  minHeight: {
    type: Number,
    default: 200
  },
  /** Maximum width (null = viewport width - 40px) */
  maxWidth: {
    type: Number,
    default: null
  },
  /** Maximum height (null = viewport height - 60px) */
  maxHeight: {
    type: Number,
    default: null
  },
  /** Allow resizing */
  resizable: {
    type: Boolean,
    default: true
  },
  /** LocalStorage key for persisting position/size */
  storageKey: {
    type: String,
    default: null
  },
  /** Initial X position (null = center) */
  initialX: {
    type: Number,
    default: null
  },
  /** Initial Y position (null = center) */
  initialY: {
    type: Number,
    default: null
  },
  /** Show close button */
  showClose: {
    type: Boolean,
    default: true
  },
  /** Show minimize button */
  showMinimize: {
    type: Boolean,
    default: false
  },
  /** Show maximize button */
  showMaximize: {
    type: Boolean,
    default: false
  },
  /** Show refresh button */
  showRefresh: {
    type: Boolean,
    default: false
  },
  /** Refresh button loading state */
  refreshLoading: {
    type: Boolean,
    default: false
  },
  /** Refresh button tooltip */
  refreshTooltip: {
    type: String,
    default: null
  },
  /** Z-index */
  zIndex: {
    type: Number,
    default: 9999
  }
})

const emit = defineEmits([
  'update:modelValue',
  'refresh',
  'minimize',
  'maximize',
  'restore',
  'close',
  'drag-start',
  'drag-end',
  'resize-start',
  'resize-end'
])

const { t } = useI18n()

// Refs
const windowRef = ref(null)
const position = ref({ x: 100, y: 100 })
const size = ref({ width: 400, height: 300 })
const isDragging = ref(false)
const isResizing = ref(false)
const isMaximized = ref(false)
const dragOffset = ref({ x: 0, y: 0 })
const preMaximizeState = ref(null)

// Computed
const windowStyle = computed(() => {
  if (isMaximized.value) {
    return {
      left: '20px',
      top: '20px',
      width: 'calc(100vw - 40px)',
      height: 'calc(100vh - 40px)',
      zIndex: props.zIndex
    }
  }
  return {
    left: `${Math.max(10, position.value.x)}px`,
    top: `${Math.max(10, position.value.y)}px`,
    width: `${size.value.width}px`,
    height: `${size.value.height}px`,
    minWidth: `${props.minWidth}px`,
    minHeight: `${props.minHeight}px`,
    maxWidth: props.maxWidth ? `${props.maxWidth}px` : 'calc(100vw - 40px)',
    maxHeight: props.maxHeight ? `${props.maxHeight}px` : 'calc(100vh - 60px)',
    zIndex: props.zIndex
  }
})

// Storage functions
function loadSavedState() {
  if (!props.storageKey) return null
  try {
    const saved = localStorage.getItem(props.storageKey)
    if (saved) return JSON.parse(saved)
  } catch (e) {
    console.warn('[LFloatingWindow] Failed to load saved state:', e)
  }
  return null
}

function saveState() {
  if (!props.storageKey || isMaximized.value) return
  try {
    const state = {
      x: position.value.x,
      y: position.value.y,
      width: size.value.width,
      height: size.value.height
    }
    localStorage.setItem(props.storageKey, JSON.stringify(state))
  } catch (e) {
    console.warn('[LFloatingWindow] Failed to save state:', e)
  }
}

// Drag functions
function startDrag(e) {
  if (e.button !== 0 || isMaximized.value) return
  isDragging.value = true
  const rect = windowRef.value.getBoundingClientRect()
  dragOffset.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  emit('drag-start')
  e.preventDefault()
}

function onDrag(e) {
  if (!isDragging.value) return
  position.value = {
    x: Math.max(0, e.clientX - dragOffset.value.x),
    y: Math.max(0, e.clientY - dragOffset.value.y)
  }
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  saveState()
  emit('drag-end')
}

// Resize functions
function startResize(e) {
  if (e.button !== 0) return
  isResizing.value = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  emit('resize-start')
  e.preventDefault()
}

function onResize(e) {
  if (!isResizing.value || !windowRef.value) return
  const rect = windowRef.value.getBoundingClientRect()
  const newWidth = Math.max(props.minWidth, e.clientX - rect.left)
  const newHeight = Math.max(props.minHeight, e.clientY - rect.top)
  size.value = { width: newWidth, height: newHeight }
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  saveState()
  emit('resize-end')
}

// Maximize/restore
function toggleMaximize() {
  if (isMaximized.value) {
    // Restore
    if (preMaximizeState.value) {
      position.value = preMaximizeState.value.position
      size.value = preMaximizeState.value.size
    }
    isMaximized.value = false
    emit('restore')
  } else {
    // Maximize
    preMaximizeState.value = {
      position: { ...position.value },
      size: { ...size.value }
    }
    isMaximized.value = true
    emit('maximize')
  }
}

// Close
function close() {
  emit('update:modelValue', false)
  emit('close')
}

// Initialize position/size
function initializeWindow() {
  const saved = loadSavedState()

  if (saved) {
    position.value = { x: saved.x, y: saved.y }
    size.value = { width: saved.width, height: saved.height }
  } else {
    // Parse initial size
    const w = typeof props.width === 'string' ? parseInt(props.width) : props.width
    const h = typeof props.height === 'string' ? parseInt(props.height) : props.height
    size.value = { width: w, height: h }

    // Position
    if (props.initialX !== null && props.initialY !== null) {
      position.value = { x: props.initialX, y: props.initialY }
    } else {
      // Center the window
      position.value = {
        x: Math.max(100, (window.innerWidth - w) / 2),
        y: Math.max(50, (window.innerHeight - h) / 2)
      }
    }
  }
}

// Watch visibility
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    initializeWindow()
  }
})

// Cleanup
onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})

// Expose for parent access
defineExpose({
  position,
  size,
  isMaximized,
  toggleMaximize,
  close
})
</script>

<style scoped>
.l-floating-window {
  position: fixed;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 2px solid var(--window-border-color, var(--llars-primary, #b0ca97));
  border-radius: 16px 4px 16px 4px; /* LLARS signature asymmetric */
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15), 0 4px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.l-floating-window.dragging {
  cursor: grabbing;
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.2), 0 6px 24px rgba(0, 0, 0, 0.12);
}

.l-floating-window.resizing {
  transition: none;
}

/* Color themes */
.l-floating-window.theme-primary {
  --window-border-color: var(--llars-primary, #b0ca97);
  --window-accent-color: var(--llars-primary, #b0ca97);
}

.l-floating-window.theme-secondary {
  --window-border-color: var(--llars-secondary, #D1BC8A);
  --window-accent-color: var(--llars-secondary, #D1BC8A);
}

.l-floating-window.theme-accent {
  --window-border-color: var(--llars-accent, #88c4c8);
  --window-accent-color: var(--llars-accent, #88c4c8);
}

.l-floating-window.theme-success {
  --window-border-color: var(--llars-success, #98d4bb);
  --window-accent-color: var(--llars-success, #98d4bb);
}

.l-floating-window.theme-warning {
  --window-border-color: var(--llars-warning, #f0c674);
  --window-accent-color: var(--llars-warning, #f0c674);
}

.l-floating-window.theme-danger {
  --window-border-color: var(--llars-danger, #e8a087);
  --window-accent-color: var(--llars-danger, #e8a087);
}

.l-floating-window.theme-ai {
  --window-border-color: #9B59B6;
  --window-accent-color: #9B59B6;
}

/* Header */
.floating-window-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--window-accent-color) 15%, transparent) 0%,
    color-mix(in srgb, var(--window-accent-color) 5%, transparent) 100%
  );
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  cursor: grab;
  user-select: none;
  flex-shrink: 0;
}

.floating-window-header:active {
  cursor: grabbing;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px 2px 8px 2px; /* Mini LLARS signature */
  background: linear-gradient(135deg, var(--window-accent-color) 0%, color-mix(in srgb, var(--window-accent-color) 80%, #000) 100%);
  color: white;
  flex-shrink: 0;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* Content */
.floating-window-content {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

/* Footer */
.floating-window-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

/* Resize Handle */
.resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 20px;
  height: 20px;
  cursor: se-resize;
  background: linear-gradient(
    135deg,
    transparent 50%,
    color-mix(in srgb, var(--window-accent-color) 40%, transparent) 50%
  );
  border-radius: 0 0 14px 0;
}

.resize-handle:hover {
  background: linear-gradient(
    135deg,
    transparent 50%,
    color-mix(in srgb, var(--window-accent-color) 60%, transparent) 50%
  );
}

/* Transition */
.floating-window-enter-active,
.floating-window-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.floating-window-enter-from,
.floating-window-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

/* Dark mode adjustments */
.v-theme--dark .l-floating-window {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(0, 0, 0, 0.25);
}

.v-theme--dark .l-floating-window.dragging {
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.5), 0 6px 24px rgba(0, 0, 0, 0.35);
}
</style>
