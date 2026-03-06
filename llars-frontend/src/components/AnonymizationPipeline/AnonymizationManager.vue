<template>
  <div class="anonymization-manager">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <LIcon size="28" color="primary">mdi-shield-check</LIcon>
        <h1 class="title">Anonymisierungs-Pipeline</h1>
      </div>
      <div class="header-right">
        <template v-if="selectedConversations.length > 0">
          <LBtn
            variant="secondary"
            prepend-icon="mdi-check-all"
            size="small"
            :disabled="!hasEditPermission"
            @click="bulkMarkCompleted"
          >
            Mark Completed ({{ selectedConversations.length }})
          </LBtn>
          <LBtn
            variant="primary"
            prepend-icon="mdi-export"
            size="small"
            @click="exportSelected"
          >
            Export Selected
          </LBtn>
        </template>
        <LBtn
          v-if="selectedConversations.length === 0"
          variant="accent"
          prepend-icon="mdi-export-variant"
          size="small"
          @click="exportAllCompleted"
        >
          Export
        </LBtn>
        <LBtn
          v-if="hasEditPermission"
          variant="secondary"
          prepend-icon="mdi-play-circle-outline"
          size="small"
          :disabled="isBatchRunning"
          @click="runBatchNer"
        >
          Run All NER
        </LBtn>
        <LBtn
          v-if="hasEditPermission"
          variant="primary"
          prepend-icon="mdi-upload"
          size="small"
          @click="openUploadDialog"
        >
          Import
        </LBtn>
      </div>
    </div>

    <!-- Batch Progress Bar -->
    <div v-if="batchProgress" class="batch-progress-bar">
      <div class="batch-progress-info">
        <LIcon size="16" color="accent">mdi-shield-sync</LIcon>
        <span>NER Processing: {{ batchProgress.completed + batchProgress.failed }} / {{ batchProgress.total }}</span>
        <span v-if="batchProgress.failed > 0" class="batch-failed">
          ({{ batchProgress.failed }} failed)
        </span>
      </div>
      <v-progress-linear
        :model-value="batchProgress.percent"
        color="#88c4c8"
        height="6"
        rounded
      />
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-chips">
        <button
          class="filter-chip"
          :class="{ active: !filters.status }"
          @click="filters.status = null"
        >
          Alle ({{ totalConversations }})
        </button>
        <button
          class="filter-chip pending"
          :class="{ active: filters.status === 'pending' }"
          @click="filters.status = 'pending'"
        >
          Pending ({{ statusCounts.pending }})
        </button>
        <button
          class="filter-chip in-progress"
          :class="{ active: filters.status === 'in_progress' }"
          @click="filters.status = 'in_progress'"
        >
          In Progress ({{ statusCounts.in_progress }})
        </button>
        <button
          class="filter-chip done"
          :class="{ active: filters.status === 'completed' }"
          @click="filters.status = 'completed'"
        >
          Completed ({{ statusCounts.completed }})
        </button>
        <button
          class="filter-chip error"
          :class="{ active: filters.status === 'error' }"
          @click="filters.status = 'error'"
        >
          Error ({{ statusCounts.error }})
        </button>
      </div>

      <div class="filter-controls">
        <v-select
          v-if="modelFilterOptions.length > 0"
          v-model="filters.model"
          :items="modelFilterOptions"
          label="Model"
          clearable
          density="compact"
          variant="outlined"
          hide-details
          class="filter-select"
        />
        <v-select
          v-if="courseFilterOptions.length > 0"
          v-model="filters.course"
          :items="courseFilterOptions"
          label="Course"
          clearable
          density="compact"
          variant="outlined"
          hide-details
          class="filter-select"
        />
        <v-text-field
          v-model="filters.search"
          placeholder="Search..."
          prepend-inner-icon="mdi-magnify"
          clearable
          density="compact"
          variant="outlined"
          hide-details
          class="filter-search"
        />

        <!-- View Toggle -->
        <LViewToggle v-model="viewMode" />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && conversations.length === 0" class="loading-state">
      <v-progress-circular indeterminate size="48" color="primary" />
      <p>Loading conversations...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="conversations.length === 0" class="empty-state">
      <LIcon size="64" color="grey-lighten-1">mdi-shield-check-outline</LIcon>
      <h3>No conversations found</h3>
      <p>Import conversations to start the anonymization pipeline.</p>
      <LBtn v-if="hasEditPermission" variant="primary" @click="openUploadDialog">
        <LIcon start>mdi-upload</LIcon>
        Import Conversations
      </LBtn>
    </div>

    <!-- Content Area -->
    <div v-else class="content-area">
      <!-- Card View -->
      <div v-if="viewMode === 'cards'" class="cards-grid">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conv-card"
          :class="[
            getStatusClass(conv.status),
            { 'conv-card--selected': selectedConversations.includes(conv.id) }
          ]"
          @click="openConversation($event, { item: conv })"
        >
          <div class="card-select" @click.stop>
            <v-checkbox
              :model-value="selectedConversations.includes(conv.id)"
              density="compact"
              hide-details
              color="primary"
              @update:model-value="toggleSelection(conv.id, $event)"
            />
          </div>

          <div class="card-status">
            <LTag :variant="getStatusVariant(conv.status)" size="small">
              {{ conv.status }}
            </LTag>
          </div>

          <div class="card-header">
            <div class="card-id">#{{ conv.id }}</div>
            <h3 class="card-title">{{ conv.title || `Conversation ${conv.id}` }}</h3>
          </div>

          <div class="card-stats">
            <span class="stat-item">
              <LIcon size="14">mdi-message-outline</LIcon>
              {{ conv.message_count }}
            </span>
            <span class="stat-item">
              <LIcon size="14">mdi-tag-outline</LIcon>
              {{ conv.entity_count }}
            </span>
            <LTag :variant="getDatasetStateVariant(conv)" size="small">
              {{ getDatasetStateLabel(conv) }}
            </LTag>
            <span v-if="conv.quality_rating" class="quality-badge">
              {{ conv.quality_rating }}/5
            </span>
          </div>

          <!-- NER Progress -->
          <div v-if="getNerProgress(conv.id)" class="card-ner-progress">
            <div class="ner-progress-label">
              <span>NER: {{ getNerProgress(conv.id).message_number }}/{{ getNerProgress(conv.id).total_messages }} messages</span>
              <span class="ner-entities">{{ getNerProgress(conv.id).entities_found }} entities</span>
            </div>
            <v-progress-linear
              :model-value="getNerProgress(conv.id).percent"
              color="#88c4c8"
              height="4"
              rounded
            />
          </div>

          <div class="card-meta">
            <span v-if="metadataModelsText(conv) !== '-'" class="meta-tag model">
              {{ metadataModelsText(conv) }}
            </span>
            <span v-if="metadataCoursesText(conv) !== '-'" class="meta-tag course">
              {{ metadataCoursesText(conv) }}
            </span>
            <span class="meta-date">{{ formatDate(conv.imported_at) }}</span>
            <span v-if="hasEditPermission" class="card-ner" @click.stop>
              <LBtn
                variant="text"
                size="small"
                :loading="isNerRunning(conv.id)"
                :disabled="isNerRunning(conv.id) || conv.status === 'in_progress'"
                @click="runNerForConversation(conv)"
              >
                <LIcon size="16">mdi-play</LIcon>
                NER
              </LBtn>
            </span>
          </div>
        </div>
      </div>

      <!-- List View -->
      <LListTable
        v-else
        :columns="listColumns"
        :items="conversations"
        actions-width="90px"
        item-key="id"
        v-model:sort-field="listSortField"
        v-model:sort-asc="listSortAsc"
        selectable
        :selected-items="selectedConversations"
        :row-class="(conv) => getStatusClass(conv.status)"
        @row-click="(conv) => openConversation($event, { item: conv })"
        @select="(conv, checked) => toggleSelection(conv.id, checked)"
        @select-all="toggleSelectAll"
      >
        <template #row="{ item: conv }">
          <div class="l-col list-col-id">{{ conv.id }}</div>
          <div class="l-col list-col-title">
            <span class="list-title">{{ conv.title || `Conversation ${conv.id}` }}</span>
          </div>
          <div class="l-col">
            <div v-if="getNerProgress(conv.id)" class="list-ner-progress">
              <v-progress-linear
                :model-value="getNerProgress(conv.id).percent"
                color="#88c4c8"
                height="4"
                rounded
              />
              <span class="list-ner-label">{{ getNerProgress(conv.id).percent }}%</span>
            </div>
            <LTag v-else :variant="getStatusVariant(conv.status)" size="small">
              {{ conv.status }}
            </LTag>
          </div>
          <div class="l-col list-col-center">{{ conv.message_count }}</div>
          <div class="l-col list-col-center">{{ conv.entity_count }}</div>
          <div class="l-col list-col-center">
            <span v-if="conv.quality_rating" class="quality-badge">{{ conv.quality_rating }}/5</span>
            <span v-else class="text-muted">-</span>
          </div>
          <div class="l-col">
            <LTag :variant="getDatasetStateVariant(conv)" size="small">
              {{ getDatasetStateLabel(conv) }}
            </LTag>
          </div>
          <div class="l-col list-col-model">{{ metadataModelsText(conv) }}</div>
          <div class="l-col list-col-date">{{ formatDate(conv.imported_at) }}</div>
        </template>
        <template v-if="hasEditPermission" #row-actions="{ item: conv }">
          <LBtn
            variant="text"
            size="small"
            :loading="isNerRunning(conv.id)"
            :disabled="isNerRunning(conv.id) || conv.status === 'in_progress'"
            @click="runNerForConversation(conv)"
          >
            NER
          </LBtn>
        </template>
      </LListTable>

      <!-- Pagination -->
      <div v-if="totalConversations > itemsPerPage" class="pagination-bar">
        <LBtn
          variant="text"
          size="small"
          :disabled="tableOptions.page <= 1"
          @click="goToPage(tableOptions.page - 1)"
        >
          <LIcon>mdi-chevron-left</LIcon>
        </LBtn>
        <span class="pagination-info">
          {{ (tableOptions.page - 1) * itemsPerPage + 1 }}–{{ Math.min(tableOptions.page * itemsPerPage, totalConversations) }}
          of {{ totalConversations }}
        </span>
        <LBtn
          variant="text"
          size="small"
          :disabled="tableOptions.page * itemsPerPage >= totalConversations"
          @click="goToPage(tableOptions.page + 1)"
        >
          <LIcon>mdi-chevron-right</LIcon>
        </LBtn>
      </div>
    </div>

    <!-- Export Dialog -->
    <v-dialog v-model="exportDialog" max-width="500">
      <v-card class="dialog-card">
        <v-card-title class="d-flex align-center gap-2">
          <LIcon color="primary">mdi-export</LIcon>
          Export Conversations
        </v-card-title>
        <v-card-text>
          <p>Export {{ exportCount }} conversation(s) as JSON?</p>
          <p class="text-caption text-medium-emphasis mt-2">
            Only high-quality conversations are exported (rating > 2, not excluded from export).
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="exportDialog = false">Cancel</LBtn>
          <LBtn
            variant="primary"
            prepend-icon="mdi-download"
            :loading="exportLoading"
            @click="confirmExport"
          >
            Export
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Upload Dialog -->
    <v-dialog v-model="uploadDialog" max-width="640">
      <v-card class="dialog-card">
        <v-card-title class="d-flex align-center gap-2">
          <LIcon color="primary">mdi-upload</LIcon>
          Import Conversations
        </v-card-title>
        <v-card-text>
          <v-file-input
            v-model="uploadFile"
            accept=".json,application/json"
            label="Conversation JSON file"
            prepend-icon="mdi-file-upload"
            variant="outlined"
            density="comfortable"
            hide-details
          />
          <LCheckbox
            v-model="uploadRunNer"
            label="Run NER immediately after import"
            class="mt-3"
          />
          <p class="text-caption text-medium-emphasis mt-3 mb-0">
            Supported format is generic JSON with one conversation object or an array of conversations.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" :disabled="uploadLoading" @click="uploadDialog = false">
            Cancel
          </LBtn>
          <LBtn
            variant="primary"
            prepend-icon="mdi-upload"
            :loading="uploadLoading"
            @click="importConversations"
          >
            Import
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useSnackbar } from '@/composables/useSnackbar'
import { usePermissions } from '@/composables/usePermissions'
import { useAnonymizationPipeline } from '@/composables/useAnonymizationPipeline'

