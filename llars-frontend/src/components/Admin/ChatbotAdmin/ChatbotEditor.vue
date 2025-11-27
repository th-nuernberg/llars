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
        <v-tabs-window v-model="activeTab" class="h-100">
          <!-- General Tab -->
          <v-tabs-window-item value="general" eager>
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
          </v-tabs-window-item>

          <!-- LLM Settings Tab -->
          <v-tabs-window-item value="llm" eager>
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
                  <v-text-field
                    v-model="formData.model_name"
                    label="Modell"
                    hint="z.B. gpt-4, gpt-3.5-turbo"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                  />
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
          </v-tabs-window-item>

          <!-- RAG Settings Tab -->
          <v-tabs-window-item value="rag" eager>
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
          </v-tabs-window-item>

          <!-- Collections Tab -->
          <v-tabs-window-item value="collections" eager>
            <div v-if="collections.length === 0" class="text-center pa-8">
              <v-icon size="48" color="grey-lighten-1" class="mb-2">
                mdi-folder-off
              </v-icon>
              <div class="text-medium-emphasis">
                Keine Collections verfügbar
              </div>
            </div>
            <v-list v-else>
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
          </v-tabs-window-item>

          <!-- Web Crawler Tab -->
          <v-tabs-window-item value="webcrawler" eager>
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
          </v-tabs-window-item>
        </v-tabs-window>
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
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'

const props = defineProps({
  modelValue: Boolean,
  chatbot: Object,
  collections: {
    type: Array,
    default: () => []
  },
  isEdit: Boolean
})

const emit = defineEmits(['update:modelValue', 'save', 'collection-created'])

// State
const activeTab = ref('general')
const formData = ref({
  name: '',
  display_name: '',
  description: '',
  icon: 'mdi-robot',
  color: '#b0ca97',
  system_prompt: '',
  model_name: 'gpt-4',
  temperature: 0.7,
  max_tokens: 2000,
  top_p: 1.0,
  rag_enabled: false,
  rag_retrieval_k: 5,
  rag_min_relevance: 0.6,
  rag_include_sources: true,
  welcome_message: '',
  fallback_message: '',
  is_active: true,
  is_public: false,
  collection_ids: []
})

const promptLineCount = ref(10)

// Crawler State
const crawlerUrls = ref('')
const crawlerMaxPages = ref(30)
const crawlerMaxDepth = ref(2)
const crawling = ref(false)
const crawlStatus = ref(null)
const crawlJobId = ref(null)
const crawlProgress = ref(null)
const crawledPages = ref([])

// WebSocket for crawler
let crawlerSocket = null

// Icon options
const iconOptions = [
  { title: 'Robot', value: 'mdi-robot' },
  { title: 'Account', value: 'mdi-account' },
  { title: 'Chat', value: 'mdi-chat' },
  { title: 'Help', value: 'mdi-help-circle' },
  { title: 'Information', value: 'mdi-information' },
  { title: 'Support', value: 'mdi-face-agent' },
  { title: 'Book', value: 'mdi-book-open-page-variant' },
  { title: 'Lightbulb', value: 'mdi-lightbulb' }
]

// Prompt templates
const promptTemplates = [
  {
    name: 'Support',
    icon: 'mdi-face-agent',
    prompt: 'Du bist ein freundlicher Support-Mitarbeiter. Beantworte Fragen höflich und präzise. Wenn du etwas nicht weißt, gib das ehrlich zu und biete an, weiterzuhelfen.'
  },
  {
    name: 'FAQ',
    icon: 'mdi-help-circle',
    prompt: 'Du bist ein FAQ-Bot. Beantworte häufige Fragen basierend auf den verfügbaren Dokumenten. Halte deine Antworten kurz und präzise.'
  },
  {
    name: 'Onboarding',
    icon: 'mdi-account-star',
    prompt: 'Du bist ein Onboarding-Assistent. Führe neue Benutzer freundlich durch die ersten Schritte. Erkläre Funktionen verständlich und gebe hilfreiche Tipps.'
  },
  {
    name: 'Technisch',
    icon: 'mdi-wrench',
    prompt: 'Du bist ein technischer Assistent. Beantworte Fragen präzise und sachlich. Gebe technische Details, wenn nötig, und verwende Fachbegriffe korrekt.'
  }
]

// Validation rules
const rules = {
  required: v => !!v || 'Dieses Feld ist erforderlich'
}

// Computed
const isCollectionSelected = computed(() => {
  return (collectionId) => formData.value.collection_ids.includes(collectionId)
})

// Crawler URL validation
const parsedCrawlerUrls = computed(() => {
  return crawlerUrls.value
    .split('\n')
    .map(u => u.trim())
    .filter(u => u.length > 0)
})

const hasValidCrawlerUrls = computed(() => {
  return parsedCrawlerUrls.value.length > 0 && parsedCrawlerUrls.value.every(u =>
    u.startsWith('http://') || u.startsWith('https://')
  )
})

// Methods
function updateLineCount() {
  const lines = (formData.value.system_prompt || '').split('\n').length
  promptLineCount.value = Math.max(lines, 10)
}

function applyPromptTemplate(template) {
  formData.value.system_prompt = template.prompt
  updateLineCount()
}

function toggleCollection(collectionId) {
  const index = formData.value.collection_ids.indexOf(collectionId)
  if (index > -1) {
    formData.value.collection_ids.splice(index, 1)
  } else {
    formData.value.collection_ids.push(collectionId)
  }
}

