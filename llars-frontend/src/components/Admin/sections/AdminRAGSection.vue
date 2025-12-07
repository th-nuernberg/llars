<template>
  <div class="admin-rag">
    <!-- Stats Cards -->
    <v-row class="mb-4">
      <v-col cols="6" md="3">
        <v-skeleton-loader v-if="isLoading('stats')" type="card" height="100" />
        <v-card v-else variant="tonal" color="primary">
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
        <v-skeleton-loader v-if="isLoading('stats')" type="card" height="100" />
        <v-card v-else variant="tonal" color="success">
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
        <v-skeleton-loader v-if="isLoading('stats')" type="card" height="100" />
        <v-card v-else variant="tonal" color="info">
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
        <v-skeleton-loader v-if="isLoading('stats')" type="card" height="100" />
        <v-card v-else variant="tonal" color="warning">
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
    <v-skeleton-loader v-if="isLoading('embedding')" type="card" height="250" class="mb-4" />
    <v-card v-else class="mb-4" variant="outlined">
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
        <LBtn
          variant="text"
          size="small"
          @click="fetchEmbeddingInfo"
          :loading="loadingEmbeddingInfo"
          prepend-icon="mdi-refresh"
        >
          Aktualisieren
        </LBtn>
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
            <v-skeleton-loader v-if="isLoading('documents')" type="table" />
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
                <LBtn variant="primary" @click="fetchDocuments" :loading="loadingDocuments" prepend-icon="mdi-refresh">
                  Aktualisieren
                </LBtn>
              </v-col>
            </v-row>

            <v-data-table
              v-if="!isLoading('documents')"
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
                <LIconBtn
                  icon="mdi-delete"
                  variant="danger"
                  tooltip="Löschen"
                  @click="confirmDeleteDocument(item)"
                />
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- Collections Tab -->
        <v-window-item value="collections">
          <v-card-text>
            <v-skeleton-loader v-if="isLoading('collections')" type="table" />
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
                <LBtn
                  variant="primary"
                  @click="createCollection"
                  :loading="creatingCollection"
                  :disabled="!newCollectionName"
                  block
                  prepend-icon="mdi-plus"
                >
                  Collection erstellen
                </LBtn>
              </v-col>
            </v-row>

            <v-data-table
              v-if="!isLoading('collections')"
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
                <LIconBtn
                  icon="mdi-eye"
                  variant="primary"
                  tooltip="Details anzeigen"
                  @click.stop="openCollectionDetail(item)"
                />
                <LIconBtn
                  icon="mdi-delete"
                  variant="danger"
                  tooltip="Löschen"
                  @click.stop="confirmDeleteCollection(item)"
                  :disabled="item.name === 'default' || item.name === 'general'"
                />
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

            <LBtn
              variant="primary"
              size="large"
              @click="uploadFiles"
              :loading="uploading"
              :disabled="!filesToUpload || filesToUpload.length === 0"
              prepend-icon="mdi-upload"
            >
              {{ filesToUpload?.length || 0 }} Datei(en) hochladen
            </LBtn>

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
          <LBtn variant="text" @click="deleteDocDialog = false">Abbrechen</LBtn>
          <LBtn variant="danger" @click="deleteDocument" :loading="deletingDocument">Löschen</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Collection Dialog -->
    <v-dialog v-model="deleteCollDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon color="error" class="mr-2">mdi-delete-alert</v-icon>
          Collection löschen?
        </v-card-title>
        <v-card-text>
          <p>Möchten Sie die Collection "<strong>{{ collectionToDelete?.display_name || collectionToDelete?.name }}</strong>" löschen?</p>
          <v-alert
            v-if="collectionToDelete?.document_count > 0"
            type="warning"
            variant="tonal"
            class="mt-3"
            density="compact"
          >
            <strong>Achtung:</strong> Diese Collection enthält {{ collectionToDelete?.document_count }} Dokument(e).
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <LBtn variant="text" @click="deleteCollDialog = false">Abbrechen</LBtn>
          <LBtn
            v-if="collectionToDelete?.document_count > 0"
            variant="tonal"
            @click="deleteCollection(true)"
            :loading="deletingCollection"
          >
            Inkl. Dokumente löschen
          </LBtn>
          <LBtn
            variant="danger"
            @click="deleteCollection(false)"
            :loading="deletingCollection"
            :disabled="collectionToDelete?.document_count > 0"
          >
            Löschen
          </LBtn>
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
          <LIconBtn icon="mdi-close" @click="collectionDetailDialog = false" />
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

          <!-- Embedding Progress Card - shown when there are pending/processing documents -->
          <v-card
            v-if="collectionEmbeddingProgress.pending > 0 || collectionEmbeddingProgress.processing > 0"
            class="ma-4"
            variant="outlined"
            color="warning"
          >
            <v-card-title class="d-flex align-center py-2">
              <v-icon start color="warning" size="small">mdi-progress-clock</v-icon>
              <span class="text-body-1">Embedding-Verarbeitung</span>
              <v-spacer></v-spacer>
              <v-chip color="warning" size="x-small" variant="flat">
                {{ collectionEmbeddingProgress.pending + collectionEmbeddingProgress.processing }} ausstehend
              </v-chip>
            </v-card-title>
            <v-card-text class="pt-0">
              <div class="d-flex align-center mb-2">
                <span class="text-body-2 mr-3">Fortschritt:</span>
                <v-progress-linear
                  :model-value="collectionEmbeddingProgressPercent"
                  color="primary"
                  height="16"
                  rounded
                  striped
                >
                  <template v-slot:default>
                    <span class="text-caption">{{ collectionEmbeddingProgress.indexed }} / {{ collectionEmbeddingProgress.total }}</span>
                  </template>
                </v-progress-linear>
              </div>
              <div class="d-flex gap-2 flex-wrap">
                <v-chip size="x-small" color="warning" variant="tonal">
                  <v-icon start size="x-small">mdi-clock-outline</v-icon>
                  {{ collectionEmbeddingProgress.pending }} warten
                </v-chip>
                <v-chip size="x-small" color="info" variant="tonal">
                  <v-icon start size="x-small">mdi-cog</v-icon>
                  {{ collectionEmbeddingProgress.processing }} verarbeiten
                </v-chip>
                <v-chip size="x-small" color="success" variant="tonal">
                  <v-icon start size="x-small">mdi-check</v-icon>
                  {{ collectionEmbeddingProgress.indexed }} fertig
                </v-chip>
                <v-chip v-if="collectionEmbeddingProgress.failed > 0" size="x-small" color="error" variant="tonal">
                  <v-icon start size="x-small">mdi-alert</v-icon>
                  {{ collectionEmbeddingProgress.failed }} fehlgeschlagen
                </v-chip>
              </div>
            </v-card-text>
          </v-card>

          <!-- Documents List -->
          <div class="pa-4">
            <div class="d-flex align-center mb-3">
              <h3 class="text-h6">Dokumente in dieser Collection</h3>
              <v-spacer></v-spacer>
              <LBtn
                size="small"
                variant="secondary"
                @click="fetchCollectionDocuments"
                :loading="loadingCollectionDocs"
                prepend-icon="mdi-refresh"
              >
                Aktualisieren
              </LBtn>
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
                <LIconBtn
                  icon="mdi-eye"
                  variant="primary"
                  tooltip="Vorschau"
                  @click.stop="openDocumentPreview(item)"
                />
                <LIconBtn
                  icon="mdi-download"
                  tooltip="Download"
                  @click.stop="downloadDocument(item)"
                />
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
          <LIconBtn icon="mdi-close" @click="documentPreviewDialog = false" />
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
          <LBtn
            variant="secondary"
            @click="downloadDocument(previewDocument)"
            prepend-icon="mdi-download"
          >
            Download
          </LBtn>
          <v-spacer></v-spacer>
          <LBtn variant="text" @click="documentPreviewDialog = false">Schließen</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { getSocket } from '@/services/socketService';
