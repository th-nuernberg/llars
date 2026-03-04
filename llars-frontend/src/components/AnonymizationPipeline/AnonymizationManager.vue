<template>
  <div class="anonymization-manager">
    <!-- Header -->
    <div class="page-header">
      <h1>Conversation Anonymization</h1>
      <p class="text-medium-emphasis">
        Review and edit anonymized conversations before export
      </p>
    </div>

    <!-- Filters & Search -->
    <v-card class="mb-4" flat>
      <v-card-text>
        <div class="d-flex align-center gap-4 flex-wrap">
          <!-- Status Filter -->
          <v-select
            v-model="filters.status"
            :items="statusOptions"
            label="Status"
            clearable
            density="comfortable"
            variant="outlined"
            style="max-width: 200px"
          />

          <v-select
            v-model="filters.model"
            :items="modelFilterOptions"
            label="AI Model"
            clearable
            density="comfortable"
            variant="outlined"
            style="max-width: 260px"
          />

          <v-select
            v-model="filters.course"
            :items="courseFilterOptions"
            label="Course"
            clearable
            density="comfortable"
            variant="outlined"
            style="max-width: 260px"
          />

          <!-- Search -->
          <v-text-field
            v-model="filters.search"
            label="Search conversations"
            prepend-inner-icon="mdi-magnify"
            clearable
            density="comfortable"
            variant="outlined"
            hide-details
            style="flex: 1; min-width: 250px"
          />

          <div class="ml-auto d-flex gap-2">
            <!-- Bulk Actions -->
            <template v-if="selectedConversations.length > 0">
              <LBtn
                variant="secondary"
                prepend-icon="mdi-check-all"
                :disabled="!hasEditPermission"
                @click="bulkMarkCompleted"
              >
                Mark Completed ({{ selectedConversations.length }})
              </LBtn>
              <LBtn
                variant="primary"
                prepend-icon="mdi-export"
                @click="exportSelected"
              >
                Export Selected
              </LBtn>
            </template>

            <!-- Export All Completed -->
            <LBtn
              v-else
              variant="accent"
              prepend-icon="mdi-export-variant"
              @click="exportAllCompleted"
            >
              Export All Completed
            </LBtn>

            <LBtn
              v-if="hasEditPermission"
              variant="secondary"
              prepend-icon="mdi-upload"
              @click="openUploadDialog"
            >
              Upload Conversations
            </LBtn>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Data Table -->
    <v-card flat>
      <v-data-table
        v-model="selectedConversations"
        :headers="headers"
        :items="conversations"
        :loading="loading"
        :items-per-page="itemsPerPage"
        :items-length="totalConversations"
        show-select
        item-value="id"
        @update:options="handleTableOptions"
        @click:row="openConversation"
      >
        <!-- Status Column -->
        <template #[`item.status`]="{ item }">
          <LTag :variant="getStatusVariant(item.status)">
            {{ item.status }}
          </LTag>
        </template>

        <!-- Message Count -->
        <template #[`item.message_count`]="{ item }">
          <div class="text-center">{{ item.message_count }}</div>
        </template>

        <!-- Entity Count -->
        <template #[`item.entity_count`]="{ item }">
          <div class="text-center">{{ item.entity_count }}</div>
        </template>

        <!-- Quality Rating -->
        <template #[`item.quality_rating`]="{ item }">
          <div class="d-flex align-center justify-center">
            <span v-if="!item.quality_rating" class="text-medium-emphasis">-</span>
            <LRatingScale
              v-else
              :model-value="item.quality_rating"
              :min="1"
              :max="5"
              :step="1"
              :show-labels="false"
              :show-value-labels="false"
              size="small"
              variant="gradient"
              :disabled="true"
              aria-label="Conversation quality rating"
              class="table-rating-scale"
            />
          </div>
        </template>

        <!-- Dataset State -->
        <template #[`item.dataset_state`]="{ item }">
          <LTag :variant="getDatasetStateVariant(item)">
            {{ getDatasetStateLabel(item) }}
          </LTag>
        </template>

        <!-- Models -->
        <template #[`item.models`]="{ item }">
          <span class="metadata-cell">{{ metadataModelsText(item) }}</span>
        </template>

        <!-- Courses -->
        <template #[`item.courses`]="{ item }">
          <span class="metadata-cell">{{ metadataCoursesText(item) }}</span>
        </template>

        <!-- Imported Date -->
        <template #[`item.imported_at`]="{ item }">
          {{ formatDate(item.imported_at) }}
        </template>

        <!-- Actions -->
        <template #[`item.actions`]="{ item }">
          <LActionGroup
            :actions="buildActions(item)"
            size="small"
            @action="(action) => handleAction(action, item)"
          />
        </template>
      </v-data-table>
    </v-card>

    <!-- Export Dialog -->
    <v-dialog v-model="exportDialog" max-width="500">
      <v-card>
        <v-card-title>Export Conversations</v-card-title>
        <v-card-text>
          <p>Export {{ exportCount }} conversation(s) as JSON?</p>
          <p class="text-caption text-medium-emphasis mt-2">
            Only high-quality conversations are exported (rating > 2, not excluded from export).
          </p>
          <p class="text-caption text-medium-emphasis">
            Quality ratings are included in the exported metadata.
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

    <v-dialog v-model="uploadDialog" max-width="640">
      <v-card>
        <v-card-title>Import Conversations</v-card-title>
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
          <v-checkbox
            v-model="uploadRunNer"
            color="primary"
            label="Run NER immediately after import"
            hide-details
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
import LRatingScale from '@/components/common/LRatingScale.vue'

