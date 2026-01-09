<template>
  <div class="admin-rag">
    <!-- Stats Cards -->
    <v-row class="mb-4">
      <v-col cols="6" md="3">
        <v-skeleton-loader v-if="isLoading('stats')" type="card" height="100" />
        <v-card v-else variant="tonal" color="primary">
          <v-card-text class="d-flex align-center">
            <LIcon size="32" class="mr-3">mdi-file-document-multiple</LIcon>
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
            <LIcon size="32" class="mr-3">mdi-check-circle</LIcon>
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
            <LIcon size="32" class="mr-3">mdi-folder-multiple</LIcon>
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
            <LIcon size="32" class="mr-3">mdi-harddisk</LIcon>
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
        <LIcon start color="primary">mdi-brain</LIcon>
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
                  <LIcon color="primary" size="small">mdi-cube-outline</LIcon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">Aktives Model</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold">{{ embeddingInfo.model_name }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <LIcon color="primary" size="small">mdi-vector-line</LIcon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">Dimensionen</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold">{{ embeddingInfo.dimensions }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <LIcon color="primary" size="small">mdi-server</LIcon>
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
                  <LIcon :color="embeddingInfo.litellm_configured ? 'success' : 'warning'" size="small">
                    {{ embeddingInfo.litellm_configured ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                  </LIcon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">LiteLLM Status</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold">
                  {{ embeddingInfo.litellm_configured ? 'Konfiguriert' : 'Nicht konfiguriert' }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="embeddingInfo.litellm_configured">
                <template v-slot:prepend>
                  <LIcon color="primary" size="small">mdi-link</LIcon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">LiteLLM URL</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold text-truncate" style="max-width: 300px;">
                  {{ embeddingInfo.litellm_base_url }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <LIcon color="primary" size="small">mdi-swap-horizontal</LIcon>
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
              <LIcon size="small" color="grey" class="mr-2">mdi-folder-open</LIcon>
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
          <LIcon start>mdi-file-document</LIcon>
          Dokumente
        </v-tab>
        <v-tab value="collections">
          <LIcon start>mdi-folder</LIcon>
          Collections
        </v-tab>
        <v-tab value="upload">
          <LIcon start>mdi-upload</LIcon>
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
              <template v-slot:item.title="{ item }">
                <div class="d-flex align-center">
                  <LIcon :color="getFileTypeColor(item.mime_type)" class="mr-2">
                    {{ getFileTypeIcon(item.mime_type) }}
                  </LIcon>
                  <span class="font-weight-medium">{{ item.title || item.filename }}</span>
                </div>
              </template>

              <template v-slot:item.file_size_bytes="{ item }">
                {{ formatFileSize(item.file_size_bytes) }}
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
                  icon="mdi-eye"
                  variant="text"
                  tooltip="Ansehen"
                  class="mr-1"
                  @click="openDocumentViewer(item)"
                />
                <LIconBtn
                  icon="mdi-download"
                  variant="text"
                  tooltip="Herunterladen"
                  class="mr-1"
                  :href="`/api/rag/documents/${item.id}/download`"
                  target="_blank"
                />
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
                  <LIcon color="primary" class="mr-2">mdi-folder</LIcon>
                  <span class="font-weight-medium text-primary">{{ item.name }}</span>
                  <LIcon size="small" class="ml-1" color="grey">mdi-open-in-new</LIcon>
                </div>
              </template>

              <template v-slot:item.created_by="{ item }">
                <v-chip size="small" variant="tonal" color="grey">
                  <LIcon start size="small">mdi-account</LIcon>
                  {{ item.created_by || 'Unbekannt' }}
                </v-chip>
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
                <LActionGroup
                  :actions="getCollectionActions(item)"
                  @action="(key) => handleCollectionAction(key, item)"
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
                  :items="uploadCollectionOptions"
                  item-title="title"
                  item-value="value"
                  label="Ziel-Collection"
                  variant="outlined"
                  prepend-inner-icon="mdi-folder"
                  clearable
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

            <!-- Upload Error Message -->
            <v-alert
              v-if="uploadError"
              type="error"
              variant="tonal"
              class="mt-4"
              closable
              @click:close="clearUploadMessages"
            >
              {{ uploadError }}
            </v-alert>

            <!-- Upload Success Message -->
            <v-alert
              v-if="uploadMessage"
              type="success"
              variant="tonal"
              class="mt-4"
              closable
              @click:close="clearUploadMessages"
            >
              {{ uploadMessage }}
            </v-alert>
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
          <LIcon color="error" class="mr-2">mdi-delete-alert</LIcon>
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

    <CollectionShareDialog
      v-model="collectionShareDialog"
      :collection="shareCollection"
      @saved="handleCollectionShareSaved"
      @error="handleCollectionShareError"
    />

    <!-- Collection Detail Dialog -->
    <v-dialog v-model="collectionDetailDialog" max-width="1200" scrollable>
      <v-card v-if="selectedCollection">
        <v-card-title class="d-flex align-center bg-primary">
          <LIcon start color="white">mdi-folder-open</LIcon>
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
                      <LIcon start size="small">mdi-file-document-multiple</LIcon>
                      {{ selectedCollection.document_count }} Dokumente
                    </v-chip>
                  </v-col>
                  <v-col cols="6">
                    <v-chip color="info" variant="flat" size="small">
                      <LIcon start size="small">mdi-harddisk</LIcon>
                      {{ formatFileSize(selectedCollection.total_size_bytes) }}
                    </v-chip>
                  </v-col>
                </v-row>
                <v-row dense class="mt-2">
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis">
                      <LIcon size="x-small" class="mr-1">mdi-puzzle</LIcon>
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
              <LIcon start color="warning" size="small">mdi-progress-clock</LIcon>
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
                  <LIcon start size="x-small">mdi-clock-outline</LIcon>
                  {{ collectionEmbeddingProgress.pending }} warten
                </v-chip>
                <v-chip size="x-small" color="info" variant="tonal">
                  <LIcon start size="x-small">mdi-cog</LIcon>
                  {{ collectionEmbeddingProgress.processing }} verarbeiten
                </v-chip>
                <v-chip size="x-small" color="success" variant="tonal">
                  <LIcon start size="x-small">mdi-check</LIcon>
                  {{ collectionEmbeddingProgress.indexed }} fertig
                </v-chip>
                <v-chip v-if="collectionEmbeddingProgress.failed > 0" size="x-small" color="error" variant="tonal">
                  <LIcon start size="x-small">mdi-alert</LIcon>
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
              <LBtn
                v-if="canReindexCollection(selectedCollection)"
                size="small"
                variant="warning"
                class="ml-2"
                @click="reindexCollection"
                :loading="reindexingCollection"
                :disabled="collectionDocuments.length === 0"
                prepend-icon="mdi-refresh-circle"
              >
                Neu indexieren
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
                  <LIcon :color="getDocumentColor(item)" class="mr-2">
                    {{ getDocumentIcon(item) }}
                  </LIcon>
                  <div>
                    <div class="font-weight-medium text-primary d-flex align-center flex-wrap">
                      <span>{{ item.title || item.filename }}</span>
                      <v-chip
                        v-if="isWebcrawlDocument(item)"
                        size="x-small"
                        color="info"
                        variant="tonal"
                        class="ml-2"
                      >
                        Webcrawl
                      </v-chip>
                      <v-chip
                        v-if="item.link_type === 'linked'"
                        size="x-small"
                        color="secondary"
                        variant="tonal"
                        class="ml-2"
                      >
                        verlinkt
                      </v-chip>
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      {{ item.filename }}
                    </div>
                    <div v-if="item.source_url" class="text-caption text-medium-emphasis d-flex align-center mt-1">
                      <LIcon size="12" class="mr-1">mdi-web</LIcon>
                      <a :href="item.source_url" target="_blank" class="text-truncate">
                        {{ item.source_url }}
                      </a>
                    </div>
                  </div>
                </div>
              </template>

              <template v-slot:item.file_size_bytes="{ item }">
                {{ formatFileSize(item.file_size_bytes) }}
              </template>

              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  <LIcon start size="x-small">{{ getStatusIcon(item.status) }}</LIcon>
                  {{ item.status }}
                </v-chip>
              </template>

              <template v-slot:item.chunk_count="{ item }">
                <v-chip size="small" variant="tonal" color="info">
                  {{ item.chunk_count || 0 }} Chunks
                </v-chip>
              </template>

              <template v-slot:item.actions="{ item }">
                <LActionGroup
                  :actions="['view', 'download']"
                  @action="(key) => handleDocumentDetailAction(key, item)"
                />
              </template>

              <template v-slot:no-data>
                <div class="text-center pa-8">
                  <LIcon size="64" color="grey-lighten-1" class="mb-4">mdi-folder-open-outline</LIcon>
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

    <!-- Document Viewer Dialog (with Screenshot & Chunks support) -->
    <DocumentViewer
      v-model="documentPreviewDialog"
      :document="previewDocumentForViewer"
      @download="downloadDocument"
      @delete="handleDeleteFromViewer"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import axios from 'axios';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { usePermissions } from '@/composables/usePermissions';
import { useAuth } from '@/composables/useAuth';
import { getSocket } from '@/services/socketService';
import DocumentViewer from '@/components/RAG/DocumentViewer.vue';
import CollectionShareDialog from '@/components/RAG/CollectionShareDialog.vue';
import {
  useRAGStats,
  useRAGDocuments,
  useRAGCollections,
  useRAGHelpers
} from './AdminRAGSection/composables';

// Skeleton Loading
const { isLoading, withLoading } = useSkeletonLoading(['stats', 'embedding', 'collections', 'documents']);
const { hasPermission } = usePermissions();
const { tokenParsed } = useAuth();
const currentUsername = computed(() => tokenParsed.value?.preferred_username || '');

// Local UI State
const activeTab = ref('collections');
const collectionShareDialog = ref(false);
const shareCollection = ref(null);

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
  reindexingCollection,
  collectionHeaders,
  collectionDocHeaders,
  fetchCollections,
  createCollection: createCollectionFn,
  confirmDeleteCollection,
  deleteCollection: deleteCollectionFn,
  openCollectionDetail,
  fetchCollectionDocuments,
  applyDocumentProgress,
  applyDocumentProcessed,
  reindexCollection
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
  uploadError,
  uploadMessage,
  deleteDocDialog,
  documentToDelete,
  deletingDocument,
  documentHeaders,
  collectionOptions,
  uploadCollectionOptions,
  filteredDocuments,
  fetchDocuments,
  handleFileSelect,
  uploadFiles: uploadFilesFn,
  clearUploadMessages,
  confirmDeleteDocument,
  deleteDocument: deleteDocumentFn
} = useRAGDocuments(collections);

const {
  formatFileSize,
  formatDate,
  getFileTypeIcon,
  getFileTypeColor,
  getDocumentIcon,
  getDocumentColor,
  isWebcrawlDocument,
  getStatusColor,
  getStatusIcon,
  downloadDocument,
  acceptedFileTypes
} = useRAGHelpers();

// Document Preview Dialog
const documentPreviewDialog = ref(false);
const previewDocument = ref(null);

// Computed property to transform previewDocument for DocumentViewer format
const previewDocumentForViewer = computed(() => {
  if (!previewDocument.value) return null;
  const doc = previewDocument.value;
  // Map to DocumentViewer expected format
  return {
    id: doc.id,
    filename: doc.filename,
    file_type: doc.file_type || getFileExtension(doc.filename),
    file_size: doc.file_size_bytes || doc.file_size,
    status: doc.status,
    chunk_count: doc.chunk_count,
    collection_name: doc.collection_name || selectedCollection.value?.display_name || selectedCollection.value?.name,
    uploaded_at: doc.uploaded_at,
    indexed_at: doc.indexed_at,
    retrieval_count: doc.retrieval_count,
    metadata: doc.metadata,
    md5_hash: doc.file_hash
  };
});

// Helper function to extract file extension
function getFileExtension(filename) {
  if (!filename) return '';
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
}

// Handle delete from DocumentViewer
async function handleDeleteFromViewer(doc) {
  documentPreviewDialog.value = false;
  // Use the existing delete flow
  documentToDelete.value = doc;
  deleteDocDialog.value = true;
}

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

const canShareCollections = computed(() => hasPermission('feature:rag:share'));

// Check if user can reindex a collection
// Only allowed if: can_edit AND (is owner OR collection is not public)
const canReindexCollection = (collection) => {
  if (!collection) return false;
  if (!collection.can_edit) return false;
  // Owner can always reindex
  if (collection.created_by === currentUsername.value) return true;
  // Non-owners can only reindex if collection is NOT public (i.e., explicitly shared)
  return collection.is_public === false;
};

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
    await fetchCollections();  // Update collection document counts
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
const openDocumentPreview = (doc) => {
  previewDocument.value = doc;
  documentPreviewDialog.value = true;
};

const openCollectionShareDialog = (collection) => {
  shareCollection.value = collection;
  collectionShareDialog.value = true;
};

const handleCollectionShareSaved = () => {
  collectionShareDialog.value = false;
  shareCollection.value = null;
};

const handleCollectionShareError = (message) => {
  alert(message || 'Fehler beim Speichern der Zugriffsrechte');
};

// Track which collection is being reindexed
const reindexingCollectionId = ref(null);

// Reindex a collection by ID directly
const reindexCollectionById = async (collectionId) => {
  reindexingCollectionId.value = collectionId;
  try {
    await axios.post(`/api/rag/collections/${collectionId}/reindex`);
    await fetchCollections();
    await fetchStats();
  } catch (error) {
    console.error('Error reindexing collection:', error);
    const errorMsg = error.response?.data?.error || 'Reindexierung fehlgeschlagen';
    alert(errorMsg);
  }
  reindexingCollectionId.value = null;
};

// Get actions for collection row
const getCollectionActions = (item) => {
  const actions = [
    { key: 'view', icon: 'mdi-eye', tooltip: 'Details anzeigen', variant: 'primary' }
  ];

  // Only show reindex button if user can reindex this collection
  if (canReindexCollection(item)) {
    actions.push({
      key: 'reindex',
      icon: 'mdi-refresh-circle',
      tooltip: 'Neu indexieren',
      variant: 'warning',
      disabled: item.document_count === 0,
      loading: reindexingCollectionId.value === item.id
    });
  }

  if (canShareCollections.value && (item.can_share ?? true)) {
    actions.push({
      key: 'share',
      icon: 'mdi-account-multiple-plus',
      tooltip: 'Zugriff teilen',
      variant: 'primary'
    });
  }

  actions.push({
    key: 'delete',
    icon: 'mdi-delete',
    tooltip: 'Löschen',
    variant: 'danger',
    disabled: item.can_delete === false || item.name === 'default' || item.name === 'general'
  });

  return actions;
};

// Handle collection action group clicks
const handleCollectionAction = (actionKey, item) => {
  switch (actionKey) {
    case 'view':
      openCollectionDetail(item);
      break;
    case 'reindex':
      reindexCollectionById(item.id);
      break;
    case 'share':
      openCollectionShareDialog(item);
      break;
    case 'delete':
      confirmDeleteCollection(item);
      break;
  }
};

// Handle document detail action group clicks
const handleDocumentDetailAction = (actionKey, item) => {
  switch (actionKey) {
    case 'view':
      openDocumentPreview(item);
      break;
    case 'download':
      downloadDocument(item);
      break;
  }
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
      applyDocumentProcessed(data);
      await fetchStats();
      await fetchDocuments();
    });
    socket.on('rag:document_progress', (data) => {
      handleDocumentProgress(data);
      applyDocumentProgress(data);
      if (data.status === 'indexed' || data.status === 'failed') {
        fetchDocuments();
      }
    });

    // Real-time updates when another user uploads a document
    socket.on('rag:document_uploaded', async (data) => {
      console.log('[RAG] Dokument hochgeladen (von anderem User):', data.document?.filename, '- Collection:', data.collection?.display_name);
      // Refresh data to show the new document
      await fetchDocuments();
      await fetchCollections();
      await fetchStats();
    });

    // Real-time updates when a collection is shared with the current user
    socket.on('rag:collection_shared', async (data) => {
      console.log('[RAG] Collection geteilt:', data.collection?.name, '- von:', data.shared_by);
      // Refresh collections to show newly shared collections
      await fetchCollections();
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
    socket.off('rag:document_uploaded');
    socket.off('rag:collection_shared');
    socket.emit('rag:unsubscribe_queue');
    console.log('[RAG] WebSocket unsubscribed');
  }
}

watch(collectionShareDialog, (value) => {
  if (!value) {
    shareCollection.value = null;
  }
});

// Lifecycle
onMounted(async () => {
  // Load all fast APIs in parallel - don't wait for each other
  const fastLoads = Promise.all([
    withLoading('stats', fetchStats),
    withLoading('collections', fetchCollections),
    withLoading('documents', fetchDocuments),
    fetchProcessingQueue()
  ]);

  // Load embedding info independently (slow due to LiteLLM connection attempt)
  // This doesn't block the rest of the page
  withLoading('embedding', fetchEmbeddingInfo);

  // Wait for fast APIs to complete
  await fastLoads;

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
</style>
