<template>
  <v-dialog
    :model-value="modelValue"
    max-width="1000"
    persistent
    scrollable
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <!-- Header -->
      <v-card-title class="d-flex align-center justify-space-between bg-primary">
        <div class="d-flex align-center">
          <v-icon class="mr-2">{{ isEdit ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
          <span>{{ isEdit ? 'Chatbot bearbeiten' : 'Neuer Chatbot' }}</span>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="closeDialog"
        />
      </v-card-title>

      <!-- Tabs -->
      <v-tabs v-model="activeTab" bg-color="surface">
        <v-tab value="general">
          <v-icon start>mdi-information</v-icon>
          Allgemein
        </v-tab>
        <v-tab value="llm">
          <v-icon start>mdi-brain</v-icon>
          LLM-Einstellungen
        </v-tab>
        <v-tab value="rag">
          <v-icon start>mdi-magnify</v-icon>
          RAG
        </v-tab>
        <v-tab value="collections">
          <v-icon start>mdi-folder-multiple</v-icon>
          Collections
        </v-tab>
        <v-tab value="webcrawler">
          <v-icon start>mdi-spider-web</v-icon>
          Web Crawler
        </v-tab>
      </v-tabs>

      <!-- Content -->
      <v-card-text style="height: 500px; overflow-y: auto;">
        <!-- Skeleton Loading for Crawler -->
        <v-skeleton-loader v-if="isLoading('crawler')" type="article"></v-skeleton-loader>

        <v-window v-else v-model="activeTab" class="h-100">
          <!-- General Tab -->
          <v-window-item value="general" eager>
            <v-form ref="formGeneral">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.name"
                    label="Technischer Name"
                    hint="Eindeutiger Bezeichner (z.B. support-bot)"
                    persistent-hint
                    :rules="[rules.required]"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.display_name"
                    label="Anzeigename"
                    hint="Name wie er Benutzern angezeigt wird"
                    persistent-hint
                    :rules="[rules.required]"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12">
                  <v-textarea
                    v-model="formData.description"
                    label="Beschreibung"
                    hint="Kurze Beschreibung des Chatbot-Zwecks"
                    persistent-hint
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <!-- Icon Selection -->
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formData.icon"
                    label="Icon"
                    :items="iconOptions"
                    variant="outlined"
                    density="comfortable"
                  >
                    <template #selection="{ item }">
                      <v-icon class="mr-2">{{ item.value }}</v-icon>
                      {{ item.title }}
                    </template>
                    <template #item="{ props, item }">
                      <v-list-item v-bind="props">
                        <template #prepend>
                          <v-icon>{{ item.value }}</v-icon>
                        </template>
                      </v-list-item>
                    </template>
                  </v-select>
                </v-col>

                <!-- Color Picker -->
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.color"
                    label="Farbe"
                    variant="outlined"
                    density="comfortable"
                  >
                    <template #prepend-inner>
                      <input
                        v-model="formData.color"
                        type="color"
                        style="width: 32px; height: 32px; border: none; cursor: pointer"
                      >
                    </template>
                  </v-text-field>
                </v-col>

                <!-- Welcome & Fallback Messages -->
                <v-col cols="12">
                  <v-textarea
                    v-model="formData.welcome_message"
                    label="Willkommensnachricht"
                    hint="Erste Nachricht beim Start eines Gesprächs"
                    persistent-hint
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12">
                  <v-textarea
                    v-model="formData.fallback_message"
                    label="Fallback-Nachricht"
                    hint="Nachricht bei Fehlern oder wenn keine Antwort möglich"
                    persistent-hint
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <!-- Status Switches -->
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="formData.is_active"
                    label="Chatbot aktiv"
                    color="success"
                    hide-details
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="formData.is_public"
                    label="Öffentlich verfügbar"
                    color="primary"
                    hide-details
                  />
                </v-col>
              </v-row>
            </v-form>
          </v-window-item>

          <!-- LLM Settings Tab -->
          <v-window-item value="llm" eager>
            <v-form ref="formLLM">
              <v-row>
                <!-- Prompt Templates -->
                <v-col cols="12">
                  <v-card variant="outlined" class="mb-4">
                    <v-card-title class="text-subtitle-1">
                      <v-icon start>mdi-text-box-multiple</v-icon>
                      Prompt-Vorlagen
                    </v-card-title>
                    <v-card-text>
                      <v-chip-group>
                        <v-chip
                          v-for="template in promptTemplates"
                          :key="template.name"
                          variant="outlined"
                          @click="applyPromptTemplate(template)"
                        >
                          <v-icon start>{{ template.icon }}</v-icon>
                          {{ template.name }}
                        </v-chip>
                      </v-chip-group>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- System Prompt -->
                <v-col cols="12">
                  <div class="text-subtitle-2 mb-2">System Prompt</div>
                  <v-card variant="outlined" class="prompt-editor">
                    <v-card-text class="pa-0">
                      <div class="d-flex">
                        <!-- Line numbers -->
                        <div class="line-numbers">
                          <div
                            v-for="n in promptLineCount"
                            :key="n"
                            class="line-number"
                          >
                            {{ n }}
                          </div>
                        </div>
                        <!-- Textarea -->
                        <textarea
                          v-model="formData.system_prompt"
                          class="prompt-textarea"
                          placeholder="Definieren Sie die Rolle und das Verhalten des Chatbots..."
                          @input="updateLineCount"
                        />
                      </div>
                    </v-card-text>
                  </v-card>
                  <div class="text-caption text-medium-emphasis mt-1">
                    {{ formData.system_prompt?.length || 0 }} Zeichen
                  </div>
                </v-col>

                <!-- Model Settings -->
                <v-col cols="12">
                  <v-combobox
                    v-model="formData.model_name"
                    :items="llmModelItems"
                    item-title="title"
                    item-value="value"
                    label="Modell"
                    hint="Wähle ein Modell aus der Registry oder gib eine Model-ID ein"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                    :loading="llmModelsLoading"
                    clearable
                  >
                    <template #append>
                      <v-btn
                        icon
                        variant="text"
                        size="small"
                        :loading="llmModelsLoading"
                        @click="syncAndLoadModels"
                      >
                        <v-icon>mdi-refresh</v-icon>
                        <v-tooltip activator="parent" location="top">
                          Modelle synchronisieren
                        </v-tooltip>
                      </v-btn>
                    </template>

                    <template #item="{ props: itemProps, item }">
                      <v-list-item v-bind="itemProps">
                        <template #prepend>
                          <v-icon :color="item.raw.supports_vision ? 'success' : 'grey'">
                            {{ item.raw.supports_vision ? 'mdi-image' : 'mdi-text' }}
                          </v-icon>
                        </template>
                        <v-list-item-title>{{ item.raw.display_name }}</v-list-item-title>
                        <v-list-item-subtitle class="text-caption">
                          {{ item.raw.provider }} · {{ item.raw.model_id }}
                        </v-list-item-subtitle>
                      </v-list-item>
                    </template>
                  </v-combobox>

                  <v-alert
                    v-if="selectedLlmModel"
                    type="info"
                    variant="tonal"
                    class="mt-2"
                  >
                    <div class="d-flex align-center justify-space-between">
                      <div class="text-caption">
                        {{ selectedLlmModel.provider }} · {{ formatNumber(selectedLlmModel.context_window) }} Kontext · Max Output {{ formatNumber(selectedLlmModel.max_output_tokens) }}
                      </div>
                      <div class="d-flex ga-2">
                        <v-chip
                          v-if="selectedLlmModel.supports_vision"
                          size="x-small"
                          color="success"
                          variant="flat"
                        >
                          Vision
                        </v-chip>
                        <v-chip
                          v-if="selectedLlmModel.supports_reasoning"
                          size="x-small"
                          color="primary"
                          variant="flat"
                        >
                          Reasoning
                        </v-chip>
                      </div>
                    </div>
                  </v-alert>
                </v-col>

                <!-- Temperature Slider -->
                <v-col cols="12">
                  <div class="text-subtitle-2 mb-2">
                    Temperatur: {{ formData.temperature }}
                  </div>
                  <v-slider
                    v-model="formData.temperature"
                    :min="0"
                    :max="2"
                    :step="0.1"
                    thumb-label
                    color="primary"
                  >
                    <template #prepend>
                      <div class="text-caption">Präzise</div>
                    </template>
                    <template #append>
                      <div class="text-caption">Kreativ</div>
                    </template>
                  </v-slider>
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="formData.max_tokens"
                    label="Max. Tokens"
                    type="number"
                    hint="Maximale Antwortlänge"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="formData.top_p"
                    label="Top P"
                    type="number"
                    :min="0"
                    :max="1"
                    :step="0.1"
                    hint="Nucleus Sampling (0-1)"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
              </v-row>
            </v-form>
          </v-window-item>

          <!-- RAG Settings Tab -->
          <v-window-item value="rag" eager>
            <v-form ref="formRAG">
              <v-row>
                <v-col cols="12">
                  <v-switch
                    v-model="formData.rag_enabled"
                    label="RAG aktivieren"
                    color="info"
                    hide-details
                  />
                  <div class="text-caption text-medium-emphasis mt-2">
                    Retrieval-Augmented Generation für wissensbasierte Antworten
                  </div>
                </v-col>

                <template v-if="formData.rag_enabled">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="formData.rag_retrieval_k"
                      label="Anzahl Dokumente (k)"
                      type="number"
                      :min="1"
                      :max="20"
                      hint="Wie viele relevante Dokumente abgerufen werden"
                      persistent-hint
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="formData.rag_min_relevance"
                      label="Minimale Relevanz"
                      type="number"
                      :min="0"
                      :max="1"
                      :step="0.05"
                      hint="Schwellwert für Dokumenten-Relevanz (0-1)"
                      persistent-hint
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>

                  <v-col cols="12">
                    <v-switch
                      v-model="formData.rag_include_sources"
                      label="Quellen in Antwort einbeziehen"
                      color="primary"
                      hide-details
                    />
                    <div class="text-caption text-medium-emphasis mt-2">
                      Zeigt Quellenangaben in den Antworten an
                    </div>
                  </v-col>
                </template>
              </v-row>
            </v-form>
          </v-window-item>

          <!-- Collections Tab -->
          <v-window-item value="collections" eager>
            <div v-if="collections.length === 0" class="text-center pa-8">
              <v-icon size="48" color="grey-lighten-1" class="mb-2">
                mdi-folder-off
              </v-icon>
              <div class="text-medium-emphasis">
                Keine Collections verfügbar
              </div>
            </div>
            <template v-else>
              <v-list>
                <v-list-item
                  v-for="collection in collections"
                  :key="collection.id"
                >
                  <template #prepend>
                    <v-checkbox-btn
                      :model-value="isCollectionSelected(collection.id)"
                      @update:model-value="toggleCollection(collection.id)"
                    />
                  </template>
                  <v-list-item-title>{{ collection.display_name }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ collection.document_count || 0 }} Dokumente
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <v-divider class="my-4" />

              <div class="d-flex align-center mb-2">
                <v-icon class="mr-2" color="primary">mdi-upload</v-icon>
                <span class="text-subtitle-1 font-weight-medium">Dokumente hinzufügen</span>
              </div>
              <v-alert type="info" variant="tonal" density="compact" class="mb-3">
                Laden Sie PDFs, Markdown oder TXT direkt in eine zugewiesene Collection hoch.
              </v-alert>

              <v-row v-if="selectedCollectionsForUpload.length > 0">
                <v-col
                  v-for="collection in selectedCollectionsForUpload"
                  :key="collection.id"
                  cols="12"
                  md="6"
                >
                  <v-card variant="outlined">
                    <v-card-title class="d-flex align-center">
                      <v-icon class="mr-2">mdi-folder</v-icon>
                      <span class="text-truncate">{{ collection.display_name || collection.name }}</span>
                      <v-spacer />
                      <LBtn
                        size="small"
                        variant="primary"
                        prepend-icon="mdi-upload"
                        @click="openUploadDialogForCollection(collection.id)"
                      >
                        Upload
                      </LBtn>
                    </v-card-title>
                    <v-card-text class="text-caption text-medium-emphasis">
                      {{ collection.document_count || 0 }} Dokumente
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
              <div v-else class="text-center pa-6 text-medium-emphasis">
                <v-icon size="48" class="mb-2">mdi-folder-plus</v-icon>
                <div>Bitte zuerst mindestens eine Collection auswählen.</div>
              </div>
            </template>
          </v-window-item>

          <!-- Web Crawler Tab -->
          <v-window-item value="webcrawler" eager>
            <v-row>
              <v-col cols="12">
                <v-alert type="info" variant="tonal" class="mb-4">
                  <template #prepend>
                    <v-icon>mdi-spider-web</v-icon>
                  </template>
                  <div class="text-subtitle-2">Website automatisch crawlen</div>
                  <div class="text-body-2">
                    Geben Sie URLs ein, die automatisch gecrawlt und als RAG-Collection für diesen Chatbot hinzugefügt werden sollen.
                  </div>
                </v-alert>
              </v-col>

              <v-col cols="12">
                <v-textarea
                  v-model="crawlerUrls"
                  label="URLs zum Crawlen"
                  placeholder="https://example.com&#10;https://docs.example.com"
                  hint="Eine URL pro Zeile. Der Crawler folgt internen Links automatisch."
                  persistent-hint
                  rows="4"
                  variant="outlined"
                />
              </v-col>

              <v-col cols="12">
                <v-expansion-panels>
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon start>mdi-cog</v-icon>
                      Crawler-Einstellungen
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-row>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="crawlerMaxPages"
                            label="Max. Seiten pro URL"
                            type="number"
                            min="1"
                            max="100"
                            variant="outlined"
                            density="compact"
                          />
                        </v-col>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="crawlerMaxDepth"
                            label="Max. Link-Tiefe"
                            type="number"
                            min="1"
                            max="5"
                            variant="outlined"
                            density="compact"
                          />
                        </v-col>
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-col>

              <!-- Crawl Status -->
              <v-col cols="12" v-if="crawlStatus">
                <v-alert
                  :type="crawlStatus.success ? 'success' : crawlStatus.error ? 'error' : 'info'"
                  variant="tonal"
                >
                  <div class="font-weight-bold">{{ crawlStatus.message }}</div>
                  <div v-if="crawlStatus.pages_crawled !== undefined" class="text-body-2">
                    {{ crawlStatus.pages_crawled }} Seiten gecrawlt
                    <template v-if="crawlStatus.documents_created">,
                      {{ crawlStatus.documents_created }} Dokumente erstellt
                    </template>
                  </div>
                  <!-- Progress bar -->
                  <v-progress-linear
                    v-if="crawling && crawlProgress"
                    :model-value="(crawlProgress.pages_crawled / crawlProgress.max_pages) * 100"
                    color="primary"
                    height="8"
                    rounded
                    class="mt-2"
                  >
                    <template v-slot:default>
                      {{ crawlProgress.pages_crawled }} / {{ crawlProgress.max_pages }}
                    </template>
                  </v-progress-linear>
                  <!-- Current URL being crawled -->
                  <div v-if="crawlStatus.current_url" class="text-caption text-truncate mt-1">
                    <v-icon size="small">mdi-link</v-icon>
                    {{ crawlStatus.current_url }}
                  </div>
                </v-alert>

                <!-- Live crawled pages list -->
                <v-card v-if="crawling && crawledPages.length > 0" variant="outlined" class="mt-2">
                  <v-card-title class="text-subtitle-2 py-2">
                    <v-icon start size="small">mdi-format-list-bulleted</v-icon>
                    Zuletzt gecrawlte Seiten
                  </v-card-title>
                  <v-list dense class="py-0" style="max-height: 150px; overflow-y: auto;">
                    <v-list-item
                      v-for="(url, index) in crawledPages"
                      :key="index"
                      density="compact"
                      class="text-caption"
                    >
                      <v-icon start size="x-small" color="success">mdi-check</v-icon>
                      <span class="text-truncate">{{ url }}</span>
                    </v-list-item>
                  </v-list>
                </v-card>
              </v-col>

              <v-col cols="12">
                <v-btn
                  color="primary"
                  variant="outlined"
                  :loading="crawling"
                  :disabled="!hasValidCrawlerUrls"
                  @click="startCrawlForChatbot"
                  prepend-icon="mdi-spider-web"
                >
                  Website crawlen und Collection erstellen
                </v-btn>
              </v-col>
            </v-row>
          </v-window-item>
        </v-window>
      </v-card-text>

      <!-- Actions -->
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="closeDialog">
          Abbrechen
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          @click="saveChanges"
        >
          {{ isEdit ? 'Speichern' : 'Erstellen' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <DocumentUploadDialog
    v-model="uploadDialogOpen"
    :collections="selectedCollectionsForUpload"
    :initial-collection-id="uploadInitialCollectionId"
    @uploaded="handleDocumentsUploaded"
  />
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import axios from 'axios';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import DocumentUploadDialog from '@/components/RAG/DocumentUploadDialog.vue';
import {
  useChatbotForm,
  useChatbotCrawler
} from './ChatbotEditor/composables';

const props = defineProps({
  modelValue: Boolean,
  chatbot: Object,
  collections: {
    type: Array,
    default: () => []
  },
  isEdit: Boolean
});

const emit = defineEmits(['update:modelValue', 'save', 'collection-created', 'documents-uploaded']);

// Skeleton Loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['crawler']);

// Initialize composables
const {
  formData,
  activeTab,
  promptLineCount,
  iconOptions,
  promptTemplates,
  rules,
  isCollectionSelected,
  updateLineCount,
  applyPromptTemplate,
  toggleCollection,
  loadChatbot,
  prepareForSave
} = useChatbotForm();

const {
  crawlerUrls,
  crawlerMaxPages,
  crawlerMaxDepth,
  crawling,
  crawlStatus,
  crawlProgress,
  crawledPages,
  hasValidCrawlerUrls,
  startCrawl,
  resetCrawler
} = useChatbotCrawler();

const uploadDialogOpen = ref(false);
const uploadInitialCollectionId = ref(null);

const selectedCollectionsForUpload = computed(() => {
  const ids = formData.value?.collection_ids || [];
  return (props.collections || []).filter(c => ids.includes(c.id));
});

// ===== LLM Models =====
const llmModels = ref([]);
const llmModelsLoading = ref(false);

const selectedLlmModel = computed(() => {
  const modelId = formData.value?.model_name;
  if (!modelId) return null;
  return llmModels.value.find(m => m.model_id === modelId) || null;
});

const llmModelItems = computed(() => {
  const current = formData.value?.model_name;
  const items = Array.isArray(llmModels.value) ? [...llmModels.value] : [];
  const hasCurrent = current && items.some(m => m.model_id === current);

  if (current && !hasCurrent) {
    items.unshift({
      model_id: current,
      display_name: current,
      provider: 'custom',
      supports_vision: false,
      supports_reasoning: false,
      context_window: 0,
      max_output_tokens: 0
    });
  }

  return items.map(m => ({
    title: m.display_name || m.model_id,
    value: m.model_id,
    ...m
  }));
});

function formatNumber(value) {
  if (typeof value !== 'number') return value || '';
  try {
    return value.toLocaleString();
  } catch {
    return String(value);
  }
}

async function loadModels() {
  llmModelsLoading.value = true;
  try {
    const response = await axios.get('/api/llm/models?active_only=true');
    if (response.data?.success) {
      llmModels.value = response.data.models || [];

      // Default selection for "create" mode only
      if (!props.isEdit) {
        const current = formData.value?.model_name;
        const def = llmModels.value.find(m => m.is_default) || llmModels.value[0];
        if (def?.model_id && (!current || current === 'gpt-4')) {
          formData.value.model_name = def.model_id;
        }
      }
    } else {
      llmModels.value = [];
    }
  } catch (error) {
    console.warn('[ChatbotEditor] Error loading LLM models:', error);
    llmModels.value = [];
  } finally {
    llmModelsLoading.value = false;
  }
}

async function syncAndLoadModels() {
  llmModelsLoading.value = true;
  try {
    await axios.post('/api/llm/models/sync');
  } catch (error) {
    console.warn('[ChatbotEditor] Model sync failed:', error);
  } finally {
    llmModelsLoading.value = false;
  }
  await loadModels();
}

// Methods
function closeDialog() {
  emit('update:modelValue', false);
  activeTab.value = 'general';
  resetCrawler();
}

function openUploadDialogForCollection(collectionId) {
  uploadInitialCollectionId.value = collectionId;
  uploadDialogOpen.value = true;
}

function handleDocumentsUploaded() {
  emit('documents-uploaded', { collection_id: uploadInitialCollectionId.value });
}

async function startCrawlForChatbot() {
  const chatbotName = formData.value.display_name || formData.value.name || 'Chatbot';

  await withLoading('crawler', async () => {
    await startCrawl(chatbotName, {
      onComplete: (data) => {
        // Auto-add the new collection to the chatbot
        if (data.collection_id && !formData.value.collection_ids.includes(data.collection_id)) {
          formData.value.collection_ids.push(data.collection_id);
        }
        // Emit event to refresh collections list in parent
        emit('collection-created', data.collection_id);
      }
    });
  });
}

function saveChanges() {
  const dataToSave = prepareForSave(props.isEdit, props.chatbot?.id);
  emit('save', dataToSave);
}

// Watch for chatbot changes
watch(() => props.chatbot, (newChatbot) => {
  loadChatbot(newChatbot);
}, { immediate: true });

// Load models when dialog opens
watch(() => props.modelValue, (isOpen) => {
  if (!isOpen) {
    llmModels.value = [];
    return;
  }
  loadModels();
}, { immediate: true });
</script>

<style scoped>
.prompt-editor {
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.line-numbers {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 8px;
  text-align: right;
  user-select: none;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.line-number {
  line-height: 1.5;
  font-size: 12px;
}

.prompt-textarea {
  flex: 1;
  border: none;
  outline: none;
  padding: 8px 12px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  min-height: 300px;
  background: transparent;
  color: rgb(var(--v-theme-on-surface));
}

.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}
</style>
