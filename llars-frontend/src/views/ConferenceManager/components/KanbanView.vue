<template>
  <div class="kanban-view">
    <div class="kanban-hint mb-3">
      <v-icon size="14" class="mr-1">mdi-information-outline</v-icon>
      <span>{{ t('conferenceManager.kanban.dragHint') }}</span>
    </div>

    <div class="kanban-board">
      <div
        v-for="status in PAPER_STATUSES"
        :key="status.value"
        class="kanban-column"
      >
        <!-- Column Header -->
        <div class="column-header" :style="{ borderTopColor: status.color }">
          <v-icon size="18" :color="status.color">{{ status.icon }}</v-icon>
          <span class="column-title">{{ t(status.labelKey) }}</span>
          <v-chip size="x-small" variant="tonal">
            {{ getColumnPapers(status.value).length }}
          </v-chip>
        </div>

        <!-- Draggable Papers -->
        <draggable
          :list="getColumnPapers(status.value)"
          group="papers"
          item-key="id"
          class="column-content"
          ghost-class="ghost-card"
          :animation="200"
          @change="(evt) => onDragChange(status.value, evt)"
        >
          <template #item="{ element }">
            <KanbanCard :paper="element" @click="editPaper(element)" />
          </template>
        </draggable>

        <!-- Empty state -->
        <div
          v-if="getColumnPapers(status.value).length === 0"
          class="column-empty"
        >
          {{ t('conferenceManager.kanban.emptyColumn') }}
        </div>
      </div>
    </div>

    <!-- Edit dialog -->
    <PaperFormDialog
      v-model="showEditDialog"
      :paper="selectedPaper"
      @saved="onSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import draggable from 'vuedraggable'
import { PAPER_STATUSES } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'
import KanbanCard from './KanbanCard.vue'
import PaperFormDialog from './PaperFormDialog.vue'

const { t } = useI18n()
const { papers, updatePaperStatus, fetchPapers } = useConferenceManager()

const showEditDialog = ref(false)
const selectedPaper = ref(null)

// Group papers by status into separate reactive arrays
const papersByStatus = computed(() => {
  const grouped = {}
  for (const status of PAPER_STATUSES) {
    grouped[status.value] = papers.value
      .filter(p => p.status === status.value)
      .map(p => ({ ...p })) // shallow copy for draggable
  }
  return grouped
})

function getColumnPapers(status) {
  return papersByStatus.value[status] || []
}

async function onDragChange(targetStatus, evt) {
  if (!evt.added) return

  const paper = evt.added.element
  if (paper.status === targetStatus) return

  try {
    await updatePaperStatus(paper.id, targetStatus)
  } catch (err) {
    console.error('Failed to update paper status:', err)
    await fetchPapers()
  }
}

function editPaper(paper) {
  selectedPaper.value = paper
  showEditDialog.value = true
}

function onSaved() {
  fetchPapers()
}
</script>

<style scoped>
.kanban-hint {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.kanban-board {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
  min-height: 400px;
}

.kanban-column {
  flex: 1;
  min-width: 220px;
  max-width: 300px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-top: 3px solid;
  border-radius: 12px 12px 0 0;
  font-weight: 500;
  font-size: 0.875rem;
}

.column-title {
  flex: 1;
}

.column-content {
  flex: 1;
  padding: 0 8px 8px;
  min-height: 60px;
}

.column-empty {
  padding: 16px;
  text-align: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.ghost-card {
  opacity: 0.4;
}

@media (max-width: 960px) {
  .kanban-board {
    flex-wrap: nowrap;
  }

  .kanban-column {
    min-width: 200px;
  }
}
</style>