import {
  useRAGStats,
  useRAGDocuments,
  useRAGCollections,
  useRAGHelpers
} from './AdminRAGSection/composables';

// Skeleton Loading
const { isLoading, withLoading } = useSkeletonLoading(['stats', 'embedding', 'collections', 'documents']);

// Local UI State
const activeTab = ref('collections');

// Initialize composables
const {
  stats,
  embeddingInfo,
  loadingEmbeddingInfo,
  processingQueue,
  loadingQueue,
  processingProgress,
  fetchStats,
  fetchEmbeddingInfo,
  fetchProcessingQueue,
  updateQueueFromWebSocket,
  handleDocumentProgress
} = useRAGStats();

const {
  collections,
  loadingCollections,
  newCollectionName,
  creatingCollection,
  deleteCollDialog,
  collectionToDelete,
  deletingCollection,
  collectionDetailDialog,
  selectedCollection,
  collectionDocuments,
  loadingCollectionDocs,
  collectionHeaders,
  collectionDocHeaders,
  fetchCollections,
  createCollection: createCollectionFn,
  confirmDeleteCollection,
  deleteCollection: deleteCollectionFn,
  openCollectionDetail,
  fetchCollectionDocuments
} = useRAGCollections();

const {
  documents,
  documentSearch,
  collectionFilter,
  loadingDocuments,
  filesToUpload,
  uploadCollection,
  uploading,
  uploadProgress,
  deleteDocDialog,
  documentToDelete,
  deletingDocument,
  documentHeaders,
  collectionOptions,
  filteredDocuments,
  fetchDocuments,
  handleFileSelect,
  uploadFiles: uploadFilesFn,
  confirmDeleteDocument,
  deleteDocument: deleteDocumentFn
} = useRAGDocuments(collections);