const router = useRouter()
const { showSuccess, showError } = useSnackbar()
const { hasPermission, fetchPermissions } = usePermissions()

// Session management with live Socket.IO updates
const {
  conversations: pipelineConversations,
  totalConversations: pipelineTotalConversations,
  loading: pipelineLoading,
  availableModels: pipelineModels,
  availableCourses: pipelineCourses,
  hasConversationsWithoutModel: pipelineHasNoModel,
  statusCounts: pipelineStatusCounts,
  nerProgress,
  batchProgress,
  isBatchRunning,
  loadConversations: pipelineLoadConversations,
  runNer: pipelineRunNer,
  batchRunNer,
  importConversations: pipelineImport,
  isNerRunning: pipelineIsNerRunning,
  getNerProgress,
} = useAnonymizationPipeline({ autoJoinOverview: true })

// State - use pipeline composable refs directly
const conversations = pipelineConversations
const selectedConversations = ref([])
const loading = pipelineLoading
const totalConversations = pipelineTotalConversations
const exportDialog = ref(false)
const exportLoading = ref(false)
const exportMode = ref(null)
const uploadDialog = ref(false)
const uploadFile = ref(null)
const uploadRunNer = ref(false)
const uploadLoading = ref(false)
const itemsPerPage = ref(50)
const availableModels = pipelineModels
const availableCourses = pipelineCourses
const hasConversationsWithoutModel = pipelineHasNoModel
const statusCounts = pipelineStatusCounts
const viewMode = ref('list')
const listSortField = ref(null)
const listSortAsc = ref(true)

