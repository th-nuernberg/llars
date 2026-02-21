<template>
  <div class="step-review pa-6">
    <!-- Summary Cards -->
    <v-row class="mb-4">
      <v-col cols="6" sm="3">
        <v-card variant="tonal" color="primary" class="pa-4 text-center">
          <LIcon size="32" class="mb-2">mdi-file-document-multiple</LIcon>
          <div class="text-h5">{{ itemCount }}</div>
          <div class="text-caption">{{ $t('dataImporter.stepReview.stats.entries') }}</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card variant="tonal" color="secondary" class="pa-4 text-center">
          <LIcon size="32" class="mb-2">mdi-message-text</LIcon>
          <div class="text-h5">{{ messageCount }}</div>
          <div class="text-caption">{{ $t('dataImporter.stepReview.stats.messages') }}</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card variant="tonal" color="success" class="pa-4 text-center">
          <LIcon size="32" class="mb-2">mdi-account-edit</LIcon>
          <div class="text-h5">{{ raterCount }}</div>
          <div class="text-caption">{{ $t('dataImporter.stepReview.stats.raters') }}</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card variant="tonal" color="info" class="pa-4 text-center">
          <LIcon size="32" class="mb-2">mdi-eye</LIcon>
          <div class="text-h5">{{ evaluatorCount }}</div>
          <div class="text-caption">{{ $t('dataImporter.stepReview.stats.evaluators') }}</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Configuration Summary -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title>
        <LIcon class="mr-2">mdi-clipboard-check</LIcon>
        {{ $t('dataImporter.stepReview.config.title') }}
      </v-card-title>

      <v-card-text>
        <v-table density="compact">
          <tbody>
            <tr>
              <td class="text-medium-emphasis" style="width: 40%">{{ $t('dataImporter.stepReview.config.scenarioName') }}</td>
              <td class="font-weight-medium">{{ scenarioConfig?.name || '—' }}</td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">{{ $t('dataImporter.stepReview.config.taskType') }}</td>
              <td>
                <v-chip size="small" :color="taskTypeColor">
                  <LIcon start size="small">{{ taskTypeIcon }}</LIcon>
                  {{ taskTypeName }}
                </v-chip>
              </td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">{{ $t('dataImporter.stepReview.config.sourceFormat') }}</td>
              <td>{{ formatName }}</td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">{{ $t('dataImporter.stepReview.config.period') }}</td>
              <td>
                {{ formatDate(scenarioConfig?.beginDate) }}
                <template v-if="scenarioConfig?.endDate">
                  — {{ formatDate(scenarioConfig?.endDate) }}
                </template>
                <template v-else>
                  ({{ $t('dataImporter.stepReview.config.unlimited') }})
                </template>
              </td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">{{ $t('dataImporter.stepReview.config.distribution') }}</td>
              <td>{{ distributionModeName }}</td>
            </tr>
            <tr>
              <td class="text-medium-emphasis">{{ $t('dataImporter.stepReview.config.order') }}</td>
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
      <div class="font-weight-medium mb-2">{{ $t('dataImporter.stepReview.warnings.title') }}</div>
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
        <div class="text-h6 mb-2">{{ $t('dataImporter.stepReview.ready.title') }}</div>
        <div class="text-body-2 text-medium-emphasis mb-4">
          {{ $t('dataImporter.stepReview.ready.body') }}
        </div>

        <v-checkbox
          v-model="confirmImport"
          :label="$t('dataImporter.stepReview.ready.confirm')"
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
        <div class="text-h6">{{ $t('dataImporter.stepReview.progress.title') }}</div>
        <div class="text-body-2 text-medium-emphasis">
          {{ $t('dataImporter.stepReview.progress.body') }}
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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
    warns.push(t('dataImporter.stepReview.warnings.noEntries'))
  }

  if (raterCount.value === 0) {
    warns.push(t('dataImporter.stepReview.warnings.noRaters'))
  }

  if (!props.scenarioConfig?.endDate) {
    warns.push(t('dataImporter.stepReview.warnings.noEndDate'))
  }

  return warns
})

const taskTypes = {
  rating: { name: 'Rating', icon: 'mdi-star', color: 'amber' },
  ranking: { name: 'Ranking', icon: 'mdi-sort', color: 'blue' },
  mail_rating: { name: 'Mail Rating', icon: 'mdi-email-check', color: 'green' },
  comparison: { name: 'Comparison', icon: 'mdi-compare', color: 'purple' },
  authenticity: { name: 'Authenticity', icon: 'mdi-shield-check', color: 'orange' },
  judge: { name: 'Chatbot Arena', icon: 'mdi-sword-cross', color: 'teal' },
  labeling: { name: 'Labeling', icon: 'mdi-label-multiple', color: 'indigo' }
}

const normalizeTaskType = (taskType) => {
  if (taskType === 'classification') return 'labeling'
  if (taskType === 'text_classification') return 'labeling'
  if (taskType === 'text_rating') return 'rating'
  return taskType
}

const taskTypeName = computed(() => {
  const taskType = normalizeTaskType(props.scenarioConfig?.taskType)
  return taskTypes[taskType]?.name || taskType
})

const taskTypeIcon = computed(() => {
  const taskType = normalizeTaskType(props.scenarioConfig?.taskType)
  return taskTypes[taskType]?.icon || 'mdi-help'
})

const taskTypeColor = computed(() => {
  const taskType = normalizeTaskType(props.scenarioConfig?.taskType)
  return taskTypes[taskType]?.color || 'grey'
})

const formatName = computed(() => {
  const format = props.session?.detected_format
  if (!format) return t('dataImporter.stepReview.formats.unknown')
  const key = `dataImporter.stepReview.formats.${format}`
  return t(key) !== key ? t(key) : format
})

const distributionModeName = computed(() => {
  const mode = props.scenarioConfig?.distributionMode
  if (mode === 'all') return t('dataImporter.stepScenario.distribution.modes.all')
  if (mode === 'round_robin') return t('dataImporter.stepScenario.distribution.modes.roundRobin')
  return mode
})

const orderModeName = computed(() => {
  const mode = props.scenarioConfig?.orderMode
  if (mode === 'original') return t('dataImporter.stepScenario.distribution.orderModes.original')
  if (mode === 'shuffle_all') return t('dataImporter.stepScenario.distribution.orderModes.shuffleAll')
  if (mode === 'shuffle_per_user') return t('dataImporter.stepScenario.distribution.orderModes.shufflePerUser')
  return mode
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
