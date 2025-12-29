<template>
  <div class="system-settings-section">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-cog</v-icon>
        System-Einstellungen
        <v-spacer />
        <LBtn
          v-if="hasChanges"
          variant="primary"
          :loading="saving"
          prepend-icon="mdi-content-save"
          @click="saveSettings"
        >
          Speichern
        </LBtn>
      </v-card-title>
      <v-card-subtitle>
        Konfigurierbare Parameter für Crawler, RAG und System-Verhalten
      </v-card-subtitle>

      <v-card-text>
        <v-skeleton-loader v-if="loading" type="article" />

        <template v-else>
          <!-- Crawler Timeouts -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1">
              <v-icon class="mr-2" size="small">mdi-timer-outline</v-icon>
              Crawler Timeouts
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawl_timeout_seconds"
                    label="Crawl Timeout (Sekunden)"
                    type="number"
                    :min="60"
                    :max="86400"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 3600 (1 Stunde). Für große Websites erhöhen."
                    persistent-hint
                  >
                    <template #append-inner>
                      <span class="text-caption text-medium-emphasis">
                        {{ formatDuration(settings.crawl_timeout_seconds) }}
                      </span>
                    </template>
                  </v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.embedding_timeout_seconds"
                    label="Embedding Timeout (Sekunden)"
                    type="number"
                    :min="60"
                    :max="86400"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 7200 (2 Stunden). Für große Collections erhöhen."
                    persistent-hint
                  >
                    <template #append-inner>
                      <span class="text-caption text-medium-emphasis">
                        {{ formatDuration(settings.embedding_timeout_seconds) }}
                      </span>
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Crawler Defaults -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1">
              <v-icon class="mr-2" size="small">mdi-spider-web</v-icon>
              Crawler Defaults
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawler_default_max_pages"
                    label="Standard Max-Seiten"
                    type="number"
                    :min="1"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 500. Maximale Seiten pro Crawl im Chatbot Wizard."
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawler_default_max_depth"
                    label="Standard Crawl-Tiefe"
                    type="number"
                    :min="1"
                    :max="10"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 3. Wie viele Link-Ebenen verfolgt werden."
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- RAG Settings -->
          <v-card variant="outlined">
            <v-card-title class="text-subtitle-1">
              <v-icon class="mr-2" size="small">mdi-file-document-multiple</v-icon>
              RAG Chunking
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.rag_default_chunk_size"
                    label="Standard Chunk-Größe"
                    type="number"
                    :min="100"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 1000 Zeichen pro Chunk."
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.rag_default_chunk_overlap"
                    label="Standard Chunk-Überlappung"
                    type="number"
                    :min="0"
                    :max="5000"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 200 Zeichen Überlappung zwischen Chunks."
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Last Updated Info -->
          <div v-if="settings.updated_at" class="text-caption text-medium-emphasis mt-4">
            Zuletzt aktualisiert: {{ formatDate(settings.updated_at) }}
          </div>
        </template>
      </v-card-text>
    </v-card>

    <!-- Snackbar for feedback -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(true)
const saving = ref(false)
const snackbar = reactive({
  show: false,
  text: '',
  color: 'success'
})

const settings = reactive({
  crawl_timeout_seconds: 3600,
  embedding_timeout_seconds: 7200,
  crawler_default_max_pages: 500,
  crawler_default_max_depth: 3,
  rag_default_chunk_size: 1000,
  rag_default_chunk_overlap: 200,
  updated_at: null
})

const originalSettings = ref({})

const hasChanges = computed(() => {
  return JSON.stringify(settings) !== JSON.stringify(originalSettings.value)
})

async function loadSettings() {
  loading.value = true
  try {
    const response = await axios.get('/api/admin/system/settings')
    if (response.data.success) {
      Object.assign(settings, response.data.settings)
      originalSettings.value = { ...response.data.settings }
    }
  } catch (error) {
    console.error('Failed to load system settings:', error)
    snackbar.text = 'Fehler beim Laden der Einstellungen'
    snackbar.color = 'error'
    snackbar.show = true
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const response = await axios.patch('/api/admin/system/settings', {
      crawl_timeout_seconds: settings.crawl_timeout_seconds,
      embedding_timeout_seconds: settings.embedding_timeout_seconds,
      crawler_default_max_pages: settings.crawler_default_max_pages,
      crawler_default_max_depth: settings.crawler_default_max_depth,
      rag_default_chunk_size: settings.rag_default_chunk_size,
      rag_default_chunk_overlap: settings.rag_default_chunk_overlap
    })

    if (response.data.success) {
      Object.assign(settings, response.data.settings)
      originalSettings.value = { ...response.data.settings }
      snackbar.text = 'Einstellungen gespeichert'
      snackbar.color = 'success'
      snackbar.show = true
    }
  } catch (error) {
    console.error('Failed to save system settings:', error)
    snackbar.text = 'Fehler beim Speichern'
    snackbar.color = 'error'
    snackbar.show = true
  } finally {
    saving.value = false
  }
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0 && minutes > 0) return `${hours}h ${minutes}min`
  if (hours > 0) return `${hours}h`
  return `${minutes}min`
}

function formatDate(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('de-DE')
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.system-settings-section {
  max-width: 900px;
}
</style>
