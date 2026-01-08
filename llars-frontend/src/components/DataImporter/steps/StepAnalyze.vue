<template>
  <div class="step-analyze pa-6">
    <!-- Detection Result Card -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2" color="success">mdi-check-circle</LIcon>
        Format erkannt
        <v-spacer />
        <v-chip color="primary" size="small">
          {{ session?.format_confidence ? Math.round(session.format_confidence * 100) : 0 }}% Konfidenz
        </v-chip>
      </v-card-title>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-caption text-medium-emphasis">Erkanntes Format</div>
            <div class="text-h6">{{ formatName }}</div>
          </v-col>
          <v-col cols="12" md="6">
            <div class="text-caption text-medium-emphasis">Anzahl Einträge</div>
            <div class="text-h6">{{ itemCount }}</div>
          </v-col>
        </v-row>

        <!-- Detected Fields -->
        <div v-if="detectedFields.length" class="mt-4">
          <div class="text-caption text-medium-emphasis mb-2">Erkannte Felder</div>
          <div class="d-flex flex-wrap gap-2">
            <v-chip
              v-for="field in detectedFields"
              :key="field"
              size="small"
              variant="tonal"
            >
              {{ field }}
            </v-chip>
          </div>
        </div>

        <!-- Suggested Task Type -->
        <div v-if="suggestedTaskType" class="mt-4">
          <div class="text-caption text-medium-emphasis mb-2">Empfohlener Aufgabentyp</div>
          <v-chip color="secondary" size="small">
            <LIcon start size="small">{{ taskTypeIcon }}</LIcon>
            {{ taskTypeName }}
          </v-chip>
        </div>
      </v-card-text>
    </v-card>

    <!-- AI Analysis Card -->
    <v-card variant="outlined" class="mb-4 ai-card">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2" color="purple">mdi-robot</LIcon>
        KI-Analyse
        <v-chip class="ml-2" size="x-small" color="purple" variant="tonal">
          Optional
        </v-chip>
        <v-spacer />
        <LBtn
          v-if="!aiAnalysis"
          variant="secondary"
          size="small"
          :loading="loading"
          :disabled="loading"
          prepend-icon="mdi-magic-staff"
          @click="$emit('ai-analyze')"
        >
          KI analysieren lassen
        </LBtn>
      </v-card-title>

      <v-card-text>
        <template v-if="aiAnalysis">
          <!-- AI Results -->
          <v-alert type="success" variant="tonal" density="compact" class="mb-4">
            KI-Analyse abgeschlossen
          </v-alert>

          <div v-if="aiAnalysis.reasoning" class="mb-4">
            <div class="text-caption text-medium-emphasis mb-1">Begründung</div>
            <div class="text-body-2">{{ aiAnalysis.reasoning }}</div>
          </div>

          <div v-if="aiAnalysis.field_mapping" class="mb-4">
            <div class="text-caption text-medium-emphasis mb-2">Vorgeschlagenes Mapping</div>
            <v-table density="compact">
              <tbody>
                <tr v-for="(value, key) in aiAnalysis.field_mapping" :key="key">
                  <td class="text-caption">{{ key }}</td>
                  <td>
                    <LIcon size="small" class="mx-2">mdi-arrow-right</LIcon>
                  </td>
                  <td class="font-weight-medium">{{ value || '—' }}</td>
                </tr>
              </tbody>
            </v-table>
          </div>

          <div v-if="aiAnalysis.warnings?.length" class="mt-4">
            <v-alert
              v-for="(warning, idx) in aiAnalysis.warnings"
              :key="idx"
              type="warning"
              variant="tonal"
              density="compact"
              class="mb-2"
            >
              {{ warning }}
            </v-alert>
          </div>
        </template>

        <template v-else>
          <div class="text-body-2 text-medium-emphasis">
            Lasse die KI deine Datenstruktur analysieren und optimale Mappings vorschlagen.
            Dies ist optional - du kannst auch direkt fortfahren.
          </div>
        </template>
      </v-card-text>
    </v-card>

    <!-- Data Preview -->
    <v-card variant="outlined">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-eye</LIcon>
        Daten-Vorschau
        <v-spacer />
        <LBtn
          variant="text"
          size="small"
          :loading="loadingSample"
          @click="loadSample"
        >
          Aktualisieren
        </LBtn>
      </v-card-title>

      <v-card-text>
        <div v-if="sampleData.length" class="sample-preview">
          <div
            v-for="(item, idx) in sampleData"
            :key="idx"
            class="sample-item pa-3 mb-2"
          >
            <div class="d-flex align-center mb-2">
              <v-chip size="x-small" color="primary" variant="tonal">
                #{{ item.id || idx + 1 }}
              </v-chip>
              <span v-if="item.subject" class="ml-2 text-body-2 font-weight-medium">
                {{ item.subject }}
              </span>
            </div>

            <div v-if="item.conversation" class="conversation-preview">
              <div
                v-for="(msg, msgIdx) in item.conversation.slice(0, 3)"
                :key="msgIdx"
                class="message-preview d-flex mb-1"
              >
                <v-chip
                  size="x-small"
                  :color="msg.role === 'user' ? 'blue' : 'green'"
                  variant="tonal"
                  class="mr-2"
                  style="min-width: 70px"
                >
                  {{ msg.role }}
                </v-chip>
                <span class="text-caption text-truncate">
                  {{ truncate(msg.content, 100) }}
                </span>
              </div>
              <div v-if="item.conversation.length > 3" class="text-caption text-medium-emphasis mt-1">
                ... und {{ item.conversation.length - 3 }} weitere Nachrichten
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center text-medium-emphasis pa-4">
          Keine Vorschau verfügbar
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import importService from '@/services/importService'

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

