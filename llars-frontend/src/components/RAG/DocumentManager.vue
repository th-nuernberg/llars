<template>
  <v-card>
    <v-card-title class="d-flex align-center pa-4">
      <LIcon icon="mdi-file-document-multiple" class="mr-2"></LIcon>
      {{ $t('rag.documentManager.title') }}
      <v-spacer></v-spacer>
      <LBtn
        variant="primary"
        prepend-icon="mdi-upload"
        @click="$emit('upload')"
      >
        {{ $t('rag.documentManager.upload') }}
      </LBtn>
    </v-card-title>

    <v-divider></v-divider>

    <!-- Filter Section -->
    <v-card-text class="pa-4">
      <v-row>
        <v-col cols="12" md="4">
          <v-select
            v-model="selectedCollection"
            :label="$t('rag.documentManager.filterCollection')"
            :items="collectionItems"
            variant="outlined"
            density="comfortable"
            clearable
          ></v-select>
        </v-col>

        <v-col cols="12" md="4">
          <v-select
            v-model="selectedStatus"
            :label="$t('rag.documentManager.filterStatus')"
            :items="statusItems"
            variant="outlined"
            density="comfortable"
            clearable
          >
            <template v-slot:selection="{ item }">
              <v-chip :color="item.raw.color" size="small">{{ item.raw.title }}</v-chip>
            </template>
            <template v-slot:item="{ item, props }">
              <v-list-item v-bind="props">
                <template v-slot:prepend>
                  <v-chip :color="item.raw.color" size="small">{{ item.raw.title }}</v-chip>
                </template>
              </v-list-item>
            </template>
          </v-select>
        </v-col>

        <v-col cols="12" md="4">
          <v-text-field
            v-model="search"
            :label="$t('rag.documentManager.search')"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="comfortable"
            clearable
          ></v-text-field>
        </v-col>
      </v-row>

      <!-- Bulk Actions -->
      <v-row v-if="selected.length > 0" class="mt-2">
        <v-col cols="12">
          <v-alert type="info" variant="tonal" density="compact">
            <div class="d-flex align-center">
              <span>{{ $t('rag.documentManager.selectedCount', { count: selected.length }) }}</span>
              <v-spacer></v-spacer>
              <LBtn
                variant="danger"
                size="small"
                prepend-icon="mdi-delete"
                @click="handleBulkDelete"
              >
                {{ $t('rag.documentManager.deleteSelected') }}
              </LBtn>
            </div>
          </v-alert>
        </v-col>
      </v-row>
    </v-card-text>

    <v-divider></v-divider>

    <!-- Table -->
    <v-skeleton-loader
      v-if="loading"
      type="table-heading, table-thead, table-tbody"
    ></v-skeleton-loader>

    <v-data-table
      v-else
      v-model="selected"
      :headers="headers"
      :items="filteredDocuments"
      :search="search"
      item-value="id"
      show-select
      :items-per-page="10"
      class="elevation-0"
    >
      <!-- Dateiname mit Icon -->
      <template v-slot:item.filename="{ item }">
        <div class="d-flex align-center">
          <LIcon :icon="getFileIcon(item.file_type)" :color="getFileColor(item.file_type)" class="mr-2"></LIcon>
          <span>{{ item.filename }}</span>
        </div>
      </template>

      <!-- Collection Badge -->
      <template v-slot:item.collection="{ item }">
        <LTag
          :variant="getCollectionVariant(item.collection_name)"
          size="sm"
        >
          {{ getCollectionDisplayName(item.collection_name) }}
        </LTag>
      </template>

      <!-- Größe formatiert -->
      <template v-slot:item.file_size="{ item }">
        {{ formatSize(item.file_size) }}
      </template>

      <!-- Status Badge -->
      <template v-slot:item.status="{ item }">
        <LTag
          :variant="getStatusVariant(item.status)"
          size="sm"
        >
          {{ getStatusText(item.status) }}
        </LTag>
      </template>

      <!-- Chunks -->
      <template v-slot:item.chunk_count="{ item }">
        <LTag variant="gray" size="sm">
          {{ item.chunk_count || 0 }}
        </LTag>
      </template>

      <!-- Abrufe -->
      <template v-slot:item.retrieval_count="{ item }">
        {{ item.retrieval_count || 0 }}
      </template>

      <!-- Datum formatiert -->
      <template v-slot:item.uploaded_at="{ item }">
        {{ formatDate(item.uploaded_at) }}
      </template>

      <!-- Aktionen -->
      <template v-slot:item.actions="{ item }">
        <LActionGroup
          :actions="['view', 'download', 'delete']"
          @action="(key) => handleDocumentAction(key, item)"
        />
      </template>

      <!-- Empty State -->
      <template v-slot:no-data>
        <div class="text-center pa-8">
          <LIcon size="64" color="grey-lighten-1" class="mb-4">mdi-file-document-multiple-outline</LIcon>
          <div class="text-h6 mb-2">{{ $t('rag.documentManager.empty.title') }}</div>
          <div class="text-medium-emphasis mb-4">
            {{ search || selectedCollection || selectedStatus ? $t('rag.documentManager.empty.hintFilter') : $t('rag.documentManager.empty.hintUpload') }}
          </div>
          <LBtn
            v-if="!search && !selectedCollection && !selectedStatus"
            variant="primary"
            prepend-icon="mdi-upload"
            @click="$emit('upload')"
          >
            {{ $t('rag.documentManager.empty.uploadFirst') }}
          </LBtn>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  documents: {
    type: Array,
    default: () => []
  },
  collections: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  initialCollectionFilter: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['upload', 'view', 'delete', 'download'])

