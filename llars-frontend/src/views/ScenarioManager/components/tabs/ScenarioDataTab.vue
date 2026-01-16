<template>
  <div class="data-tab">
    <!-- Header Actions -->
    <div class="tab-header">
      <h3>{{ $t('scenarioManager.data.title') }}</h3>
      <div class="header-actions">
        <LBtn variant="primary" @click="showImportDialog = true">
          <LIcon start>mdi-upload</LIcon>
          {{ $t('scenarioManager.data.importData') }}
        </LBtn>
      </div>
    </div>

    <!-- Data Stats -->
    <div class="data-stats" v-if="scenario">
      <div class="stat-card">
        <LIcon size="24" color="primary">mdi-email-multiple-outline</LIcon>
        <div class="stat-info">
          <span class="stat-value">{{ scenario.thread_count || 0 }}</span>
          <span class="stat-label">{{ $t('scenarioManager.data.threads') }}</span>
        </div>
      </div>
      <div class="stat-card">
        <LIcon size="24" color="accent">mdi-message-text-outline</LIcon>
        <div class="stat-info">
          <span class="stat-value">{{ scenario.message_count || 0 }}</span>
          <span class="stat-label">{{ $t('scenarioManager.data.messages') }}</span>
        </div>
      </div>
      <div class="stat-card">
        <LIcon size="24" color="secondary">mdi-tag-multiple-outline</LIcon>
        <div class="stat-info">
          <span class="stat-value">{{ scenario.feature_count || 0 }}</span>
          <span class="stat-label">{{ $t('scenarioManager.data.features') }}</span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!scenario?.thread_count" class="empty-state">
      <LIcon size="80" color="grey-lighten-1">mdi-database-off-outline</LIcon>
      <h3>{{ $t('scenarioManager.data.emptyTitle') }}</h3>
      <p>{{ $t('scenarioManager.data.emptyDescription') }}</p>
      <LBtn variant="primary" @click="showImportDialog = true">
        <LIcon start>mdi-upload</LIcon>
        {{ $t('scenarioManager.data.importFirst') }}
      </LBtn>
    </div>

    <!-- Threads List -->
    <div v-else class="threads-section">
      <div class="threads-header">
        <v-text-field
          v-model="searchQuery"
          :placeholder="$t('scenarioManager.data.searchThreads')"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="compact"
          hide-details
          clearable
          class="search-field"
        />
        <v-select
          v-model="sortBy"
          :items="sortOptions"
          item-title="label"
          item-value="value"
          variant="outlined"
          density="compact"
          hide-details
          class="sort-select"
        />
      </div>

      <!-- Threads Table -->
      <v-data-table
        :headers="tableHeaders"
        :items="filteredThreads"
        :loading="loadingThreads"
        :items-per-page="10"
        class="threads-table"
      >
        <template #item.subject="{ item }">
          <div class="thread-subject">
            <span class="subject-text">{{ item.subject || $t('scenarioManager.data.noSubject') }}</span>
            <span class="message-count">
              <LIcon size="14">mdi-message-outline</LIcon>
              {{ item.message_count }}
            </span>
          </div>
        </template>

        <template #item.status="{ item }">
          <LTag :variant="getStatusVariant(item.status)" size="sm">
            {{ $t(`scenarioManager.data.status.${item.status || 'pending'}`) }}
          </LTag>
        </template>

        <template #item.actions="{ item }">
          <v-btn icon size="small" variant="text" @click="viewThread(item)">
            <LIcon size="18">mdi-eye-outline</LIcon>
          </v-btn>
          <v-btn icon size="small" variant="text" color="error" @click="confirmRemoveThread(item)">
            <LIcon size="18">mdi-delete-outline</LIcon>
          </v-btn>
        </template>
      </v-data-table>
    </div>

    <!-- Import Dialog -->
    <v-dialog v-model="showImportDialog" max-width="800" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="primary" class="mr-2">mdi-database-import-outline</LIcon>
          {{ $t('scenarioManager.data.importTitle') }}
          <v-spacer />
          <v-btn icon variant="text" @click="closeImportDialog" :disabled="importing">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <!-- Import Progress -->
          <div v-if="importing" class="import-progress mb-4">
            <p class="text-body-2 mb-2">{{ $t('scenarioManager.data.importing') }}</p>
            <v-progress-linear
              :model-value="importProgress"
              color="primary"
              height="8"
              rounded
            />
            <p class="text-caption text-center mt-1">{{ importProgress }}%</p>
          </div>

          <!-- Import Error -->
          <v-alert v-if="importError" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="resetImport">
            {{ importError }}
          </v-alert>

          <div v-if="!importing" class="import-options">
            <div class="import-option" @click="importMethod = 'file'" :class="{ selected: importMethod === 'file' }">
              <LIcon size="32" color="primary">mdi-file-upload-outline</LIcon>
              <h4>{{ $t('scenarioManager.data.importFile') }}</h4>
              <p>{{ $t('scenarioManager.data.importFileDesc') }}</p>
            </div>
            <div class="import-option" @click="importMethod = 'existing'" :class="{ selected: importMethod === 'existing' }">
              <LIcon size="32" color="accent">mdi-database-search-outline</LIcon>
              <h4>{{ $t('scenarioManager.data.importExisting') }}</h4>
              <p>{{ $t('scenarioManager.data.importExistingDesc') }}</p>
            </div>
          </div>

          <!-- File Upload -->
          <div v-if="importMethod === 'file' && !importing" class="import-content">
            <v-file-input
              v-model="uploadFile"
              :label="$t('scenarioManager.data.selectFile')"
              accept=".json,.csv,.xlsx"
              variant="outlined"
              prepend-icon=""
              prepend-inner-icon="mdi-file-outline"
            />
            <v-alert type="info" variant="tonal" density="compact" class="mt-4">
              {{ $t('scenarioManager.data.supportedFormats') }}
            </v-alert>
          </div>

          <!-- Existing Data Selection -->
          <div v-if="importMethod === 'existing' && !importing" class="import-content">
            <p class="text-body-2 mb-4">{{ $t('scenarioManager.data.selectExistingDesc') }}</p>

            <!-- Loading state -->
            <div v-if="loadingAvailable" class="text-center py-4">
              <v-progress-circular indeterminate color="primary" />
            </div>

            <!-- No threads available -->
            <v-alert v-else-if="availableThreads.length === 0" type="info" variant="tonal" density="compact">
              {{ $t('scenarioManager.data.noAvailableThreads') }}
            </v-alert>

            <!-- Thread selection -->
            <div v-else class="thread-selection">
              <v-text-field
                v-model="availableSearch"
                :placeholder="$t('scenarioManager.data.searchAvailable')"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="compact"
                hide-details
                clearable
                class="mb-3"
              />

              <div class="selection-header">
                <v-checkbox
                  v-model="selectAll"
                  :label="$t('scenarioManager.data.selectAll')"
                  density="compact"
                  hide-details
                  @change="toggleSelectAll"
                />
                <span class="selection-count">
                  {{ selectedThreadIds.length }} / {{ filteredAvailableThreads.length }}
                  {{ $t('scenarioManager.data.selected') }}
                </span>
              </div>

              <div class="thread-list">
                <div
                  v-for="thread in filteredAvailableThreads.slice(0, 50)"
                  :key="thread.thread_id"
                  class="thread-select-item"
                  :class="{ selected: selectedThreadIds.includes(thread.thread_id) }"
                  @click="toggleThread(thread.thread_id)"
                >
                  <v-checkbox
                    :model-value="selectedThreadIds.includes(thread.thread_id)"
                    density="compact"
                    hide-details
                    @click.stop
                    @change="toggleThread(thread.thread_id)"
                  />
                  <div class="thread-info">
                    <span class="thread-subject">{{ thread.subject || $t('scenarioManager.data.noSubject') }}</span>
                    <span class="thread-meta">
                      <LIcon size="12">mdi-message-outline</LIcon>
                      {{ thread.message_count || 0 }}
                      <span v-if="thread.sender" class="ml-2">
                        <LIcon size="12">mdi-account-outline</LIcon>
                        {{ thread.sender }}
                      </span>
                    </span>
                  </div>
                </div>
              </div>

              <div v-if="filteredAvailableThreads.length > 50" class="text-caption text-center mt-2">
                {{ $t('scenarioManager.data.showingFirst', { count: 50, total: filteredAvailableThreads.length }) }}
              </div>
            </div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="closeImportDialog" :disabled="importing">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="primary" :disabled="!canImport || importing" :loading="importing" @click="doImport">
            {{ $t('scenarioManager.data.import') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useDataImport } from '../../composables/useDataImport'
import { useScenarioManager } from '../../composables/useScenarioManager'

const props = defineProps({
  scenario: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['data-imported'])

const { t } = useI18n()

// Import composable
const {
  importing,
  importProgress,
  importError,
  importFileToScenario,
  resetImport
} = useDataImport()

const {
  getAvailableThreads,
  addThreadsToScenario
} = useScenarioManager()

// State
const showImportDialog = ref(false)
const importMethod = ref('file')
const uploadFile = ref(null)
const loadingThreads = ref(false)
const searchQuery = ref('')
const sortBy = ref('date_desc')
const threads = ref([])
const threadsError = ref(null)

// State for existing threads import
const loadingAvailable = ref(false)
const availableThreads = ref([])
const selectedThreadIds = ref([])
const selectAll = ref(false)
const availableSearch = ref('')

// Sort options
const sortOptions = computed(() => [
  { label: t('scenarioManager.data.sortNewest'), value: 'date_desc' },
  { label: t('scenarioManager.data.sortOldest'), value: 'date_asc' },
  { label: t('scenarioManager.data.sortSubject'), value: 'subject' }
])

// Table headers
const tableHeaders = computed(() => [
  { title: t('scenarioManager.data.subject'), key: 'subject', sortable: true },
  { title: t('scenarioManager.data.sender'), key: 'sender', sortable: true },
  { title: t('scenarioManager.data.date'), key: 'created_at', sortable: true },
  { title: t('scenarioManager.data.statusHeader'), key: 'status', sortable: true },
  { title: '', key: 'actions', sortable: false, width: 100 }
])

// Computed
const canImport = computed(() => {
  if (importMethod.value === 'file') {
    return uploadFile.value !== null
  }
  if (importMethod.value === 'existing') {
    return selectedThreadIds.value.length > 0
  }
  return false
})

const filteredAvailableThreads = computed(() => {
  if (!availableSearch.value) return availableThreads.value
  const query = availableSearch.value.toLowerCase()
  return availableThreads.value.filter(t =>
    t.subject?.toLowerCase().includes(query) ||
    t.sender?.toLowerCase().includes(query)
  )
})

const filteredThreads = computed(() => {
  let result = threads.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t =>
      t.subject?.toLowerCase().includes(query) ||
      t.sender?.toLowerCase().includes(query)
    )
  }
  return result
})

