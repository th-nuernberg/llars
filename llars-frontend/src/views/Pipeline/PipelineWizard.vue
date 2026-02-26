<template>
  <div class="pipeline-wizard">
    <!-- Header -->
    <div class="wizard-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goBack">
        {{ $t('pipeline.backToHub') }}
      </LBtn>
      <div class="header-info">
        <h1 class="header-title">{{ $t('pipeline.wizard.title') }}</h1>
        <p class="header-subtitle">{{ $t('pipeline.wizard.subtitle') }}</p>
      </div>
    </div>

    <!-- Stepper -->
    <div class="wizard-content">
      <v-stepper v-model="currentStep" flat>
        <v-stepper-header>
          <v-stepper-item :value="1" :title="$t('pipeline.wizard.step1')" />
          <v-divider />
          <v-stepper-item :value="2" :title="$t('pipeline.wizard.step2')" />
          <v-divider />
          <v-stepper-item :value="3" :title="$t('pipeline.wizard.step3')" />
        </v-stepper-header>

        <v-stepper-window>
          <!-- Step 1: Basic Config -->
          <v-stepper-window-item :value="1">
            <div class="step-content">
              <v-text-field
                v-model="form.name"
                :label="$t('pipeline.wizard.name')"
                :rules="[v => !!v || $t('pipeline.wizard.nameRequired')]"
                variant="outlined"
                density="comfortable"
              />

              <v-textarea
                v-model="form.description"
                :label="$t('pipeline.wizard.description')"
                variant="outlined"
                density="comfortable"
                rows="2"
                auto-grow
              />

              <v-textarea
                v-model="form.taskSpec"
                :label="$t('pipeline.wizard.taskSpec')"
                :hint="$t('pipeline.wizard.taskSpecHint')"
                persistent-hint
                variant="outlined"
                density="comfortable"
                rows="4"
                auto-grow
              />

              <v-select
                v-model="form.scenarioType"
                :items="scenarioTypeOptions"
                :label="$t('pipeline.wizard.scenarioType')"
                variant="outlined"
                density="comfortable"
              />

              <v-select
                v-model="form.evaluationType"
                :items="evaluationTypeOptions"
                :label="$t('pipeline.wizard.evaluationType')"
                variant="outlined"
                density="comfortable"
              />
            </div>
          </v-stepper-window-item>

          <!-- Step 2: Models & Data -->
          <v-stepper-window-item :value="2">
            <div class="step-content">
              <LlmModelSelect
                v-model="form.candidateModels"
                :label="$t('pipeline.wizard.candidateModels')"
                multiple
              />

              <LlmModelSelect
                v-model="form.evalModel"
                :label="$t('pipeline.wizard.evalModel')"
                :hint="$t('pipeline.wizard.evalModelHint')"
                persistent-hint
              />

              <LlmModelSelect
                v-model="form.metaModel"
                :label="$t('pipeline.wizard.metaModel')"
                :hint="$t('pipeline.wizard.metaModelHint')"
                persistent-hint
              />

              <v-text-field
                v-if="form.scenarioType === 'migration'"
                v-model="form.referenceModelId"
                :label="$t('pipeline.wizard.referenceModel')"
                variant="outlined"
                density="comfortable"
              />
            </div>
          </v-stepper-window-item>

          <!-- Step 3: Limits & Thresholds -->
          <v-stepper-window-item :value="3">
            <div class="step-content">
              <v-text-field
                v-model.number="form.maxIterations"
                :label="$t('pipeline.wizard.maxIterations')"
                type="number"
                :min="1"
                :max="50"
                variant="outlined"
                density="comfortable"
              />

              <v-text-field
                v-model.number="form.budgetTokens"
                :label="$t('pipeline.wizard.budgetTokens')"
                type="number"
                :min="10000"
                variant="outlined"
                density="comfortable"
                :suffix="$t('pipeline.wizard.tokens')"
              />

              <v-text-field
                v-model.number="form.globalThreshold"
                :label="$t('pipeline.wizard.globalThreshold')"
                type="number"
                :min="1"
                :max="5"
                :step="0.1"
                variant="outlined"
                density="comfortable"
              />

              <v-text-field
                v-model.number="form.numPromptVariants"
                :label="$t('pipeline.wizard.numVariants')"
                type="number"
                :min="1"
                :max="10"
                variant="outlined"
                density="comfortable"
              />

              <v-checkbox
                v-model="form.autoStart"
                :label="$t('pipeline.wizard.autoStart')"
                color="primary"
                density="comfortable"
              />

              <!-- Summary -->
              <div class="summary-card">
                <h4>{{ $t('pipeline.wizard.summary') }}</h4>
                <div class="summary-row">
                  <span>{{ $t('pipeline.wizard.name') }}:</span>
                  <strong>{{ form.name || '—' }}</strong>
                </div>
                <div class="summary-row">
                  <span>{{ $t('pipeline.models') }}:</span>
                  <strong>{{ form.candidateModels.length }} {{ $t('pipeline.wizard.selected') }}</strong>
                </div>
                <div class="summary-row">
                  <span>{{ $t('pipeline.wizard.maxIterations') }}:</span>
                  <strong>{{ form.maxIterations }}</strong>
                </div>
                <div class="summary-row">
                  <span>{{ $t('pipeline.budget') }}:</span>
                  <strong>{{ (form.budgetTokens / 1000).toFixed(0) }}k {{ $t('pipeline.wizard.tokens') }}</strong>
                </div>
              </div>
            </div>
          </v-stepper-window-item>
        </v-stepper-window>

        <!-- Navigation -->
        <div class="wizard-nav">
          <LBtn
            v-if="currentStep > 1"
            variant="tonal"
            @click="currentStep--"
          >
            {{ $t('common.back') }}
          </LBtn>
          <v-spacer />
          <LBtn
            v-if="currentStep < 3"
            variant="primary"
            :disabled="!canProceed"
            @click="currentStep++"
          >
            {{ $t('common.next') }}
          </LBtn>
          <LBtn
            v-else
            variant="primary"
            :loading="isCreating"
            :disabled="!canCreate"
            @click="handleCreate"
          >
            <v-icon start size="18">mdi-rocket-launch</v-icon>
            {{ form.autoStart ? $t('pipeline.wizard.createAndStart') : $t('pipeline.wizard.create') }}
          </LBtn>
        </div>
      </v-stepper>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePipeline } from './composables/usePipeline'