const filters = ref({
  status: null,
  model: null,
  course: null,
  search: ''
})

const tableOptions = ref({
  page: 1,
  itemsPerPage: 50
})

const NO_MODEL_FILTER_VALUE = '__NO_MODEL__'

const modelFilterOptions = computed(() => {
  const options = (availableModels.value || []).map(model => ({ title: model, value: model }))
  if (hasConversationsWithoutModel.value) {
    options.unshift({ title: 'No model (human-human)', value: NO_MODEL_FILTER_VALUE })
  }
  return options
})

const courseFilterOptions = computed(() =>
  (availableCourses.value || []).map(course => ({ title: course, value: course }))
)

const exportCount = computed(() => {
  if (exportMode.value === 'selected') return selectedConversations.value.length
  return conversations.value.filter(c => c.status === 'completed').length
})

const hasEditPermission = computed(() =>
  hasPermission('feature:anonymization-pipeline:edit')
)

const allSelected = computed(() =>
  conversations.value.length > 0 &&
  conversations.value.every(c => selectedConversations.value.includes(c.id))
)

const someSelected = computed(() =>
  selectedConversations.value.length > 0
)

const listColumns = computed(() => [
  { key: 'id', label: '#', width: '50px' },
  { key: 'title', label: 'Title', flex: true, sortable: true },
  { key: 'status', label: 'Status', width: '100px' },
  { key: 'message_count', label: 'Msgs', width: '55px' },
  { key: 'entity_count', label: 'Entities', width: '65px' },
  { key: 'quality_rating', label: 'Quality', width: '65px' },
  { key: 'dataset', label: 'Dataset', width: '95px' },
  { key: 'model', label: 'Model', width: '140px' },
  { key: 'imported_at', label: 'Date', width: '95px', sortable: true },
])