// Methods
function getStatusVariant(status) {
  const map = {
    pending: 'default',
    evaluated: 'success',
    in_progress: 'info'
  }
  return map[status] || 'default'
}

function viewThread(thread) {
  // TODO: Open thread detail view
  console.log('View thread:', thread)
}

function confirmRemoveThread(thread) {
  // TODO: Confirm and remove thread
  console.log('Remove thread:', thread)
}

/**
 * Load available threads for import from existing data
 */
async function loadAvailableThreads() {
  if (!props.scenario?.id) return

  loadingAvailable.value = true
  try {
    const result = await getAvailableThreads(props.scenario.id, { per_page: 200 })
    availableThreads.value = result.threads || []
  } catch (error) {
    console.error('Failed to load available threads:', error)
    availableThreads.value = []
  } finally {
    loadingAvailable.value = false
  }
}

function toggleThread(threadId) {
  const index = selectedThreadIds.value.indexOf(threadId)
  if (index === -1) {
    selectedThreadIds.value.push(threadId)
  } else {
    selectedThreadIds.value.splice(index, 1)
  }
  selectAll.value = selectedThreadIds.value.length === filteredAvailableThreads.value.length
}

function toggleSelectAll() {
  if (selectAll.value) {
    selectedThreadIds.value = filteredAvailableThreads.value.map(t => t.thread_id)
  } else {
    selectedThreadIds.value = []
  }
}