const emit = defineEmits(['ai-analyze', 'continue'])

const sampleData = ref([])
const loadingSample = ref(false)

const formatNames = {
  openai: 'OpenAI/ChatML',
  lmsys: 'LMSYS Pairwise',
  jsonl: 'JSONL',
  csv: 'CSV/Tabular',
  llars: 'LLARS Native'
}

const taskTypes = {
  rating: { name: 'Rating', icon: 'mdi-star' },
  ranking: { name: 'Ranking', icon: 'mdi-sort' },
  mail_rating: { name: 'Mail Rating', icon: 'mdi-email-check' },
  comparison: { name: 'Comparison', icon: 'mdi-compare' },
  authenticity: { name: 'Authenticity', icon: 'mdi-shield-check' }
}

const formatName = computed(() => {
  return formatNames[props.session?.detected_format] || props.session?.detected_format || 'Unbekannt'
})

const itemCount = computed(() => {
  return props.session?.item_count || props.session?.structure?.item_count || 0
})

const detectedFields = computed(() => {
  return props.session?.structure?.fields || []
})

const suggestedTaskType = computed(() => {
  return props.session?.structure?.ai_suggested_task_type ||
         props.session?.suggested_task_type ||
         props.session?.structure?.task_type
})

const taskTypeName = computed(() => {
  return taskTypes[suggestedTaskType.value]?.name || suggestedTaskType.value
})

const taskTypeIcon = computed(() => {
  return taskTypes[suggestedTaskType.value]?.icon || 'mdi-help'
})

const aiAnalysis = computed(() => {
  return props.session?.ai_analysis
})

const truncate = (str, len) => {
  if (!str) return ''
  return str.length > len ? str.substring(0, len) + '...' : str
}

const loadSample = async () => {
  if (!props.session?.session_id) return

  loadingSample.value = true
  try {
    const result = await importService.getSample(props.session.session_id, 3)
    sampleData.value = result.sample || []
  } catch (err) {
    console.error('Failed to load sample:', err)
  } finally {
    loadingSample.value = false
  }
}

onMounted(() => {
  loadSample()
})
</script>

<style scoped>
.ai-card {
  border-color: rgba(156, 39, 176, 0.3);
}

.sample-preview {
  max-height: 400px;
  overflow-y: auto;
}

.sample-item {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
}

.conversation-preview {
  padding-left: 8px;
  border-left: 2px solid rgba(var(--v-theme-primary), 0.3);
}

.message-preview {
  align-items: flex-start;
}

.gap-2 {
  gap: 8px;
}
</style>
