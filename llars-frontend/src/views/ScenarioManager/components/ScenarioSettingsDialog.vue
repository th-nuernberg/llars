<template>
  <v-card class="settings-dialog">
    <v-card-title class="d-flex align-center">
      <LIcon color="primary" class="mr-2">mdi-cog-outline</LIcon>
      {{ $t('scenarioManager.settings.title') }}
      <v-spacer />
      <v-btn icon variant="text" @click="$emit('close')">
        <LIcon>mdi-close</LIcon>
      </v-btn>
    </v-card-title>

    <v-card-text>
      <v-form ref="form" v-model="formValid">
        <!-- Basic Info -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.basicInfo') }}</h4>

          <v-text-field
            v-model="formData.scenario_name"
            :label="$t('scenarioManager.settings.name')"
            :rules="[rules.required]"
            variant="outlined"
            class="mb-4"
          >
            <template #append-inner>
              <LAIFieldButton
                field-key="scenario.settings.name"
                :context="{
                  scenario_type: scenario.function_type,
                  existing_description: formData.description,
                  existing_name: formData.scenario_name
                }"
                icon-only
                size="small"
                @generated="formData.scenario_name = $event"
              />
            </template>
          </v-text-field>

          <div class="markdown-field">
            <div class="markdown-field__header">
              <span class="markdown-field__label">{{ $t('scenarioManager.settings.description') }}</span>
              <LAIFieldButton
                field-key="scenario.settings.description"
                :context="{
                  scenario_type: scenario.function_type,
                  scenario_name: formData.scenario_name,
                  existing_description: formData.description
                }"
                icon-only
                size="small"
                @generated="formData.description = $event"
              />
            </div>
            <LMarkdownEditor
              v-model="formData.description"
              :placeholder="$t('scenarioManager.settings.description')"
              :rows="8"
            />
          </div>
        </div>

        <!-- Evaluation Briefing -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('evaluation.briefing.title') }}</h4>

          <div class="markdown-field mb-4">
            <div class="markdown-field__label">{{ $t('evaluation.briefing.taskDescription') }}</div>
            <LMarkdownEditor
              :model-value="briefingTaskDescription"
              :placeholder="$t('evaluation.briefing.taskDescriptionPlaceholder')"
              :rows="6"
              @update:modelValue="updateBriefingTaskDescription"
            />
          </div>

          <div class="markdown-field">
            <div class="markdown-field__label">{{ $t('evaluation.briefing.criteria') }}</div>
            <LMarkdownEditor
              :model-value="briefingCriteria"
              :placeholder="briefingCriteriaPlaceholder"
              :rows="8"
              @update:modelValue="updateBriefingCriteria"
            />
          </div>
        </div>

        <!-- Time Period -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.timePeriod') }}</h4>

          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="formData.begin"
                :label="$t('scenarioManager.settings.startDate')"
                type="date"
                variant="outlined"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="formData.end"
                :label="$t('scenarioManager.settings.endDate')"
                type="date"
                variant="outlined"
              />
            </v-col>
          </v-row>
        </div>

        <!-- Distribution Settings -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.distribution') }}</h4>

          <v-radio-group v-model="formData.config.distribution_mode">
            <v-radio value="all">
              <template #label>
                <div class="radio-label">
                  <span class="radio-title">{{ $t('scenarioManager.settings.distributionAll') }}</span>
                  <span class="radio-desc">{{ $t('scenarioManager.settings.distributionAllDesc') }}</span>
                </div>
              </template>
            </v-radio>
            <v-radio value="random">
              <template #label>
                <div class="radio-label">
                  <span class="radio-title">{{ $t('scenarioManager.settings.distributionRandom') }}</span>
                  <span class="radio-desc">{{ $t('scenarioManager.settings.distributionRandomDesc') }}</span>
                </div>
              </template>
            </v-radio>
            <v-radio value="sequential">
              <template #label>
                <div class="radio-label">
                  <span class="radio-title">{{ $t('scenarioManager.settings.distributionSequential') }}</span>
                  <span class="radio-desc">{{ $t('scenarioManager.settings.distributionSequentialDesc') }}</span>
                </div>
              </template>
            </v-radio>
          </v-radio-group>
        </div>

        <!-- Order Settings -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.order') }}</h4>

          <v-radio-group v-model="formData.config.order_mode">
            <v-radio value="fixed" :label="$t('scenarioManager.settings.orderFixed')" />
            <v-radio value="random" :label="$t('scenarioManager.settings.orderRandom')" />
          </v-radio-group>
        </div>

        <!-- Visibility -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.visibility') }}</h4>

          <v-select
            v-model="formData.visibility"
            :items="visibilityOptions"
            item-title="label"
            item-value="value"
            variant="outlined"
          />
        </div>

        <!-- Status -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.status') }}</h4>

          <v-select
            v-model="formData.status"
            :items="statusOptions"
            item-title="label"
            item-value="value"
            variant="outlined"
          />
        </div>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <LBtn variant="text" color="error" @click="confirmDelete">
        <LIcon start>mdi-delete-outline</LIcon>
        {{ $t('scenarioManager.settings.delete') }}
      </LBtn>
      <v-spacer />
      <LBtn variant="text" @click="$emit('close')">
        {{ $t('common.cancel') }}
      </LBtn>
      <LBtn variant="primary" :loading="saving" :disabled="!formValid" @click="saveSettings">
        {{ $t('common.save') }}
      </LBtn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  criteriaListToMarkdown,
  getLocalizedText,
  setLocalizedText
} from '@/utils/scenarioBriefing'
import { useScenarioManager } from '../composables/useScenarioManager'

