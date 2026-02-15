<!--
  GenerationWizard.vue - Batch Generation Job Wizard

  5-step wizard for creating batch generation jobs:
  1. Source Selection (Previous Generation, Manual Data, Prompt Only)
  2. Prompt Selection (Templates with variants)
  3. Model Selection (LLM models)
  4. Configuration (Parameters, budget limits)
  5. Review & Create

  Follows LLARS design patterns with asymmetric border-radius.
-->
<template>
  <v-card class="generation-wizard">
    <!-- Header -->
    <v-card-title class="wizard-header">
      <LIcon color="primary" class="mr-3" size="28">mdi-auto-fix</LIcon>
      <span>{{ $t('generation.wizard.title') }}</span>
      <v-spacer />
      <v-btn icon variant="text" @click="$emit('close')">
        <LIcon>mdi-close</LIcon>
      </v-btn>
    </v-card-title>

    <!-- Stepper -->
    <div class="wizard-stepper">
      <div
        v-for="(step, index) in steps"
        :key="step.key"
        class="step"
        :class="{
          active: currentStep === index,
          completed: currentStep > index,
          clickable: currentStep > index
        }"
        @click="currentStep > index && goToStep(index)"
      >
        <div class="step-indicator">
          <LIcon v-if="currentStep > index" size="18">mdi-check</LIcon>
          <LIcon v-else size="18">{{ step.icon }}</LIcon>
        </div>
        <span class="step-label">{{ step.label }}</span>
      </div>
    </div>

    <v-divider />

    <!-- Step Content -->
    <v-card-text class="wizard-content">
      <!-- Step 1: Source Selection -->
      <div v-if="currentStep === 0" class="step-content">
        <h3 class="step-title">{{ $t('generation.wizard.step1.title') }}</h3>
        <p class="step-description">{{ $t('generation.wizard.step1.description') }}</p>

        <div class="source-options">
          <!-- Previous Generation Source -->
          <LTooltip :text="$t('generation.wizard.step1.fromJobTooltip')" location="bottom">
            <div
              class="source-card"
              :class="{ selected: formData.sourceType === 'from_job' }"
              @click="selectSourceType('from_job')"
            >
              <div class="source-icon" style="background-color: rgba(176, 202, 151, 0.2);">
                <LIcon color="primary" size="32">mdi-history</LIcon>
              </div>
              <h4>{{ $t('generation.wizard.step1.fromJobSource') }}</h4>
              <p>{{ $t('generation.wizard.step1.fromJobSourceDesc') }}</p>
            </div>
          </LTooltip>

          <!-- Manual Data Source -->
          <LTooltip :text="$t('generation.wizard.step1.manualTooltip')" location="bottom">
            <div
              class="source-card"
              :class="{ selected: formData.sourceType === 'manual' }"
              @click="selectSourceType('manual')"
            >
              <div class="source-icon" style="background-color: rgba(136, 196, 200, 0.2);">
                <LIcon color="accent" size="32">mdi-file-upload-outline</LIcon>
              </div>
              <h4>{{ $t('generation.wizard.step1.manualSource') }}</h4>
              <p>{{ $t('generation.wizard.step1.manualSourceDesc') }}</p>
            </div>
          </LTooltip>

          <!-- Prompt Template Source -->
          <LTooltip :text="$t('generation.wizard.step1.promptOnlyTooltip')" location="bottom">
            <div
              class="source-card"
              :class="{ selected: formData.sourceType === 'prompt_only' }"
              @click="selectSourceType('prompt_only')"
            >
              <div class="source-icon" style="background-color: rgba(209, 188, 138, 0.2);">
                <LIcon color="secondary" size="32">mdi-text-box-multiple-outline</LIcon>
              </div>
              <h4>{{ $t('generation.wizard.step1.promptOnlySource') }}</h4>
              <p>{{ $t('generation.wizard.step1.promptOnlySourceDesc') }}</p>
            </div>
          </LTooltip>
        </div>

        <!-- Job Selection -->
        <div v-if="formData.sourceType === 'from_job'" class="source-config mt-6">
          <v-autocomplete
            v-model="formData.sourceJobId"
            :items="completedJobs"
            :loading="loadingJobs"
            item-title="name"
            item-value="id"
            :label="$t('generation.wizard.step1.selectJob')"
            variant="outlined"
            clearable
            @update:model-value="onJobSelected"
          >
            <template v-slot:item="{ props, item }">
              <v-list-item v-bind="props">
                <template v-slot:prepend>
                  <LIcon size="20" class="mr-2">mdi-auto-fix</LIcon>
                </template>
                <template v-slot:subtitle>
                  {{ item.raw.total_items }} Outputs · {{ item.raw.created_at_formatted }}
                </template>
              </v-list-item>
            </template>
          </v-autocomplete>

          <v-alert v-if="selectedJobInfo" type="info" variant="tonal" class="mt-4">
            <div class="job-info">
              <strong>{{ selectedJobInfo.name }}</strong>
              <div class="mt-2">
                <LTag variant="info" size="small" class="mr-2">
                  {{ selectedJobItemCount }} Items
                </LTag>
                <LTag variant="success" size="small">
                  {{ selectedJobInfo.completed_items }}/{{ selectedJobInfo.total_items }} Outputs
                </LTag>
              </div>
            </div>
          </v-alert>
        </div>

        <!-- Manual Data Input -->
        <div v-if="formData.sourceType === 'manual'" class="source-config mt-6">
          <div
            class="upload-zone"
            :class="{ 'drag-over': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="handleFileDrop"
            @click="$refs.fileInput.click()"
          >
            <input
              ref="fileInput"
              type="file"
              accept=".json,.csv"
              hidden
              @change="handleFileSelect"
            />
            <LIcon size="48" color="primary" class="upload-icon">mdi-cloud-upload-outline</LIcon>
            <p class="upload-text">{{ $t('generation.wizard.step1.dropFiles') }}</p>
            <p class="upload-hint">JSON, CSV</p>
          </div>

          <v-textarea
            v-model="formData.manualData"
            :label="$t('generation.wizard.step1.pasteData')"
            :placeholder="$t('generation.wizard.step1.pasteDataPlaceholder')"
            variant="outlined"
            rows="4"
            class="mt-4"
          />

          <div v-if="parsedManualItems.length > 0" class="mt-4">
            <LTag variant="success">
              {{ parsedManualItems.length }} {{ $t('generation.wizard.step1.itemsParsed') }}
            </LTag>
          </div>
        </div>

        <!-- Prompt Only - No source data needed -->
        <div v-if="formData.sourceType === 'prompt_only'" class="source-config mt-6">
          <v-alert type="info" variant="tonal">
            {{ $t('generation.wizard.step1.promptOnlyInfo') }}
          </v-alert>
        </div>
      </div>

      <!-- Step 2: Prompt Selection -->
      <div v-if="currentStep === 1" class="step-content">
        <h3 class="step-title">{{ $t('generation.wizard.step2.title') }}</h3>
        <p class="step-description">{{ $t('generation.wizard.step2.description') }}</p>

        <!-- Prompt Templates List -->
        <div v-if="loadingPrompts" class="loading-state">
          <v-progress-circular indeterminate color="primary" />
          <span class="ml-3">{{ $t('common.loading') }}</span>
        </div>

        <div v-else class="prompts-selection">
          <div
            v-for="template in promptTemplates"
            :key="template.id"
            class="selection-item"
            :class="{ selected: isPromptSelected(template.id) }"
            @click="togglePromptSelection(template)"
          >
            <LIcon class="item-icon" size="20" color="secondary">mdi-text-box-outline</LIcon>
            <div class="item-info">
              <span class="item-name">{{ template.name }}</span>
              <span v-if="template.description" class="item-detail">{{ template.description }}</span>
            </div>
            <LIcon v-if="isPromptSelected(template.id)" color="primary">mdi-check-circle</LIcon>
          </div>

          <div v-if="promptTemplates.length === 0" class="empty-prompts">
            <LIcon size="48" color="grey">mdi-text-box-remove-outline</LIcon>
            <p>{{ $t('generation.wizard.step2.noPrompts') }}</p>
          </div>
        </div>

        <!-- Selected Summary -->
        <div v-if="formData.prompts.length > 0" class="selection-summary mt-4">
          <LTag variant="success">
            {{ formData.prompts.length }} {{ $t('generation.wizard.step2.promptsSelected') }}
          </LTag>
        </div>
      </div>

      <!-- Step 3: Model Selection -->
      <div v-if="currentStep === 2" class="step-content">
        <h3 class="step-title">{{ $t('generation.wizard.step3.title') }}</h3>
        <p class="step-description">{{ $t('generation.wizard.step3.description') }}</p>

        <!-- Model Selection -->
        <div v-if="loadingModels" class="loading-state">
          <v-progress-circular indeterminate color="primary" />
          <span class="ml-3">{{ $t('common.loading') }}</span>
        </div>

        <div v-else class="models-selection">
          <div
            v-for="model in availableModels"
            :key="model.id"
            class="selection-item"
            :class="{ selected: formData.llmModels.includes(model.model_id) }"
            @click="toggleModelSelection(model.model_id)"
          >
            <LIcon class="item-icon" size="20" color="accent">mdi-robot-outline</LIcon>
            <div class="item-info">
              <span class="item-name">
                {{ model.is_user_provider ? (model.label || model.model_id) : model.model_id }}
              </span>
              <span v-if="model.input_cost_per_million != null || model.output_cost_per_million != null" class="item-detail">
                ${{ model.input_cost_per_million || 0 }} in / ${{ model.output_cost_per_million || 0 }} out per 1M tokens
              </span>
            </div>
            <LIcon v-if="formData.llmModels.includes(model.model_id)" color="primary">mdi-check-circle</LIcon>
          </div>

          <div v-if="availableModels.length === 0" class="empty-models">
            <LIcon size="48" color="grey">mdi-robot-off-outline</LIcon>
            <p>{{ $t('generation.wizard.step3.noModels') }}</p>
          </div>
        </div>

        <!-- Selected Summary -->
        <div v-if="formData.llmModels.length > 0" class="selection-summary mt-4">
          <LTag variant="success">
            {{ formData.llmModels.length }} {{ $t('generation.wizard.step3.modelsSelected') }}
          </LTag>
        </div>
      </div>

      <!-- Step 4: Configuration -->
      <div v-if="currentStep === 3" class="step-content">
        <h3 class="step-title">{{ $t('generation.wizard.step4.title') }}</h3>
        <p class="step-description">{{ $t('generation.wizard.step4.description') }}</p>

        <div class="config-form">
          <!-- Job Name (auto-generated, editable) -->
          <v-text-field
            v-model="formData.name"
            :label="$t('generation.wizard.step4.jobName')"
            :rules="[v => !!v || $t('validation.required')]"
            variant="outlined"
            :hint="$t('generation.wizard.step4.jobNameHint')"
            persistent-hint
            class="mb-6"
          />

          <!-- Generation Parameters -->
          <h4 class="subsection-title">{{ $t('generation.wizard.step4.parameters') }}</h4>

          <v-row>
            <v-col cols="12" md="6">
              <v-slider
                v-model="formData.generationParams.temperature"
                :label="$t('generation.wizard.step4.temperature')"
                :min="0"
                :max="2"
                :step="0.1"
                thumb-label
                class="mb-4"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="formData.generationParams.max_tokens"
                :label="$t('generation.wizard.step4.maxTokens')"
                type="number"
                variant="outlined"
                :min="1"
                :max="128000"
                :placeholder="$t('generation.wizard.step4.maxTokensPlaceholder')"
                :hint="$t('generation.wizard.step4.maxTokensHint')"
                persistent-hint
                clearable
              />
            </v-col>
          </v-row>

          <v-divider class="mb-4" />

          <!-- Budget Limit -->
          <h4 class="subsection-title">{{ $t('generation.wizard.step4.budget') }}</h4>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="formData.budgetLimit"
                :label="$t('generation.wizard.step4.budgetLimit')"
                type="number"
                variant="outlined"
                prefix="$"
                :min="0"
                :step="0.01"
                :hint="$t('generation.wizard.step4.budgetHint')"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="formData.generationParams.retry_count"
                :label="$t('generation.wizard.step4.retryCount')"
                type="number"
                variant="outlined"
                :min="0"
                :max="5"
              />
            </v-col>
          </v-row>
        </div>
      </div>

      <!-- Step 5: Review -->
      <div v-if="currentStep === 4" class="step-content">
        <h3 class="step-title">{{ $t('generation.wizard.step5.title') }}</h3>
        <p class="step-description">{{ $t('generation.wizard.step5.description') }}</p>

        <div class="review-summary">
          <!-- Job Info -->
          <div class="review-section">
            <h4>
              <LIcon class="mr-2" size="20">mdi-information-outline</LIcon>
              {{ $t('generation.wizard.step5.jobInfo') }}
            </h4>
            <div class="review-item">
              <span class="review-label">{{ $t('generation.wizard.step4.jobName') }}:</span>
              <span class="review-value">{{ formData.name }}</span>
            </div>
          </div>

          <!-- Source Info -->
          <div class="review-section">
            <h4>
              <LIcon class="mr-2" size="20">mdi-database-outline</LIcon>
              {{ $t('generation.wizard.step5.sourceInfo') }}
            </h4>
            <div class="review-item">
              <span class="review-label">{{ $t('generation.wizard.step1.title') }}:</span>
              <span class="review-value">{{ getSourceTypeLabel(formData.sourceType) }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">{{ $t('generation.wizard.step5.itemCount') }}:</span>
              <span class="review-value">{{ totalItemCount }}</span>
            </div>
          </div>

          <!-- Matrix Info -->
          <div class="review-section">
            <h4>
              <LIcon class="mr-2" size="20">mdi-grid</LIcon>
              {{ $t('generation.wizard.step5.matrix') }}
            </h4>
            <div class="matrix-preview">
              <div class="matrix-item">
                <span class="matrix-value">{{ totalItemCount }}</span>
                <span class="matrix-label">Items</span>
              </div>
              <LIcon size="20" color="grey">mdi-close</LIcon>
              <div class="matrix-item">
                <span class="matrix-value">{{ formData.prompts.length }}</span>
                <span class="matrix-label">Prompts</span>
              </div>
              <LIcon size="20" color="grey">mdi-close</LIcon>
              <div class="matrix-item">
                <span class="matrix-value">{{ formData.llmModels.length }}</span>
                <span class="matrix-label">Models</span>
              </div>
              <LIcon size="20" color="grey">mdi-equal</LIcon>
              <div class="matrix-item total">
                <span class="matrix-value">{{ totalOutputs }}</span>
                <span class="matrix-label">Outputs</span>
              </div>
            </div>
          </div>

          <!-- Cost Estimate -->
          <div v-if="costEstimate" class="review-section">
            <h4>
              <LIcon class="mr-2" size="20">mdi-currency-usd</LIcon>
              {{ $t('generation.wizard.step5.costEstimate') }}
            </h4>
            <div class="cost-estimate">
              <div class="cost-value">${{ costEstimate.estimated_cost_usd?.toFixed(4) || '0.00' }}</div>
              <div class="cost-breakdown">
                <span>{{ costEstimate.total_outputs?.toLocaleString() || 0 }} Outputs</span>
                <span class="cost-note">{{ costEstimate.note }}</span>
              </div>
              <!-- Per-Model Breakdown -->
              <div v-if="costEstimate.cost_breakdown" class="cost-model-breakdown">
                <div
                  v-for="(breakdown, modelId) in costEstimate.cost_breakdown"
                  :key="modelId"
                  class="cost-model-item"
                >
                  <span class="cost-model-name">{{ formatCostModelName(modelId) }}</span>
                  <span class="cost-model-value">
                    {{ breakdown.estimated_cost_usd != null ? `$${breakdown.estimated_cost_usd.toFixed(4)}` : '?' }}
                  </span>
                  <span class="cost-model-outputs">{{ breakdown.outputs }} Outputs</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </v-card-text>

    <!-- Footer -->
    <v-divider />
    <v-card-actions class="wizard-actions">
      <LBtn
        v-if="currentStep > 0"
        variant="tonal"
        @click="previousStep"
      >
        <LIcon start>mdi-chevron-left</LIcon>
        {{ $t('common.back') }}
      </LBtn>
      <v-spacer />
      <LBtn
        v-if="currentStep < steps.length - 1"
        variant="primary"
        :disabled="!canProceed"
        @click="nextStep"
      >
        {{ $t('common.next') }}
        <LIcon end>mdi-chevron-right</LIcon>
      </LBtn>
      <LBtn
        v-else
        variant="primary"
        :loading="isCreating"
        :disabled="!canCreate"
        @click="createJob"
      >
        <LIcon start>mdi-rocket-launch</LIcon>
        {{ $t('generation.wizard.createJob') }}
      </LBtn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useGeneration } from '@/composables/useGeneration'
