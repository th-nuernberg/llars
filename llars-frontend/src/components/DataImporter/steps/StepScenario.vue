<template>
  <div class="step-scenario pa-6">
    <!-- AI Suggestion Banner -->
    <v-card
      v-if="aiSuggestion && !aiSuggestionDismissed"
      variant="tonal"
      color="purple"
      class="mb-4"
    >
      <v-card-text>
        <div class="d-flex align-start">
          <LIcon class="mr-3 mt-1" color="purple">mdi-robot</LIcon>
          <div class="flex-grow-1">
            <div class="text-subtitle-2 font-weight-bold mb-1">
              {{ $t('dataImporter.stepScenario.aiSuggestion.title') }}
            </div>
            <div class="text-body-2 mb-3">
              {{ aiSuggestion.reasoning }}
            </div>
            <div class="d-flex flex-wrap gap-2">
              <LBtn
                size="small"
                variant="primary"
                prepend-icon="mdi-check"
                @click="applyAiSuggestion"
              >
                {{ $t('dataImporter.stepScenario.aiSuggestion.apply') }}
              </LBtn>
              <LBtn
                size="small"
                variant="text"
                @click="aiSuggestionDismissed = true"
              >
                {{ $t('dataImporter.stepScenario.aiSuggestion.manual') }}
              </LBtn>
            </div>
          </div>
          <v-btn
            icon="mdi-close"
            size="x-small"
            variant="text"
            @click="aiSuggestionDismissed = true"
          />
        </div>
      </v-card-text>
    </v-card>

    <!-- Scenario Mode Selection -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text class="pa-4">
        <v-radio-group v-model="scenarioMode" inline hide-details>
          <v-radio value="new" color="primary">
            <template #label>
              <div class="d-flex align-center">
                <LIcon class="mr-2" size="small">mdi-plus-circle</LIcon>
                <span>{{ $t('dataImporter.stepScenario.mode.new') }}</span>
              </div>
            </template>
          </v-radio>
          <v-radio value="existing" color="primary">
            <template #label>
              <div class="d-flex align-center">
                <LIcon class="mr-2" size="small">mdi-folder-open</LIcon>
                <span>{{ $t('dataImporter.stepScenario.mode.existing') }}</span>
              </div>
            </template>
          </v-radio>
        </v-radio-group>
      </v-card-text>
    </v-card>

    <!-- Existing Scenario Selection -->
    <v-card v-if="scenarioMode === 'existing'" variant="outlined" class="mb-4">
      <v-card-title>
        <LIcon class="mr-2">mdi-folder-open</LIcon>
        {{ $t('dataImporter.stepScenario.existingScenario.title') }}
      </v-card-title>

      <v-card-text>
        <v-autocomplete
          v-model="localConfig.existingScenarioId"
          :label="$t('dataImporter.stepScenario.existingScenario.select')"
          variant="outlined"
          density="comfortable"
          :items="existingScenarios"
          :item-title="scenario => `${scenario.name} (${scenario.thread_count || 0} Threads)`"
          item-value="scenario_id"
          :loading="loadingScenarios"
          :placeholder="$t('dataImporter.stepScenario.existingScenario.searchPlaceholder')"
          clearable
        >
          <template #item="{ item, props }">
            <v-list-item v-bind="props">
              <template #prepend>
                <LIcon :color="getTaskTypeColor(item.raw.function_type)">
                  {{ getTaskTypeIcon(item.raw.function_type) }}
                </LIcon>
              </template>
              <v-list-item-subtitle>
                {{ item.raw.thread_count || 0 }} Threads |
                {{ getTaskTypeName(item.raw.function_type) }}
              </v-list-item-subtitle>
            </v-list-item>
          </template>
        </v-autocomplete>

        <v-alert v-if="localConfig.existingScenarioId" type="info" variant="tonal" class="mt-3">
          {{ $t('dataImporter.stepScenario.existingScenario.newEntries', { count: itemCount }) }}
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- New Scenario Configuration -->
    <template v-if="scenarioMode === 'new'">
      <!-- Basic Info -->
      <v-card variant="outlined" class="mb-4">
        <v-card-title>
          <LIcon class="mr-2">mdi-information</LIcon>
          {{ $t('dataImporter.stepScenario.scenarioInfo.title') }}
          <v-spacer />
          <v-btn
            v-if="!aiGeneratingName"
            size="x-small"
            variant="tonal"
            color="purple"
            prepend-icon="mdi-robot"
            @click="generateAiName"
          >
            {{ $t('dataImporter.stepScenario.scenarioInfo.aiName') }}
          </v-btn>
          <v-progress-circular v-else size="20" width="2" indeterminate color="purple" />
        </v-card-title>

        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="localConfig.name"
                :label="$t('dataImporter.stepScenario.scenarioInfo.name')"
                variant="outlined"
                density="comfortable"
                :placeholder="$t('dataImporter.stepScenario.scenarioInfo.namePlaceholder')"
                :rules="[v => !!v || $t('dataImporter.stepScenario.scenarioInfo.nameRequired')]"
              >
                <template #append-inner>
                  <v-tooltip :text="$t('dataImporter.stepScenario.scenarioInfo.aiNameTooltip')">
                    <template #activator="{ props }">
                      <v-btn
                        v-bind="props"
                        icon
                        size="x-small"
                        variant="text"
                        color="purple"
                        :loading="aiGeneratingName"
                        @click="generateAiName"
                      >
                        <LIcon>wand</LIcon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </template>
              </v-text-field>
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="localConfig.taskType"
                :label="$t('dataImporter.stepScenario.scenarioInfo.taskType')"
                variant="outlined"
                density="comfortable"
                :items="taskTypes"
                item-title="name"
                item-value="value"
              >
                <template #item="{ item, props }">
                  <v-list-item v-bind="props">
                    <template #prepend>
                      <LIcon :color="item.raw.color">{{ item.raw.icon }}</LIcon>
                    </template>
                    <v-list-item-subtitle>{{ item.raw.description }}</v-list-item-subtitle>
                  </v-list-item>
                </template>

                <template #selection="{ item }">
                  <LIcon class="mr-2" :color="item.raw.color">{{ item.raw.icon }}</LIcon>
                  {{ item.raw.name }}
                </template>
              </v-select>
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="localConfig.sourceName"
                :label="$t('dataImporter.stepScenario.scenarioInfo.sourceName')"
                variant="outlined"
                density="comfortable"
                :placeholder="$t('dataImporter.stepScenario.scenarioInfo.sourceNamePlaceholder')"
                :hint="$t('dataImporter.stepScenario.scenarioInfo.sourceNameHint')"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-textarea
                v-model="localConfig.description"
                :label="$t('dataImporter.stepScenario.scenarioInfo.description')"
                variant="outlined"
                density="comfortable"
                rows="2"
                :placeholder="$t('dataImporter.stepScenario.scenarioInfo.descriptionPlaceholder')"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Dates -->
      <v-card variant="outlined" class="mb-4">
        <v-card-title>
          <LIcon class="mr-2">mdi-calendar</LIcon>
          {{ $t('dataImporter.stepScenario.dates.title') }}
        </v-card-title>

        <v-card-text>
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="localConfig.beginDate"
                :label="$t('dataImporter.stepScenario.dates.startDate')"
                type="date"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="localConfig.endDate"
                :label="$t('dataImporter.stepScenario.dates.endDate')"
                type="date"
                variant="outlined"
                density="comfortable"
                :hint="$t('dataImporter.stepScenario.dates.endDateHint')"
                persistent-hint
              />
            </v-col>
          </v-row>

          <!-- Quick Date Buttons -->
          <div class="d-flex flex-wrap gap-2 mt-2">
            <v-chip
              v-for="preset in datePresets"
              :key="preset.label"
              size="small"
              variant="tonal"
              @click="applyDatePreset(preset)"
            >
              {{ preset.label }}
            </v-chip>
          </div>
        </v-card-text>
      </v-card>

      <!-- Distribution Settings -->
      <v-card variant="outlined" class="mb-4">
        <v-card-title>
          <LIcon class="mr-2">mdi-account-switch</LIcon>
          {{ $t('dataImporter.stepScenario.distribution.title') }}
        </v-card-title>

        <v-card-text>
          <v-row>
            <v-col cols="12" sm="6">
              <v-select
                v-model="localConfig.distributionMode"
                :label="$t('dataImporter.stepScenario.distribution.mode')"
                variant="outlined"
                density="comfortable"
                :items="distributionModes"
                item-title="name"
                item-value="value"
              >
                <template #item="{ item, props }">
                  <v-list-item v-bind="props">
                    <v-list-item-subtitle>{{ item.raw.description }}</v-list-item-subtitle>
                  </v-list-item>
                </template>
              </v-select>
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="localConfig.orderMode"
                :label="$t('dataImporter.stepScenario.distribution.order')"
                variant="outlined"
                density="comfortable"
                :items="orderModes"
                item-title="name"
                item-value="value"
              >
                <template #item="{ item, props }">
                  <v-list-item v-bind="props">
                    <v-list-item-subtitle>{{ item.raw.description }}</v-list-item-subtitle>
                  </v-list-item>
                </template>
              </v-select>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </template>

    <!-- Summary Info -->
    <v-alert :type="scenarioMode === 'existing' ? 'warning' : 'info'" variant="tonal" class="mt-4">
      <div class="d-flex align-center">
        <LIcon class="mr-2">
          {{ scenarioMode === 'existing' ? 'mdi-alert' : 'mdi-information' }}
        </LIcon>
        <div>
          <template v-if="scenarioMode === 'new'">
            {{ $t('dataImporter.stepScenario.summary.newScenario', { count: itemCount, name: localConfig.name || $t('dataImporter.stepScenario.summary.unnamed') }) }}
          </template>
          <template v-else>
            {{ $t('dataImporter.stepScenario.summary.existingScenario', { count: itemCount }) }}
          </template>
        </div>
      </div>
    </v-alert>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  scenarioConfig: {
    type: Object,
    required: true
  },
  session: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:scenarioConfig'])

