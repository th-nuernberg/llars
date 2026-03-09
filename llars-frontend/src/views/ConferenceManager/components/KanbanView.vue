<template>
  <div class="kanban-view">
    <div class="kanban-board">
      <div
        v-for="status in PAPER_STATUSES"
        :key="status.value"
        class="kanban-column"
        :class="{ 'drop-active': dragTarget === status.value }"
      >
        <!-- Column Header -->
        <div class="column-header">
          <div class="column-icon-wrap" :style="{ backgroundColor: status.color + '18' }">
            <v-icon size="18" :color="status.color">{{ status.icon }}</v-icon>
          </div>
          <span class="column-title">{{ t(status.labelKey) }}</span>
          <v-chip
            size="x-small"
            variant="flat"
            :style="{ backgroundColor: status.color + '22', color: status.color, borderRadius: '6px 2px 6px 2px' }"
          >
            {{ getColumnPapers(status.value).length }}
          </v-chip>
          <v-btn
            icon
            size="x-small"
            variant="text"
            class="add-btn"
            @click="createWithStatus(status.value)"
          >
            <v-icon size="16">mdi-plus</v-icon>
            <v-tooltip activator="parent" location="top">{{ t('conferenceManager.kanban.addPaper') }}</v-tooltip>
          </v-btn>
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
          @start="dragTarget = null"
          @end="dragTarget = null"
        >
          <template #item="{ element }">
            <KanbanCard
              :paper="element"
              :conferences="conferences"
              :latex-access="getLatexAccess(element.id)"
              @click="editPaper(element)"
              @delete="confirmDeletePaper(element)"
              @open-workspace="(wsId) => router.push(`/LatexCollab/workspace/${wsId}`)"
              @request-latex-access="handleRequestAccess"
            />
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

    <!-- Create dialog (with pre-selected status) -->
    <PaperFormDialog
      v-model="showCreateDialog"
      :paper="newPaperDefaults"
      @saved="onSaved"
    />

    <!-- Delete Confirm -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>{{ t('conferenceManager.actions.confirmDelete') }}</v-card-title>
        <v-card-text>
          {{ t('conferenceManager.actions.confirmDeletePaper', { name: deletingPaper?.title }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">{{ t('conferenceManager.actions.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" @click="doDelete">{{ t('conferenceManager.actions.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useSnackbar } from '@/composables/useSnackbar'
import draggable from 'vuedraggable'
import { PAPER_STATUSES } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'
import KanbanCard from './KanbanCard.vue'
import PaperFormDialog from './PaperFormDialog.vue'

const { t } = useI18n()
const router = useRouter()
const { showSuccess } = useSnackbar()
const { papers, conferences, updatePaperStatus, fetchPapers, deletePaper, latexAccessMap, requestLatexAccess } = useConferenceManager()

const showEditDialog = ref(false)
const showCreateDialog = ref(false)
const selectedPaper = ref(null)
const newPaperDefaults = ref(null)
const dragTarget = ref(null)
const deleteDialog = ref(false)
const deletingPaper = ref(null)

const papersByStatus = computed(() => {
  const grouped = {}
  for (const status of PAPER_STATUSES) {
    grouped[status.value] = papers.value
      .filter(p => p.status === status.value)
      .map(p => ({ ...p }))
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

function createWithStatus(status) {
  newPaperDefaults.value = { status }
  showCreateDialog.value = true
}

function confirmDeletePaper(paper) {
  deletingPaper.value = paper
  deleteDialog.value = true
}

async function doDelete() {
  if (deletingPaper.value) {
    await deletePaper(deletingPaper.value.id)
  }
  deleteDialog.value = false
  deletingPaper.value = null
}

function getLatexAccess(paperId) {
  const entry = latexAccessMap.value[String(paperId)]
  return {
    hasAccess: entry?.has_access || false,
    requestStatus: entry?.request_status || null,
  }
}

async function handleRequestAccess(workspaceId) {
  try {
    await requestLatexAccess(workspaceId)
    showSuccess(t('conferenceManager.paper.requestSent'))
  } catch (err) {
    console.error('Request access failed:', err)
  }
}

function onSaved() {
  fetchPapers()
}
</script>

<style scoped>
.kanban-board {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
  min-height: 400px;
}

.kanban-board::-webkit-scrollbar {
  height: 6px;
}

.kanban-board::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}

.kanban-column {
  flex: 1;
  min-width: 220px;
  max-width: 300px;
  background: linear-gradient(180deg, rgba(var(--v-theme-on-surface), 0.04) 0%, rgba(var(--v-theme-on-surface), 0.01) 100%);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  transition: background 0.3s, box-shadow 0.3s;
}

.kanban-column.drop-active {
  background: linear-gradient(180deg, rgba(var(--v-theme-primary), 0.08) 0%, rgba(var(--v-theme-primary), 0.02) 100%);
  box-shadow: inset 0 0 0 2px rgba(var(--v-theme-primary), 0.3);
}

.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  font-weight: 500;
  font-size: 0.875rem;
}

.column-icon-wrap {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.column-title {
  flex: 1;
}

.add-btn {
  opacity: 0.4;
  transition: opacity 0.2s;
}

.kanban-column:hover .add-btn {
  opacity: 1;
}

.column-content {
  flex: 1;
  padding: 0 8px 8px;
  min-height: 60px;
  overflow-y: auto;
  max-height: calc(100vh - 340px);
}

.column-content::-webkit-scrollbar {
  width: 0;
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

@media (max-width: 600px) {
  .kanban-board {
    -webkit-overflow-scrolling: touch;
    scroll-snap-type: x mandatory;
    padding-bottom: 12px;
  }

  .kanban-column {
    min-width: 75vw;
    max-width: 85vw;
    scroll-snap-align: start;
    flex-shrink: 0;
  }

  .column-header {
    padding: 8px 10px;
  }

  .add-btn {
    opacity: 1;
  }
}
</style>
