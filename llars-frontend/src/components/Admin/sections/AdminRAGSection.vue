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

    <!-- Processing Queue Card - shows pending/processing documents -->
    <v-card v-if="processingQueue.pending > 0 || processingQueue.processing > 0" class="mb-4" variant="outlined" color="warning">
      <v-card-title class="d-flex align-center">
        <v-icon start color="warning" class="mr-2">mdi-progress-clock</v-icon>
        Embedding-Verarbeitung
        <v-spacer></v-spacer>
        <v-chip color="warning" size="small" variant="flat">
          {{ processingQueue.pending + processingQueue.processing }} in Warteschlange
        </v-chip>
      </v-card-title>
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="8">
            <div class="d-flex align-center mb-2">
              <span class="text-body-2 mr-3">Fortschritt:</span>
              <v-progress-linear
                :model-value="processingProgress"
                color="primary"
                height="20"
                rounded
                striped
              >
                <template v-slot:default>
                  {{ processingQueue.indexed }} / {{ processingQueue.total }} indexiert
                </template>
              </v-progress-linear>
            </div>
            <div class="d-flex gap-4">
              <v-chip size="small" color="warning" variant="tonal">
                <v-icon start size="small">mdi-clock-outline</v-icon>
                {{ processingQueue.pending }} warten
              </v-chip>
              <v-chip size="small" color="info" variant="tonal">
                <v-icon start size="small">mdi-cog</v-icon>
                {{ processingQueue.processing }} werden verarbeitet
              </v-chip>
              <v-chip size="small" color="success" variant="tonal">
                <v-icon start size="small">mdi-check</v-icon>
                {{ processingQueue.indexed }} fertig
              </v-chip>
            </div>
          </v-col>
          <v-col cols="12" md="4" class="text-right">
            <v-btn
              variant="outlined"
              size="small"
              @click="fetchProcessingQueue"
              :loading="loadingQueue"
            >
              <v-icon start size="small">mdi-refresh</v-icon>
              Aktualisieren
            </v-btn>
          </v-col>
        </v-row>
        <v-alert v-if="processingQueue.pending > 0 || processingQueue.processing > 0" type="info" variant="tonal" density="compact" class="mt-3">
          <v-icon start size="small">mdi-information</v-icon>
          Dokumente werden im Hintergrund durch das Embedding-Model verarbeitet. Dies kann einige Minuten dauern.
        </v-alert>
      </v-card-text>
    </v-card>

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
              hover
              @click:row="(event, { item }) => openCollectionDetail(item)"
              class="cursor-pointer"
            >
              <template v-slot:item.name="{ item }">
                <div class="d-flex align-center">
                  <v-icon color="primary" class="mr-2">mdi-folder</v-icon>
                  <span class="font-weight-medium text-primary">{{ item.name }}</span>
                  <v-icon size="small" class="ml-1" color="grey">mdi-open-in-new</v-icon>
                </div>
              </template>

              <template v-slot:item.document_count="{ item }">
                <v-chip size="small" variant="tonal" :color="item.document_count > 0 ? 'success' : 'grey'">
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
                  color="primary"
                  @click.stop="openCollectionDetail(item)"
                  title="Details anzeigen"
                >
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="error"
                  @click.stop="confirmDeleteCollection(item)"
                  :disabled="item.name === 'default' || item.name === 'general'"
                  title="Löschen"
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

    <!-- Collection Detail Dialog -->
    <v-dialog v-model="collectionDetailDialog" max-width="1200" scrollable>
      <v-card v-if="selectedCollection">
        <v-card-title class="d-flex align-center bg-primary">
          <v-icon start color="white">mdi-folder-open</v-icon>
          <span class="text-white">{{ selectedCollection.display_name || selectedCollection.name }}</span>
          <v-spacer></v-spacer>
          <v-btn icon variant="text" color="white" @click="collectionDetailDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text class="pa-0">
          <!-- Collection Info Header -->
          <v-sheet class="pa-4 bg-grey-lighten-4">
            <v-row>
              <v-col cols="12" md="8">
                <div class="text-body-2 text-medium-emphasis mb-1">Beschreibung</div>
                <div class="text-body-1">{{ selectedCollection.description || 'Keine Beschreibung' }}</div>
              </v-col>
              <v-col cols="12" md="4">
                <v-row dense>
                  <v-col cols="6">
                    <v-chip color="primary" variant="flat" size="small" class="mr-1">
                      <v-icon start size="small">mdi-file-document-multiple</v-icon>
                      {{ selectedCollection.document_count }} Dokumente
                    </v-chip>
                  </v-col>
                  <v-col cols="6">
                    <v-chip color="info" variant="flat" size="small">
                      <v-icon start size="small">mdi-harddisk</v-icon>
                      {{ formatFileSize(selectedCollection.total_size_bytes) }}
                    </v-chip>
                  </v-col>
                </v-row>
                <v-row dense class="mt-2">
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis">
                      <v-icon size="x-small" class="mr-1">mdi-puzzle</v-icon>
                      Chunk: {{ selectedCollection.chunk_size || 1000 }} Zeichen, {{ selectedCollection.chunk_overlap || 200 }} Overlap
                    </div>
                  </v-col>
                </v-row>
              </v-col>
            </v-row>
          </v-sheet>

          <v-divider></v-divider>

          <!-- Documents List -->
          <div class="pa-4">
            <div class="d-flex align-center mb-3">
              <h3 class="text-h6">Dokumente in dieser Collection</h3>
              <v-spacer></v-spacer>
              <v-btn
                size="small"
                variant="outlined"
                @click="fetchCollectionDocuments"
                :loading="loadingCollectionDocs"
              >
                <v-icon start size="small">mdi-refresh</v-icon>
                Aktualisieren
              </v-btn>
            </div>

            <v-data-table
              :headers="collectionDocHeaders"
              :items="collectionDocuments"
              :loading="loadingCollectionDocs"
              :items-per-page="10"
              hover
              @click:row="(event, { item }) => openDocumentPreview(item)"
              class="cursor-pointer elevation-1"
            >
              <template v-slot:item.filename="{ item }">
                <div class="d-flex align-center">
                  <v-icon :color="getFileTypeColor(item.file_type || getFileExtension(item.filename))" class="mr-2">
                    {{ getFileTypeIcon(item.file_type || getFileExtension(item.filename)) }}
                  </v-icon>
                  <div>
                    <div class="font-weight-medium text-primary">{{ item.title || item.filename }}</div>
                    <div class="text-caption text-medium-emphasis">{{ item.filename }}</div>
                  </div>
                </div>
              </template>

              <template v-slot:item.file_size="{ item }">
                {{ formatFileSize(item.file_size_bytes || item.file_size) }}
              </template>

              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  <v-icon start size="x-small">{{ getStatusIcon(item.status) }}</v-icon>
                  {{ item.status }}
                </v-chip>
              </template>

              <template v-slot:item.chunk_count="{ item }">
                <v-chip size="small" variant="tonal" color="info">
                  {{ item.chunk_count || 0 }} Chunks
                </v-chip>
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="primary"
                  @click.stop="openDocumentPreview(item)"
                  title="Vorschau"
                >
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="info"
                  @click.stop="downloadDocument(item)"
                  title="Download"
                >
                  <v-icon>mdi-download</v-icon>
                </v-btn>
              </template>

              <template v-slot:no-data>
                <div class="text-center pa-8">
                  <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-folder-open-outline</v-icon>
                  <div class="text-h6 text-grey">Keine Dokumente in dieser Collection</div>
                  <div class="text-body-2 text-grey-darken-1">
                    Laden Sie Dokumente hoch oder starten Sie einen Crawl-Job.
                  </div>
                </div>
              </template>
            </v-data-table>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Document Preview Dialog -->
    <v-dialog v-model="documentPreviewDialog" max-width="1000" scrollable>
      <v-card v-if="previewDocument">
        <v-card-title class="d-flex align-center">
          <v-icon start :color="getFileTypeColor(previewDocument.file_type || getFileExtension(previewDocument.filename))">
            {{ getFileTypeIcon(previewDocument.file_type || getFileExtension(previewDocument.filename)) }}
          </v-icon>
          {{ previewDocument.title || previewDocument.filename }}
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="documentPreviewDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text>
          <!-- Document Metadata -->
          <v-sheet class="pa-3 mb-4 rounded" color="grey-lighten-4">
            <v-row dense>
              <v-col cols="6" md="3">
                <div class="text-caption text-medium-emphasis">Dateiname</div>
                <div class="text-body-2 font-weight-medium">{{ previewDocument.filename }}</div>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-caption text-medium-emphasis">Größe</div>
                <div class="text-body-2">{{ formatFileSize(previewDocument.file_size_bytes || previewDocument.file_size) }}</div>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-caption text-medium-emphasis">Status</div>
                <v-chip :color="getStatusColor(previewDocument.status)" size="x-small">{{ previewDocument.status }}</v-chip>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-caption text-medium-emphasis">Chunks</div>
                <div class="text-body-2">{{ previewDocument.chunk_count || 0 }}</div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-caption text-medium-emphasis">Hochgeladen</div>
                <div class="text-body-2">{{ formatDate(previewDocument.uploaded_at) }}</div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-caption text-medium-emphasis">MIME-Type</div>
                <div class="text-body-2">{{ previewDocument.mime_type || '-' }}</div>
              </v-col>
            </v-row>
          </v-sheet>

          <!-- PDF Preview -->
          <div v-if="isPdfDocument(previewDocument)" class="pdf-preview-container">
            <div class="text-subtitle-1 mb-2 d-flex align-center">
              <v-icon start color="red">mdi-file-pdf-box</v-icon>
              PDF Vorschau
            </div>
            <iframe
              :src="getDocumentPreviewUrl(previewDocument)"
              class="pdf-iframe"
              frameborder="0"
            ></iframe>
          </div>

          <!-- Text/Markdown Preview -->
          <div v-else-if="isTextDocument(previewDocument)" class="text-preview-container">
            <div class="text-subtitle-1 mb-2 d-flex align-center">
              <v-icon start color="blue">mdi-file-document-outline</v-icon>
              Textvorschau
            </div>
            <v-skeleton-loader v-if="loadingPreviewContent" type="paragraph@5"></v-skeleton-loader>
            <pre v-else class="text-preview pa-3 rounded bg-grey-lighten-4">{{ previewContent }}</pre>
          </div>

          <!-- Unsupported Format -->
          <div v-else class="text-center pa-8">
            <v-icon size="64" color="grey">mdi-file-question</v-icon>
            <div class="text-h6 mt-2">Vorschau nicht verfügbar</div>
            <div class="text-body-2 text-grey">
              Für diesen Dateityp ist keine Vorschau möglich.
            </div>
          </div>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-btn
            variant="outlined"
            color="primary"
            @click="downloadDocument(previewDocument)"
          >
            <v-icon start>mdi-download</v-icon>
            Download
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="documentPreviewDialog = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { getSocket } from '@/services/socketService';

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