const {
  formatFileSize,
  formatDate,
  getFileTypeIcon,
  getFileTypeColor,
  getStatusColor,
  getStatusIcon,
  getFileExtension,
  isPdfDocument,
  isTextDocument,
  getDocumentPreviewUrl,
  downloadDocument,
  acceptedFileTypes
} = useRAGHelpers();

// Document Preview Dialog
const documentPreviewDialog = ref(false);
const previewDocument = ref(null);
const previewContent = ref('');
const loadingPreviewContent = ref(false);

// Computed: Collection embedding progress based on collectionDocuments
const collectionEmbeddingProgress = computed(() => {
  const docs = collectionDocuments.value || [];
  const pending = docs.filter(d => d.status === 'pending').length;
  const processing = docs.filter(d => d.status === 'processing').length;
  const indexed = docs.filter(d => d.status === 'indexed').length;
  const failed = docs.filter(d => d.status === 'failed').length;
  return {
    pending,
    processing,
    indexed,
    failed,
    total: docs.length
  };
});

const collectionEmbeddingProgressPercent = computed(() => {
  const progress = collectionEmbeddingProgress.value;
  if (progress.total === 0) return 0;
  return Math.round((progress.indexed / progress.total) * 100);
});

// Wrapper functions for composables (with callbacks for data refresh)
const createCollection = async () => {
  await createCollectionFn(async () => {
    await fetchCollections();
    await fetchStats();
  });
};

const uploadFiles = async () => {
  await uploadFilesFn(async () => {
    await fetchDocuments();
    await fetchStats();
    activeTab.value = 'documents';
  });
};

const deleteDocument = async () => {
  await deleteDocumentFn(async () => {
    await fetchDocuments();
    await fetchStats();
  });
};

const deleteCollection = async (force = false) => {
  await deleteCollectionFn(force, async () => {
    await fetchCollections();
    await fetchDocuments();
    await fetchStats();
  });
};

// Document Preview Functions (local - not in composables)
const openDocumentPreview = async (doc) => {
  previewDocument.value = doc;
  previewContent.value = '';
  documentPreviewDialog.value = true;

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

// WebSocket für Echtzeit-Updates
let socket = null;

function setupWebSocket() {
  socket = getSocket();

  if (socket) {
    socket.on('rag:queue_list', updateQueueFromWebSocket);
    socket.on('rag:queue_updated', updateQueueFromWebSocket);
    socket.on('rag:progress', (data) => {
      console.log('[RAG] Progress-Update:', data.queue_id, data.progress_percent + '%', data.current_step);
    });
    socket.on('rag:document_processed', async (data) => {
      console.log('[RAG] Dokument verarbeitet:', data.filename, '-', data.status);
      await fetchStats();
      await fetchDocuments();
    });
    socket.on('rag:document_progress', (data) => {
      handleDocumentProgress(data);
      if (data.status === 'indexed' || data.status === 'failed') {
        fetchDocuments();
      }
    });

    if (socket.connected) {
      socket.emit('rag:subscribe_queue');
      console.log('[RAG] WebSocket subscribed');
    }

    socket.on('connect', () => {
      socket.emit('rag:subscribe_queue');
      console.log('[RAG] WebSocket reconnected und subscribed');
    });
  }
}

function cleanupWebSocket() {
  if (socket) {
    socket.off('rag:queue_list');
    socket.off('rag:queue_updated');
    socket.off('rag:progress');
    socket.off('rag:document_processed');
    socket.off('rag:document_progress');
    socket.emit('rag:unsubscribe_queue');
    console.log('[RAG] WebSocket unsubscribed');
  }
}

// Lifecycle
onMounted(async () => {
  await withLoading('stats', async () => {
    await fetchStats();
  });

  await withLoading('embedding', async () => {
    await fetchEmbeddingInfo();
  });

  await withLoading('collections', async () => {
    await fetchCollections();
  });

  await withLoading('documents', async () => {
    await fetchDocuments();
  });

  await fetchProcessingQueue();
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