function closeDialog() {
  emit('update:modelValue', false)
  activeTab.value = 'general'
  // Reset crawler state
  crawlerUrls.value = ''
  crawlStatus.value = null
}

// WebSocket functions for crawler
function initCrawlerSocket() {
  if (crawlerSocket) return

  crawlerSocket = io('/', {
    path: '/socket.io',
    transports: ['websocket', 'polling']
  })

  crawlerSocket.on('connect', () => {
    console.log('[Crawler Socket] Connected')
  })

  crawlerSocket.on('crawler:joined', (data) => {
    console.log('[Crawler Socket] Joined session:', data)
  })

  crawlerSocket.on('crawler:progress', (data) => {
    console.log('[Crawler Socket] Progress:', data)
    crawlProgress.value = data
    crawlStatus.value = {
      message: `Crawle ${data.current_url_index}/${data.total_urls} URLs - ${data.pages_crawled} Seiten...`,
      current_url: data.current_url,
      pages_crawled: data.pages_crawled,
      max_pages: data.max_pages
    }
  })

  crawlerSocket.on('crawler:page_crawled', (data) => {
    console.log('[Crawler Socket] Page crawled:', data)
    crawledPages.value.push(data.url)
    // Keep only last 10 pages for display
    if (crawledPages.value.length > 10) {
      crawledPages.value.shift()
    }
  })

  crawlerSocket.on('crawler:complete', (data) => {
    console.log('[Crawler Socket] Complete:', data)
    crawling.value = false
    crawlStatus.value = {
      success: true,
      message: `Crawl abgeschlossen!`,
      pages_crawled: data.pages_crawled,
      documents_created: data.documents_created,
      collection_id: data.collection_id
    }

    // Auto-add the new collection to the chatbot
    if (data.collection_id && !formData.value.collection_ids.includes(data.collection_id)) {
      formData.value.collection_ids.push(data.collection_id)
    }

    // Emit event to refresh collections list in parent
    emit('collection-created', data.collection_id)

    // Leave the room
    if (crawlJobId.value) {
      crawlerSocket.emit('crawler:leave_session', { session_id: crawlJobId.value })
    }
  })

  crawlerSocket.on('crawler:error', (data) => {
    console.error('[Crawler Socket] Error:', data)
    crawling.value = false
    crawlStatus.value = {
      error: true,
      message: data.error || 'Crawl fehlgeschlagen'
    }
  })
}

function cleanupCrawlerSocket() {
  if (crawlerSocket) {
    if (crawlJobId.value) {
      crawlerSocket.emit('crawler:leave_session', { session_id: crawlJobId.value })
    }
    crawlerSocket.disconnect()
    crawlerSocket = null
  }
}

// Crawler function with WebSocket
async function startCrawlForChatbot() {
  if (!hasValidCrawlerUrls.value) return

  crawling.value = true
  crawlStatus.value = { message: 'Crawl wird gestartet...' }
  crawledPages.value = []
  crawlProgress.value = null

  // Initialize WebSocket
  initCrawlerSocket()

  try {
    const chatbotName = formData.value.display_name || formData.value.name || 'Chatbot'
    const response = await axios.post('/api/crawler/start', {
      urls: parsedCrawlerUrls.value,
      collection_name: `${chatbotName} - Web`,
      collection_description: `Automatisch gecrawlt für Chatbot '${chatbotName}'`,
      max_pages_per_site: crawlerMaxPages.value,
      max_depth: crawlerMaxDepth.value
    })

    if (response.data.success && response.data.job_id) {
      crawlJobId.value = response.data.job_id

      // Join the WebSocket room for this crawl session
      crawlerSocket.emit('crawler:join_session', { session_id: response.data.job_id })

      crawlStatus.value = {
        message: 'Crawl gestartet, warte auf Updates...',
        job_id: response.data.job_id
      }
    } else {
      crawling.value = false
      crawlStatus.value = {
        error: true,
        message: response.data.error || 'Crawl konnte nicht gestartet werden'
      }
    }
  } catch (error) {
    console.error('Crawl error:', error)
    crawling.value = false
    crawlStatus.value = {
      error: true,
      message: error.response?.data?.error || 'Fehler beim Starten des Crawls'
    }
  }
}

// Lifecycle
onUnmounted(() => {
  cleanupCrawlerSocket()
})

function saveChanges() {
  const dataToSave = { ...formData.value }
  if (props.isEdit) {
    dataToSave.id = props.chatbot.id
  }
  emit('save', dataToSave)
}

// Watch for chatbot changes
watch(() => props.chatbot, (newChatbot) => {
  if (newChatbot) {
    formData.value = {
      ...formData.value,
      ...newChatbot,
      collection_ids: newChatbot.collections?.map(c => c.id) || []
    }
    updateLineCount()
  } else {
    // Reset for new chatbot
    formData.value = {
      name: '',
      display_name: '',
      description: '',
      icon: 'mdi-robot',
      color: '#b0ca97',
      system_prompt: '',
      model_name: 'gpt-4',
      temperature: 0.7,
      max_tokens: 2000,
      top_p: 1.0,
      rag_enabled: false,
      rag_retrieval_k: 5,
      rag_min_relevance: 0.6,
      rag_include_sources: true,
      welcome_message: '',
      fallback_message: '',
      is_active: true,
      is_public: false,
      collection_ids: []
    }
  }
}, { immediate: true })
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