/**
 * Import selected existing threads
 */
async function importExistingThreads() {
  if (!props.scenario?.id || selectedThreadIds.value.length === 0) return

  try {
    await addThreadsToScenario(props.scenario.id, selectedThreadIds.value)

    // Success
    showImportDialog.value = false
    selectedThreadIds.value = []
    availableThreads.value = []
    emit('data-imported')

    // Reload threads after import
    await loadThreads()
  } catch (error) {
    console.error('Import failed:', error)
  }
}

/**
 * Load threads for the current scenario.
 */
async function loadThreads() {
  if (!props.scenario?.id) return

  loadingThreads.value = true
  threadsError.value = null

  try {
    const response = await axios.get(`/api/scenarios/${props.scenario.id}/threads`, {
      params: {
        per_page: 100,
        search: searchQuery.value || undefined
      }
    })
    threads.value = response.data.threads || []
  } catch (error) {
    console.error('Failed to load threads:', error)
    threadsError.value = error.response?.data?.error || error.message
    threads.value = []
  } finally {
    loadingThreads.value = false
  }
}

async function doImport() {
  if (!props.scenario?.id) return

  // Handle existing threads import
  if (importMethod.value === 'existing') {
    await importExistingThreads()
    return
  }

  // Handle file import
  if (!uploadFile.value) return

  try {
    // Get the file from v-file-input (it returns an array)
    const file = Array.isArray(uploadFile.value) ? uploadFile.value[0] : uploadFile.value

    if (!file) {
      console.error('No file selected')
      return
    }

    await importFileToScenario(file, {
      scenarioId: props.scenario.id,
      taskType: props.scenario.function_type_name
    })

    // Success
    showImportDialog.value = false
    uploadFile.value = null
    emit('data-imported')

    // Reload threads after import
    await loadThreads()
  } catch (error) {
    console.error('Import failed:', error)
    // Error is handled by the composable and stored in importError
  }
}

