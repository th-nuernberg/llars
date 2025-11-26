<template>
  <div class="admin-rag">
    <!-- Stats Cards -->
    <v-row class="mb-4">
      <v-col cols="6" md="3">
        <v-card variant="tonal" color="primary">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-file-document-multiple</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ stats.total_documents }}</div>
              <div class="text-caption">Dokumente</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card variant="tonal" color="success">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-check-circle</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ stats.processed }}</div>
              <div class="text-caption">Verarbeitet</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card variant="tonal" color="info">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-folder-multiple</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ stats.total_collections }}</div>
              <div class="text-caption">Collections</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card variant="tonal" color="warning">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-harddisk</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ formatFileSize(stats.total_size) }}</div>
              <div class="text-caption">Gesamtgröße</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Embedding Model Info Card -->
    <v-card class="mb-4" variant="outlined">
      <v-card-title class="d-flex align-center">
        <v-icon start color="primary">mdi-brain</v-icon>
        Embedding Model
        <v-spacer></v-spacer>
        <v-chip
          :color="embeddingInfo.is_primary ? 'success' : 'warning'"
          size="small"
          variant="flat"
        >
          {{ embeddingInfo.is_primary ? 'LiteLLM Proxy' : 'Fallback (Local)' }}
        </v-chip>
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-list density="compact" class="bg-transparent">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-cube-outline</v-icon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">Aktives Model</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold">{{ embeddingInfo.model_name }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-vector-line</v-icon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">Dimensionen</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold">{{ embeddingInfo.dimensions }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-server</v-icon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">Model Typ</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold text-uppercase">{{ embeddingInfo.model_type }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>
          <v-col cols="12" md="6">
            <v-list density="compact" class="bg-transparent">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon :color="embeddingInfo.litellm_configured ? 'success' : 'warning'" size="small">
                    {{ embeddingInfo.litellm_configured ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                  </v-icon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">LiteLLM Status</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold">
                  {{ embeddingInfo.litellm_configured ? 'Konfiguriert' : 'Nicht konfiguriert' }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="embeddingInfo.litellm_configured">
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-link</v-icon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">LiteLLM URL</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold text-truncate" style="max-width: 300px;">
                  {{ embeddingInfo.litellm_base_url }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-swap-horizontal</v-icon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">Fallback Model</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold">{{ embeddingInfo.fallback_model }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
        <v-divider class="my-2"></v-divider>
        <v-row>
          <v-col cols="12">
            <div class="d-flex align-center">
              <v-icon size="small" color="grey" class="mr-2">mdi-folder-open</v-icon>
              <span class="text-caption text-medium-emphasis mr-2">Collection:</span>
              <code class="text-caption">{{ embeddingInfo.collection_name }}</code>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-btn
          variant="text"
          size="small"
          @click="fetchEmbeddingInfo"
          :loading="loadingEmbeddingInfo"
        >
          <v-icon start size="small">mdi-refresh</v-icon>
          Aktualisieren
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Tabs for Documents and Upload -->
    <v-card>
      <v-tabs v-model="activeTab" bg-color="primary">
        <v-tab value="documents">
          <v-icon start>mdi-file-document</v-icon>
          Dokumente
        </v-tab>
        <v-tab value="collections">
          <v-icon start>mdi-folder</v-icon>
          Collections
        </v-tab>
        <v-tab value="upload">
          <v-icon start>mdi-upload</v-icon>
          Hochladen
        </v-tab>
      </v-tabs>

      <v-window v-model="activeTab">
        <!-- Documents Tab -->
        <v-window-item value="documents">
          <v-card-text>
            <v-row class="mb-4">
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="documentSearch"
                  label="Dokument suchen"
                  prepend-inner-icon="mdi-magnify"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="collectionFilter"
                  :items="collectionOptions"
                  label="Collection Filter"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                ></v-select>
              </v-col>
              <v-col cols="12" md="4" class="d-flex justify-end">
                <v-btn color="primary" @click="fetchDocuments" :loading="loadingDocuments">
                  <v-icon start>mdi-refresh</v-icon>
                  Aktualisieren
                </v-btn>
              </v-col>
            </v-row>

            <v-data-table
              :headers="documentHeaders"
              :items="filteredDocuments"
              :loading="loadingDocuments"
              :items-per-page="10"
            >
              <template v-slot:item.filename="{ item }">
                <div class="d-flex align-center">
                  <v-icon :color="getFileTypeColor(item.file_type)" class="mr-2">
                    {{ getFileTypeIcon(item.file_type) }}
                  </v-icon>
                  <span class="font-weight-medium">{{ item.filename }}</span>
                </div>
              </template>

              <template v-slot:item.file_size="{ item }">
                {{ formatFileSize(item.file_size) }}
              </template>

              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  {{ item.status }}
                </v-chip>
              </template>

              <template v-slot:item.uploaded_at="{ item }">
                {{ formatDate(item.uploaded_at) }}
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="error"
                  @click="confirmDeleteDocument(item)"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- Collections Tab -->
        <v-window-item value="collections">
          <v-card-text>
            <v-row class="mb-4">
              <v-col cols="12" md="8">
                <v-text-field
                  v-model="newCollectionName"
                  label="Neue Collection erstellen"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  placeholder="Collection-Name eingeben"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-btn
                  color="primary"
                  @click="createCollection"
                  :loading="creatingCollection"
                  :disabled="!newCollectionName"
                  block
                  height="48"
                >
                  <v-icon start>mdi-plus</v-icon>
                  Collection erstellen
                </v-btn>
              </v-col>
            </v-row>

            <v-data-table
              :headers="collectionHeaders"
              :items="collections"
              :loading="loadingCollections"
              :items-per-page="10"
            >
              <template v-slot:item.name="{ item }">
                <div class="d-flex align-center">
                  <v-icon color="primary" class="mr-2">mdi-folder</v-icon>
                  <span class="font-weight-medium">{{ item.name }}</span>
                </div>
              </template>

              <template v-slot:item.document_count="{ item }">
                <v-chip size="small" variant="tonal">
                  {{ item.document_count }} Dokumente
                </v-chip>
              </template>

              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="error"
                  @click="confirmDeleteCollection(item)"
                  :disabled="item.name === 'default'"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- Upload Tab -->
        <v-window-item value="upload">
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="uploadCollection"
                  :items="collectionOptions.filter(c => c !== 'Alle')"
                  label="Ziel-Collection"
                  variant="outlined"
                  prepend-inner-icon="mdi-folder"
                ></v-select>
              </v-col>
            </v-row>

            <v-file-input
              v-model="filesToUpload"
              label="Dateien auswählen"
              variant="outlined"
              prepend-icon="mdi-paperclip"
              multiple
              show-size
              :accept="acceptedFileTypes"
              @update:modelValue="handleFileSelect"
            >
              <template v-slot:selection="{ fileNames }">
                <v-chip
                  v-for="fileName in fileNames"
                  :key="fileName"
                  class="ma-1"
                  size="small"
                  closable
                >
                  {{ fileName }}
                </v-chip>
              </template>
            </v-file-input>

            <v-alert type="info" variant="tonal" class="mb-4">
              <strong>Unterstützte Formate:</strong> PDF, TXT, MD, DOCX, DOC
              <br>
              <strong>Maximale Dateigröße:</strong> 50 MB pro Datei
            </v-alert>

            <v-btn
              color="primary"
              size="large"
              @click="uploadFiles"
              :loading="uploading"
              :disabled="!filesToUpload || filesToUpload.length === 0"
            >
              <v-icon start>mdi-upload</v-icon>
              {{ filesToUpload?.length || 0 }} Datei(en) hochladen
            </v-btn>

            <!-- Upload Progress -->
            <v-progress-linear
              v-if="uploading"
              :model-value="uploadProgress"
              color="primary"
              height="20"
              class="mt-4"
              rounded
            >
              <template v-slot:default="{ value }">
                {{ Math.round(value) }}%
              </template>
            </v-progress-linear>
          </v-card-text>
        </v-window-item>
      </v-window>
    </v-card>

    <!-- Delete Document Dialog -->
    <v-dialog v-model="deleteDocDialog" max-width="400">
      <v-card>
        <v-card-title>Dokument löschen?</v-card-title>
        <v-card-text>
          Möchten Sie "{{ documentToDelete?.filename }}" wirklich löschen?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDocDialog = false">Abbrechen</v-btn>
          <v-btn color="error" @click="deleteDocument" :loading="deletingDocument">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Collection Dialog -->
    <v-dialog v-model="deleteCollDialog" max-width="400">
      <v-card>
        <v-card-title>Collection löschen?</v-card-title>
        <v-card-text>
          Möchten Sie die Collection "{{ collectionToDelete?.name }}" und alle enthaltenen Dokumente löschen?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteCollDialog = false">Abbrechen</v-btn>
          <v-btn color="error" @click="deleteCollection" :loading="deletingCollection">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

// State
const activeTab = ref('documents');
const stats = ref({
  total_documents: 0,
  processed: 0,
  total_collections: 0,
  total_size: 0
});

// Embedding Info
const embeddingInfo = ref({
  model_name: 'Loading...',
  model_type: '-',
  dimensions: 0,
  is_primary: false,
  primary_model: '-',
  fallback_model: '-',
  litellm_configured: false,
  litellm_base_url: '-',
  vectorstore_dir: '-',
  collection_name: '-'
});
const loadingEmbeddingInfo = ref(false);

// Documents
const documents = ref([]);
const documentSearch = ref('');
const collectionFilter = ref(null);
const loadingDocuments = ref(false);

// Collections
const collections = ref([]);
const loadingCollections = ref(false);
const newCollectionName = ref('');
const creatingCollection = ref(false);

// Upload
const filesToUpload = ref([]);
const uploadCollection = ref('default');
const uploading = ref(false);
const uploadProgress = ref(0);
const acceptedFileTypes = '.pdf,.txt,.md,.docx,.doc';

// Delete dialogs
const deleteDocDialog = ref(false);
const documentToDelete = ref(null);
const deletingDocument = ref(false);
const deleteCollDialog = ref(false);
const collectionToDelete = ref(null);
const deletingCollection = ref(false);

// Table headers
const documentHeaders = [
  { title: 'Dateiname', key: 'filename', sortable: true },
  { title: 'Collection', key: 'collection_name', sortable: true },
  { title: 'Größe', key: 'file_size', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Hochgeladen', key: 'uploaded_at', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
];

const collectionHeaders = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Dokumente', key: 'document_count', sortable: true },
  { title: 'Erstellt', key: 'created_at', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
];

// Computed
const collectionOptions = computed(() => {
  const options = ['Alle', ...collections.value.map(c => c.name)];
  return options;
});

const filteredDocuments = computed(() => {
  return documents.value.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(documentSearch.value.toLowerCase());
    const matchesCollection = !collectionFilter.value || collectionFilter.value === 'Alle' ||
      doc.collection_name === collectionFilter.value;
    return matchesSearch && matchesCollection;
  });
});

// Helper functions
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getFileTypeIcon = (type) => {
  const icons = {
    'pdf': 'mdi-file-pdf-box',
    'txt': 'mdi-file-document-outline',
    'md': 'mdi-language-markdown',
    'docx': 'mdi-file-word',
    'doc': 'mdi-file-word'
  };
  return icons[type] || 'mdi-file';
};

const getFileTypeColor = (type) => {
  const colors = {
    'pdf': 'red',
    'txt': 'grey',
    'md': 'blue',
    'docx': 'blue',
    'doc': 'blue'
  };
  return colors[type] || 'grey';
};

const getStatusColor = (status) => {
  const colors = {
    'processed': 'success',
    'pending': 'warning',
    'processing': 'info',
    'error': 'error'
  };
  return colors[status] || 'grey';
};

// API calls
const fetchEmbeddingInfo = async () => {
  loadingEmbeddingInfo.value = true;
  try {
    const response = await axios.get('/api/rag/embedding-info');
    if (response.data.success && response.data.embedding) {
      embeddingInfo.value = response.data.embedding;
    }
  } catch (error) {
    console.error('Error fetching embedding info:', error);
    embeddingInfo.value = {
      model_name: 'Error loading',
      model_type: 'error',
      dimensions: 0,
      is_primary: false,
      primary_model: '-',
      fallback_model: '-',
      litellm_configured: false,
      litellm_base_url: '-',
      vectorstore_dir: '-',
      collection_name: '-'
    };
  }
  loadingEmbeddingInfo.value = false;
};

const fetchStats = async () => {
  try {
    const response = await axios.get('/api/rag/stats');
    // Transform nested format to flat format expected by template
    const data = response.data;
    if (data.stats) {
      stats.value = {
        total_documents: data.stats.documents?.total || 0,
        processed: data.stats.documents?.by_status?.processed || data.stats.documents?.total || 0,
        total_collections: data.stats.collections?.total || 0,
        total_size: data.stats.documents?.total_size_bytes || 0
      };
    } else {
      // Already flat format
      stats.value = data;
    }
  } catch (error) {
    console.error('Error fetching stats:', error);
  }
};

const fetchDocuments = async () => {
  loadingDocuments.value = true;
  try {
    const response = await axios.get('/api/rag/documents');
    documents.value = response.data.documents || [];
  } catch (error) {
    console.error('Error fetching documents:', error);
  }
  loadingDocuments.value = false;
};

const fetchCollections = async () => {
  loadingCollections.value = true;
  try {
    const response = await axios.get('/api/rag/collections');
    collections.value = response.data.collections || [];
  } catch (error) {
    console.error('Error fetching collections:', error);
  }
  loadingCollections.value = false;
};

const createCollection = async () => {
  if (!newCollectionName.value) return;

  creatingCollection.value = true;
  try {
    await axios.post('/api/rag/collections', { name: newCollectionName.value });
    newCollectionName.value = '';
    await fetchCollections();
    await fetchStats();
  } catch (error) {
    console.error('Error creating collection:', error);
  }
  creatingCollection.value = false;
};

const handleFileSelect = (files) => {
  filesToUpload.value = files;
};

const uploadFiles = async () => {
  if (!filesToUpload.value || filesToUpload.value.length === 0) return;

  uploading.value = true;
  uploadProgress.value = 0;

  const formData = new FormData();
  for (const file of filesToUpload.value) {
    formData.append('files', file);
  }
  formData.append('collection', uploadCollection.value || 'default');

  try {
    await axios.post('/api/rag/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      }
    });

    filesToUpload.value = [];
    await fetchDocuments();
    await fetchStats();
    activeTab.value = 'documents';
  } catch (error) {
    console.error('Error uploading files:', error);
  }

  uploading.value = false;
};

const confirmDeleteDocument = (doc) => {
  documentToDelete.value = doc;
  deleteDocDialog.value = true;
};

const deleteDocument = async () => {
  if (!documentToDelete.value) return;

  deletingDocument.value = true;
  try {
    await axios.delete(`/api/rag/documents/${documentToDelete.value.id}`);
    deleteDocDialog.value = false;
    documentToDelete.value = null;
    await fetchDocuments();
    await fetchStats();
  } catch (error) {
    console.error('Error deleting document:', error);
  }
  deletingDocument.value = false;
};

const confirmDeleteCollection = (coll) => {
  collectionToDelete.value = coll;
  deleteCollDialog.value = true;
};

const deleteCollection = async () => {
  if (!collectionToDelete.value) return;

  deletingCollection.value = true;
  try {
    await axios.delete(`/api/rag/collections/${collectionToDelete.value.id}`);
    deleteCollDialog.value = false;
    collectionToDelete.value = null;
    await fetchCollections();
    await fetchDocuments();
    await fetchStats();
  } catch (error) {
    console.error('Error deleting collection:', error);
  }
  deletingCollection.value = false;
};

onMounted(() => {
  fetchStats();
  fetchDocuments();
  fetchCollections();
  fetchEmbeddingInfo();
});
</script>
