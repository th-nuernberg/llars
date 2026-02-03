<template>
  <div class="wizard-host">
    <v-card class="wizard-card" variant="outlined">
      <!-- Header -->
      <v-card-title class="d-flex align-center pa-4">
        <LIcon class="mr-2" color="primary">llars:evaluation-assistant</LIcon>
        <div>
          <div class="text-h6">{{ $t('dataImporter.title') }}</div>
          <div class="text-caption text-medium-emphasis">
            {{ $t('dataImporter.wizard.subtitle') }}
          </div>
        </div>
        <v-spacer />

        <!-- Processing Indicator -->
        <template v-if="isProcessing">
          <div class="d-flex align-center mr-3">
            <v-progress-circular
              indeterminate
              size="18"
              width="2"
              color="primary"
              class="mr-2"
            />
            <span class="text-caption text-medium-emphasis">
              {{ statusText }}
            </span>
          </div>
        </template>

        <LBtn
          variant="text"
          size="small"
          prepend-icon="mdi-close"
          @click="handleClose"
        >
          {{ $t('dataImporter.wizard.close') }}
        </LBtn>
      </v-card-title>

      <v-divider />

      <!-- Custom Stepper Header -->
      <div class="wizard-steps pa-4">
        <div class="d-flex justify-space-between align-center">
          <template v-for="(step, index) in steps" :key="step.value">
            <div
              class="step-item text-center"
              :class="{
                'step-active': currentStep === step.value,
                'step-complete': currentStep > step.value,
                'step-clickable': canNavigateToStep(step.value),
                'step-disabled': !canNavigateToStep(step.value)
              }"
              @click="navigateToStep(step.value)"
            >
              <div class="step-circle mx-auto mb-1">
                <LIcon v-if="currentStep > step.value" size="small" color="white">
                  mdi-check
                </LIcon>
                <LIcon v-else size="small" :color="currentStep === step.value ? 'white' : 'grey'">
                  {{ step.icon }}
                </LIcon>
              </div>
              <div class="step-title text-caption">{{ step.title }}</div>
            </div>

            <!-- Connector Line -->
            <div
              v-if="index < steps.length - 1"
              class="step-connector flex-grow-1 mx-2"
              :class="{ 'step-connector-complete': currentStep > step.value }"
            />
          </template>
        </div>
      </div>

      <v-divider />

      <!-- Step Content -->
      <v-card-text class="step-content pa-0">
        <!-- Step 1: Upload -->
        <StepUpload
          v-if="currentStep === 1"
          v-model:session="session"
          v-model:sessions="sessions"
          :loading="loading"
          :error="error"
          @uploaded="handleFilesUploaded"
        />

        <!-- Step 2: Describe (NEW - Intent + Data Preview) -->
        <StepDescribe
          v-else-if="currentStep === 2"
          :session="session"
          :sessions="sessions"
          :loading="loading"
          @analyzed="handleIntentAnalyzed"
        />

        <!-- Step 3: Review & Configure -->
        <StepReviewNew
          v-else-if="currentStep === 3"
          v-model:scenario-config="scenarioConfig"
          v-model:user-config="userConfig"
          :session="session"
          :sessions="sessions"
          :analysis-result="analysisResult"
          :loading="loading"
          :error="error"
        />

        <!-- Step 4: User Invitation -->
        <StepUsers
          v-else-if="currentStep === 4"
          v-model:user-config="userConfig"
          :session="session"
          :scenario-config="scenarioConfig"
          :loading="loading"
        />

        <!-- Step 5: Execute Import -->
        <div v-else-if="currentStep === 5" class="step-execute pa-6">
          <div class="execute-summary">
            <LIcon size="64" color="primary" class="mb-4">mdi-rocket-launch</LIcon>
            <h2 class="text-h5 mb-2">{{ $t('dataImporter.wizard.execute.ready') }}</h2>
            <p class="text-body-1 text-medium-emphasis mb-6">
              {{ $t('dataImporter.wizard.execute.filesWillBeImported', { count: sessions.length, name: scenarioConfig.name }) }}
            </p>

            <div class="summary-cards">
              <div class="summary-card">
                <div class="summary-value">{{ sessions.length }}</div>
                <div class="summary-label">{{ $t('dataImporter.wizard.execute.files') }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-value">{{ totalItemCount.toLocaleString() }}</div>
                <div class="summary-label">{{ $t('dataImporter.wizard.execute.entries') }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-value">{{ getTaskTypeLabel(scenarioConfig.taskType) }}</div>
                <div class="summary-label">{{ $t('dataImporter.wizard.execute.taskType') }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-value">{{ totalUsersCount }}</div>
                <div class="summary-label">{{ $t('dataImporter.wizard.execute.users') }}</div>
              </div>
            </div>

            <LBtn
              variant="primary"
              size="x-large"
              prepend-icon="mdi-play"
              :loading="importing"
              :disabled="importing"
              class="mt-6"
              @click="handleExecuteImport"
            >
              {{ $t('dataImporter.wizard.execute.startImport') }}
            </LBtn>

            <!-- Import Progress -->
            <div v-if="importing" class="import-progress mt-6">
              <v-progress-linear
                :model-value="importProgress"
                color="primary"
                height="8"
                rounded
              />
              <div class="text-caption text-medium-emphasis mt-2">
                {{ importStatus }}
              </div>
            </div>

            <!-- Import Complete -->
            <v-alert
              v-if="importComplete"
              type="success"
              variant="tonal"
              class="mt-6"
            >
              <div class="text-body-1 font-weight-medium">
                {{ $t('dataImporter.wizard.execute.successMessage', { count: importResult?.imported_count || 0 }) }}
              </div>
            </v-alert>
          </div>
        </div>
      </v-card-text>

      <v-divider />

      <!-- Footer Navigation -->
      <v-card-actions class="pa-4">
        <LBtn
          v-if="currentStep > 1 && !importComplete"
          variant="text"
          prepend-icon="mdi-arrow-left"
          :disabled="loading || importing"
          @click="previousStep"
        >
          {{ $t('dataImporter.wizard.back') }}
        </LBtn>

        <v-spacer />

        <LBtn
          v-if="currentStep < 5 && !importComplete"
          variant="primary"
          append-icon="mdi-arrow-right"
          :disabled="!canProceed || loading"
          :loading="loading"
          @click="nextStep"
        >
          {{ nextButtonText }}
        </LBtn>

        <LBtn
          v-if="importComplete"
          variant="primary"
          prepend-icon="mdi-check"
          @click="handleComplete"
        >
          {{ $t('dataImporter.wizard.done') }}
        </LBtn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSnackbar } from '@/composables/useSnackbar'

const { t } = useI18n()

import StepUpload from './steps/StepUpload.vue'
import StepDescribe from './steps/StepDescribe.vue'
import StepReviewNew from './steps/StepReviewNew.vue'
import StepUsers from './steps/StepUsers.vue'

import { useImportWizard } from './composables/useImportWizard'

const emit = defineEmits(['close', 'complete'])
const router = useRouter()
const { showSuccess, showError } = useSnackbar()

// Wizard state
const {
  session,
  loading,
  error,
  isProcessing,
  statusText,
  executeImport,
  resetSession
} = useImportWizard()

const currentStep = ref(1)
const sessions = ref([])
const analysisResult = ref(null)
const importing = ref(false)
const importProgress = ref(0)
const importStatus = ref('')
const importComplete = ref(false)
const importResult = ref(null)

// Scenario & User config
const scenarioConfig = ref({
  name: '',
  taskType: 'mail_rating',
  beginDate: new Date().toISOString().split('T')[0],
  endDate: '',
  distributionMode: 'all',
  orderMode: 'original'
})

const userConfig = ref({
  raters: [],
  evaluators: []
})

// Step definitions (5 steps with user invitation)
const steps = computed(() => [
  { value: 1, title: t('dataImporter.wizard.steps.upload'), icon: 'mdi-upload' },
  { value: 2, title: t('dataImporter.wizard.steps.describe'), icon: 'mdi-chat-question' },
  { value: 3, title: t('dataImporter.wizard.steps.configure'), icon: 'mdi-cog' },
  { value: 4, title: t('dataImporter.wizard.steps.users'), icon: 'mdi-account-group' },
  { value: 5, title: t('dataImporter.wizard.steps.import'), icon: 'mdi-rocket-launch' }
])

const taskTypeLabels = computed(() => ({
  rating: t('dataImporter.wizard.taskTypes.rating'),
  ranking: t('dataImporter.wizard.taskTypes.ranking'),
  comparison: t('dataImporter.wizard.taskTypes.comparison'),
  mail_rating: t('dataImporter.wizard.taskTypes.mail_rating'),
  authenticity: t('dataImporter.wizard.taskTypes.authenticity'),
  labeling: t('dataImporter.wizard.taskTypes.labeling'),
  classification: t('dataImporter.wizard.taskTypes.labeling'),
  text_classification: t('dataImporter.wizard.taskTypes.labeling')
}))

const normalizeTaskType = (taskType) => {
  if (!taskType) return taskType
  if (taskType === 'classification' || taskType === 'text_classification') return 'labeling'
  if (taskType === 'text_rating') return 'rating'
  return taskType
}

// Computed
const totalItemCount = computed(() => {
  return sessions.value.reduce((sum, s) => sum + (s.item_count || s.structure?.item_count || 0), 0)
})

const totalUsersCount = computed(() => {
  return (userConfig.value.raters?.length || 0) + (userConfig.value.evaluators?.length || 0)
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1:
      return sessions.value.length > 0
    case 2:
      return analysisResult.value != null
    case 3:
      return scenarioConfig.value.name?.trim().length > 0
    case 4:
      // Users step - always allow proceeding (optional)
      return true
    case 5:
      return true
    default:
      return false
  }
})

const nextButtonText = computed(() => {
  switch (currentStep.value) {
    case 1:
      return t('dataImporter.wizard.nextButtons.continue')
    case 2:
      return t('dataImporter.wizard.nextButtons.configure')
    case 3:
      return t('dataImporter.wizard.nextButtons.inviteUsers')
    case 4:
      return t('dataImporter.wizard.nextButtons.prepareImport')
    default:
      return t('dataImporter.wizard.nextButtons.continue')
  }
})

// Navigation
const canNavigateToStep = (step) => {
  if (step <= currentStep.value) return true
  if (step === currentStep.value + 1 && canProceed.value) return true
  return false
}

const navigateToStep = (step) => {
  if (canNavigateToStep(step) && !importing.value) {
    currentStep.value = step
  }
}

const nextStep = () => {
  if (currentStep.value < 5 && canProceed.value) {
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// Helper
function getTaskTypeLabel(type) {
  return taskTypeLabels.value[type] || type
}

// Event handlers
const handleFilesUploaded = (uploadedSessions) => {
  const resultArray = Array.isArray(uploadedSessions) ? uploadedSessions : [uploadedSessions]
  sessions.value = resultArray

  if (resultArray.length > 0) {
    const firstResult = resultArray[0]

    // Auto-suggest scenario name
    if (!scenarioConfig.value.name) {
      if (resultArray.length === 1 && firstResult.filename) {
        scenarioConfig.value.name = firstResult.filename.replace(/\.[^/.]+$/, '')
      } else {
        scenarioConfig.value.name = t('dataImporter.wizard.autoName', { count: resultArray.length })
      }
    }

    // Move to describe step
    currentStep.value = 2
  }
}

const handleIntentAnalyzed = (result) => {
  const normalizedTaskType = normalizeTaskType(result?.task_type)
  analysisResult.value = { ...result, task_type: normalizedTaskType }

  // Apply analyzed settings
  if (normalizedTaskType) {
    scenarioConfig.value.taskType = normalizedTaskType
  }

  // Store evaluation criteria for later use
  if (result.evaluation_criteria?.length) {
    scenarioConfig.value.evaluationCriteria = result.evaluation_criteria
  }
}

const handleExecuteImport = async () => {
  importing.value = true
  importProgress.value = 0
  importStatus.value = t('dataImporter.wizard.execute.preparing')

  try {
    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      if (importProgress.value < 90) {
        importProgress.value += 10
      }
    }, 500)

    importStatus.value = t('dataImporter.wizard.execute.transforming')
    importProgress.value = 20

    // Execute with AI analysis for transformation
    const normalizedTaskType = normalizeTaskType(scenarioConfig.value.taskType)
    const normalizedAnalysis = analysisResult.value
      ? { ...analysisResult.value, task_type: normalizedTaskType }
      : null

    const result = await executeImport({
      taskType: normalizedTaskType,
      sourceName: scenarioConfig.value.name,
      aiAnalysis: normalizedAnalysis
    })

    importStatus.value = t('dataImporter.wizard.execute.importing')

    clearInterval(progressInterval)
    importProgress.value = 100
    importStatus.value = t('dataImporter.wizard.execute.complete')

    importResult.value = result
    importComplete.value = true

    showSuccess(t('dataImporter.wizard.execute.successMessage', { count: result?.imported_count || 0 }))

  } catch (err) {
    showError(t('dataImporter.wizard.execute.errorMessage', { error: err.message || t('dataImporter.wizard.execute.unknownError') }))
  } finally {
    importing.value = false
  }
}

const handleClose = () => {
  emit('close')
}

const handleComplete = () => {
  emit('complete', {
    session: importResult.value,
    scenarioConfig: scenarioConfig.value,
    userConfig: userConfig.value
  })
}

// Watch for task type from analysis
watch(() => analysisResult.value?.task_type, (newType) => {
  if (newType) {
    scenarioConfig.value.taskType = normalizeTaskType(newType)
  }
})
</script>

<style scoped>
.wizard-host {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
}

.wizard-card {
  border-radius: 16px 4px 16px 4px;
}

.wizard-steps {
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.step-item {
  flex: 0 0 auto;
  min-width: 90px;
  cursor: default;
  transition: opacity 0.2s;
}

.step-item.step-clickable {
  cursor: pointer;
}

.step-item.step-clickable:hover .step-circle {
  transform: scale(1.1);
}

.step-item.step-disabled {
  opacity: 0.5;
}

.step-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
  background: rgb(var(--v-theme-surface-variant));
  color: rgb(var(--v-theme-on-surface-variant));
}

.step-active .step-circle {
  background: #b0ca97;
  color: white;
}

.step-complete .step-circle {
  background: #98d4bb;
  color: white;
}

.step-title {
  font-weight: 500;
  white-space: nowrap;
}

.step-connector {
  height: 2px;
  background: rgb(var(--v-theme-surface-variant));
  transition: background 0.3s;
}

.step-connector-complete {
  background: #98d4bb;
}

.step-content {
  min-height: 450px;
  max-height: 65vh;
  overflow-y: auto;
}

/* Execute Step */
.step-execute {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.execute-summary {
  text-align: center;
  max-width: 500px;
}

.summary-cards {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.summary-card {
  flex: 1;
  max-width: 140px;
  padding: 16px;
  background: rgba(var(--v-theme-primary), 0.08);
  border-radius: 12px 4px 12px 4px;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #6a8a52;
}

.summary-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

.import-progress {
  max-width: 300px;
  margin: 0 auto;
}
</style>