/**
 * Close import dialog and reset state.
 */
function closeImportDialog() {
  showImportDialog.value = false
  uploadFile.value = null
  selectedThreadIds.value = []
  availableThreads.value = []
  resetImport()
}

// Load available threads when switching to existing import mode
watch(importMethod, (newMethod) => {
  if (newMethod === 'existing' && props.scenario?.id) {
    loadAvailableThreads()
  }
})

// Load threads when scenario changes or on mount
watch(() => props.scenario?.id, (newId) => {
  if (newId) {
    loadThreads()
  }
}, { immediate: true })

// Reload threads when search changes (with debounce)
let searchTimeout = null
watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadThreads()
  }, 300)
})

onMounted(() => {
  if (props.scenario?.id) {
    loadThreads()
  }
})
</script>

<style scoped>
.data-tab {
  max-width: 1200px;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.tab-header h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

/* Data Stats */
.data-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 10px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  background-color: rgb(var(--v-theme-surface));
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 12px;
}

.empty-state h3 {
  margin: 16px 0 8px;
  font-size: 1.1rem;
  font-weight: 600;
}

.empty-state p {
  margin-bottom: 24px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  max-width: 400px;
}

/* Threads Section */
.threads-section {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.threads-header {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.search-field {
  flex: 1;
  max-width: 300px;
}

.sort-select {
  width: 180px;
}

.thread-subject {
  display: flex;
  align-items: center;
  gap: 8px;
}

.subject-text {
  font-weight: 500;
}

.message-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Import Dialog */
.import-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.import-option {
  padding: 24px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.import-option:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.import-option.selected {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.import-option h4 {
  margin: 12px 0 8px;
  font-size: 1rem;
}

.import-option p {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
}

.import-content {
  margin-top: 16px;
}

/* Thread Selection for existing import */
.thread-selection {
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  margin-bottom: 8px;
}

.selection-count {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.thread-list {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
}

.thread-select-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.thread-select-item:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
}

.thread-select-item.selected {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.thread-select-item .thread-info {
  flex: 1;
  min-width: 0;
}

.thread-select-item .thread-subject {
  display: block;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.thread-select-item .thread-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 2px;
}
</style>
