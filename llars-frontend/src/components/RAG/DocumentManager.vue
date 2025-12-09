<template>
  <v-card>
    <v-card-title class="d-flex align-center pa-4">
      <v-icon icon="mdi-file-document-multiple" class="mr-2"></v-icon>
      Dokumente
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        prepend-icon="mdi-upload"
        @click="$emit('upload')"
      >
        Hochladen
      </v-btn>
    </v-card-title>

    <v-divider></v-divider>

    <!-- Filter Section -->
    <v-card-text class="pa-4">
      <v-row>
        <v-col cols="12" md="4">
          <v-select
            v-model="selectedCollection"
            label="Collection filtern"
            :items="collectionItems"
            variant="outlined"
            density="comfortable"
            clearable
          ></v-select>
        </v-col>

        <v-col cols="12" md="4">
          <v-select
            v-model="selectedStatus"
            label="Status filtern"
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
            label="Suche"
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
              <span>{{ selected.length }} Dokument(e) ausgewählt</span>
              <v-spacer></v-spacer>
              <v-btn
                color="error"
                variant="text"
                prepend-icon="mdi-delete"
                @click="handleBulkDelete"
              >
                Ausgewählte löschen
              </v-btn>
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
          <v-icon :icon="getFileIcon(item.file_type)" :color="getFileColor(item.file_type)" class="mr-2"></v-icon>
          <span>{{ item.filename }}</span>
        </div>
      </template>

      <!-- Collection Badge -->
      <template v-slot:item.collection="{ item }">
        <v-chip
          size="small"
          :color="getCollectionColor(item.collection_name)"
        >
          {{ getCollectionDisplayName(item.collection_name) }}
        </v-chip>
      </template>

      <!-- Größe formatiert -->
      <template v-slot:item.file_size="{ item }">
        {{ formatSize(item.file_size) }}
      </template>

      <!-- Status Badge -->
      <template v-slot:item.status="{ item }">
        <v-chip
          size="small"
          :color="getStatusColor(item.status)"
        >
          {{ getStatusText(item.status) }}
        </v-chip>
      </template>

      <!-- Chunks -->
      <template v-slot:item.chunk_count="{ item }">
        <v-chip size="small" variant="outlined">
          {{ item.chunk_count || 0 }}
        </v-chip>
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
        <v-btn
          icon="mdi-eye"
          size="small"
          variant="text"
          @click="$emit('view', item)"
        ></v-btn>
        <v-btn
          icon="mdi-download"
          size="small"
          variant="text"
          @click="$emit('download', item)"
        ></v-btn>
        <v-btn
          icon="mdi-delete"
          size="small"
          variant="text"
          color="error"
          @click="$emit('delete', item)"
        ></v-btn>
      </template>

      <!-- Empty State -->
      <template v-slot:no-data>
        <div class="text-center pa-8">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-file-document-multiple-outline</v-icon>
          <div class="text-h6 mb-2">Keine Dokumente gefunden</div>
          <div class="text-medium-emphasis mb-4">
            {{ search || selectedCollection || selectedStatus ? 'Versuchen Sie, Ihre Filter anzupassen.' : 'Laden Sie Ihr erstes Dokument hoch.' }}
          </div>
          <v-btn
            v-if="!search && !selectedCollection && !selectedStatus"
            color="primary"
            prepend-icon="mdi-upload"
            @click="$emit('upload')"
          >
            Dokument hochladen
          </v-btn>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

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

const headers = [
  { title: 'Dateiname', key: 'filename', sortable: true },
  { title: 'Collection', key: 'collection', sortable: true },
  { title: 'Größe', key: 'file_size', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Chunks', key: 'chunk_count', sortable: true },
  { title: 'Abrufe', key: 'retrieval_count', sortable: true },
  { title: 'Hochgeladen', key: 'uploaded_at', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
]

const collectionItems = computed(() => {
  return props.collections.map(c => ({
    value: c.name,
    title: c.display_name || c.name
  }))
})

const statusItems = [
  { value: 'pending', title: 'Ausstehend', color: 'warning' },
  { value: 'processing', title: 'Verarbeitung', color: 'info' },
  { value: 'indexed', title: 'Indexiert', color: 'success' },
  { value: 'failed', title: 'Fehler', color: 'error' }
]

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

const getStatusText = (status) => {
  const textMap = {
    'pending': 'Ausstehend',
    'processing': 'Verarbeitung',
    'indexed': 'Indexiert',
    'failed': 'Fehler'
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
