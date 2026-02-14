<template>
  <div class="l-tabs-container">
    <div
      class="l-tabs"
      :class="[tabsClasses, { 'l-tabs--no-animate': !pillAnimating }]"
      ref="tabsRef"
    >
      <!-- Sliding pill indicator for pill variant -->
      <div
        v-if="variant === 'pill'"
        class="l-tabs__pill"
      />
      <button
        v-for="(tab, index) in tabs"
        :key="tab.value || index"
        :ref="el => setTabRef(el, index)"
        class="l-tab"
        :class="{ 'l-tab--active': modelValue === (tab.value || index) }"
        @click="selectTab(tab.value || index)"
      >
        <LIcon v-if="tab.icon" class="l-tab__icon">{{ tab.icon }}</LIcon>
        <span class="l-tab__label">{{ tab.label }}</span>
        <span v-if="tab.badge !== undefined" class="l-tab__badge">{{ tab.badge }}</span>
      </button>
    </div>
    <div v-if="$slots.default" class="l-tabs-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
/**
 * LTabs - LLARS Global Tabs Component
 *
 * A modern tab navigation component with the signature LLARS styling.
 * Features the primary color background with white text and smooth transitions.
 *
 * Props:
 *   - modelValue: Current active tab value (v-model)
 *   - tabs: Array of tab definitions { value, label, icon?, badge? }
 *   - variant: 'filled' (default) | 'outlined' | 'underlined' | 'pill'
 *   - grow: Boolean - tabs take equal width
 *
 * Events:
 *   - update:modelValue: Emitted when tab changes
 *
 * Usage:
 *   <LTabs
 *     v-model="activeTab"
 *     :tabs="[
 *       { value: 'chatbots', label: 'Chatbots', icon: 'mdi-robot' },
 *       { value: 'collections', label: 'Collections', icon: 'mdi-folder-multiple' },
 *       { value: 'documents', label: 'Dokumente', icon: 'mdi-file-document-multiple' }
 *     ]"
 *     variant="pill"
 *   />
 */
import { computed, ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: 0
  },
  tabs: {
    type: Array,
    required: true,
    validator: (v) => v.every(tab => tab.label)
  },
  variant: {
    type: String,
    default: 'filled',
    validator: (v) => ['filled', 'outlined', 'underlined', 'pill'].includes(v)
  },
  grow: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const tabsRef = ref(null)
const tabElements = ref([])
const pillAnimating = ref(false)
let resizeObserver = null

const tabsClasses = computed(() => ({
  [`l-tabs--${props.variant}`]: true,
  'l-tabs--grow': props.grow
}))

function setTabRef(el, index) {
  if (el) tabElements.value[index] = el
}

function selectTab(value) {
  emit('update:modelValue', value)
}

// Pill positioning via CSS custom properties on the container
function movePill() {
  if (props.variant !== 'pill' || !tabsRef.value) return
  const activeIndex = props.tabs.findIndex(
    (tab, i) => (tab.value || i) === props.modelValue
  )
  const el = tabElements.value[activeIndex]
  if (!el) return

  tabsRef.value.style.setProperty('--pill-x', `${el.offsetLeft}px`)
  tabsRef.value.style.setProperty('--pill-w', `${el.offsetWidth}px`)
}

// Track changes - enable animation after first render
watch(() => props.modelValue, () => {
  pillAnimating.value = true
  nextTick(movePill)
})
watch(() => props.tabs, () => nextTick(movePill), { deep: true })

onMounted(() => {
  // Double nextTick to ensure DOM is fully rendered including fonts
  nextTick(() => {
    nextTick(() => {
      movePill()
      if (tabsRef.value && props.variant === 'pill') {
        resizeObserver = new ResizeObserver(() => movePill())
        resizeObserver.observe(tabsRef.value)
      }
    })
  })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})
</script>

<style scoped>
/* Container */
.l-tabs-container {
  display: flex;
  flex-direction: column;
}

/* Tabs Bar - Uses CSS Variables for automatic Light/Dark mode */
.l-tabs {
  display: flex;
  gap: 4px;
  padding: 6px;
  background: var(--llars-primary);
  border-radius: var(--llars-radius, 16px 4px 16px 4px);
  overflow-x: auto;
  scrollbar-width: thin;
  margin-bottom: 16px;
}