// Local state
const localConfig = ref({ ...props.scenarioConfig })
const scenarioMode = ref('new')
const existingScenarios = ref([])
const loadingScenarios = ref(false)
const aiSuggestion = ref(null)
const aiSuggestionDismissed = ref(false)
const aiGeneratingName = ref(false)

// Sync back to parent
watch(localConfig, (newVal) => {
  emit('update:scenarioConfig', { ...newVal, mode: scenarioMode.value })
}, { deep: true })

watch(scenarioMode, (mode) => {
  emit('update:scenarioConfig', { ...localConfig.value, mode })
})

// Sync from parent
watch(() => props.scenarioConfig, (newVal) => {
  localConfig.value = { ...newVal }
  if (newVal.mode) {
    scenarioMode.value = newVal.mode
  }
}, { deep: true })

// Watch session for AI suggestions
watch(() => props.session, (session) => {
  if (session?.structure?.suggested_task_type || session?.task_type) {
    generateAiSuggestion()
  }
}, { immediate: true })

const itemCount = computed(() => {
  return props.session?.item_count ||
         props.session?.validation?.stats?.total_items ||
         0
})

// Generate AI suggestion based on session data
const generateAiSuggestion = () => {
  const session = props.session
  if (!session) return

  const detectedFormat = session.detected_format
  const structure = session.structure || {}
  const suggestedType = structure.suggested_task_type || session.task_type

  // Build reasoning based on detected data
  let reasoning = ''
  let taskType = 'rating'

  if (detectedFormat === 'lmsys' || structure.detected_item_type === 'text_pair') {
    taskType = 'comparison'
    reasoning = 'Deine Daten enthalten Text-Paare, die sich ideal für paarweise Vergleiche eignen. Empfehlung: Comparison-Task für A/B-Bewertungen.'
  } else if (structure.detected_item_type === 'qa_pair') {
    taskType = 'rating'
    reasoning = 'Deine Daten enthalten Frage-Antwort-Paare. Empfehlung: Rating-Task um die Qualität der Antworten zu bewerten.'
  } else if (structure.detected_item_type === 'conversation') {
    taskType = 'mail_rating'
    reasoning = 'Deine Daten enthalten Konversationen. Empfehlung: Mail-Rating für die Bewertung der gesamten Gesprächsqualität.'
  } else if (structure.detected_item_type === 'single_text') {
    taskType = 'rating'
    reasoning = 'Deine Daten enthalten einzelne Texte. Empfehlung: Rating-Task für die Bewertung der Textqualität.'
  } else {
    taskType = suggestedType || 'rating'
    reasoning = 'Basierend auf der Datenstruktur empfehlen wir einen Rating-Task für flexible Bewertungen.'
  }

  taskType = normalizeTaskType(taskType)

  aiSuggestion.value = {
    taskType,
    reasoning,
    name: generateDefaultName(taskType),
    distributionMode: 'all',
    orderMode: 'shuffle_all'
  }
}