// Processing Queue
const processingQueue = ref({
  pending: 0,
  processing: 0,
  indexed: 0,
  error: 0,
  total: 0
});
const loadingQueue = ref(false);

// Computed for progress
const processingProgress = computed(() => {
  if (processingQueue.value.total === 0) return 0;
  return (processingQueue.value.indexed / processingQueue.value.total) * 100;
});

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

// Collection Detail Dialog
const collectionDetailDialog = ref(false);
const selectedCollection = ref(null);
const collectionDocuments = ref([]);
const loadingCollectionDocs = ref(false);

// Document Preview Dialog
const documentPreviewDialog = ref(false);
const previewDocument = ref(null);
const previewContent = ref('');
const loadingPreviewContent = ref(false);

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

const collectionDocHeaders = [
  { title: 'Dateiname', key: 'filename', sortable: true },
  { title: 'Größe', key: 'file_size', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Chunks', key: 'chunk_count', sortable: true },
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
    'indexed': 'success',
    'pending': 'warning',
    'processing': 'info',
    'error': 'error'
  };
  return colors[status] || 'grey';
};

const getStatusIcon = (status) => {
  const icons = {
    'processed': 'mdi-check-circle',
    'indexed': 'mdi-check-circle',
    'pending': 'mdi-clock-outline',
    'processing': 'mdi-cog-sync',
    'error': 'mdi-alert-circle'
  };
  return icons[status] || 'mdi-help-circle';
};