import { parseUserProviderModelId } from '@/utils/formatters'

const emit = defineEmits(['close', 'created'])

const { t } = useI18n()
const { createJob: createGenerationJob, estimateCost } = useGeneration()

// Steps configuration
const steps = [
  { key: 'source', label: t('generation.wizard.steps.source'), icon: 'mdi-database' },
  { key: 'prompts', label: t('generation.wizard.steps.prompts'), icon: 'mdi-text-box' },
  { key: 'models', label: t('generation.wizard.steps.models'), icon: 'mdi-robot' },
  { key: 'config', label: t('generation.wizard.steps.config'), icon: 'mdi-cog' },
  { key: 'review', label: t('generation.wizard.steps.review'), icon: 'mdi-check-all' }
]

// State
const currentStep = ref(0)
const isCreating = ref(false)
const isDragging = ref(false)

// Loading states
const loadingJobs = ref(false)
const loadingPrompts = ref(false)
const loadingModels = ref(false)

// Data
const completedJobs = ref([])
const promptTemplates = ref([])
const availableModels = ref([])
const selectedJobInfo = ref(null)
const costEstimate = ref(null)

// Form data
const formData = ref({
  name: '',
  sourceType: 'from_job',
  sourceJobId: null,
  manualData: '',
  prompts: [],
  llmModels: [],
  generationParams: {
    temperature: 0.7,
    max_tokens: null,  // null = unlimited (good for reasoning models like Magistral)
    retry_count: 3
  },
  budgetLimit: null
})

