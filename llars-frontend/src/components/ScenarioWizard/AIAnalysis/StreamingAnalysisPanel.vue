<template>
  <div class="streaming-analysis-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-left">
        <v-icon size="22" class="mr-2" color="#b0ca97">mdi-robot</v-icon>
        <span class="header-title">{{ $t('scenarioWizard.analysis.title') }}</span>
      </div>
      <div class="header-right">
        <v-chip
          v-if="isComplete"
          size="small"
          color="success"
          variant="tonal"
        >
          <v-icon start size="14">mdi-check</v-icon>
          {{ $t('scenarioWizard.analysis.complete') }}
        </v-chip>
        <v-chip
          v-else-if="isStreaming"
          size="small"
          color="primary"
          variant="tonal"
        >
          <v-progress-circular
            indeterminate
            size="12"
            width="2"
            class="mr-2"
          />
          {{ $t('scenarioWizard.analysis.analyzing') }}
        </v-chip>
      </div>
    </div>

    <!-- Analysis Cards Grid -->
    <div class="cards-grid">
      <!-- Row 1: Eval Type + Scenario Suggestion -->
      <div class="cards-row">
        <EvalTypeCard
          :eval-type="config.evalType"
          :confidence="parsed.evalTypeConfidence"
          :loading="fieldState.evalType === 'pending' && isStreaming"
          :streaming="fieldState.evalType === 'streaming'"
          :editable="isComplete"
          class="card-eval-type"
          @update:eval-type="updateConfig('evalType', $event)"
        />

        <ScenarioSuggestionCard
          :name="config.scenarioName"
          :description="config.scenarioDescription"
          :loading="fieldState.scenarioName === 'pending' && isStreaming"
          :streaming="isStreaming && !isComplete"
          :name-streaming="fieldState.scenarioName === 'streaming'"
          :description-streaming="fieldState.scenarioDescription === 'streaming'"
          :editable="isComplete"
          class="card-scenario"
          @update:name="updateConfig('scenarioName', $event)"
          @update:description="updateConfig('scenarioDescription', $event)"
          @regenerate="$emit('regenerate')"
        />
      </div>

      <!-- Row 2: Reasoning (full width) -->
      <ReasoningCard
        v-if="parsed.evalTypeReasoning || isStreaming"
        :reasoning="parsed.evalTypeReasoning"
        :loading="fieldState.evalTypeReasoning === 'pending' && isStreaming"
        :streaming="fieldState.evalTypeReasoning === 'streaming'"
        class="card-reasoning"
      />

      <!-- Config Generation Indicator (shows while config_suggestions is streaming) -->
      <div
        v-if="fieldState.configSuggestions === 'streaming' && isStreaming"
        class="config-generating"
      >
        <v-progress-circular
          indeterminate
          size="18"
          width="2"
          color="#b0ca97"
          class="mr-3"
        />
        <span>{{ $t('scenarioWizard.analysis.generatingConfig') }}</span>
      </div>

      <!-- Row 3: Data Stats + Quality + Recommendations -->
      <div class="cards-row cards-row--stats">
        <DataStatsCard
          :item-count="dataSummary.itemCount"
          :field-count="dataSummary.fieldsCount"
          :file-count="dataSummary.fileCount"
          :fields="dataSummary.fields"
          class="card-data"
        />

        <DataQualityCard
          :completeness="dataQuality?.completeness"
          :issues="dataQuality?.issues"
          :recommendations="dataQuality?.recommendations"
          :loading="fieldState.dataQuality === 'pending' && isStreaming"
          class="card-quality"
        />
      </div>
    </div>

    <!-- AI Chat Panel -->
    <AIChatPanel
      v-if="showChat"
      :data="analyzedData"
      :current-config="config"
      :initial-message="chatInitialMessage"
      @config-update="handleChatConfigUpdate"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import EvalTypeCard from './EvalTypeCard.vue'
