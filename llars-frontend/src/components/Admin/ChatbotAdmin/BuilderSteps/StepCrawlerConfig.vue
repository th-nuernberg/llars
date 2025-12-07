<template>
  <v-card flat class="pa-4">
    <div class="text-center mb-6">
      <v-icon size="64" color="primary">mdi-web</v-icon>
      <h2 class="text-h5 mt-4">Website URL eingeben</h2>
      <p class="text-medium-emphasis">
        Geben Sie die URL der Website ein, aus der der Chatbot lernen soll.
      </p>
    </div>

    <v-text-field
      v-model="localUrl"
      label="Website URL"
      placeholder="https://example.com"
      prepend-inner-icon="mdi-link"
      variant="outlined"
      :rules="[rules.required, rules.url]"
      :error-messages="errorMessage"
      @keyup.enter="$emit('start')"
      @update:model-value="updateUrl"
    />

    <!-- Crawler Options -->
    <v-expansion-panels class="mt-4">
      <v-expansion-panel>
        <v-expansion-panel-title>
          <v-icon class="mr-2">mdi-cog</v-icon>
          Erweiterte Crawler-Einstellungen
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model.number="localConfig.maxPages"
                label="Max. Seiten"
                type="number"
                min="1"
                max="500"
                variant="outlined"
                density="compact"
                @update:model-value="updateConfig"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model.number="localConfig.maxDepth"
                label="Max. Tiefe"
                type="number"
                min="1"
                max="10"
                variant="outlined"
                density="compact"
                @update:model-value="updateConfig"
              />
            </v-col>
          </v-row>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      class="mt-4"
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
      maxDepth: 3
    })
  },
  errorMessage: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:url', 'update:config', 'start'])

// Local state
const localUrl = ref(props.url)
const localConfig = ref({ ...props.config })

// Validation rules
const rules = {
  required: v => !!v || 'Pflichtfeld',
  url: v => {
    if (!v) return true
    try {
      new URL(v)
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
  emit('update:config', localConfig.value)
}

// Watch props for external updates
watch(() => props.url, (newVal) => {
  localUrl.value = newVal
})

watch(() => props.config, (newVal) => {
  localConfig.value = { ...newVal }
}, { deep: true })
</script>

<style scoped>
/* Styles inherited from parent */
</style>
