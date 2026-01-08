<template>
  <div class="step-review pa-6">
    <!-- Summary Cards -->
    <v-row class="mb-4">
      <v-col cols="6" sm="3">
        <v-card variant="tonal" color="primary" class="pa-4 text-center">
          <LIcon size="32" class="mb-2">mdi-file-document-multiple</LIcon>
          <div class="text-h5">{{ itemCount }}</div>
          <div class="text-caption">Einträge</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card variant="tonal" color="secondary" class="pa-4 text-center">
          <LIcon size="32" class="mb-2">mdi-message-text</LIcon>
          <div class="text-h5">{{ messageCount }}</div>
          <div class="text-caption">Nachrichten</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card variant="tonal" color="success" class="pa-4 text-center">
          <LIcon size="32" class="mb-2">mdi-account-edit</LIcon>
          <div class="text-h5">{{ raterCount }}</div>
          <div class="text-caption">Rater</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card variant="tonal" color="info" class="pa-4 text-center">
          <LIcon size="32" class="mb-2">mdi-eye</LIcon>
          <div class="text-h5">{{ evaluatorCount }}</div>
          <div class="text-caption">Evaluator</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Configuration Summary -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title>
        <LIcon class="mr-2">mdi-clipboard-check</LIcon>
        Konfiguration
      </v-card-title>

      <v-card-text>
        <v-table density="compact">
          <tbody>
            <tr>
              <td class="text-medium-emphasis" style="width: 40%">Szenario-Name</td>
              <td class="font-weight-medium">{{ scenarioConfig?.name || '—' }}</td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">Aufgabentyp</td>
              <td>
                <v-chip size="small" :color="taskTypeColor">
                  <LIcon start size="small">{{ taskTypeIcon }}</LIcon>
                  {{ taskTypeName }}
                </v-chip>
              </td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">Quell-Format</td>
              <td>{{ formatName }}</td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">Zeitraum</td>
              <td>
                {{ formatDate(scenarioConfig?.beginDate) }}
                <template v-if="scenarioConfig?.endDate">
                  — {{ formatDate(scenarioConfig?.endDate) }}
                </template>
                <template v-else>
                  (unbegrenzt)
                </template>
              </td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">Verteilung</td>
              <td>{{ distributionModeName }}</td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">Reihenfolge</td>
              <td>{{ orderModeName }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>

    <!-- Warnings -->
    <v-alert
      v-if="warnings.length"
      type="warning"
      variant="tonal"
      class="mb-4"
    >
      <div class="font-weight-medium mb-2">Hinweise:</div>
      <ul class="pl-4 mb-0">
        <li v-for="(warn, idx) in warnings" :key="idx">{{ warn }}</li>
      </ul>
    </v-alert>

    <!-- Error -->
    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      class="mb-4"
    >
      {{ error }}
    </v-alert>

    <!-- Ready to Import -->
    <v-card
      v-if="!error"
      variant="outlined"
      class="ready-card"
    >
      <v-card-text class="text-center pa-6">
        <LIcon size="64" color="success" class="mb-4">mdi-rocket-launch</LIcon>
        <div class="text-h6 mb-2">Bereit zum Import</div>
        <div class="text-body-2 text-medium-emphasis mb-4">
          Alle Einstellungen wurden geprüft. Klicke auf "Import starten" um die Daten
          zu importieren und das Szenario zu erstellen.
        </div>

        <v-checkbox
          v-model="confirmImport"
          label="Ich habe die Konfiguration überprüft"
          color="success"
          hide-details
          class="d-inline-flex"
        />
      </v-card-text>
    </v-card>

    <!-- Import Progress -->
    <v-card v-if="loading" variant="outlined" class="mt-4">
      <v-card-text class="text-center pa-6">
        <v-progress-circular indeterminate color="primary" size="48" class="mb-4" />
        <div class="text-h6">Import läuft...</div>
        <div class="text-body-2 text-medium-emphasis">
          Bitte warte, während die Daten importiert werden.
        </div>
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
  scenarioConfig: {
    type: Object,
    default: null
  },
  userConfig: {
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

const emit = defineEmits(['execute'])

const confirmImport = ref(false)

const itemCount = computed(() => {
  return props.session?.item_count ||
         props.session?.validation?.stats?.total_items ||
         0
})

const messageCount = computed(() => {
  return props.session?.validation?.stats?.total_messages || 0
})

const raterCount = computed(() => {
  return props.userConfig?.raters?.length || 0
})

const evaluatorCount = computed(() => {
  return props.userConfig?.evaluators?.length || props.userConfig?.viewers?.length || 0
})

const warnings = computed(() => {
  const warns = []

  if (itemCount.value === 0) {
    warns.push('Keine Einträge zum Importieren gefunden.')
  }

  if (raterCount.value === 0) {
    warns.push('Keine Rater ausgewählt. Das Szenario kann nicht bewertet werden.')
  }

  if (!props.scenarioConfig?.endDate) {
    warns.push('Kein Enddatum gesetzt. Das Szenario bleibt unbegrenzt aktiv.')
  }

  return warns
})

const taskTypes = {
  rating: { name: 'Rating', icon: 'mdi-star', color: 'amber' },
  ranking: { name: 'Ranking', icon: 'mdi-sort', color: 'blue' },
  mail_rating: { name: 'Mail Rating', icon: 'mdi-email-check', color: 'green' },
  comparison: { name: 'Comparison', icon: 'mdi-compare', color: 'purple' },
  authenticity: { name: 'Authenticity', icon: 'mdi-shield-check', color: 'orange' },
  judge: { name: 'LLM-as-Judge', icon: 'mdi-gavel', color: 'teal' },
  text_classification: { name: 'Text Classification', icon: 'mdi-label-multiple', color: 'indigo' },
  text_rating: { name: 'Text Rating', icon: 'mdi-text-box-check', color: 'cyan' }
}

const taskTypeName = computed(() => {
  return taskTypes[props.scenarioConfig?.taskType]?.name || props.scenarioConfig?.taskType
})

const taskTypeIcon = computed(() => {
  return taskTypes[props.scenarioConfig?.taskType]?.icon || 'mdi-help'
})

const taskTypeColor = computed(() => {
  return taskTypes[props.scenarioConfig?.taskType]?.color || 'grey'
})

const formatNames = {
  openai: 'OpenAI/ChatML',
  lmsys: 'LMSYS Pairwise',
  jsonl: 'JSONL',
  csv: 'CSV/Tabular',
  llars: 'LLARS Native',
  generic: 'Generic Text Data'
}

const formatName = computed(() => {
  return formatNames[props.session?.detected_format] || props.session?.detected_format || 'Unbekannt'
})

const distributionModes = {
  all: 'Alle sehen alles',
  round_robin: 'Round Robin'
}

const distributionModeName = computed(() => {
  return distributionModes[props.scenarioConfig?.distributionMode] || props.scenarioConfig?.distributionMode
})

const orderModes = {
  original: 'Original',
  shuffle_all: 'Zufällig (alle gleich)',
  shuffle_per_user: 'Zufällig (pro Nutzer)'
}

const orderModeName = computed(() => {
  return orderModes[props.scenarioConfig?.orderMode] || props.scenarioConfig?.orderMode
})

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('de-DE')
}
</script>

<style scoped>
.ready-card {
  border-color: rgb(var(--v-theme-success));
  background: rgba(var(--v-theme-success), 0.02);
}
</style>
