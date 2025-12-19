<template>
  <div class="l-action-group" :class="groupClasses">
    <template v-for="(action, index) in resolvedActions" :key="action.key || index">
      <!-- Slot for custom action content (e.g., dialogs with trigger buttons) -->
      <slot v-if="$slots[action.key]" :name="action.key" :action="action" />

      <!-- Standard action button -->
      <LIconBtn
        v-else
        :icon="action.icon"
        :variant="action.variant"
        :tooltip="action.tooltip"
        :loading="action.loading"
        :disabled="action.disabled"
        :size="size"
        @click.stop="handleAction(action)"
      />
    </template>
  </div>
</template>

<script setup>
/**
 * LActionGroup - LLARS Global Action Button Group Component
 *
 * A consistent action button group for tables and cards.
 * Supports preset actions and custom configurations.
 *
 * Preset actions:
 *   - view: View details (mdi-eye)
 *   - edit: Edit item (mdi-pencil)
 *   - delete: Delete item (mdi-delete, danger)
 *   - stats: View statistics (mdi-chart-bar)
 *   - download: Download item (mdi-download)
 *   - copy: Copy item (mdi-content-copy)
 *   - lock: Lock/disable item (mdi-lock)
 *   - unlock: Unlock/enable item (mdi-lock-open-variant)
 *   - refresh: Refresh/reload (mdi-refresh)
 *   - close: Close/dismiss (mdi-close)
 *
 * Usage:
 *   <!-- Simple preset array -->
 *   <LActionGroup :actions="['view', 'edit', 'delete']" @action="handleAction" />
 *
 *   <!-- Mixed presets and custom -->
 *   <LActionGroup
 *     :actions="[
 *       'stats',
 *       { key: 'custom', icon: 'mdi-star', tooltip: 'Favorit' },
 *       'delete'
 *     ]"
 *     @action="handleAction"
 *   />
 *
 *   <!-- With custom slot (e.g., for dialog trigger) -->
 *   <LActionGroup :actions="['stats', 'edit', 'delete']" @action="handleAction">
 *     <template #edit="{ action }">
 *       <MyEditDialog :item="item" />
 *     </template>
 *   </LActionGroup>
 */
import { computed } from 'vue'

const props = defineProps({
  /**
   * Array of action configurations
   * Can be preset names (strings) or custom action objects
   */
  actions: {
    type: Array,
    required: true,
    validator: (v) => v.every(a => typeof a === 'string' || typeof a === 'object')
  },

  /**
   * Button size (applies to all buttons)
   */
  size: {
    type: String,
    default: 'small',
    validator: (v) => ['x-small', 'small', 'default', 'large', 'x-large'].includes(v)
  },

  /**
   * Gap between buttons
   */
  gap: {
    type: String,
    default: 'sm',
    validator: (v) => ['none', 'xs', 'sm', 'md', 'lg'].includes(v)
  },

  /**
   * Alignment
   */
  align: {
    type: String,
    default: 'end',
    validator: (v) => ['start', 'center', 'end'].includes(v)
  }
})

const emit = defineEmits(['action'])

// Preset action definitions
const presets = {
  view: {
    key: 'view',
    icon: 'mdi-eye',
    tooltip: 'Anzeigen',
    variant: 'default'
  },
  edit: {
    key: 'edit',
    icon: 'mdi-pencil',
    tooltip: 'Bearbeiten',
    variant: 'default'
  },
  delete: {
    key: 'delete',
    icon: 'mdi-delete',
    tooltip: 'Löschen',
    variant: 'danger'
  },
  stats: {
    key: 'stats',
    icon: 'mdi-chart-bar',
    tooltip: 'Statistiken',
    variant: 'default'
  },
  download: {
    key: 'download',
    icon: 'mdi-download',
    tooltip: 'Herunterladen',
    variant: 'default'
  },
  copy: {
    key: 'copy',
    icon: 'mdi-content-copy',
    tooltip: 'Kopieren',
    variant: 'default'
  },
  lock: {
    key: 'lock',
    icon: 'mdi-lock',
    tooltip: 'Sperren',
    variant: 'warning'
  },
  unlock: {
    key: 'unlock',
    icon: 'mdi-lock-open-variant',
    tooltip: 'Entsperren',
    variant: 'success'
  },
  refresh: {
    key: 'refresh',
    icon: 'mdi-refresh',
    tooltip: 'Aktualisieren',
    variant: 'default'
  },
  close: {
    key: 'close',
    icon: 'mdi-close',
    tooltip: 'Schließen',
    variant: 'default'
  },
  add: {
    key: 'add',
    icon: 'mdi-plus',
    tooltip: 'Hinzufügen',
    variant: 'success'
  },
  settings: {
    key: 'settings',
    icon: 'mdi-cog',
    tooltip: 'Einstellungen',
    variant: 'default'
  },
  info: {
    key: 'info',
    icon: 'mdi-information',
    tooltip: 'Information',
    variant: 'default'
  },
  play: {
    key: 'play',
    icon: 'mdi-play',
    tooltip: 'Starten',
    variant: 'success'
  },
  pause: {
    key: 'pause',
    icon: 'mdi-pause',
    tooltip: 'Pausieren',
    variant: 'warning'
  },
  stop: {
    key: 'stop',
    icon: 'mdi-stop',
    tooltip: 'Stoppen',
    variant: 'danger'
  }
}

// Resolve actions to full configuration objects
const resolvedActions = computed(() => {
  return props.actions.map((action, index) => {
    // If string, look up preset
    if (typeof action === 'string') {
      const preset = presets[action]
      if (!preset) {
        console.warn(`LActionGroup: Unknown preset "${action}"`)
        return { key: action, icon: 'mdi-help', tooltip: action, variant: 'default' }
      }
      return { ...preset }
    }

    // If object, merge with preset if key matches
    if (action.preset && presets[action.preset]) {
      return { ...presets[action.preset], ...action, key: action.key || action.preset }
    }

    // Return custom action with defaults
    return {
      key: action.key || `action-${index}`,
      icon: action.icon || 'mdi-circle',
      tooltip: action.tooltip || '',
      variant: action.variant || 'default',
      loading: action.loading || false,
      disabled: action.disabled || false
    }
  })
})

const groupClasses = computed(() => ({
  [`l-action-group--gap-${props.gap}`]: true,
  [`l-action-group--align-${props.align}`]: true
}))

const handleAction = (action) => {
  emit('action', action.key, action)
}
</script>

<style scoped>
.l-action-group {
  display: inline-flex;
  align-items: center;
}

/* Gap variants */
.l-action-group--gap-none {
  gap: 0;
}

.l-action-group--gap-xs {
  gap: 2px;
}

.l-action-group--gap-sm {
  gap: 4px;
}

.l-action-group--gap-md {
  gap: 8px;
}

.l-action-group--gap-lg {
  gap: 12px;
}

/* Alignment */
.l-action-group--align-start {
  justify-content: flex-start;
}

.l-action-group--align-center {
  justify-content: center;
}

.l-action-group--align-end {
  justify-content: flex-end;
}
</style>