const getFileExtension = (filename) => {
  if (!filename) return '';
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
};

const isPdfDocument = (doc) => {
  if (!doc) return false;
  const ext = doc.file_type || getFileExtension(doc.filename);
  return ext === 'pdf' || doc.mime_type === 'application/pdf';
};

const isTextDocument = (doc) => {
  if (!doc) return false;
  const ext = doc.file_type || getFileExtension(doc.filename);
  const textExtensions = ['txt', 'md', 'markdown', 'text'];
  const textMimeTypes = ['text/plain', 'text/markdown'];
  return textExtensions.includes(ext) || textMimeTypes.includes(doc.mime_type);
};

const getDocumentPreviewUrl = (doc) => {
  if (!doc || !doc.id) return '';
  // Return the backend URL for serving the document
  return `/api/rag/documents/${doc.id}/download`;
};

// WebSocket für Echtzeit-Updates
let socket = null;

// WebSocket Event-Handler für Queue-Updates
function handleQueueUpdate(data) {
  if (data.queue) {
    // Verarbeite die Queue-Daten
    const byStatus = {
      pending: 0,
      processing: 0,
      indexed: 0,
      error: 0
    };

    data.queue.forEach(item => {
      if (item.status === 'queued') byStatus.pending++;
      else if (item.status === 'processing') byStatus.processing++;
      else if (item.status === 'completed') byStatus.indexed++;
      else if (item.status === 'failed') byStatus.error++;
    });

    processingQueue.value = {
      pending: byStatus.pending,
      processing: byStatus.processing,
      indexed: byStatus.indexed,
      error: byStatus.error,
      total: data.queue.length
    };

    console.log('[RAG] Queue-Update erhalten:', processingQueue.value);
  }
}