/* Dark mode: use a darker, more subtle version */
.v-theme--dark .l-tabs {
  background: color-mix(in srgb, var(--llars-primary) 35%, #1e1e1e);
}

.v-theme--dark .l-tabs--outlined {
  background: transparent;
  border-color: color-mix(in srgb, var(--llars-primary) 60%, #1e1e1e);
}

.l-tabs--grow {
  gap: 0;
}

.l-tabs--grow .l-tab {
  flex: 1;
}

/* ═══════════════════════════════════════════
   Pill Variant - Sliding indicator
   ═══════════════════════════════════════════ */
.l-tabs--pill {
  background: rgba(var(--v-theme-on-surface), 0.06);
  padding: 4px;
  position: relative;
  gap: 2px;
}

.v-theme--dark .l-tabs--pill {
  background: rgba(255, 255, 255, 0.08);
}

/* The sliding pill - reads position from CSS custom properties on parent */
.l-tabs__pill {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 0;
  transform: translateX(var(--pill-x, 0));
  width: var(--pill-w, 0px);
  background: var(--llars-primary);
  border-radius: 12px 3px 12px 3px;
  z-index: 0;
  pointer-events: none;
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.15, 1),
              width 0.3s cubic-bezier(0.4, 0, 0.15, 1);
  will-change: transform, width;
}

/* Disable animation on initial render */
.l-tabs--no-animate .l-tabs__pill {
  transition: none;
}

.v-theme--dark .l-tabs__pill {
  background: color-mix(in srgb, var(--llars-primary) 65%, #2a2a2a);
}

/* Pill variant tab overrides */
.l-tabs--pill .l-tab {
  position: relative;
  z-index: 1;
  color: rgba(var(--v-theme-on-surface), 0.55);
  background: transparent;
  border-radius: 12px 3px 12px 3px;
  padding: 10px 20px;
  text-transform: none;
  letter-spacing: 0.01em;
  font-weight: 500;
  font-size: 0.875rem;
}

.l-tabs--pill .l-tab:hover:not(.l-tab--active) {
  color: rgba(var(--v-theme-on-surface), 0.8);
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.l-tabs--pill .l-tab--active {
  color: white;
  background: transparent;
  font-weight: 600;
}

.v-theme--dark .l-tabs--pill .l-tab {
  color: rgba(255, 255, 255, 0.5);
}

.v-theme--dark .l-tabs--pill .l-tab:hover:not(.l-tab--active) {
  color: rgba(255, 255, 255, 0.75);
  background: rgba(255, 255, 255, 0.04);
}

.v-theme--dark .l-tabs--pill .l-tab--active {
  color: white;
}

/* Pill variant badge */
.l-tabs--pill .l-tab__badge {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.l-tabs--pill .l-tab--active .l-tab__badge {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

/* ═══════════════════════════════════════════
   Outlined Variant
   ═══════════════════════════════════════════ */
.l-tabs--outlined {
  background: transparent;
  border: 2px solid var(--llars-primary);
  padding: 4px;
}

.l-tabs--outlined .l-tab {
  color: var(--llars-primary);
}

.l-tabs--outlined .l-tab--active {
  background: var(--llars-primary);
  color: white;
}

.l-tabs--outlined .l-tab:hover:not(.l-tab--active) {
  background: rgba(var(--v-theme-on-surface), 0.08);
}

/* ═══════════════════════════════════════════
   Underlined Variant
   ═══════════════════════════════════════════ */
.l-tabs--underlined {
  background: transparent;
  border-radius: 0;
  border-bottom: 2px solid rgba(var(--v-theme-on-surface), 0.12);
  padding: 0;
  gap: 0;
}

.l-tabs--underlined .l-tab {
  color: rgba(var(--v-theme-on-surface), 0.7);
  border-radius: 0;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  padding: 12px 20px;
}

.l-tabs--underlined .l-tab--active {
  color: var(--llars-primary);
  background: transparent;
  border-bottom-color: var(--llars-primary);
}

.l-tabs--underlined .l-tab:hover:not(.l-tab--active) {
  background: rgba(var(--v-theme-on-surface), 0.04);
  color: rgb(var(--v-theme-on-surface));
}

/* ═══════════════════════════════════════════
   Individual Tab (base / filled)
   ═══════════════════════════════════════════ */
.l-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.9rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  border-radius: 12px 3px 12px 3px;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.l-tab:hover:not(.l-tab--active) {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.l-tab--active {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  font-weight: 600;
}

/* Dark mode: brighter active state for better contrast */
.v-theme--dark .l-tab--active {
  background: color-mix(in srgb, var(--llars-primary) 50%, transparent);
}

/* Tab Icon */
.l-tab__icon {
  font-size: 1.1em;
  opacity: 0.9;
}

.l-tab--active .l-tab__icon {
  opacity: 1;
}

/* Tab Label */
.l-tab__label {
  line-height: 1;
}

/* Tab Badge */
.l-tab__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.l-tab--active .l-tab__badge {
  background: rgba(255, 255, 255, 0.4);
}

/* Content Area */
.l-tabs-content {
  padding-top: 16px;
}

/* Scrollbar Styling */
.l-tabs::-webkit-scrollbar {
  height: 4px;
}

.l-tabs::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.l-tabs::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.l-tabs::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* Pill variant scrollbar (dark on light) */
.l-tabs--pill::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.l-tabs--pill::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
}

.l-tabs--pill::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.25);
}
</style>
