<template>
  <v-card flat class="pa-4">
    <div class="text-center mb-6">
      <LIcon size="64" color="primary">mdi-web</LIcon>
      <h2 class="text-h5 mt-4">Website URL eingeben</h2>
      <p class="text-medium-emphasis">
        Geben Sie die URL der Website ein, aus der der Chatbot lernen soll.
      </p>
    </div>

    <v-text-field
      v-model="localUrl"
      label="Website URL"
      placeholder="example.com"
      prepend-inner-icon="mdi-link"
      variant="outlined"
      :rules="[rules.required, rules.url]"
      :error-messages="errorMessage"
      :disabled="loading"
      autofocus
      @keyup.enter="handleStart"
      @update:model-value="updateUrl"
    />

    <!-- Crawler Options -->
    <v-expansion-panels class="mt-4">
      <v-expansion-panel>
        <v-expansion-panel-title>
          <LIcon class="mr-2">mdi-cog</LIcon>
          Erweiterte Crawler-Einstellungen
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="localConfig.maxPages"
                label="Max. Seiten"
                type="number"
                min="1"
                max="500"
                variant="outlined"
                density="compact"
                hint="Maximale Anzahl zu crawlender Seiten"
                persistent-hint
                :disabled="loading"
                @update:model-value="updateConfig"
              >
                <template #prepend-inner>
                  <LIcon size="small">mdi-file-document-multiple</LIcon>
                </template>
              </v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="localConfig.maxDepth"
                label="Max. Tiefe"
                type="number"
                min="1"
                max="10"
                variant="outlined"
                density="compact"
                hint="Wie tief Links verfolgt werden"
                persistent-hint
                :disabled="loading"
                @update:model-value="updateConfig"
              >
                <template #prepend-inner>
                  <LIcon size="small">mdi-sitemap</LIcon>
                </template>
              </v-text-field>
            </v-col>
          </v-row>

          <v-divider class="my-4" />

          <!-- Crawler Mode -->
          <div class="text-subtitle-2 mb-2">Crawler-Modus</div>

          <v-switch
            v-model="localConfig.usePlaywright"
            color="primary"
            density="compact"
            hide-details
            :disabled="loading"
            @update:model-value="updateConfig"
          >
            <template #label>
              <div class="d-flex align-center">
                <LIcon size="small" class="mr-2" :color="localConfig.usePlaywright ? 'primary' : 'grey'">
                  mdi-web
                </LIcon>
                <span>Playwright Browser (JavaScript-Rendering)</span>
              </div>
            </template>
          </v-switch>

          <v-expand-transition>
            <div v-if="localConfig.usePlaywright" class="ml-8 mt-2">
              <v-switch
                v-model="localConfig.takeScreenshots"
                color="primary"
                density="compact"
                hide-details
                :disabled="loading"
                @update:model-value="updateConfig"
              >
                <template #label>
                  <div class="d-flex align-center">
                    <LIcon size="small" class="mr-2" :color="localConfig.takeScreenshots ? 'primary' : 'grey'">
                      mdi-camera
                    </LIcon>
                    <span>Screenshots erstellen</span>
                  </div>
                </template>
              </v-switch>
              <p class="text-caption text-medium-emphasis mt-1 ml-8">
                Screenshots werden als Bild-Chunks gespeichert (Standard: an)
              </p>

              <v-switch
                v-model="localConfig.useVisionLlm"
                color="deep-purple"
                density="compact"
                hide-details
                :disabled="loading || !localConfig.takeScreenshots"
                @update:model-value="updateConfig"
              >
                <template #label>
                  <div class="d-flex align-center">
                    <LIcon size="small" class="mr-2" :color="localConfig.useVisionLlm ? 'deep-purple' : 'grey'">
                      mdi-eye
                    </LIcon>
                    <span>Vision-LLM Extraktion (Experimentell)</span>
                  </div>
                </template>
              </v-switch>
              <p class="text-caption text-medium-emphasis mt-1 ml-8">
                Verwendet ein Vision-LLM um Screenshots intelligent zu analysieren
              </p>
            </div>
          </v-expand-transition>

          <p class="text-caption text-medium-emphasis mt-3">
            <LIcon size="x-small" class="mr-1">mdi-information</LIcon>
            <strong>Playwright:</strong> Rendert JavaScript, extrahiert Bilder, optional Screenshots.
            <strong>Basic:</strong> Schneller, nur statisches HTML.
          </p>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Info Card -->
    <v-card variant="tonal" color="info" class="mt-4 pa-3">
      <div class="d-flex align-start">
        <LIcon class="mr-3 mt-1">mdi-information</LIcon>
        <div>
          <div class="text-subtitle-2">So funktioniert's:</div>
          <ol class="text-body-2 text-medium-emphasis pl-4 mb-0">
            <li>Der Crawler erkundet die Website und sammelt Inhalte</li>
            <li>Texte werden in Chunks aufgeteilt und als Embeddings gespeichert</li>
            <li>Der Chatbot nutzt diese Wissensbasis zur Beantwortung von Fragen</li>
          </ol>
        </div>
      </div>
    </v-card>

    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      class="mt-4"
      closable
    >
      {{ errorMessage }}
    </v-alert>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  url: {
    type: String,
    default: ''
  },
  config: {
    type: Object,
    default: () => ({
      maxPages: 50,
      maxDepth: 3,
      usePlaywright: true,
      useVisionLlm: false,
      takeScreenshots: true
    })
  },
  errorMessage: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:url', 'update:config', 'start'])