const props = defineProps({
  scenario: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'saved'])

const { t, locale } = useI18n()
const { updateScenario } = useScenarioManager()

// State
const form = ref(null)
const formValid = ref(true)
const saving = ref(false)

const formData = ref({
  scenario_name: '',
  description: '',
  begin: null,
  end: null,
  status: 'draft',
  visibility: 'private',
  config: {
    distribution_mode: 'all',
    order_mode: 'random'
  }
})

// Options
const visibilityOptions = computed(() => [
  { value: 'private', label: t('scenarioManager.settings.visibilityPrivate') },
  { value: 'team', label: t('scenarioManager.settings.visibilityTeam') },
  { value: 'public', label: t('scenarioManager.settings.visibilityPublic') }
])

const statusOptions = computed(() => [
  { value: 'draft', label: t('scenarioManager.status.draft') },
  { value: 'data_collection', label: t('scenarioManager.status.dataCollection') },
  { value: 'evaluating', label: t('scenarioManager.status.evaluating') },
  { value: 'completed', label: t('scenarioManager.status.completed') },
  { value: 'archived', label: t('scenarioManager.status.archived') }
])

const isComparisonScenario = computed(() => {
  const typeId = Number(props.scenario?.function_type_id)
  const typeName = String(
    props.scenario?.function_type_name ||
    props.scenario?.function_type ||
    ''
  ).toLowerCase()

  return typeId === 4 || typeName === 'comparison'
})

const briefingEvalConfig = computed(() => {
  const evalConfig = formData.value.config?.eval_config
  if (!evalConfig || typeof evalConfig !== 'object') return null
  return evalConfig.config && typeof evalConfig.config === 'object' ? evalConfig.config : null
})

const briefingTaskDescription = computed(() => {
  return (
    getLocalizedText(briefingEvalConfig.value?.taskDescriptionMarkdown, locale.value) ||
    getLocalizedText(briefingEvalConfig.value?.question, locale.value)
  )
})

const briefingCriteria = computed(() => {
  return getLocalizedText(briefingEvalConfig.value?.criteriaMarkdown, locale.value)
})

const briefingCriteriaPlaceholder = computed(() => [
  locale.value === 'en' ? '## What should be evaluated?' : '## Worauf sollte geachtet werden?',
  locale.value === 'en' ? '- Argumentation and traceability' : '- Argumentation und Nachvollziehbarkeit',
  locale.value === 'en' ? '- Factual accuracy' : '- Fachliche Genauigkeit',
  locale.value === 'en' ? '- Style and clarity' : '- Stil und Klarheit'
].join('\n'))

// Validation rules
const rules = {
  required: v => !!v || t('validation.required')
}

