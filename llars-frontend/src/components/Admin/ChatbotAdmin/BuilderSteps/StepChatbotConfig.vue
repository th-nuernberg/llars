<template>
  <v-card flat class="pa-3">
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

    <h3 class="text-h6 mb-3">Chatbot konfigurieren</h3>

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
              <LIcon>mdi-auto-fix</LIcon>
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
              <LIcon>mdi-auto-fix</LIcon>
              <v-tooltip activator="parent" location="top">
                Mit KI generieren
              </v-tooltip>
            </v-btn>
          </template>
        </v-text-field>
      </v-col>
    </v-row>

    <v-textarea
      ref="systemPromptRef"
      v-model="localConfig.systemPrompt"
      label="System Prompt"
      prepend-inner-icon="mdi-text-box"
      variant="outlined"
      rows="3"
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
          <LIcon>mdi-auto-fix</LIcon>
          <v-tooltip activator="parent" location="top">
            Mit KI generieren
          </v-tooltip>
        </v-btn>
      </template>
    </v-textarea>

    <LlmModelSelect
      v-model="localConfig.modelName"
      label="LLM Modell"
      :rules="[rules.required]"
      :clearable="true"
      :allow-sync="true"
      @update:model-value="updateConfig"
    />

    <v-textarea
      ref="welcomeMessageRef"
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
          <LIcon>mdi-auto-fix</LIcon>
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
          variant="outlined"
          placeholder="mdi-robot"
          density="compact"
          :loading="generatingFields.icon"
          @update:model-value="updateConfig"
        >
          <template #prepend-inner>
            <v-icon
              :color="localConfig.color || '#5d7a4a'"
              :class="{ 'icon-generating': generatingFields.icon }"
            >
              {{ localConfig.icon || 'mdi-robot' }}
            </v-icon>
          </template>
          <template #append>
            <v-btn
              icon
              variant="text"
              size="small"
              :loading="generatingFields.icon"
              :disabled="!canGenerate"
              @click="$emit('generate-field', 'icon')"
            >
              <LIcon>mdi-auto-fix</LIcon>
              <v-tooltip activator="parent" location="top">
                Icon mit KI vorschlagen
              </v-tooltip>
            </v-btn>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="localConfig.color"
          label="Farbe"
          variant="outlined"
          type="color"
          density="compact"
          :loading="generatingFields.color"
          @update:model-value="updateConfig"
        >
          <template #prepend-inner>
            <div
              :class="{ 'color-generating': generatingFields.color }"
              :style="{
                width: '24px',
                height: '24px',
                borderRadius: '4px',
                backgroundColor: localConfig.color || '#5d7a4a',
                border: '1px solid rgba(0,0,0,0.2)'
              }"
            />
          </template>
          <template #append>
            <v-btn
              icon
              variant="text"
              size="small"
              :loading="generatingFields.color"
              :disabled="!canGenerate"
              @click="$emit('generate-field', 'color')"
            >
              <LIcon>mdi-auto-fix</LIcon>
              <v-tooltip activator="parent" location="top">
                Farbe mit KI vorschlagen
              </v-tooltip>
            </v-btn>
          </template>
        </v-text-field>
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({
      name: '',
      displayName: '',
      systemPrompt: 'Du bist ein hilfreicher Assistent.',
      modelName: '',
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
      welcome_message: false,
      icon: false,
      color: false
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
const systemPromptRef = ref(null)
const welcomeMessageRef = ref(null)

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

const scrollTextareaToBottom = (fieldRef) => {
  nextTick(() => {
    requestAnimationFrame(() => {
      const textarea = fieldRef.value?.$el?.querySelector('textarea')
      if (textarea) {
        textarea.scrollTop = textarea.scrollHeight
      }
    })
  })
}

// Watch props for external updates
watch(() => props.config, (newVal) => {
  localConfig.value = { ...newVal }
}, { deep: true })

watch(() => localConfig.value.systemPrompt, () => {
  if (props.generatingFields?.system_prompt) {
    scrollTextareaToBottom(systemPromptRef)
  }
})

watch(() => localConfig.value.welcomeMessage, () => {
  if (props.generatingFields?.welcome_message) {
    scrollTextareaToBottom(welcomeMessageRef)
  }
})
</script>

<style scoped>
/* Icon generation animation */
.icon-generating {
  animation: icon-pulse 1s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.9);
  }
}

/* Color generation animation */
.color-generating {
  animation: color-pulse 1s ease-in-out infinite;
  box-shadow: 0 0 0 2px rgba(176, 202, 151, 0.5);
}

@keyframes color-pulse {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 0 2px rgba(176, 202, 151, 0.5);
  }
  50% {
    opacity: 0.7;
    box-shadow: 0 0 0 4px rgba(176, 202, 151, 0.3);
  }
}
</style>