import LBtn from '@/components/common/LBtn.vue'
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'

const router = useRouter()
const { t } = useI18n()
const { createRun } = usePipeline()

const currentStep = ref(1)
const isCreating = ref(false)

const form = ref({
  name: '',
  description: '',
  taskSpec: '',
  scenarioType: 'greenfield',
  evaluationType: 'rating',
  candidateModels: [],
  evalModel: null,
  metaModel: null,
  referenceModelId: null,
  maxIterations: 10,
  budgetTokens: 500000,
  globalThreshold: 4.0,
  numPromptVariants: 3,
  autoStart: true,
})

const scenarioTypeOptions = computed(() => [
  { title: t('pipeline.wizard.greenfield'), value: 'greenfield' },
  { title: t('pipeline.wizard.migration'), value: 'migration' },
])

const evaluationTypeOptions = computed(() => [
  { title: t('pipeline.wizard.evalTypeRating'), value: 'rating' },
  { title: t('pipeline.wizard.evalTypeRanking'), value: 'ranking' },
  { title: t('pipeline.wizard.evalTypeComparison'), value: 'comparison' },
])

const canProceed = computed(() => {
  if (currentStep.value === 1) {
    return !!form.value.name && !!form.value.taskSpec
  }
  if (currentStep.value === 2) {
    return form.value.candidateModels.length > 0
  }
  return true
})

const canCreate = computed(() => {
  return !!form.value.name
    && !!form.value.taskSpec
    && form.value.candidateModels.length > 0
    && form.value.maxIterations > 0
    && form.value.budgetTokens > 0
})

function goBack() {
  router.push({ name: 'PipelineHub' })
}

async function handleCreate() {
  isCreating.value = true
  try {
    const run = await createRun({
      name: form.value.name,
      description: form.value.description,
      candidate_models: form.value.candidateModels,
      scenario_type: form.value.scenarioType,
      reference_model_id: form.value.referenceModelId,
      max_iterations: form.value.maxIterations,
      budget_tokens_total: form.value.budgetTokens,
      auto_start: form.value.autoStart,
      config: {
        task_spec: form.value.taskSpec,
        evaluation_type: form.value.evaluationType,
        eval_model_id: form.value.evalModel,
        meta_model_id: form.value.metaModel,
        num_prompt_variants: form.value.numPromptVariants,
        thresholds: {
          global_threshold: form.value.globalThreshold,
        },
        generation_params: {
          temperature: 0.7,
          max_tokens: null,
        },
      },
    })

    if (run) {
      router.push({ name: 'PipelineSession', params: { runId: run.id } })
    }
  } finally {
    isCreating.value = false
  }
}
</script>

<style scoped>
.pipeline-wizard {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.wizard-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.header-info {
  flex: 1;
}

.header-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.header-subtitle {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
}

.wizard-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 0;
}

.wizard-nav {
  display: flex;
  align-items: center;
  padding: 16px 0;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.summary-card {
  padding: 16px;
  background: rgba(var(--v-theme-primary), 0.04);
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  border-radius: 12px 3px 12px 3px;
}

.summary-card h4 {
  margin: 0 0 12px 0;
  font-size: 0.9rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  padding: 4px 0;
}

.summary-row span {
  color: rgba(var(--v-theme-on-surface), 0.6);
}
</style>
