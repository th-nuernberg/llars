<template>
  <div class="l-tabs-container">
    <div class="l-tabs" :class="tabsClasses">
      <button
        v-for="(tab, index) in tabs"
        :key="tab.value || index"
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
 *   - variant: 'filled' (default) | 'outlined' | 'underlined'
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
 *   />
 */
import { computed } from 'vue'

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
    validator: (v) => ['filled', 'outlined', 'underlined'].includes(v)
  },
  grow: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const tabsClasses = computed(() => ({
  [`l-tabs--${props.variant}`]: true,
  'l-tabs--grow': props.grow
}))

function selectTab(value) {
  emit('update:modelValue', value)
}
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

/* Outlined Variant */
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

/* Underlined Variant */
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

/* Individual Tab */
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
</style>