// Local state
const localUrl = ref(props.url)
const localConfig = ref({
  maxPages: props.config.maxPages || 50,
  maxDepth: props.config.maxDepth || 3,
  usePlaywright: props.config.usePlaywright !== false,
  useVisionLlm: props.config.useVisionLlm || false,
  takeScreenshots: props.config.takeScreenshots !== false
})

const FALLBACK_URL = 'https://www.dg-agentur.de/'
const SCHEME_REGEX = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//

const isBlank = (value) => !value || !value.trim()

const getEffectiveUrl = (value) => {
  if (isBlank(value)) return ''
  const trimmed = value.trim()
  if (SCHEME_REGEX.test(trimmed)) {
    return trimmed
  }
  return FALLBACK_URL
}

// Validation rules
const rules = {
  required: v => !isBlank(v) || 'URL ist erforderlich',
  url: v => {
    if (isBlank(v)) return true
    const trimmed = v.trim()
    if (!SCHEME_REGEX.test(trimmed)) return true
    try {
      const url = new URL(trimmed)
      if (!['http:', 'https:'].includes(url.protocol)) {
        return 'URL muss mit http:// oder https:// beginnen'
      }
      return true
    } catch {
      return 'Ungültige URL'
    }
  }
}

// Update handlers
const updateUrl = () => {
  emit('update:url', localUrl.value)
}

const updateConfig = () => {
  const normalized = {
    ...localConfig.value
  }
  if (!normalized.takeScreenshots) {
    normalized.useVisionLlm = false
  }
  emit('update:config', normalized)
}

const handleStart = () => {
  if (!props.loading) {
    const effectiveUrl = getEffectiveUrl(localUrl.value)
    if (!effectiveUrl) return
    try {
      const url = new URL(effectiveUrl)
      if (!['http:', 'https:'].includes(url.protocol)) {
        return
      }
      emit('start')
    } catch {
      // Invalid URL, don't emit
    }
  }
}

// Watch props for external updates
watch(() => props.url, (newVal) => {
  localUrl.value = newVal
})

watch(() => props.config, (newVal) => {
  localConfig.value = {
    maxPages: newVal.maxPages || 50,
    maxDepth: newVal.maxDepth || 3,
    usePlaywright: newVal.usePlaywright !== false,
    useVisionLlm: newVal.useVisionLlm || false,
    takeScreenshots: newVal.takeScreenshots !== false
  }
}, { deep: true })
</script>

<style scoped>
ol {
  margin-top: 4px;
}

ol li {
  margin-bottom: 2px;
}
</style>