// Computed
const parsedManualItems = computed(() => {
  if (!formData.value.manualData) return []
  try {
    const data = JSON.parse(formData.value.manualData)
    return Array.isArray(data) ? data : [data]
  } catch {
    // Try CSV parsing
    const lines = formData.value.manualData.trim().split('\n')
    if (lines.length > 1) {
      return lines.slice(1).map((line, i) => ({ id: i + 1, content: line }))
    }
    return []
  }
})

const selectedJobItemCount = computed(() => {
  if (!selectedJobInfo.value) return 0
  const sources = selectedJobInfo.value.config_json?.sources || {}
  if (sources.item_count != null) return sources.item_count
  // Fallback: total_items / (prompts × models)
  const prompts = selectedJobInfo.value.config_json?.prompts?.length || 1
  const models = selectedJobInfo.value.config_json?.llm_models?.length || 1
  return Math.ceil(selectedJobInfo.value.total_items / (prompts * models))
})

const totalItemCount = computed(() => {
  if (formData.value.sourceType === 'from_job') {
    return selectedJobItemCount.value
  }
  if (formData.value.sourceType === 'manual') {
    return parsedManualItems.value.length
  }
  return 1 // prompt_only
})

const totalOutputs = computed(() => {
  return totalItemCount.value * formData.value.prompts.length * formData.value.llmModels.length
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0: // Source
      if (formData.value.sourceType === 'from_job') {
        return !!formData.value.sourceJobId
      }
      if (formData.value.sourceType === 'manual') {
        return parsedManualItems.value.length > 0
      }
      return true // prompt_only
    case 1: // Prompts
      return formData.value.prompts.length > 0
    case 2: // Models
      return formData.value.llmModels.length > 0
    case 3: // Config
      return !!formData.value.name
    default:
      return true
  }
})

