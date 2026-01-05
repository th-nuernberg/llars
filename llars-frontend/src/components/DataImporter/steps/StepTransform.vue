<template>
  <div class="step-transform pa-6">
    <!-- Transformation Status -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" :color="statusColor">{{ statusIcon }}</v-icon>
        {{ statusTitle }}
      </v-card-title>

      <v-card-text>
        <template v-if="session?.status === 'transformed' || session?.status === 'validated'">
          <v-row>
            <v-col cols="6" sm="3">
              <div class="text-caption text-medium-emphasis">Gesamt</div>
              <div class="text-h5">{{ stats.total_items || 0 }}</div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="text-caption text-medium-emphasis">Erfolgreich</div>
              <div class="text-h5 text-success">{{ stats.successfully_parsed || 0 }}</div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="text-caption text-medium-emphasis">Fehlgeschlagen</div>
              <div class="text-h5 text-error">{{ stats.failed || 0 }}</div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="text-caption text-medium-emphasis">Nachrichten</div>
              <div class="text-h5">{{ validation?.stats?.total_messages || 0 }}</div>
            </v-col>
          </v-row>
        </template>

        <template v-else>
          <div class="text-body-2 text-medium-emphasis">
            Daten werden in das LLARS-Format transformiert. Dies geschieht automatisch basierend auf dem erkannten Format.
          </div>
        </template>
      </v-card-text>
    </v-card>

    <!-- Warnings & Errors -->
    <template v-if="warnings.length || errors.length">
      <v-alert
        v-for="(err, idx) in errors"
        :key="'error-' + idx"
        type="error"
        variant="tonal"
        density="compact"
        class="mb-2"
      >
        {{ err }}
      </v-alert>

      <v-alert
        v-for="(warn, idx) in warnings"
        :key="'warn-' + idx"
        type="warning"
        variant="tonal"
        density="compact"
        class="mb-2"
      >
        {{ warn }}
      </v-alert>
    </template>

    <!-- Field Mapping Options -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-map</v-icon>
        Feld-Mapping
        <v-spacer />
        <v-switch
          v-model="useCustomMapping"
          label="Anpassen"
          density="compact"
          hide-details
          color="primary"
        />
      </v-card-title>

      <v-card-text v-if="useCustomMapping">
        <v-row dense>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="customMapping.id_field"
              label="ID-Feld"
              density="compact"
              variant="outlined"
              placeholder="z.B. conversation_id"
              hint="Feld für eindeutige ID"
              persistent-hint
            />
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="customMapping.messages_field"
              label="Nachrichten-Feld"
              density="compact"
              variant="outlined"
              placeholder="z.B. messages, turns, conversation"
              hint="Feld mit Konversationsnachrichten"
              persistent-hint
            />
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="customMapping.role_field"
              label="Rollen-Feld"
              density="compact"
              variant="outlined"
              placeholder="z.B. role, sender"
              hint="Feld für Nachrichtenrolle"
              persistent-hint
            />
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="customMapping.content_field"
              label="Inhalt-Feld"
              density="compact"
              variant="outlined"
              placeholder="z.B. content, text, message"
              hint="Feld für Nachrichteninhalt"
              persistent-hint
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end mt-4">
          <LBtn
            variant="primary"
            size="small"
            :loading="loading"
            @click="applyCustomMapping"
          >
            Mapping anwenden
          </LBtn>
        </div>
      </v-card-text>
    </v-card>

    <!-- AI Script Generation -->
    <v-card variant="outlined" class="ai-card">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="purple">mdi-code-braces</v-icon>
        KI-Transformationsskript
        <v-chip class="ml-2" size="x-small" color="purple" variant="tonal">
          Für komplexe Formate
        </v-chip>
        <v-spacer />
        <LBtn
          v-if="!aiScript"
          variant="secondary"
          size="small"
          :loading="loading"
          prepend-icon="mdi-magic-staff"
          @click="generateScript"
        >
          Skript generieren
        </LBtn>
      </v-card-title>

      <v-card-text>
        <template v-if="aiScript?.script">
          <v-alert
            :type="aiScript.success ? 'success' : 'warning'"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            {{ aiScript.success ? 'Skript erfolgreich generiert' : 'Skript mit Warnungen generiert' }}
          </v-alert>

          <div class="script-editor">
            <pre class="script-content"><code>{{ aiScript.script }}</code></pre>
          </div>

          <div class="d-flex justify-end mt-4 gap-2">
            <LBtn variant="text" size="small" @click="aiScript = null">
              Verwerfen
            </LBtn>
            <LBtn
              variant="primary"
              size="small"
              :loading="loading"
              prepend-icon="mdi-play"
              @click="executeScript"
            >
              Skript ausführen
            </LBtn>
          </div>
        </template>

        <template v-else>
          <div class="text-body-2 text-medium-emphasis">
            Wenn deine Daten ein komplexes oder unbekanntes Format haben, kann die KI ein
            Python-Transformationsskript generieren. Das Skript wird vor der Ausführung
            angezeigt und kann manuell geprüft werden.
          </div>
        </template>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  session: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['transform', 'ai-script'])

const useCustomMapping = ref(false)
const customMapping = ref({
  id_field: '',
  messages_field: '',
  role_field: '',
  content_field: ''
})

const aiScript = ref(null)

const stats = computed(() => {
  return props.session?.validation?.stats || {}
})

const validation = computed(() => {
  return props.session?.validation
})

const warnings = computed(() => {
  return props.session?.warnings || []
})

const errors = computed(() => {
  return props.session?.errors || []
})

const statusColor = computed(() => {
  if (props.session?.status === 'validated') return 'success'
  if (props.session?.status === 'transformed') return 'info'
  if (errors.value.length) return 'error'
  return 'grey'
})

const statusIcon = computed(() => {
  if (props.session?.status === 'validated') return 'mdi-check-circle'
  if (props.session?.status === 'transformed') return 'mdi-swap-horizontal'
  if (errors.value.length) return 'mdi-alert-circle'
  return 'mdi-clock-outline'
})

const statusTitle = computed(() => {
  if (props.session?.status === 'validated') return 'Transformation & Validierung erfolgreich'
  if (props.session?.status === 'transformed') return 'Transformation abgeschlossen'
  if (errors.value.length) return 'Transformation mit Fehlern'
  return 'Transformation ausstehend'
})

const applyCustomMapping = () => {
  const mappings = {}
  Object.entries(customMapping.value).forEach(([key, value]) => {
    if (value?.trim()) {
      mappings[key] = value.trim()
    }
  })

  emit('transform', { mappings })
}

const generateScript = () => {
  emit('ai-script', customMapping.value)
}

const executeScript = () => {
  // Script execution would be handled by backend
  emit('transform', { use_ai_script: true })
}
</script>

<style scoped>
.ai-card {
  border-color: rgba(156, 39, 176, 0.3);
}

.script-editor {
  background: rgb(var(--v-theme-surface-variant));
  border-radius: 8px;
  overflow: hidden;
}

.script-content {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow-y: auto;
}

.gap-2 {
  gap: 8px;
}
</style>
