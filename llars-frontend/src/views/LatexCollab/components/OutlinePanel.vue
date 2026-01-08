<!--
  OutlinePanel.vue

  Document outline/structure panel for LaTeX documents.
  Shows section hierarchy for navigation.
-->
<template>
  <div class="tree-outline-panel" :class="{ collapsed: collapsed }">
    <div class="tree-outline-header">
      <div class="tree-outline-title">
        <LIcon size="14">mdi-format-list-bulleted</LIcon>
        Verzeichnis
      </div>
      <v-btn
        icon
        variant="text"
        size="x-small"
        :title="collapsed ? 'Verzeichnis anzeigen' : 'Verzeichnis ausblenden'"
        @click="$emit('toggle-collapsed')"
      >
        <LIcon size="16">{{ collapsed ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</LIcon>
      </v-btn>
    </div>
    <div v-if="!collapsed" class="tree-outline-list">
      <div v-if="items.length === 0" class="tree-outline-empty">
        {{ emptyLabel }}
      </div>
      <div
        v-for="item in items"
        :key="item.id"
        class="tree-outline-item"
        :style="{ paddingLeft: `${8 + item.depth * 12}px` }"
      >
        <button
          v-if="item.hasChildren"
          class="tree-outline-toggle"
          type="button"
          :title="isItemCollapsed(item.id) ? 'Aufklappen' : 'Einklappen'"
          @click.stop="$emit('toggle-item', item.id)"
        >
          <LIcon size="14">
            {{ isItemCollapsed(item.id) ? 'mdi-chevron-right' : 'mdi-chevron-down' }}
          </LIcon>
        </button>
        <span v-else class="tree-outline-spacer"></span>
        <button
          class="tree-outline-link"
          type="button"
          :title="item.title"
          @click="$emit('jump-to-item', item)"
        >
          {{ item.title }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  collapsed: {
    type: Boolean,
    default: false
  },
  items: {
    type: Array,
    default: () => []
  },
  emptyLabel: {
    type: String,
    default: 'Kein Dokument'
  },
  isItemCollapsed: {
    type: Function,
    default: () => false
  }
})

defineEmits(['toggle-collapsed', 'toggle-item', 'jump-to-item'])
</script>

<style scoped>
.tree-outline-panel {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
  max-height: 40%;
  display: flex;
  flex-direction: column;
}

.tree-outline-panel.collapsed {
  max-height: none;
}

.tree-outline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.tree-outline-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tree-outline-list {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 8px;
}

.tree-outline-empty {
  padding: 12px;
  text-align: center;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.tree-outline-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
}

.tree-outline-toggle {
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
  flex-shrink: 0;
}

.tree-outline-toggle:hover {
  color: rgb(var(--v-theme-primary));
}

.tree-outline-spacer {
  width: 20px;
  flex-shrink: 0;
}

.tree-outline-link {
  flex: 1;
  border: none;
  background: transparent;
  text-align: left;
  padding: 4px 6px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  cursor: pointer;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.15s ease;
}

.tree-outline-link:hover {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}
</style>
