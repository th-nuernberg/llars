<!--
  OutlinePanelContent.vue

  Document outline content for the tree stack panel.
  Shows section hierarchy without its own header.
-->
<template>
  <div class="outline-panel-content">
    <div v-if="items.length === 0" class="outline-empty">
      {{ emptyLabel }}
    </div>
    <div
      v-for="item in items"
      :key="item.id"
      class="outline-item"
      :style="{ paddingLeft: `${8 + item.depth * 12}px` }"
    >
      <button
        v-if="item.hasChildren"
        class="outline-toggle"
        type="button"
        :title="isItemCollapsed(item.id) ? $t('latexCollab.outline.expand') : $t('latexCollab.outline.collapse')"
        @click.stop="$emit('toggle-item', item.id)"
      >
        <LIcon size="14">
          {{ isItemCollapsed(item.id) ? 'mdi-chevron-right' : 'mdi-chevron-down' }}
        </LIcon>
      </button>
      <span v-else class="outline-spacer"></span>
      <button
        class="outline-link"
        type="button"
        :title="item.title"
        @click="$emit('jump-to-item', item)"
      >
        {{ item.title }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => []
  },
  emptyLabel: {
    type: String,
    default: ''
  },
  isItemCollapsed: {
    type: Function,
    default: () => false
  }
})

defineEmits(['toggle-item', 'jump-to-item'])
</script>

<style scoped>
.outline-panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.outline-empty {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.outline-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
}

.outline-toggle {
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

.outline-toggle:hover {
  color: rgb(var(--v-theme-primary));
}

.outline-spacer {
  width: 20px;
  flex-shrink: 0;
}

.outline-link {
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

.outline-link:hover {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}
</style>
