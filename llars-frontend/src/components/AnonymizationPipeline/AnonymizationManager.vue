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

          <!-- Bulk Actions -->
          <div v-if="selectedConversations.length > 0" class="ml-auto d-flex gap-2">
            <LBtn
              variant="secondary"
              prepend-icon="mdi-check-all"
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
          </div>

          <!-- Export All Completed -->
          <LBtn
            v-else
            variant="accent"
            prepend-icon="mdi-export-variant"
            class="ml-auto"
            @click="exportAllCompleted"
          >
            Export All Completed
          </LBtn>
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

        <!-- Imported Date -->
        <template #[`item.imported_at`]="{ item }">
          {{ formatDate(item.imported_at) }}
        </template>

        <!-- Actions -->
        <template #[`item.actions`]="{ item }">
          <LActionGroup
            :actions="['view', 'edit']"
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
            Only anonymized content will be exported (original content excluded).
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
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useSnackbar } from '@/composables/useSnackbar'

const router = useRouter()
const { showSuccess, showError } = useSnackbar()

// State
const conversations = ref([])
const selectedConversations = ref([])
const loading = ref(false)
const totalConversations = ref(0)
const exportDialog = ref(false)
const exportLoading = ref(false)
const exportMode = ref(null) // 'selected' | 'all_completed'
const itemsPerPage = ref(50)

const filters = ref({
  status: null,
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
  { title: 'Imported', key: 'imported_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
]

const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Completed', value: 'completed' },
  { title: 'Error', value: 'error' }
]

const exportCount = computed(() => {
  if (exportMode.value === 'selected') {
    return selectedConversations.value.length
  }
  return conversations.value.filter(c => c.status === 'completed').length
})

// Methods
async function loadConversations() {
  loading.value = true
  try {
    const params = {
      limit: tableOptions.value.itemsPerPage,
      offset: (tableOptions.value.page - 1) * tableOptions.value.itemsPerPage,
      ...(filters.value.status && { status: filters.value.status }),
      ...(filters.value.search && { search: filters.value.search })
    }

    const response = await axios.get('/api/anonymization/conversations', { params })
    conversations.value = response.data.conversations
    totalConversations.value = response.data.total
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
      ...(filters.value.search && { search: filters.value.search })
    }
  })
}

function handleAction(action, item) {
  if (action === 'view' || action === 'edit') {
    router.push({
      path: `/anonymization/${item.id}`,
      query: {
        ...(filters.value.status && { status: filters.value.status }),
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
        ? { conversation_ids: selectedConversations.value }
        : { include_all_completed: true }

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
onMounted(() => {
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

:deep(.v-data-table tbody tr) {
  cursor: pointer;
}

:deep(.v-data-table tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