function handleProgressUpdate(data) {
  console.log('[RAG] Progress-Update:', data.queue_id, data.progress_percent + '%', data.current_step);
}

function handleDocumentProcessed(data) {
  console.log('[RAG] Dokument verarbeitet:', data.filename, '-', data.status);
  // Daten aktualisieren
  fetchStats();
  fetchDocuments();
}

// WebSocket Setup
function setupWebSocket() {
  socket = getSocket();

  if (socket) {
    // Event-Listener registrieren
    socket.on('rag:queue_list', handleQueueUpdate);
    socket.on('rag:queue_updated', handleQueueUpdate);
    socket.on('rag:progress', handleProgressUpdate);
    socket.on('rag:document_processed', handleDocumentProcessed);

    // Subscription starten wenn verbunden
    if (socket.connected) {
      socket.emit('rag:subscribe_queue');
      console.log('[RAG] WebSocket subscribed');
    }

    // Bei Reconnect erneut subscriben
    socket.on('connect', () => {
      socket.emit('rag:subscribe_queue');
      console.log('[RAG] WebSocket reconnected und subscribed');
    });
  }
}

// WebSocket Cleanup
function cleanupWebSocket() {
  if (socket) {
    socket.off('rag:queue_list', handleQueueUpdate);
    socket.off('rag:queue_updated', handleQueueUpdate);
    socket.off('rag:progress', handleProgressUpdate);
    socket.off('rag:document_processed', handleDocumentProcessed);
    socket.emit('rag:unsubscribe_queue');
    console.log('[RAG] WebSocket unsubscribed');
  }
}