const canCreate = computed(() => {
  return formData.value.name &&
    formData.value.prompts.length > 0 &&
    formData.value.llmModels.length > 0 &&
    totalItemCount.value > 0
})

// Methods
function selectSourceType(type) {
  formData.value.sourceType = type
}

function goToStep(index) {
  currentStep.value = index
}

function nextStep() {
  if (canProceed.value && currentStep.value < steps.length - 1) {
    currentStep.value++

    // Load data for next step
    if (currentStep.value === 1) loadPromptTemplates()
    if (currentStep.value === 2) loadModels()
    if (currentStep.value === 3) generateJobName()
    if (currentStep.value === 4) loadCostEstimate()
  }
}

function generateJobName() {
  // Don't overwrite if user already entered a name
  if (formData.value.name) return

  const parts = []

  // Add first prompt name
  if (formData.value.prompts.length > 0) {
    const firstPrompt = formData.value.prompts[0].template_name
    parts.push(firstPrompt)
    if (formData.value.prompts.length > 1) {
      parts.push(`+${formData.value.prompts.length - 1}`)
    }
  }

  // Add source info
  if (formData.value.sourceType === 'from_job' && selectedJobInfo.value) {
    parts.push(`[from: ${selectedJobInfo.value.name}]`)
  } else if (formData.value.sourceType === 'manual') {
    parts.push(`[${parsedManualItems.value.length} Items]`)
  } else if (formData.value.sourceType === 'prompt_only') {
    parts.push('[Prompt Only]')
  }

  // Add timestamp
  const now = new Date()
  const timestamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  parts.push(timestamp)

  formData.value.name = parts.join(' ')
}

function previousStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// Source methods
async function loadJobs() {
  loadingJobs.value = true
  try {
    const response = await axios.get('/api/generation/jobs', { params: { status: 'completed' } })
    completedJobs.value = (response.data.jobs || []).map(j => ({
      ...j,
      created_at_formatted: new Date(j.created_at).toLocaleDateString()
    }))
  } catch (error) {
    console.error('Failed to load jobs:', error)
  } finally {
    loadingJobs.value = false
  }
}

function onJobSelected(jobId) {
  selectedJobInfo.value = completedJobs.value.find(j => j.id === jobId) || null
}

function handleFileDrop(event) {
  isDragging.value = false
  const files = event.dataTransfer.files
  if (files.length > 0) {
    processFile(files[0])
  }
}

function handleFileSelect(event) {
  const files = event.target.files
  if (files.length > 0) {
    processFile(files[0])
  }
}

async function processFile(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    formData.value.manualData = e.target.result
  }
  reader.readAsText(file)
}

// Prompt methods
async function loadPromptTemplates() {
  loadingPrompts.value = true
  try {
    const response = await axios.get('/api/prompts/templates')
    promptTemplates.value = response.data.templates || []
  } catch (error) {
    console.error('Failed to load prompts:', error)
  } finally {
    loadingPrompts.value = false
  }
}

