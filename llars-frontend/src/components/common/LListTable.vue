<template>
  <div class="l-list-table" :class="{ 'l-list-table--striped': striped, 'l-list-table--bordered': bordered }">
    <!-- Header -->
    <div class="l-list-header" :style="gridStyle">
      <!-- Select-all column -->
      <div v-if="selectable" class="l-col l-col--select">
        <v-checkbox
          :model-value="allSelected"
          :indeterminate="someSelected && !allSelected"
          density="compact"
          hide-details
          color="primary"
          @update:model-value="$emit('select-all', $event)"
        />
      </div>

      <!-- User-defined columns -->
      <div
        v-for="col in columns"
        :key="col.key"
        class="l-col"
        :class="[
          col.class,
          {
            'l-col--sortable': col.sortable,
            'l-col--sorted': sortField === col.key,
          }
        ]"
        @click="col.sortable ? handleSort(col.key) : undefined"
      >
        <span class="l-col__label">{{ col.label }}</span>
        <LIcon
          v-if="col.sortable && sortField === col.key"
          size="12"
          class="l-col__sort-icon"
          :class="{ 'l-col__sort-icon--desc': !sortAsc }"
        >
          {{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
        </LIcon>
        <LIcon
          v-else-if="col.sortable"
          size="12"
          class="l-col__sort-icon l-col__sort-icon--idle"
        >
          mdi-arrow-up-down
        </LIcon>
      </div>

      <!-- Actions column (placeholder for alignment) -->
      <div v-if="actionsWidth" class="l-col l-col--actions" />
    </div>

    <!-- Rows -->
    <div
      v-for="(item, index) in items"
      :key="itemKey ? item[itemKey] : index"
      class="l-list-row"
      :style="gridStyle"
      :class="[
        rowClass?.(item, index),
        {
          'l-list-row--selected': isSelected(item),
          'l-list-row--clickable': clickable
        }
      ]"
      @click="handleRowClick(item, $event)"
    >
      <!-- Select column -->
      <div v-if="selectable" class="l-col l-col--select" @click.stop>
        <v-checkbox
          :model-value="isSelected(item)"
          density="compact"
          hide-details
          color="primary"
          @update:model-value="$emit('select', item, $event)"
        />
      </div>

      <!-- Data columns via slot -->
      <slot name="row" :item="item" :index="index" />

      <!-- Actions column -->
      <div v-if="actionsWidth" class="l-col l-col--actions" @click.stop>
        <slot name="row-actions" :item="item" :index="index" />
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="items.length === 0" class="l-list-empty">
      <slot name="empty">
        <LIcon size="40" color="grey-lighten-1">mdi-inbox-outline</LIcon>
        <p>{{ emptyText }}</p>
      </slot>
    </div>
  </div>
</template>

<script setup>
/**
 * LListTable - Global LLARS List/Table Component
 *
 * A CSS-grid-based table with LLARS design system styling.
 * Column widths are defined in `columns` and automatically applied
 * to both headers and rows via a shared grid template — consumers
 * do NOT need to set widths on their slotted row elements.
 *
 * Usage:
 *   <LListTable
 *     :columns="[
 *       { key: 'id', label: '#', width: '60px' },
 *       { key: 'name', label: 'Name', flex: true, sortable: true },
 *       { key: 'status', label: 'Status', width: '100px' },
 *     ]"
 *     :items="data"
 *     item-key="id"
 *     v-model:sort-field="sortField"
 *     v-model:sort-asc="sortAsc"
 *     clickable
 *     @row-click="handleClick"
 *   >
 *     <template #row="{ item }">
 *       <div class="l-col">{{ item.id }}</div>
 *       <div class="l-col">{{ item.name }}</div>
 *       <div class="l-col"><LTag>{{ item.status }}</LTag></div>
 *     </template>
 *   </LListTable>
 */
import { computed } from 'vue'

const props = defineProps({
  columns: {
    type: Array,
    required: true
  },
  items: {
    type: Array,
    default: () => []
  },
  itemKey: {
    type: String,
    default: 'id'
  },
  sortField: {
    type: String,
    default: null
  },
  sortAsc: {
    type: Boolean,
    default: true
  },
  selectable: {
    type: Boolean,
    default: false
  },
  selectedItems: {
    type: Array,
    default: () => []
  },
  clickable: {
    type: Boolean,
    default: true
  },
  striped: {
    type: Boolean,
    default: false
  },
  bordered: {
    type: Boolean,
    default: true
  },
  emptyText: {
    type: String,
    default: 'No items found'
  },
  rowClass: {
    type: Function,
    default: null
  },
  actionsWidth: {
    type: String,
    default: null
  }
})

const emit = defineEmits([
  'update:sortField',
  'update:sortAsc',
  'row-click',
  'select',
  'select-all',
  'sort-change'
])

const allSelected = computed(() =>
  props.items.length > 0 &&
  props.items.every(item => props.selectedItems.includes(item[props.itemKey]))
)

const someSelected = computed(() =>
  props.selectedItems.length > 0
)

/**
 * Build a CSS grid-template-columns string from the columns definition.
 * - `width: '72px'` → `72px`
 * - `flex: true` or `flex: 1` → `minmax(0, 1fr)`
 * - `flex: 2` → `minmax(0, 2fr)`
 * - no width/flex → `auto`
 * Prepends 40px for select column and appends 90px for actions column.
 */
const gridStyle = computed(() => {
  const tracks = []
  if (props.selectable) tracks.push('40px')
  for (const col of props.columns) {
    if (col.flex) {
      const fr = typeof col.flex === 'number' ? col.flex : 1
      tracks.push(`minmax(0, ${fr}fr)`)
    } else if (col.width) {
      tracks.push(col.width)
    } else {
      tracks.push('auto')
    }
  }
  if (props.actionsWidth) tracks.push(props.actionsWidth)
  return { gridTemplateColumns: tracks.join(' ') }
})

function isSelected(item) {
  return props.selectedItems.includes(item[props.itemKey])
}

function handleSort(key) {
  if (props.sortField === key) {
    if (!props.sortAsc) {
      // Third click: clear sort
      emit('update:sortField', null)
      emit('sort-change', { field: null, asc: true })
    } else {
      // Second click: descending
      emit('update:sortAsc', false)
      emit('sort-change', { field: key, asc: false })
    }
  } else {
    // First click: ascending
    emit('update:sortField', key)
    emit('update:sortAsc', true)
    emit('sort-change', { field: key, asc: true })
  }
}

function handleRowClick(item, event) {
  if (props.clickable) {
    emit('row-click', item, event)
  }
}
</script>

<style scoped>
.l-list-table {
  width: 100%;
}

.l-list-table--bordered {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px 3px 8px 3px;
}

.l-list-table--bordered .l-list-header {
  border-radius: 7px 2px 0 0;
}

.l-list-table--bordered .l-list-row:last-child {
  border-radius: 0 0 7px 2px;
}

/* Header */
.l-list-header {
  display: grid;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(var(--v-theme-on-surface), 0.45);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
  user-select: none;
  position: sticky;
  top: 0;
  z-index: 1;
}

/* Columns */
.l-col {
  min-width: 0;
  overflow: hidden;
}

.l-col--select {
  width: 40px;
}

.l-col--select :deep(.v-selection-control) {
  min-height: auto;
}

.l-col--actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
}

