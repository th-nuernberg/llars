<template>
  <v-card flat class="pa-4">
    <!-- Background process banner -->
    <v-alert
      v-if="isProcessing"
      type="info"
      variant="tonal"
      class="mb-4"
    >
      <div class="d-flex align-center">
        <v-progress-circular
          indeterminate
          size="20"
          width="2"
          class="mr-3"
        />
        <span>
          {{ buildStatus === 'crawling' ? 'Crawling läuft im Hintergrund...' : 'Embedding läuft im Hintergrund...' }}
          <strong>{{ statusText }}</strong>
        </span>
      </div>
    </v-alert>

    <div class="text-center mb-6">
      <v-icon size="64" color="primary">mdi-cog</v-icon>
      <h2 class="text-h5 mt-4">Chatbot konfigurieren</h2>
      <p class="text-medium-emphasis">
        Passen Sie die Einstellungen Ihres Chatbots an.
      </p>
    </div>

    <v-row>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localConfig.name"
          label="Interner Name"
          prepend-inner-icon="mdi-identifier"
          variant="outlined"
          :rules="[rules.required]"
          hint="Nur Kleinbuchstaben und Unterstriche"
          @update:model-value="updateConfig"
        >
          <template #append>
            <v-btn
              icon
              variant="text"
              size="small"
              :loading="generatingFields.name"
              :disabled="!canGenerate"
              @click="$emit('generate-field', 'name')"
            >
              <v-icon>mdi-auto-fix</v-icon>
              <v-tooltip activator="parent" location="top">
                Mit KI generieren
              </v-tooltip>
            </v-btn>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localConfig.displayName"
          label="Anzeigename"
          prepend-inner-icon="mdi-format-title"
          variant="outlined"
          :rules="[rules.required]"
          @update:model-value="updateConfig"
        >
          <template #append>
            <v-btn
              icon
              variant="text"
              size="small"
              :loading="generatingFields.display_name"
              :disabled="!canGenerate"
              @click="$emit('generate-field', 'display_name')"
            >
              <v-icon>mdi-auto-fix</v-icon>
              <v-tooltip activator="parent" location="top">
                Mit KI generieren
              </v-tooltip>
            </v-btn>
          </template>
        </v-text-field>
      </v-col>
    </v-row>

    <v-textarea
      v-model="localConfig.systemPrompt"
      label="System Prompt"
      prepend-inner-icon="mdi-text-box"
      variant="outlined"
      rows="4"
      :rules="[rules.required]"
      @update:model-value="updateConfig"
    >
      <template #append>
        <v-btn
          icon
          variant="text"
          size="small"
          :loading="generatingFields.system_prompt"
          :disabled="!canGenerate"
          @click="$emit('generate-field', 'system_prompt')"
        >
          <v-icon>mdi-auto-fix</v-icon>
          <v-tooltip activator="parent" location="top">
            Mit KI generieren
          </v-tooltip>
        </v-btn>
      </template>
    </v-textarea>

    <v-textarea
      v-model="localConfig.welcomeMessage"
      label="Willkommensnachricht"
      prepend-inner-icon="mdi-message-text"
      variant="outlined"
      rows="2"
      @update:model-value="updateConfig"
    >
      <template #append>
        <v-btn
          icon
          variant="text"
          size="small"
          :loading="generatingFields.welcome_message"
          :disabled="!canGenerate"
          @click="$emit('generate-field', 'welcome_message')"
        >
          <v-icon>mdi-auto-fix</v-icon>
          <v-tooltip activator="parent" location="top">
            Mit KI generieren
          </v-tooltip>
        </v-btn>
      </template>
    </v-textarea>

    <v-row>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localConfig.icon"
          label="Icon"
          prepend-inner-icon="mdi-emoticon"
          variant="outlined"
          placeholder="mdi-robot"
          @update:model-value="updateConfig"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localConfig.color"
          label="Farbe"
          variant="outlined"
          type="color"
          @update:model-value="updateConfig"
        />
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({
      name: '',
      displayName: '',
      systemPrompt: 'Du bist ein hilfreicher Assistent.',
      welcomeMessage: '',
      icon: 'mdi-robot',
      color: '#5d7a4a'
    })
  },
  buildStatus: {
    type: String,
    default: 'configuring'
  },
  crawlProgress: {
    type: Object,
    default: () => ({})
  },
  embeddingProgress: {
    type: [Number, Object],
    default: 0
  },
  generatingFields: {
    type: Object,
    default: () => ({
      name: false,
      display_name: false,
      system_prompt: false,
      welcome_message: false
    })
  },
  canGenerate: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:config', 'generate-field'])

// Local state
const localConfig = ref({ ...props.config })

// Validation rules
const rules = {
  required: v => !!v || 'Pflichtfeld'
}

// Computed
const isProcessing = computed(() => {
  return ['crawling', 'embedding'].includes(props.buildStatus)
})

const embeddingPercent = computed(() => {
  if (typeof props.embeddingProgress === 'number') {
    return Math.round(props.embeddingProgress)
  }
  return Math.round(props.embeddingProgress?.progress || 0)
})

const statusText = computed(() => {
  if (props.buildStatus === 'crawling') {
    return `${props.crawlProgress.pagesProcessed || 0} Seiten`
  } else if (props.buildStatus === 'embedding') {
    return `${embeddingPercent.value}%`
  }
  return ''
})

// Update handler
const updateConfig = () => {
  emit('update:config', localConfig.value)
}

// Watch props for external updates
watch(() => props.config, (newVal) => {
  localConfig.value = { ...newVal }
}, { deep: true })
</script>

<style scoped>
/* Styles inherited from parent */
</style>