const MIN_EXPORT_QUALITY = 3

function getMetadataSummary(item) {
  return item?.metadata_summary || {}
}

function metadataModelsText(item) {
  const models = getMetadataSummary(item).models || []
  return models.length > 0 ? models.join(', ') : '-'
}

function metadataCoursesText(item) {
  const courses = getMetadataSummary(item).courses || []
  return courses.length > 0 ? courses.join(', ') : '-'
}

function isNerRunning(conversationId) {
  return pipelineIsNerRunning(conversationId)
}

function toggleSelection(id, checked) {
  if (checked) {
    if (!selectedConversations.value.includes(id)) selectedConversations.value.push(id)
  } else {
    selectedConversations.value = selectedConversations.value.filter(cid => cid !== id)
  }
}

function toggleSelectAll(checked) {
  if (checked) {
    selectedConversations.value = conversations.value.map(c => c.id)
  } else {
    selectedConversations.value = []
  }
}

// Methods
async function loadConversations() {
  const params = {
    limit: tableOptions.value.itemsPerPage,
    offset: (tableOptions.value.page - 1) * tableOptions.value.itemsPerPage,
    ...(filters.value.status && { status: filters.value.status }),
    ...(filters.value.model && { model: filters.value.model }),
    ...(filters.value.course && { course: filters.value.course }),
    ...(filters.value.search && { search: filters.value.search })
  }
  await pipelineLoadConversations(params)
}

function goToPage(page) {
  tableOptions.value.page = page
  loadConversations()
}

function openConversation(event, { item }) {
  router.push({
    path: `/anonymization/${item.id}`,
    query: {
      ...(filters.value.status && { status: filters.value.status }),
      ...(filters.value.model && { model: filters.value.model }),
      ...(filters.value.course && { course: filters.value.course }),
      ...(filters.value.search && { search: filters.value.search })
    }
  })
}