/* Sortable columns */
.l-col--sortable {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.15s;
}

.l-col--sortable:hover {
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.l-col--sorted {
  color: rgb(var(--v-theme-primary));
}

.l-col__sort-icon {
  opacity: 0.8;
  flex-shrink: 0;
  transition: opacity 0.15s, transform 0.15s;
}

.l-col__sort-icon--idle {
  opacity: 0;
}

.l-col--sortable:hover .l-col__sort-icon--idle {
  opacity: 0.3;
}

.l-col__sort-icon--desc {
  opacity: 0.5;
}

/* Rows */
.l-list-row {
  display: grid;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  transition: background 0.15s;
}

.l-list-row:last-child {
  border-bottom: none;
}

.l-list-row--clickable {
  cursor: pointer;
}

.l-list-row--clickable:hover {
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.l-list-row--selected {
  background: rgba(var(--v-theme-primary), 0.06);
}

.l-list-row--selected:hover {
  background: rgba(var(--v-theme-primary), 0.09);
}

/* Row actions: show on hover */
.l-list-row .l-col--actions {
  opacity: 0;
  transition: opacity 0.15s;
}

.l-list-row:hover .l-col--actions {
  opacity: 1;
}

/* Striped variant */
.l-list-table--striped .l-list-row:nth-child(even) {
  background: rgba(var(--v-theme-on-surface), 0.015);
}

/* Empty State */
.l-list-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 24px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.85rem;
}

/* Scrollbar */
.l-list-table::-webkit-scrollbar {
  width: 6px;
}

.l-list-table::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}

/* Responsive */
@media (max-width: 768px) {
  .l-list-header,
  .l-list-row {
    padding: 8px 12px;
    gap: 6px;
  }
}
</style>