const selected = ref([])
const search = ref('')
const selectedCollection = ref(null)
const selectedStatus = ref(null)

const headers = computed(() => [
  { title: t('rag.documentManager.headers.filename'), key: 'filename', sortable: true },
  { title: t('rag.documentManager.headers.collection'), key: 'collection', sortable: true },
  { title: t('rag.documentManager.headers.size'), key: 'file_size', sortable: true },
  { title: t('rag.documentManager.headers.status'), key: 'status', sortable: true },
  { title: t('rag.documentManager.headers.chunks'), key: 'chunk_count', sortable: true },
  { title: t('rag.documentManager.headers.retrievals'), key: 'retrieval_count', sortable: true },
  { title: t('rag.documentManager.headers.uploaded'), key: 'uploaded_at', sortable: true },
  { title: t('rag.documentManager.headers.actions'), key: 'actions', sortable: false, align: 'end' }
])

const collectionItems = computed(() => {
  return props.collections.map(c => ({
    value: c.name,
    title: c.display_name || c.name
  }))
})

const statusItems = computed(() => [
  { value: 'pending', title: t('rag.documentManager.status.pending'), color: 'warning' },
  { value: 'processing', title: t('rag.documentManager.status.processing'), color: 'info' },
  { value: 'indexed', title: t('rag.documentManager.status.indexed'), color: 'success' },
  { value: 'failed', title: t('rag.documentManager.status.failed'), color: 'error' }
])

const filteredDocuments = computed(() => {
  let filtered = [...props.documents]

  if (selectedCollection.value) {
    filtered = filtered.filter(d => d.collection_name === selectedCollection.value)
  }

  if (selectedStatus.value) {
    filtered = filtered.filter(d => d.status === selectedStatus.value)
  }

  return filtered
})

const getFileIcon = (fileType) => {
  const iconMap = {
    'pdf': 'mdi-file-pdf-box',
    'txt': 'mdi-file-document',
    'md': 'mdi-language-markdown',
    'markdown': 'mdi-language-markdown'
  }
  return iconMap[fileType?.toLowerCase()] || 'mdi-file'
}

const getFileColor = (fileType) => {
  const colorMap = {
    'pdf': 'red',
    'txt': 'blue',
    'md': 'green',
    'markdown': 'green'
  }
  return colorMap[fileType?.toLowerCase()] || 'grey'
}

const getCollectionColor = (collectionName) => {
  const collection = props.collections.find(c => c.name === collectionName)
  return collection?.color || '#1976D2'
}

const getCollectionDisplayName = (collectionName) => {
  const collection = props.collections.find(c => c.name === collectionName)
  return collection?.display_name || collectionName
}

const getStatusColor = (status) => {
  const colorMap = {
    'pending': 'warning',
    'processing': 'info',
    'indexed': 'success',
    'failed': 'error'
  }
  return colorMap[status] || 'grey'
}

const getStatusVariant = (status) => {
  const variantMap = {
    'pending': 'warning',
    'processing': 'info',
    'indexed': 'success',
    'failed': 'danger'
  }
  return variantMap[status] || 'gray'
}

const getCollectionVariant = (collectionName) => {
  // Rotate through variants based on collection name hash
  const variants = ['primary', 'secondary', 'accent', 'info']
  const hash = collectionName?.split('').reduce((a, b) => a + b.charCodeAt(0), 0) || 0
  return variants[hash % variants.length]
}

const getStatusText = (status) => {
  const textMap = {
    'pending': t('rag.documentManager.status.pending'),
    'processing': t('rag.documentManager.status.processing'),
    'indexed': t('rag.documentManager.status.indexed'),
    'failed': t('rag.documentManager.status.failed')
  }
  return textMap[status] || status
}

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Handle action group clicks
const handleDocumentAction = (actionKey, item) => {
  switch (actionKey) {
    case 'view':
      emit('view', item)
      break
    case 'download':
      emit('download', item)
      break
    case 'delete':
      emit('delete', item)
      break
  }
}

const handleBulkDelete = () => {
  emit('delete', selected.value)
}

// Apply initial collection filter
watch(() => props.initialCollectionFilter, (newFilter) => {
  if (newFilter) {
    selectedCollection.value = newFilter
  }
}, { immediate: true })
</script>

<style scoped>
.v-data-table :deep(.v-data-table__td) {
  color: rgb(var(--v-theme-on-surface));
}

.v-data-table :deep(.v-data-table__th) {
  color: rgb(var(--v-theme-on-surface));
}
</style>