// Methods
async function saveSettings() {
  if (!form.value?.validate()) return

  saving.value = true
  try {
    const configJson = {
      ...formData.value.config,
      description: formData.value.description,
      distribution_mode: formData.value.config.distribution_mode || 'all',
      order_mode: formData.value.config.order_mode || 'random'
    }

    await updateScenario(props.scenario.id, {
      scenario_name: formData.value.scenario_name,
      description: formData.value.description,
      begin: formData.value.begin,
      end: formData.value.end,
      status: formData.value.status,
      visibility: formData.value.visibility,
      config_json: configJson
    })
    emit('saved')
  } finally {
    saving.value = false
  }
}

function ensureBriefingFields() {
  if (!formData.value.config || typeof formData.value.config !== 'object') {
    formData.value.config = {}
  }

  if (!formData.value.config.eval_config || typeof formData.value.config.eval_config !== 'object') {
    formData.value.config.eval_config = { config: {} }
  }
  if (!formData.value.config.eval_config.config || typeof formData.value.config.eval_config.config !== 'object') {
    formData.value.config.eval_config.config = {}
  }

  const config = formData.value.config.eval_config.config

  if (!config.taskDescriptionMarkdown) {
    config.taskDescriptionMarkdown = isComparisonScenario.value
      ? setLocalizedText(config.question, getLocalizedText(config.question, locale.value), locale.value)
      : { de: '', en: '' }
  }

  if (!config.question && formData.value.config.question) {
    config.question = JSON.parse(JSON.stringify(formData.value.config.question))
  }

  if (isComparisonScenario.value && !config.question) {
    config.question = {
      de: 'Welche Option ist besser?',
      en: 'Which option is better?'
    }
  }

  if (!config.criteriaMarkdown) {
    config.criteriaMarkdown = {
      de: getLocalizedText(formData.value.config.criteriaMarkdown, 'de') || criteriaListToMarkdown(config.criteria, 'de'),
      en: getLocalizedText(formData.value.config.criteriaMarkdown, 'en') || criteriaListToMarkdown(config.criteria, 'en')
    }
  }
}

function updateBriefingTaskDescription(value) {
  ensureBriefingFields()
  if (!briefingEvalConfig.value) return

  briefingEvalConfig.value.taskDescriptionMarkdown = setLocalizedText(
    briefingEvalConfig.value.taskDescriptionMarkdown,
    value,
    locale.value
  )

  if (isComparisonScenario.value) {
    briefingEvalConfig.value.question = setLocalizedText(
      briefingEvalConfig.value.question,
      value,
      locale.value
    )
  }
}

function updateBriefingCriteria(value) {
  ensureBriefingFields()
  if (!briefingEvalConfig.value) return

  briefingEvalConfig.value.criteriaMarkdown = setLocalizedText(
    briefingEvalConfig.value.criteriaMarkdown,
    value,
    locale.value
  )
}

function confirmDelete() {
  // TODO: Show delete confirmation dialog
  console.log('Delete scenario')
}

onMounted(() => {
  // Initialize form with scenario data
  if (props.scenario) {
    const initialConfig = {
      ...JSON.parse(JSON.stringify(props.scenario.config_json || {})),
      distribution_mode: props.scenario.config_json?.distribution_mode || 'all',
      order_mode: props.scenario.config_json?.order_mode || 'random'
    }

    if (!initialConfig.description && props.scenario.description) {
      initialConfig.description = props.scenario.description
    }

    formData.value = {
      scenario_name: props.scenario.scenario_name || '',
      description: initialConfig.description || '',
      begin: props.scenario.begin?.split('T')[0] || null,
      end: props.scenario.end?.split('T')[0] || null,
      status: props.scenario.status || 'draft',
      visibility: props.scenario.visibility || 'private',
      config: initialConfig
    }

    ensureBriefingFields()
  }
})
</script>

<style scoped>
.settings-dialog {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.settings-dialog .v-card-text {
  overflow-y: auto;
}

.settings-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.settings-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 16px;
}

.markdown-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.markdown-field__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.markdown-field__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.radio-label {
  display: flex;
  flex-direction: column;
}

.radio-title {
  font-weight: 500;
}

.radio-desc {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
</style>