const router = useRouter()
const { showSuccess, showError } = useSnackbar()
const { hasPermission, fetchPermissions } = usePermissions()

// State
const conversations = ref([])
const selectedConversations = ref([])
const loading = ref(false)
const totalConversations = ref(0)
const exportDialog = ref(false)
const exportLoading = ref(false)
const exportMode = ref(null) // 'selected' | 'all_completed'
const uploadDialog = ref(false)
const uploadFile = ref(null)
const uploadRunNer = ref(false)
const uploadLoading = ref(false)
const nerLoadingMap = ref({})
const itemsPerPage = ref(50)
const availableModels = ref([])
const availableCourses = ref([])
const hasConversationsWithoutModel = ref(false)

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

// Table Headers
const headers = [
  { title: 'ID', key: 'id', sortable: true },
  { title: 'Title', key: 'title', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Messages', key: 'message_count', sortable: true, align: 'center' },
  { title: 'Entities', key: 'entity_count', sortable: true, align: 'center' },
  { title: 'Rating', key: 'quality_rating', sortable: true, align: 'center' },
  { title: 'State', key: 'dataset_state', sortable: false },
  { title: 'Model(s)', key: 'models', sortable: false },
  { title: 'Course(s)', key: 'courses', sortable: false },
  { title: 'Imported', key: 'imported_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
]

const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Completed', value: 'completed' },
  { title: 'Error', value: 'error' }
]
const NO_MODEL_FILTER_VALUE = '__NO_MODEL__'

const modelFilterOptions = computed(() => {
  const options = (availableModels.value || []).map(model => ({ title: model, value: model }))
  if (hasConversationsWithoutModel.value) {
    options.unshift({
      title: 'No model (human-human)',
      value: NO_MODEL_FILTER_VALUE
    })
  }
  return options
})

const courseFilterOptions = computed(() =>
  (availableCourses.value || []).map(course => ({ title: course, value: course }))
)

const exportCount = computed(() => {
  if (exportMode.value === 'selected') {
    return selectedConversations.value.length
  }
  return conversations.value.filter(c => c.status === 'completed').length
})

const hasEditPermission = computed(() =>
  hasPermission('feature:anonymization-pipeline:edit')
)
const MIN_EXPORT_QUALITY = 3

function getMetadataSummary(item) {
  return item?.metadata_summary || {}
}

function metadataModelsText(item) {
  const models = getMetadataSummary(item).models || []
  return models.length > 0 ? models.join(', ') : 'Human-Human'
}

function metadataCoursesText(item) {
  const courses = getMetadataSummary(item).courses || []
  return courses.length > 0 ? courses.join(', ') : '-'
}

function isNerRunning(conversationId) {
  return Boolean(nerLoadingMap.value[conversationId])
}

function buildActions(item) {
  const actions = ['view']

  if (hasEditPermission.value) {
    actions.unshift({
      preset: 'play',
      key: 'run_ner',
      tooltip: 'Run NER',
      loading: isNerRunning(item.id),
      disabled: isNerRunning(item.id) || item.status === 'in_progress'
    })
    actions.push('edit')
  }

  return actions
}

// Methods
async function loadConversations() {
  loading.value = true
  try {
    const params = {
      limit: tableOptions.value.itemsPerPage,
      offset: (tableOptions.value.page - 1) * tableOptions.value.itemsPerPage,
      ...(filters.value.status && { status: filters.value.status }),
      ...(filters.value.model && { model: filters.value.model }),
      ...(filters.value.course && { course: filters.value.course }),
      ...(filters.value.search && { search: filters.value.search })
    }

    const response = await axios.get('/api/anonymization/conversations', { params })
    conversations.value = response.data.conversations
    totalConversations.value = response.data.total
    availableModels.value = Array.isArray(response.data.available_models)
      ? response.data.available_models
      : []
    availableCourses.value = Array.isArray(response.data.available_courses)
      ? response.data.available_courses
      : []
    hasConversationsWithoutModel.value = Boolean(response.data.has_conversations_without_model)
  } catch (error) {
    showError('Failed to load conversations')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function handleTableOptions(options) {
  tableOptions.value = options
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

function handleAction(action, item) {
  if (action === 'run_ner') {
    runNerForConversation(item)
    return
  }

  if (action === 'view' || action === 'edit') {
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
}

function getStatusVariant(status) {
  const variants = {
    pending: 'gray',
    in_progress: 'info',
    completed: 'success',
    error: 'danger'
  }
  return variants[status] || 'gray'
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
  const labels = {
    ready: 'Ready for Export',
    low_quality: 'Low Quality',
    excluded: 'Excluded',
    in_review: 'In Review',
    unrated: 'Unrated'
  }
  return labels[getDatasetState(item)] || 'Unrated'
}

function getDatasetStateVariant(item) {
  const variants = {
    ready: 'success',
    low_quality: 'warning',
    excluded: 'danger',
    in_review: 'info',
    unrated: 'gray'
  }
  return variants[getDatasetState(item)] || 'gray'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function bulkMarkCompleted() {
  if (selectedConversations.value.length === 0) return

  const confirmed = confirm(
    `Mark ${selectedConversations.value.length} conversation(s) as completed?`
  )
  if (!confirmed) return

  try {
    await Promise.all(
      selectedConversations.value.map(id =>
        axios.patch(`/api/anonymization/conversations/${id}/status`, {
          status: 'completed'
        })
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
    const formData = new FormData()
    formData.append('file', file)
    formData.append('run_ner', String(uploadRunNer.value))

    const response = await axios.post('/api/anonymization/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    showSuccess(`Imported ${response.data.imported_count} conversation(s)`)
    if (response.data.failed_count > 0) {
      showError(`${response.data.failed_count} conversation(s) could not be imported`)
    }

    uploadDialog.value = false
    uploadFile.value = null
    await loadConversations()
  } catch (error) {
    showError(error.response?.data?.error || 'Import failed')
    console.error(error)
  } finally {
    uploadLoading.value = false
  }
}

async function runNerForConversation(item) {
  if (!hasEditPermission.value) return

  const confirmed = confirm(`Run NER for conversation "${item.title || item.id}"?`)
  if (!confirmed) return

  nerLoadingMap.value = { ...nerLoadingMap.value, [item.id]: true }
  try {
    const response = await axios.post(`/api/anonymization/conversations/${item.id}/run-ner`)
    const entityCount = response.data?.result?.entity_count ?? response.data?.conversation?.entity_count ?? 0
    showSuccess(`NER completed (${entityCount} entities)`)
    await loadConversations()
  } catch (error) {
    showError(error.response?.data?.error || 'NER processing failed')
    console.error(error)
  } finally {
    const next = { ...nerLoadingMap.value }
    delete next[item.id]
    nerLoadingMap.value = next
  }
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

    // Download as JSON file
    const blob = new Blob([JSON.stringify(response.data.export, null, 2)], {
      type: 'application/json'
    })
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
  try {
    await fetchPermissions()
  } catch (error) {
    console.error('Failed to fetch permissions:', error)
  }
  loadConversations()
})
</script>

<style scoped>
.anonymization-manager {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 500;
  margin-bottom: 8px;
}

.gap-4 {
  gap: 16px;
}

.gap-2 {
  gap: 8px;
}

.metadata-cell {
  display: inline-block;
  max-width: 280px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table-rating-scale {
  min-width: 145px;
}

.table-rating-scale :deep(.scale-buttons) {
  gap: 4px;
}

.table-rating-scale :deep(.scale-button) {
  min-width: 24px;
  width: 24px;
  height: 24px;
  padding: 0;
  border-width: 1px;
}

.table-rating-scale :deep(.scale-value) {
  font-size: 0.72rem;
}

:deep(.v-data-table tbody tr) {
  cursor: pointer;
}

:deep(.v-data-table tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
