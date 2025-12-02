<template>
  <v-container fluid class="admin-rag">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">
          <v-icon class="mr-2">mdi-database-search</v-icon>
          RAG Dokumentenverwaltung
        </h1>
      </v-col>
    </v-row>

    <!-- Permission denied message -->
    <v-row v-if="!hasPermission('feature:rag:view')">
      <v-col cols="12">
        <v-alert type="error" prominent>
          <v-icon large>mdi-lock</v-icon>
          Sie haben keine Berechtigung, diese Seite zu sehen. Erforderlich: feature:rag:view
        </v-alert>
      </v-col>
    </v-row>

    <!-- Main content -->
    <div v-else>
      <!-- Stats Overview Cards -->
      <v-row class="mb-4">
        <v-col cols="12" md="3">
          <v-card class="stat-card" elevation="2">
            <v-card-text class="text-center">
              <v-icon size="48" color="primary">mdi-folder-multiple</v-icon>
              <div class="text-h4 mt-2">{{ stats.collections?.total || 0 }}</div>
              <div class="text-subtitle-1">Collections</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="3">
          <v-card class="stat-card" elevation="2">
            <v-card-text class="text-center">
              <v-icon size="48" color="success">mdi-file-document-multiple</v-icon>
              <div class="text-h4 mt-2">{{ stats.documents?.total || 0 }}</div>
              <div class="text-subtitle-1">Dokumente</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="3">
          <v-card class="stat-card" elevation="2">
            <v-card-text class="text-center">
              <v-icon size="48" color="info">mdi-harddisk</v-icon>
              <div class="text-h4 mt-2">{{ stats.documents?.total_size_mb || 0 }} MB</div>
              <div class="text-subtitle-1">Speicher</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="3">
          <v-card class="stat-card" elevation="2">
            <v-card-text class="text-center">
              <v-icon size="48" color="warning">mdi-puzzle</v-icon>
              <div class="text-h4 mt-2">{{ stats.documents?.total_chunks || 0 }}</div>
              <div class="text-subtitle-1">Chunks</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Tabs for different sections -->
      <v-tabs v-model="activeTab" bg-color="primary">
        <v-tab value="documents">
          <v-icon left>mdi-file-document</v-icon>
          Dokumente
        </v-tab>
        <v-tab value="collections">
          <v-icon left>mdi-folder</v-icon>
          Collections
        </v-tab>
        <v-tab value="upload">
          <v-icon left>mdi-upload</v-icon>
          Upload
        </v-tab>
        <v-tab value="analytics">
          <v-icon left>mdi-chart-bar</v-icon>
          Analytik
        </v-tab>
      </v-tabs>

      <v-card class="mt-4">
        <v-window v-model="activeTab">
          <!-- Documents Tab -->
          <v-window-item value="documents">
            <v-card-text>
              <!-- Search and filters -->
              <v-row class="mb-4">
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model="searchQuery"
                    label="Dokumente suchen..."
                    prepend-icon="mdi-magnify"
                    clearable
                    @keyup.enter="loadDocuments"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="3">
                  <v-select
                    v-model="filterCollection"
                    :items="collectionsForFilter"
                    item-title="display_name"
                    item-value="id"
                    label="Collection"
                    clearable
                    @update:modelValue="loadDocuments"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="3">
                  <v-select
                    v-model="filterStatus"
                    :items="statusOptions"
                    label="Status"
                    clearable
                    @update:modelValue="loadDocuments"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="2">
                  <v-btn color="primary" block @click="loadDocuments" :loading="loadingDocuments">
                    <v-icon left>mdi-refresh</v-icon>
                    Laden
                  </v-btn>
                </v-col>
              </v-row>

              <!-- Documents data table -->
              <v-data-table
                :headers="documentHeaders"
                :items="documents"
                :loading="loadingDocuments"
                :items-per-page="20"
                class="elevation-1"
              >
                <template v-slot:item.status="{ item }">
                  <v-chip
                    :color="getStatusColor(item.status)"
                    size="small"
                  >
                    {{ item.status }}
                  </v-chip>
                </template>
                <template v-slot:item.file_size_mb="{ item }">
                  {{ item.file_size_mb }} MB
                </template>
                <template v-slot:item.uploaded_at="{ item }">
                  {{ formatDate(item.uploaded_at) }}
                </template>
                <template v-slot:item.actions="{ item }">
                  <v-btn icon size="small" @click="viewDocument(item)" title="Details">
                    <v-icon>mdi-eye</v-icon>
                  </v-btn>
                  <v-btn icon size="small" @click="downloadDocument(item)" title="Download">
                    <v-icon>mdi-download</v-icon>
                  </v-btn>
                  <v-btn
                    v-if="hasPermission('feature:rag:delete')"
                    icon
                    size="small"
                    color="error"
                    @click="confirmDeleteDocument(item)"
                    title="Löschen"
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
                <v-col cols="12" class="d-flex justify-end">
                  <v-btn
                    v-if="hasPermission('feature:rag:edit')"
                    color="success"
                    @click="showCreateCollectionDialog = true"
                  >
                    <v-icon left>mdi-plus</v-icon>
                    Neue Collection
                  </v-btn>
                </v-col>
              </v-row>

              <v-row>
                <v-col
                  v-for="collection in collections"
                  :key="collection.id"
                  cols="12"
                  md="4"
                >
                  <v-card class="collection-card" elevation="3">
                    <v-card-title>
                      <span class="mr-2">{{ collection.icon || '📁' }}</span>
                      {{ collection.display_name }}
                    </v-card-title>
                    <v-card-subtitle>{{ collection.name }}</v-card-subtitle>
                    <v-card-text>
                      <p v-if="collection.description" class="text-body-2 mb-2">
                        {{ collection.description }}
                      </p>
                      <v-chip class="mr-1 mb-1" size="small" color="primary">
                        <v-icon left size="small">mdi-file-document</v-icon>
                        {{ collection.document_count }} Dokumente
                      </v-chip>
                      <v-chip class="mr-1 mb-1" size="small" color="info">
                        <v-icon left size="small">mdi-harddisk</v-icon>
                        {{ collection.total_size_mb }} MB
                      </v-chip>
                      <v-chip class="mb-1" size="small" color="secondary">
                        <v-icon left size="small">mdi-puzzle</v-icon>
                        {{ collection.total_chunks }} Chunks
                      </v-chip>
                    </v-card-text>
                    <v-card-actions>
                      <v-btn size="small" @click="viewCollection(collection)">
                        Details
                      </v-btn>
                      <v-spacer></v-spacer>
                      <v-btn
                        v-if="hasPermission('feature:rag:edit')"
                        icon
                        size="small"
                        @click="editCollection(collection)"
                      >
                        <v-icon>mdi-pencil</v-icon>
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-window-item>

          <!-- Upload Tab -->
          <v-window-item value="upload">
            <v-card-text v-if="hasPermission('feature:rag:edit')">
              <v-row>
                <v-col cols="12" md="8" offset-md="2">
                  <v-card class="upload-zone pa-8" elevation="0" outlined>
                    <div class="text-center">
                      <v-icon size="80" color="primary">mdi-cloud-upload</v-icon>
                      <h3 class="text-h5 mt-4">Dokumente hochladen</h3>
                      <p class="text-body-2 mt-2">
                        Erlaubte Formate: PDF, TXT, MD, DOCX, DOC (max. 50 MB)
                      </p>

                      <v-file-input
                        v-model="filesToUpload"
                        label="Dateien auswählen"
                        prepend-icon="mdi-paperclip"
                        multiple
                        show-size
                        counter
                        accept=".pdf,.txt,.md,.docx,.doc"
                        class="mt-4"
                        :rules="fileRules"
                      ></v-file-input>

                      <v-select
                        v-model="uploadCollectionId"
                        :items="collections"
                        item-title="display_name"
                        item-value="id"
                        label="Collection auswählen"
                        class="mt-4"
                      ></v-select>

                      <v-btn
                        color="primary"
                        size="large"
                        class="mt-4"
                        :loading="uploading"
                        :disabled="!filesToUpload || filesToUpload.length === 0"
                        @click="uploadFiles"
                      >
                        <v-icon left>mdi-upload</v-icon>
                        {{ filesToUpload?.length || 0 }} Datei(en) hochladen
                      </v-btn>
                    </div>
                  </v-card>

                  <!-- Upload results -->
                  <v-card v-if="uploadResults" class="mt-4" elevation="2">
                    <v-card-title>Upload Ergebnis</v-card-title>
                    <v-card-text>
                      <v-alert v-if="uploadResults.uploaded?.length" type="success" class="mb-2">
                        <strong>{{ uploadResults.uploaded.length }}</strong> Datei(en) erfolgreich hochgeladen
                      </v-alert>
                      <v-alert v-if="uploadResults.skipped?.length" type="warning" class="mb-2">
                        <strong>{{ uploadResults.skipped.length }}</strong> Datei(en) übersprungen (Duplikate)
                      </v-alert>
                      <v-alert v-if="uploadResults.errors?.length" type="error" class="mb-2">
                        <strong>{{ uploadResults.errors.length }}</strong> Fehler
                        <ul>
                          <li v-for="err in uploadResults.errors" :key="err.filename">
                            {{ err.filename }}: {{ err.error }}
                          </li>
                        </ul>
                      </v-alert>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
            <v-card-text v-else>
              <v-alert type="warning">
                Sie benötigen die Berechtigung 'feature:rag:edit' zum Hochladen von Dokumenten.
              </v-alert>
            </v-card-text>
          </v-window-item>

          <!-- Analytics Tab -->
          <v-window-item value="analytics">
            <v-card-text>
              <v-row>
                <!-- Popular Documents -->
                <v-col cols="12" md="6">
                  <v-card elevation="2">
                    <v-card-title>
                      <v-icon left>mdi-fire</v-icon>
                      Top Dokumente
                    </v-card-title>
                    <v-card-text>
                      <v-list>
                        <v-list-item
                          v-for="doc in popularDocuments"
                          :key="doc.id"
                          :subtitle="`${doc.retrieval_count} Abrufe`"
                        >
                          <template v-slot:prepend>
                            <v-icon>mdi-file-document</v-icon>
                          </template>
                          <v-list-item-title>{{ doc.title || doc.filename }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item v-if="popularDocuments.length === 0">
                          <v-list-item-title class="text-grey">Keine Daten verfügbar</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- Recent Uploads -->
                <v-col cols="12" md="6">
                  <v-card elevation="2">
                    <v-card-title>
                      <v-icon left>mdi-clock-outline</v-icon>
                      Letzte Uploads
                    </v-card-title>
                    <v-card-text>
                      <v-list>
                        <v-list-item
                          v-for="doc in stats.recent_uploads || []"
                          :key="doc.id"
                          :subtitle="formatDate(doc.uploaded_at)"
                        >
                          <template v-slot:prepend>
                            <v-icon>mdi-file-upload</v-icon>
                          </template>
                          <v-list-item-title>{{ doc.title || doc.filename }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item v-if="!stats.recent_uploads?.length">
                          <v-list-item-title class="text-grey">Keine Uploads</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Status Distribution -->
              <v-row class="mt-4">
                <v-col cols="12" md="6">
                  <v-card elevation="2">
                    <v-card-title>
                      <v-icon left>mdi-chart-pie</v-icon>
                      Status Verteilung
                    </v-card-title>
                    <v-card-text>
                      <div v-for="(count, status) in stats.documents?.by_status || {}" :key="status" class="mb-2">
                        <div class="d-flex justify-space-between">
                          <span>
                            <v-chip :color="getStatusColor(status)" size="small" class="mr-2">{{ status }}</v-chip>
                          </span>
                          <span>{{ count }}</span>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-window-item>
        </v-window>
      </v-card>
    </div>

    <!-- Document Details Dialog -->
    <v-dialog v-model="showDocumentDialog" max-width="800">
      <v-card v-if="selectedDocument">
        <v-card-title>
          <v-icon left>mdi-file-document</v-icon>
          {{ selectedDocument.title || selectedDocument.filename }}
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <strong>Original Dateiname:</strong><br>
              {{ selectedDocument.original_filename }}
            </v-col>
            <v-col cols="6">
              <strong>Größe:</strong><br>
              {{ selectedDocument.file_size_mb }} MB
            </v-col>
            <v-col cols="6">
              <strong>MIME-Type:</strong><br>
              {{ selectedDocument.mime_type }}
            </v-col>
            <v-col cols="6">
              <strong>Status:</strong><br>
              <v-chip :color="getStatusColor(selectedDocument.status)" size="small">
                {{ selectedDocument.status }}
              </v-chip>
            </v-col>
            <v-col cols="6">
              <strong>Collection:</strong><br>
              {{ selectedDocument.collection_name || 'Keine' }}
            </v-col>
            <v-col cols="6">
              <strong>Sprache:</strong><br>
              {{ selectedDocument.language }}
            </v-col>
            <v-col cols="6">
              <strong>Hochgeladen von:</strong><br>
              {{ selectedDocument.uploaded_by || 'System' }}
            </v-col>
            <v-col cols="6">
              <strong>Hochgeladen am:</strong><br>
              {{ formatDate(selectedDocument.uploaded_at) }}
            </v-col>
            <v-col cols="12" v-if="selectedDocument.description">
              <strong>Beschreibung:</strong><br>
              {{ selectedDocument.description }}
            </v-col>
            <v-col cols="6">
              <strong>Chunks:</strong><br>
              {{ selectedDocument.chunk_count }}
            </v-col>
            <v-col cols="6">
              <strong>Abrufe:</strong><br>
              {{ selectedDocument.retrieval_count }}
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="downloadDocument(selectedDocument)">
            <v-icon left>mdi-download</v-icon>
            Download
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="showDocumentDialog = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create Collection Dialog -->
    <v-dialog v-model="showCreateCollectionDialog" max-width="600">
      <v-card>
        <v-card-title>Neue Collection erstellen</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newCollection.name"
            label="Interner Name (ohne Leerzeichen)"
            :rules="[v => !!v || 'Name ist erforderlich', v => /^[a-z0-9_]+$/.test(v) || 'Nur Kleinbuchstaben, Zahlen und _']"
          ></v-text-field>
          <v-text-field
            v-model="newCollection.display_name"
            label="Anzeigename"
            :rules="[v => !!v || 'Anzeigename ist erforderlich']"
          ></v-text-field>
          <v-textarea
            v-model="newCollection.description"
            label="Beschreibung"
            rows="2"
          ></v-textarea>
          <v-text-field
            v-model="newCollection.icon"
            label="Icon (Emoji)"
            maxlength="2"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCreateCollectionDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" @click="createCollection" :loading="creatingCollection">
            Erstellen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6">Dokument löschen?</v-card-title>
        <v-card-text>
          Möchten Sie das Dokument "{{ documentToDelete?.title || documentToDelete?.filename }}" wirklich löschen?
          Diese Aktion kann nicht rückgängig gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDeleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" @click="deleteDocument" :loading="deleting">
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { onMounted } from 'vue';
import { usePermissions } from '@/composables/usePermissions';
import {
  useAdminRAGState,
  useAdminRAGActions,
  useAdminRAGHelpers
} from './AdminRAG/index';

const { hasPermission } = usePermissions();

// Initialize state composable
const state = useAdminRAGState();
const {
  loadingDocuments,
  loadingCollections,
  uploading,
  creatingCollection,
  deleting,
  documents,
  collections,
  stats,
  popularDocuments,
  searchQuery,
  filterCollection,
  filterStatus,
  statusOptions,
  filesToUpload,
  uploadCollectionId,
  uploadResults,
  activeTab,
  showDocumentDialog,
  showCreateCollectionDialog,
  showDeleteDialog,
  selectedDocument,
  documentToDelete,
  newCollection,
  snackbar,
  collectionsForFilter,
  documentHeaders,
  fileRules
} = state;

// Initialize actions composable
const {
  loadDocuments,
  loadCollections,
  loadStats,
  loadPopularDocuments,
  uploadFiles,
  createCollection,
  downloadDocument,
  deleteDocument,
  loadAllData
} = useAdminRAGActions(state);

// Initialize helpers composable
const {
  viewDocument,
  viewCollection: viewCollectionFn,
  editCollection,
  confirmDeleteDocument,
  getStatusColor,
  formatDate
} = useAdminRAGHelpers(state);

// Wrapper for viewCollection to pass loadDocuments
const viewCollection = (collection) => viewCollectionFn(collection, loadDocuments);

// Lifecycle
onMounted(() => {
  if (hasPermission('feature:rag:view')) {
    loadAllData();
  }
});
</script>

<style scoped>
.admin-rag {
  max-width: 1600px;
}

.stat-card {
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.collection-card {
  height: 100%;
}

.upload-zone {
  border: 2px dashed rgba(var(--v-theme-primary), 0.5);
  border-radius: 12px;
  background: rgba(var(--v-theme-primary), 0.02);
}
</style>
