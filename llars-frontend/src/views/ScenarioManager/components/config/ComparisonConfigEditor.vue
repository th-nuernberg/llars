<template>
  <div class="comparison-config">
    <!-- Comparison Type -->
    <v-select
      v-model="localConfig.type"
      :items="comparisonTypes"
      :label="$t('scenarioManager.evalConfig.comparison.comparisonType')"
      variant="outlined"
      density="compact"
      class="mb-3"
      @update:modelValue="emitUpdate"
    />

    <!-- Test Instruction -->
    <div class="editor-section mb-4">
      <h5 class="subsection-title mb-2">{{ $t('evaluation.briefing.taskDescription') }}</h5>
      <LMarkdownEditor
        :model-value="getTaskDescription(localConfig.taskDescriptionMarkdown, localConfig.question)"
        :placeholder="$t('evaluation.briefing.taskDescriptionPlaceholder')"
        :rows="6"
        @update:modelValue="updateTaskDescription"
      />
    </div>

    <!-- Options -->
    <div class="config-options mb-4">
      <LSwitch
        v-model="localConfig.allowTie"
        :label="$t('scenarioManager.evalConfig.comparison.allowTie')"
        @update:modelValue="emitUpdate"
      />
      <LSwitch
        v-model="localConfig.showConfidence"
        :label="$t('scenarioManager.evalConfig.comparison.showConfidence')"
        @update:modelValue="emitUpdate"
      />
    </div>

    <!-- Items per comparison -->
    <v-text-field
      v-model.number="localConfig.itemsPerComparison"
      :label="$t('scenarioManager.evalConfig.comparison.itemsPerComparison')"
      type="number"
      variant="outlined"
      density="compact"
      :min="2"
      :max="5"
      class="mb-3"
      @update:modelValue="emitUpdate"
    />

    <!-- Confidence Scale (when enabled) -->
    <div v-if="localConfig.showConfidence" class="confidence-section mb-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.comparison.confidenceScale') }}</h5>
      <v-row>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.confidenceScale.min"
            :label="$t('scenarioManager.evalConfig.comparison.confidenceMin')"
            type="number"
            variant="outlined"
            density="compact"
            @update:modelValue="emitUpdate"
          />
        </v-col>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.confidenceScale.max"
            :label="$t('scenarioManager.evalConfig.comparison.confidenceMax')"
            type="number"
            variant="outlined"
            density="compact"
            @update:modelValue="emitUpdate"
          />
        </v-col>
      </v-row>
    </div>

    <!-- Criteria Editor -->
    <div class="criteria-section">
      <h5 class="subsection-title mb-2">{{ $t('evaluation.briefing.criteria') }}</h5>
      <LMarkdownEditor
        :model-value="getCriteriaMarkdown(localConfig.criteriaMarkdown)"
        :placeholder="criteriaPlaceholder"
        :rows="8"
        @update:modelValue="updateCriteriaMarkdown"
      />

    </div>

    <!-- Tournament Options (when tournament type) -->
    <div v-if="localConfig.type === 'tournament'" class="tournament-section mt-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.comparison.tournamentOptions') }}</h5>
      <v-select
        v-model="localConfig.rounds"
        :items="roundOptions"
        :label="$t('scenarioManager.evalConfig.comparison.rounds')"
        variant="outlined"
        density="compact"
        @update:modelValue="emitUpdate"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  criteriaListToMarkdown,
  getLocalizedText,
  setLocalizedText
} from '@/utils/scenarioBriefing'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])
const { t, locale } = useI18n()

const comparisonTypes = computed(() => [
  { title: t('scenarioManager.evalConfig.comparison.typeOptions.pairwise'), value: 'pairwise' },
  { title: t('scenarioManager.evalConfig.comparison.typeOptions.tournament'), value: 'tournament' }
])

const roundOptions = computed(() => [
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.auto'), value: 'auto' },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round1'), value: 1 },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round2'), value: 2 },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round3'), value: 3 }
])

const criteriaPlaceholder = computed(() => [
  locale.value === 'en' ? '## What should be evaluated?' : '## Worauf sollte geachtet werden?',
  locale.value === 'en' ? '- Argumentation and traceability' : '- Argumentation und Nachvollziehbarkeit',
  locale.value === 'en' ? '- Factual accuracy' : '- Fachliche Genauigkeit',
  locale.value === 'en' ? '- Style and clarity' : '- Stil und Klarheit'
].join('\n'))

const localConfig = ref({
  type: 'pairwise',
  question: { de: 'Welche Option ist besser?', en: 'Which option is better?' },
  taskDescriptionMarkdown: { de: '', en: '' },
  criteriaMarkdown: { de: '', en: '' },
  itemsPerComparison: 2,
  allowTie: true,
  showConfidence: false,
  confidenceScale: { min: 1, max: 5 },
  criteria: [],
  rounds: 'auto'
})

function getTaskDescription(taskDescriptionMarkdown, question) {
  return getLocalizedText(taskDescriptionMarkdown, locale.value) || getLocalizedText(question, locale.value)
}

function getCriteriaMarkdown(criteriaMarkdown) {
  return getLocalizedText(criteriaMarkdown, locale.value)
}

function updateTaskDescription(value) {
  localConfig.value.taskDescriptionMarkdown = setLocalizedText(
    localConfig.value.taskDescriptionMarkdown,
    value,
    locale.value
  )
  localConfig.value.question = setLocalizedText(localConfig.value.question, value, locale.value)
  emitUpdate()
}

function updateCriteriaMarkdown(value) {
  localConfig.value.criteriaMarkdown = setLocalizedText(
    localConfig.value.criteriaMarkdown,
    value,
    locale.value
  )
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', { ...localConfig.value })
}

function initFromProps() {
  if (props.modelValue) {
    localConfig.value = {
      ...localConfig.value,
      ...props.modelValue,
      taskDescriptionMarkdown: props.modelValue.taskDescriptionMarkdown || {
        de: getLocalizedText(props.modelValue.question, 'de'),
        en: getLocalizedText(props.modelValue.question, 'en')
      },
      criteriaMarkdown: props.modelValue.criteriaMarkdown || {
        de: criteriaListToMarkdown(props.modelValue.criteria, 'de'),
        en: criteriaListToMarkdown(props.modelValue.criteria, 'en')
      },
      criteria: props.modelValue.criteria ? [...props.modelValue.criteria] : [],
      confidenceScale: props.modelValue.confidenceScale || { min: 1, max: 5 }
    }
  }
}

watch(() => props.modelValue, initFromProps, { deep: true })

onMounted(initFromProps)
</script>

<style scoped>
.comparison-config {
  padding: 8px 0;
}

.subsection-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin: 0;
}

.config-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.editor-section,
.confidence-section,
.criteria-section,
.tournament-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}
</style>