function isPromptSelected(templateId) {
  return formData.value.prompts.some(p => p.template_id === templateId)
}

function isVariantSelected(templateId, variantName) {
  const prompt = formData.value.prompts.find(p => p.template_id === templateId)
  return prompt?.variants?.includes(variantName) || false
}

function togglePromptSelection(template) {
  const index = formData.value.prompts.findIndex(p => p.template_id === template.id)
  if (index !== -1) {
    formData.value.prompts.splice(index, 1)
  } else {
    // Add with default variant
    const defaultVariant = template.variants?.[0]?.name || 'default'
    formData.value.prompts.push({
      template_id: template.id,
      template_name: template.name,
      variants: [defaultVariant]
    })
  }
}

function toggleVariantSelection(templateId, variantName) {
  const prompt = formData.value.prompts.find(p => p.template_id === templateId)
  if (!prompt) return

  const variantIndex = prompt.variants.indexOf(variantName)
  if (variantIndex !== -1) {
    if (prompt.variants.length > 1) {
      prompt.variants.splice(variantIndex, 1)
    }
  } else {
    prompt.variants.push(variantName)
  }
}

// Model methods
async function loadModels() {
  loadingModels.value = true
  try {
    const [modelsResult, providersResult] = await Promise.allSettled([
      axios.get('/api/llm/models/available', { params: { model_type: 'llm' } }),
      axios.get('/api/user/providers/available')
    ])

    const baseModels = modelsResult.status === 'fulfilled'
      ? (modelsResult.value.data.models || [])
      : []

    let providerModels = []
    if (providersResult.status === 'fulfilled') {
      const providers = providersResult.value.data.providers || []
      for (const provider of providers) {
        if (!provider.api_key_set || provider.is_active === false) continue
        const config = provider?.config || {}

        // Support multiple selected models (OpenAI style)
        const ownerName = provider.owner_username || provider.shared_by || ''
        const selectedModels = Array.isArray(config.selected_models) ? config.selected_models : []
        if (selectedModels.length > 0) {
          for (const mid of selectedModels) {
            const modelId = (mid || '').trim()
            if (!modelId) continue
            const fullId = ownerName
              ? `user-provider:${provider.id}:${ownerName}:${modelId}`
              : `user-provider:${provider.id}:${modelId}`
            const parsed = parseUserProviderModelId(fullId)
            providerModels.push({
              id: fullId,
              model_id: fullId,
              label: parsed?.displayName || `${provider.name || 'Provider'} / ${modelId}`,
              provider_type: provider.provider_type,
              provider_name: parsed?.providerLabel || provider.name,
              is_user_provider: true
            })
          }
          continue
        }

        // Fallback: single model_id
        const modelId = (config.model_id || '').trim()
        if (!modelId) continue
        const fullId = ownerName
          ? `user-provider:${provider.id}:${ownerName}:${modelId}`
          : `user-provider:${provider.id}:${modelId}`
        const parsed = parseUserProviderModelId(fullId)
        providerModels.push({
          id: fullId,
          model_id: fullId,
          label: parsed?.displayName || `${provider.name || 'Provider'} / ${modelId}`,
          provider_type: provider.provider_type,
          provider_name: parsed?.providerLabel || provider.name,
          is_user_provider: true
        })
      }
    }

    availableModels.value = [...baseModels, ...providerModels]
  } catch (error) {
    console.error('Failed to load models:', error)
  } finally {
    loadingModels.value = false
  }
}