function getStatusVariant(status) {
  const variants = { pending: 'gray', in_progress: 'info', completed: 'success', error: 'danger' }
  return variants[status] || 'gray'
}

function getStatusClass(status) {
  return `status-${status}`
}

function getDatasetState(item) {
  if (!item) return 'unrated'
  if (item.exclude_from_export) return 'excluded'
  if (item.status !== 'completed') return 'in_review'
  if (!item.quality_rating) return 'unrated'
  if (Number(item.quality_rating) >= MIN_EXPORT_QUALITY) return 'ready'
  return 'low_quality'
}

function getDatasetStateLabel(item) {
  const labels = { ready: 'Ready', low_quality: 'Low Quality', excluded: 'Excluded', in_review: 'In Review', unrated: 'Unrated' }
  return labels[getDatasetState(item)] || 'Unrated'
}

function getDatasetStateVariant(item) {
  const variants = { ready: 'success', low_quality: 'warning', excluded: 'danger', in_review: 'info', unrated: 'gray' }
  return variants[getDatasetState(item)] || 'gray'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('de-DE', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function bulkMarkCompleted() {
  if (selectedConversations.value.length === 0) return
  const confirmed = confirm(`Mark ${selectedConversations.value.length} conversation(s) as completed?`)
  if (!confirmed) return

  try {
    await Promise.all(
      selectedConversations.value.map(id =>
        axios.patch(`/api/anonymization/conversations/${id}/status`, { status: 'completed' })
      )
    )
    showSuccess('Conversations marked as completed')
    selectedConversations.value = []
    loadConversations()
  } catch (error) {
    showError('Failed to update conversations')
    console.error(error)
  }
}

function openUploadDialog() {
  uploadFile.value = null
  uploadRunNer.value = false
  uploadDialog.value = true
}

async function importConversations() {
  const file = Array.isArray(uploadFile.value) ? uploadFile.value[0] : uploadFile.value
  if (!file) {
    showError('Please choose a JSON file')
    return
  }

  uploadLoading.value = true
  try {
    const result = await pipelineImport(file, { runNer: uploadRunNer.value })
    if (result) {
      uploadDialog.value = false
      uploadFile.value = null
      await loadConversations()
    }
  } finally {
    uploadLoading.value = false
  }
}

async function runNerForConversation(item) {
  if (!hasEditPermission.value) return
  const confirmed = confirm(`Run NER for conversation "${item.title || item.id}"?`)
  if (!confirmed) return

  await pipelineRunNer(item.id)
}

async function runBatchNer() {
  const confirmed = confirm('Run NER for all pending conversations?')
  if (!confirmed) return
  await batchRunNer()
}

function exportSelected() {
  if (selectedConversations.value.length === 0) return
  exportMode.value = 'selected'
  exportDialog.value = true
}

function exportAllCompleted() {
  exportMode.value = 'all_completed'
  exportDialog.value = true
}

async function confirmExport() {
  exportLoading.value = true
  try {
    const payload =
      exportMode.value === 'selected'
        ? { conversation_ids: selectedConversations.value, min_quality_rating: MIN_EXPORT_QUALITY }
        : { include_all_completed: true, min_quality_rating: MIN_EXPORT_QUALITY }

    const response = await axios.post('/api/anonymization/export', payload)
    const blob = new Blob([JSON.stringify(response.data.export, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `anonymized_conversations_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)

    showSuccess(`Exported ${response.data.export.metadata.conversation_count} conversations`)
    exportDialog.value = false
    selectedConversations.value = []
  } catch (error) {
    showError('Export failed')
    console.error(error)
  } finally {
    exportLoading.value = false
  }
}

// Watchers
watch(
  () => filters.value,
  () => {
    tableOptions.value.page = 1
    loadConversations()
  },
  { deep: true }
)

// Lifecycle
onMounted(async () => {
  try { await fetchPermissions() } catch (error) { console.error('Failed to fetch permissions:', error) }
  loadConversations()
})
</script>

<style scoped>
.anonymization-manager {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
}

/* Page Header */
.page-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 1.4rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
  flex-shrink: 0;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-chips {
  display: flex;
  gap: 8px;
}

.filter-chip {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 20px;
  background: transparent;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.filter-chip:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.filter-chip.active {
  background: rgba(var(--v-theme-primary), 0.15);
  border-color: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-primary));
}

.filter-chip.pending.active {
  background: rgba(var(--v-theme-warning), 0.15);
  border-color: rgb(var(--v-theme-warning));
  color: rgb(var(--v-theme-warning));
}

.filter-chip.in-progress.active {
  background: rgba(136, 196, 200, 0.15);
  border-color: #88c4c8;
  color: #88c4c8;
}

.filter-chip.done.active {
  background: rgba(152, 212, 187, 0.15);
  border-color: #98d4bb;
  color: #3d8b6a;
}

.filter-chip.error.active {
  background: rgba(232, 160, 135, 0.15);
  border-color: #e8a087;
  color: #c4705a;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-select {
  max-width: 180px;
  min-width: 140px;
}

.filter-search {
  max-width: 220px;
  min-width: 160px;
}

/* Loading & Empty States */
.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 48px;
  text-align: center;
}

.loading-state p,
.empty-state p {
  color: rgba(var(--v-theme-on-surface), 0.6);
  max-width: 400px;
}

.empty-state h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

/* Content Area */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Card Grid */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

/* Conversation Card */
.conv-card {
  position: relative;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  padding-left: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.conv-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.conv-card--selected {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.04);
}

.conv-card.status-completed { border-left: 3px solid var(--llars-success, #98d4bb); }
.conv-card.status-in_progress { border-left: 3px solid var(--llars-accent, #88c4c8); }
.conv-card.status-pending { border-left: 3px solid rgba(var(--v-theme-on-surface), 0.2); }
.conv-card.status-error { border-left: 3px solid var(--llars-danger, #e8a087); }

.card-select {
  position: absolute;
  top: 8px;
  left: 8px;
}

.card-select :deep(.v-selection-control) {
  min-height: auto;
}

.card-status {
  position: absolute;
  top: 12px;
  right: 12px;
}

.card-header {
  padding-top: 4px;
}

.card-id {
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.45);
  margin-bottom: 2px;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  padding-right: 80px;
}

.card-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.quality-badge {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
  border-radius: 10px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  flex-wrap: wrap;
}

.meta-tag {
  font-size: 0.7rem;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 6px 2px 6px 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}

.meta-tag.model {
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
}

.meta-tag.course {
  background: rgba(209, 188, 138, 0.15);
  color: #a5903e;
}

.meta-date {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  margin-left: auto;
}

.card-ner {
  margin-left: auto;
}

/* List View - column visual styles (widths come from LListTable grid) */
.list-col-id {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-weight: 500;
}

.list-col-center {
  text-align: center;
}

.list-col-model {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.list-col-date {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* List View - status borders on LListTable rows */
:deep(.l-list-row.status-completed) { border-left: 3px solid var(--llars-success, #98d4bb); }
:deep(.l-list-row.status-in_progress) { border-left: 3px solid var(--llars-accent, #88c4c8); }
:deep(.l-list-row.status-pending) { border-left: 3px solid rgba(var(--v-theme-on-surface), 0.15); }
:deep(.l-list-row.status-error) { border-left: 3px solid var(--llars-danger, #e8a087); }

.list-title {
  font-weight: 500;
  font-size: 0.85rem;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.text-muted {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

/* Pagination */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 0 0;
}

.pagination-info {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Batch Progress Bar */
.batch-progress-bar {
  flex-shrink: 0;
  padding: 10px 24px;
  background: rgba(136, 196, 200, 0.08);
  border-bottom: 1px solid rgba(136, 196, 200, 0.2);
}

.batch-progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 6px;
}

.batch-failed {
  color: var(--llars-danger, #e8a087);
}

/* Card NER Progress */
.card-ner-progress {
  padding: 6px 0;
}

.ner-progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 4px;
}

.ner-entities {
  color: var(--llars-accent, #88c4c8);
  font-weight: 500;
}

/* List NER Progress */
.list-ner-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 80px;
}

.list-ner-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--llars-accent, #88c4c8);
  white-space: nowrap;
}

/* Dialog */
.dialog-card {
  border-radius: 12px 4px 12px 4px !important;
}

/* Responsive */
@media (max-width: 900px) {
  .cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .cards-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    padding: 12px 16px;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }

  .filter-bar {
    padding: 10px 16px;
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-controls {
    width: 100%;
    flex-wrap: wrap;
  }

  .filter-search {
    flex: 1;
    max-width: none;
  }

  .content-area {
    padding: 16px;
  }

  .title {
    font-size: 1.2rem;
  }
}
</style>