const normalizeTaskType = (taskType) => {
  if (taskType === 'classification') return 'labeling'
  if (taskType === 'text_classification') return 'labeling'
  if (taskType === 'text_rating') return 'rating'
  return taskType
}

const generateDefaultName = (taskType) => {
  const today = new Date()
  const dateStr = today.toISOString().split('T')[0]
  const normalizedType = normalizeTaskType(taskType)
  const typeNames = {
    rating: 'Rating',
    ranking: 'Ranking',
    mail_rating: 'Mail-Bewertung',
    comparison: 'Vergleich',
    authenticity: 'Authentizität',
    judge: 'LLM-Judge',
    labeling: 'Labeling'
  }
  return `${typeNames[normalizedType] || 'Evaluation'} ${dateStr}`
}

const applyAiSuggestion = () => {
  if (aiSuggestion.value) {
    localConfig.value.name = aiSuggestion.value.name
    localConfig.value.taskType = aiSuggestion.value.taskType
    localConfig.value.distributionMode = aiSuggestion.value.distributionMode
    localConfig.value.orderMode = aiSuggestion.value.orderMode
    aiSuggestionDismissed.value = true
  }
}

const generateAiName = async () => {
  aiGeneratingName.value = true
  try {
    // Call AI endpoint to generate name
    const response = await axios.post('/api/import/ai/suggest-name', {
      session_id: props.session?.session_id,
      task_type: localConfig.value.taskType,
      item_count: itemCount.value
    })
    if (response.data?.name) {
      localConfig.value.name = response.data.name
    }
  } catch (error) {
    // Fallback to default name generation
    localConfig.value.name = generateDefaultName(localConfig.value.taskType)
  } finally {
    aiGeneratingName.value = false
  }
}