function toggleModelSelection(modelId) {
  const index = formData.value.llmModels.indexOf(modelId)
  if (index !== -1) {
    formData.value.llmModels.splice(index, 1)
  } else {
    formData.value.llmModels.push(modelId)
  }
}

// Cost estimate
async function loadCostEstimate() {
  const config = buildJobConfig()
  costEstimate.value = await estimateCost(config)
}

// Helper methods
function getSourceTypeLabel(type) {
  const labels = {
    from_job: t('generation.wizard.step1.fromJobSource'),
    manual: t('generation.wizard.step1.manualSource'),
    prompt_only: t('generation.wizard.step1.promptOnlySource')
  }
  return labels[type] || type
}

function formatCostModelName(modelId) {
  const parsed = parseUserProviderModelId(modelId)
  if (parsed) return parsed.displayName
  return modelId
}

function buildJobConfig() {
  const sources = {}

  if (formData.value.sourceType === 'from_job') {
    sources.type = 'from_job'
    sources.job_id = formData.value.sourceJobId
  } else if (formData.value.sourceType === 'manual') {
    sources.type = 'manual'
    sources.items = parsedManualItems.value
  } else {
    sources.type = 'prompt_only'
  }

  return {
    sources,
    prompts: formData.value.prompts,
    llm_models: formData.value.llmModels,
    generation_params: formData.value.generationParams,
    budget_limit_usd: formData.value.budgetLimit
  }
}

// Create job
async function createJob() {
  isCreating.value = true

  try {
    const job = await createGenerationJob({
      name: formData.value.name,
      config: buildJobConfig()
    })

    if (job) {
      emit('created', job)
    }
  } finally {
    isCreating.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadJobs()
})
</script>