// API calls
const fetchProcessingQueue = async () => {
  loadingQueue.value = true;
  try {
    const response = await axios.get('/api/rag/stats');
    const data = response.data;
    if (data.stats?.documents?.by_status) {
      const byStatus = data.stats.documents.by_status;
      processingQueue.value = {
        pending: byStatus.pending || 0,
        processing: byStatus.processing || 0,
        indexed: byStatus.indexed || 0,
        error: byStatus.error || 0,
        total: data.stats.documents?.total || 0
      };
    }
  } catch (error) {
    console.error('Error fetching processing queue:', error);
  }
  loadingQueue.value = false;
};

// Polling wurde durch WebSocket ersetzt - diese Funktionen bleiben für Kompatibilität
const startQueuePolling = () => {
  // Polling wurde durch WebSocket ersetzt
  console.log('[RAG] Polling deaktiviert - WebSocket wird verwendet');
};

const stopQueuePolling = () => {
  // Nichts zu tun - Polling ist deaktiviert
};

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

// Collection Detail Functions
const openCollectionDetail = async (collection) => {
  selectedCollection.value = collection;
  collectionDetailDialog.value = true;
  await fetchCollectionDocuments();
};

const fetchCollectionDocuments = async () => {
  if (!selectedCollection.value) return;

  loadingCollectionDocs.value = true;
  try {
    const response = await axios.get(`/api/rag/collections/${selectedCollection.value.id}`);
    // Update selectedCollection with detailed info (including chunk_size, chunk_overlap)
    if (response.data.collection) {
      selectedCollection.value = {
        ...selectedCollection.value,
        ...response.data.collection
      };
      collectionDocuments.value = response.data.collection.documents || [];
    } else {
      collectionDocuments.value = [];
    }
  } catch (error) {
    console.error('Error fetching collection documents:', error);
    collectionDocuments.value = [];
  }
  loadingCollectionDocs.value = false;
};

// Document Preview Functions
const openDocumentPreview = async (doc) => {
  previewDocument.value = doc;
  previewContent.value = '';
  documentPreviewDialog.value = true;

  // Load text content if it's a text document
  if (isTextDocument(doc)) {
    await loadTextContent(doc);
  }
};

const loadTextContent = async (doc) => {
  loadingPreviewContent.value = true;
  try {
    const response = await axios.get(`/api/rag/documents/${doc.id}/content`);
    previewContent.value = response.data.content || 'Inhalt konnte nicht geladen werden.';
  } catch (error) {
    console.error('Error loading document content:', error);
    previewContent.value = 'Fehler beim Laden des Inhalts.';
  }
  loadingPreviewContent.value = false;
};

const downloadDocument = async (doc) => {
  try {
    const response = await axios.get(`/api/rag/documents/${doc.id}/download`, {
      responseType: 'blob'
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', doc.filename || 'document');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading document:', error);
  }
};

onMounted(async () => {
  fetchStats();
  fetchDocuments();
  fetchCollections();
  fetchEmbeddingInfo();

  // Initiales Laden der Queue (Fallback falls WebSocket nicht sofort verbunden)
  await fetchProcessingQueue();

  // WebSocket für Echtzeit-Updates
  setupWebSocket();
});

onUnmounted(() => {
  cleanupWebSocket();
});
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer tbody tr:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.pdf-iframe {
  width: 100%;
  height: 600px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
}

.text-preview {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  max-height: 500px;
  overflow-y: auto;
}

.pdf-preview-container,
.text-preview-container {
  margin-bottom: 16px;
}
</style>
