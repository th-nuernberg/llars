<!--
  TreeStackPanel.vue

  Unified collapsible panel component for the tree stack.
  Provides consistent header styling with collapse toggle.
-->
<template>
  <div
    class="tree-stack-panel"
    :class="{ collapsed: collapsed }"
    :style="panelStyle"
  >
    <!-- Header -->
    <div class="panel-header" @click="handleHeaderClick">
      <LIcon size="16" class="panel-icon">{{ icon }}</LIcon>
      <span class="panel-title">{{ title }}</span>
      <span v-if="badge" class="panel-badge" :class="badgeVariant">{{ badge }}</span>
      <v-spacer />
      <div class="panel-actions" @click.stop>
        <slot name="actions" />
      </div>
      <button
        class="collapse-btn"
        type="button"
        :title="collapsed ? $t('common.expand') : $t('common.collapse')"
        @click.stop="$emit('update:collapsed', !collapsed)"
      >
        <LIcon size="16">{{ collapsed ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</LIcon>
      </button>
    </div>

    <!-- Content (hidden when collapsed) -->
    <div v-show="!collapsed" class="panel-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    default: 'mdi-folder'
  },
  collapsed: {
    type: Boolean,
    default: false
  },
  badge: {
    type: [String, Number],
    default: null
  },
  badgeVariant: {
    type: String,
    default: 'warning' // warning, danger, info, success
  },
  minHeight: {
    type: Number,
    default: 100
  },
  height: {
    type: Number,
    default: null
  }
})

defineEmits(['update:collapsed'])

const panelStyle = computed(() => {
  if (props.collapsed) return {}
  if (props.height) {
    return { height: `${props.height}px` }
  }
  return { minHeight: `${props.minHeight}px` }
})

function handleHeaderClick() {
  // Optional: could toggle on header click
}
</script>

<style scoped>
.tree-stack-panel {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 8px 2px 8px 2px;
  overflow: hidden;
  flex-shrink: 0;
}

.tree-stack-panel:not(.collapsed) {
  flex: 1;
  min-height: 0;
}

.tree-stack-panel.collapsed {
  flex: none;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  cursor: default;
  user-select: none;
  flex-shrink: 0;
}

.tree-stack-panel.collapsed .panel-header {
  border-bottom: none;
}

.panel-icon {
  color: var(--llars-primary, #b0ca97);
  flex-shrink: 0;
}

.panel-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.panel-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  color: white;
}

.panel-badge.warning {
  background: rgb(var(--v-theme-warning));
}

.panel-badge.danger {
  background: rgb(var(--v-theme-error));
}

.panel-badge.info {
  background: rgb(var(--v-theme-info));
}

.panel-badge.success {
  background: rgb(var(--v-theme-success));
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.panel-actions :deep(.v-btn) {
  width: 24px !important;
  height: 24px !important;
  min-width: 24px !important;
}

.collapse-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
  border-radius: 4px;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.panel-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