<style scoped>
.generation-wizard {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.wizard-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  font-size: 1.2rem;
  font-weight: 600;
}

/* Stepper */
.wizard-stepper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 24px;
  gap: 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px 2px 8px 2px;
  transition: all 0.2s ease;
}

.step.clickable {
  cursor: pointer;
}

.step.clickable:hover {
  background: rgba(var(--v-theme-primary), 0.1);
}

.step.active {
  background: rgba(var(--v-theme-primary), 0.15);
}

.step.completed .step-indicator {
  background: var(--llars-success, #98d4bb);
  color: white;
}

.step-indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--v-theme-on-surface), 0.1);
  font-size: 0.8rem;
  font-weight: 600;
}

.step.active .step-indicator {
  background: var(--llars-primary, #b0ca97);
  color: white;
}

.step-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.step.active .step-label {
  color: rgb(var(--v-theme-on-surface));
}

/* Content */
.wizard-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.step-content {
  max-width: 800px;
  margin: 0 auto;
}

.step-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.step-description {
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0 0 24px 0;
}

.subsection-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Source Options */
.source-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.source-card {
  padding: 20px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.source-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background: rgba(var(--v-theme-primary), 0.02);
}

.source-card.selected {
  border-color: var(--llars-primary, #b0ca97);
  background: rgba(var(--v-theme-primary), 0.05);
}

.source-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}

.source-card h4 {
  margin: 0 0 8px 0;
  font-size: 1rem;
}

.source-card p {
  margin: 0;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 12px 4px 12px 4px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: var(--llars-primary, #b0ca97);
  background: rgba(var(--v-theme-primary), 0.05);
}

.upload-text {
  font-size: 1rem;
  margin: 12px 0 4px 0;
}

.upload-hint {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
}

/* Prompts & Models Selection - Unified Selection Item Pattern */
.prompts-selection,
.models-selection {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selection-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px 2px 8px 2px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(var(--v-theme-on-surface), 0.01);
}

.selection-item:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background: rgba(var(--v-theme-primary), 0.02);
}

.selection-item.selected {
  border-color: var(--llars-primary, #b0ca97);
  background: rgba(var(--v-theme-primary), 0.06);
}

.selection-item .item-icon {
  flex-shrink: 0;
}

.selection-item .item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.selection-item .item-name {
  font-weight: 500;
  font-size: 0.95rem;
  color: rgb(var(--v-theme-on-surface));
}

.selection-item .item-detail {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-cost {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-family: monospace;
}

/* Selection Summary */
.selection-summary {
  padding: 12px;
  background: rgba(var(--v-theme-success), 0.1);
  border-radius: 8px;
}

/* Loading State */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

/* Empty States */
.empty-prompts,
.empty-models {
  text-align: center;
  padding: 48px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Review Summary */
.review-summary {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.review-section {
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px 2px 8px 2px;
}

.review-section h4 {
  display: flex;
  align-items: center;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.review-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.review-item:last-child {
  margin-bottom: 0;
}

.review-label {
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.review-value {
  flex: 1;
}

/* Matrix Preview */
.matrix-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
}

.matrix-item {
  text-align: center;
}

.matrix-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--llars-primary, #b0ca97);
}

.matrix-item.total .matrix-value {
  color: var(--llars-accent, #88c4c8);
}

.matrix-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Cost Estimate */
.cost-estimate {
  text-align: center;
  padding: 16px;
}

.cost-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--llars-secondary, #d1bc8a);
  font-family: monospace;
}

.cost-breakdown {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.cost-note {
  font-size: 0.75rem;
  font-style: italic;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.cost-model-breakdown {
  margin-top: 12px;
  width: 100%;
  max-width: 400px;
}

.cost-model-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  font-size: 0.8rem;
}

.cost-model-item:last-child {
  border-bottom: none;
}

.cost-model-name {
  flex: 1;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.cost-model-value {
  font-family: monospace;
  font-weight: 600;
  color: var(--llars-secondary, #d1bc8a);
}

.cost-model-outputs {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Actions */
.wizard-actions {
  padding: 16px 20px;
}
</style>