// Load existing scenarios
const loadExistingScenarios = async () => {
  loadingScenarios.value = true
  try {
    const response = await axios.get('/api/scenarios')
    existingScenarios.value = response.data?.scenarios || response.data || []
  } catch (error) {
    console.error('Failed to load scenarios:', error)
    existingScenarios.value = []
  } finally {
    loadingScenarios.value = false
  }
}

onMounted(() => {
  loadExistingScenarios()
})

// Task type helpers
const taskTypes = computed(() => [
  { value: 'rating', name: t('dataImporter.stepScenario.taskTypes.rating'), icon: 'mdi-star', color: 'amber', description: t('dataImporter.stepScenario.taskTypes.ratingDesc') },
  { value: 'ranking', name: t('dataImporter.stepScenario.taskTypes.ranking'), icon: 'mdi-sort', color: 'blue', description: t('dataImporter.stepScenario.taskTypes.rankingDesc') },
  { value: 'mail_rating', name: t('dataImporter.stepScenario.taskTypes.mailRating'), icon: 'mdi-email-check', color: 'green', description: t('dataImporter.stepScenario.taskTypes.mailRatingDesc') },
  { value: 'comparison', name: t('dataImporter.stepScenario.taskTypes.comparison'), icon: 'mdi-compare', color: 'purple', description: t('dataImporter.stepScenario.taskTypes.comparisonDesc') },
  { value: 'authenticity', name: t('dataImporter.stepScenario.taskTypes.authenticity'), icon: 'mdi-shield-check', color: 'orange', description: t('dataImporter.stepScenario.taskTypes.authenticityDesc') },
  { value: 'judge', name: t('dataImporter.stepScenario.taskTypes.judge'), icon: 'mdi-sword-cross', color: 'teal', description: t('dataImporter.stepScenario.taskTypes.judgeDesc') },
  { value: 'labeling', name: t('dataImporter.stepScenario.taskTypes.labeling'), icon: 'mdi-label-multiple', color: 'indigo', description: t('dataImporter.stepScenario.taskTypes.labelingDesc') }
])

const getTaskTypeIcon = (type) => {
  const normalizedType = normalizeTaskType(type)
  return taskTypes.value.find(t => t.value === normalizedType)?.icon || 'mdi-help-circle'
}

const getTaskTypeColor = (type) => {
  const normalizedType = normalizeTaskType(type)
  return taskTypes.value.find(t => t.value === normalizedType)?.color || 'grey'
}

const getTaskTypeName = (type) => {
  const normalizedType = normalizeTaskType(type)
  return taskTypes.value.find(t => t.value === normalizedType)?.name || normalizedType
}

const distributionModes = computed(() => [
  { value: 'all', name: t('dataImporter.stepScenario.distribution.modes.all'), description: t('dataImporter.stepScenario.distribution.modes.allDesc') },
  { value: 'round_robin', name: t('dataImporter.stepScenario.distribution.modes.roundRobin'), description: t('dataImporter.stepScenario.distribution.modes.roundRobinDesc') }
])

const orderModes = computed(() => [
  { value: 'original', name: t('dataImporter.stepScenario.distribution.orderModes.original'), description: t('dataImporter.stepScenario.distribution.orderModes.originalDesc') },
  { value: 'shuffle_all', name: t('dataImporter.stepScenario.distribution.orderModes.shuffleAll'), description: t('dataImporter.stepScenario.distribution.orderModes.shuffleAllDesc') },
  { value: 'shuffle_per_user', name: t('dataImporter.stepScenario.distribution.orderModes.shufflePerUser'), description: t('dataImporter.stepScenario.distribution.orderModes.shufflePerUserDesc') }
])

const datePresets = computed(() => [
  { label: t('dataImporter.stepScenario.dates.presets.1week'), days: 7 },
  { label: t('dataImporter.stepScenario.dates.presets.2weeks'), days: 14 },
  { label: t('dataImporter.stepScenario.dates.presets.1month'), days: 30 },
  { label: t('dataImporter.stepScenario.dates.presets.3months'), days: 90 }
])

const applyDatePreset = (preset) => {
  const today = new Date()
  const endDate = new Date(today)
  endDate.setDate(endDate.getDate() + preset.days)

  localConfig.value.beginDate = today.toISOString().split('T')[0]
  localConfig.value.endDate = endDate.toISOString().split('T')[0]
}
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}
</style>