import ScenarioSuggestionCard from './ScenarioSuggestionCard.vue'
import ReasoningCard from './ReasoningCard.vue'
import DataStatsCard from './DataStatsCard.vue'
import DataQualityCard from './DataQualityCard.vue'
import AIChatPanel from './AIChatPanel.vue'
import { useStreamingParser, FIELD_STATE } from './useStreamingParser'

const { t } = useI18n()

const props = defineProps({
  analyzedData: {
    type: Array,
    default: () => []
  },
  dataSummary: {
    type: Object,
    default: () => ({
      itemCount: 0,
      fieldsCount: 0,
      fileCount: 1,
      fields: []
    })
  },
  dataQuality: {
    type: Object,
    default: null
  },
  showChat: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:config', 'regenerate'])

// Use streaming parser
const {
  parsed,
  fieldState,
  isStreaming,
  isComplete,
  processChunk,
  processSuggestions,
  processDataQuality,
  finalize,
  setError,
  reset
} = useStreamingParser()

// Config state (editable)
const config = reactive({
  evalType: null,
  scenarioName: '',
  scenarioDescription: '',
  labels: [],
  scales: [],
  buckets: []
})

// Watch parsed values and sync to config
watch(() => parsed.evalType, (v) => {
  if (v && !config.evalType) config.evalType = v
})
watch(() => parsed.scenarioName, (v) => {
  if (v) config.scenarioName = v
})
watch(() => parsed.scenarioDescription, (v) => {
  if (v) config.scenarioDescription = v
})

// Computed
const chatInitialMessage = computed(() => {
  if (!isComplete.value) return null

  const evalType = config.evalType || 'rating'
  return t('scenarioWizard.chat.initialMessage', {
    evalType: t(`scenarioWizard.evalTypes.${evalType}`, evalType)
  })
})

// Methods
function updateConfig(field, value) {
  config[field] = value
  emit('update:config', { ...config })
}

function handleChatConfigUpdate({ field, value }) {
  console.log('Chat config update received:', { field, value })

  // Map backend field names to frontend field names
  const fieldMapping = {
    'task_type': 'evalType',
    'scenario_name': 'scenarioName',
    'scenario_description': 'scenarioDescription'
  }
  const mappedField = fieldMapping[field] || field

  config[mappedField] = value
  console.log('Emitting config update:', { ...config })
  emit('update:config', { ...config })
}

// Expose methods for parent to call
defineExpose({
  processChunk,
  processSuggestions,
  processDataQuality,
  finalize,
  setError,
  reset,
  config,
  isStreaming,
  isComplete
})
</script>

<style scoped>
.streaming-analysis-panel {
  background: rgba(var(--v-theme-on-surface), 0.01);
  border: 1px solid rgba(176, 202, 151, 0.2);
  border-radius: 20px 6px 20px 6px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: rgba(176, 202, 151, 0.06);
  border-bottom: 1px solid rgba(176, 202, 151, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #b0ca97;
}

/* Cards Grid */
.cards-grid {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cards-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 16px;
}

.cards-row--stats {
  grid-template-columns: 1fr 1fr;
}

/* Responsive */
@media (max-width: 900px) {
  .cards-row {
    grid-template-columns: 1fr;
  }

  .cards-row--stats {
    grid-template-columns: 1fr;
  }
}

/* Individual card classes - fixed heights for consistent layout */
.card-eval-type {
  height: 220px;
}

.card-scenario {
  height: 220px;
}

.card-reasoning {
  /* Full width by default, height controlled by component */
}

.card-data,
.card-quality {
  height: 200px;
}

/* Config Generating Indicator */
.config-generating {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 20px;
  background: rgba(176, 202, 151, 0.08);
  border: 1px dashed rgba(176, 202, 151, 0.3);
  border-radius: 12px 4px 12px 4px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 14px;
  animation: pulse-border 2s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { border-color: rgba(176, 202, 151, 0.3); }
  50% { border-color: rgba(176, 202, 151, 0.6); }
}
</style>
