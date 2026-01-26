<!--
  GenerationJobDetail.vue - Job Detail View

  Shows detailed information about a generation job including:
  - Status and progress
  - Configuration summary
  - Output list with pagination
  - Export and scenario creation actions
-->
<template>
  <div class="job-detail" :class="{ 'is-mobile': isMobile }">
    <!-- Header -->
    <div class="detail-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goBack">
        {{ $t('generation.title') }}
      </LBtn>
      <div class="header-info">
        <h1>{{ currentJob?.name || $t('common.loading') }}</h1>
        <p v-if="currentJob?.description" class="text-medium-emphasis">
          {{ currentJob.description }}
        </p>
      </div>
      <div class="header-actions">
        <!-- Job Actions -->
        <LBtn
          v-if="canStart"
          variant="primary"
          @click="handleStart"
        >
          <LIcon start>mdi-play</LIcon>
          {{ $t('generation.actions.start') }}
        </LBtn>
        <LBtn
          v-if="canPause"
          variant="secondary"
          @click="handlePause"
        >
          <LIcon start>mdi-pause</LIcon>
          {{ $t('generation.actions.pause') }}
        </LBtn>
        <LBtn
          v-if="canCancel"
          variant="danger"
          @click="handleCancel"
        >
          <LIcon start>mdi-stop</LIcon>
          {{ $t('generation.actions.cancel') }}
        </LBtn>

        <!-- Export Menu -->
        <v-menu offset-y>
          <template v-slot:activator="{ props }">
            <LBtn variant="tonal" v-bind="props">
              <LIcon start>mdi-export</LIcon>
              {{ $t('generation.actions.export') }}
              <LIcon end>mdi-chevron-down</LIcon>
            </LBtn>
          </template>
          <v-list density="compact">
            <v-list-item @click="handleExportCsv">
              <template v-slot:prepend>
                <LIcon size="18" class="mr-2">mdi-file-delimited</LIcon>
              </template>
              <v-list-item-title>CSV</v-list-item-title>
            </v-list-item>
            <v-list-item @click="handleExportJson">
              <template v-slot:prepend>
                <LIcon size="18" class="mr-2">mdi-code-json</LIcon>
              </template>
              <v-list-item-title>JSON</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <!-- Open Scenario Wizard -->
        <LBtn
          v-if="canCreateScenario"
          variant="accent"
          @click="openScenarioWizard"
        >
          <LIcon start>mdi-wizard-hat</LIcon>
          {{ $t('generation.actions.scenarioWizard') }}
        </LBtn>
      </div>
    </div>

    <!-- Main Content -->
    <div class="detail-content">
      <!-- Left: Progress and Info -->
      <div class="info-panel">
        <!-- Progress Card -->
        <LCard class="progress-card">
          <template #title>
            <LIcon :color="statusColor" class="mr-2">{{ statusIcon }}</LIcon>
            {{ statusLabel }}
          </template>

          <!-- Progress Bar -->
          <div class="progress-section">
            <div class="progress-stats">
              <span class="progress-text">
                {{ currentJob?.progress?.completed || 0 }} / {{ currentJob?.progress?.total || 0 }}
              </span>
              <span class="progress-percent">{{ progressPercent }}%</span>
            </div>
            <v-progress-linear
              :model-value="progressPercent"
              :color="statusColor"
              height="8"
              rounded
            />
            <div v-if="currentJob?.progress?.failed" class="failed-info">
              <LIcon size="16" color="error" class="mr-1">mdi-alert</LIcon>
              {{ currentJob.progress.failed }} {{ $t('generation.failed') }}
            </div>

            <!-- Currently Processing Indicator (Socket.IO driven) -->
            <div v-if="currentlyProcessing" class="processing-info">
              <div class="processing-header">
                <v-progress-circular indeterminate size="16" width="2" color="primary" class="mr-2" />
                <span>{{ $t('generation.detail.currentlyProcessing') }}</span>
              </div>
              <div class="processing-item">
                <LIcon size="14" class="mr-1">mdi-robot</LIcon>
                <span class="model-name">{{ currentlyProcessing.model }}</span>
                <span class="item-name">{{ currentlyProcessing.itemName }}</span>
              </div>
            </div>
          </div>

          <!-- Stats Grid -->
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">{{ $t('generation.detail.created') }}</span>
              <span class="stat-value">{{ formatDate(currentJob?.created_at) }}</span>
            </div>
            <div v-if="currentJob?.started_at" class="stat-item">
              <span class="stat-label">{{ $t('generation.detail.started') }}</span>
              <span class="stat-value">{{ formatDate(currentJob?.started_at) }}</span>
            </div>
            <div v-if="currentJob?.completed_at" class="stat-item">
              <span class="stat-label">{{ $t('generation.detail.completed') }}</span>
              <span class="stat-value">{{ formatDate(currentJob?.completed_at) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">{{ $t('generation.detail.totalCost') }}</span>
              <span class="stat-value cost">${{ (currentJob?.total_cost_usd || 0).toFixed(4) }}</span>
            </div>
          </div>
        </LCard>

        <!-- Configuration Card -->
        <LCard class="config-card">
          <template #title>
            <LIcon color="secondary" class="mr-2">mdi-cog</LIcon>
            {{ $t('generation.detail.configuration') }}
          </template>

          <div class="config-section">
            <h4>{{ $t('generation.detail.source') }}</h4>
            <LTag :variant="sourceVariant">
              <LIcon start size="14">{{ sourceIcon }}</LIcon>
              {{ sourceLabel }}
            </LTag>
          </div>

          <div class="config-section">
            <h4>{{ $t('generation.detail.prompts') }}</h4>
            <div class="config-tags">
              <LTag
                v-for="prompt in jobConfig?.prompts || []"
                :key="prompt.template_id"
                variant="info"
                size="small"
              >
                {{ prompt.template_name || `Template #${prompt.template_id}` }}
              </LTag>
            </div>
          </div>

          <div class="config-section">
            <h4>{{ $t('generation.detail.models') }}</h4>
            <div class="config-tags">
              <LTag
                v-for="model in jobConfig?.llm_models || []"
                :key="model"
                variant="accent"
                size="small"
              >
                {{ model }}
              </LTag>
            </div>
          </div>

          <div v-if="jobConfig?.generation_params" class="config-section">
            <h4>{{ $t('generation.detail.parameters') }}</h4>
            <div class="params-list">
              <span>Temperature: {{ jobConfig.generation_params.temperature }}</span>
              <span>Max Tokens: {{ jobConfig.generation_params.max_tokens }}</span>
            </div>
          </div>
        </LCard>
      </div>

      <!-- Right: Outputs Table -->
      <div class="outputs-panel">
        <LCard class="outputs-card">
          <template #title>
            <LIcon color="primary" class="mr-2">mdi-text-box-multiple</LIcon>
            {{ $t('generation.detail.outputs') }}
            <LTag variant="info" size="small" class="ml-2">
              {{ outputsPagination.total }}
            </LTag>
          </template>

          <template #actions>
            <!-- Status Filter -->
            <v-menu offset-y>
              <template v-slot:activator="{ props }">
                <LBtn variant="text" size="small" v-bind="props">
                  <LIcon start size="16">mdi-filter-variant</LIcon>
                  {{ outputFilter || $t('generation.detail.allOutputs') }}
                </LBtn>
              </template>
              <v-list density="compact">
                <v-list-item @click="outputFilter = null">
                  <v-list-item-title>{{ $t('generation.detail.allOutputs') }}</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item @click="outputFilter = 'completed'">
                  <v-list-item-title>{{ $t('generation.status.completed') }}</v-list-item-title>
                </v-list-item>
                <v-list-item @click="outputFilter = 'failed'">
                  <v-list-item-title>{{ $t('generation.status.failed') }}</v-list-item-title>
                </v-list-item>
                <v-list-item @click="outputFilter = 'pending'">
                  <v-list-item-title>{{ $t('generation.status.pending') }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </template>

          <!-- Live Streaming Preview -->
          <div v-if="currentlyProcessing" class="streaming-preview">
            <div class="streaming-header">
              <v-progress-circular indeterminate size="14" width="2" color="primary" class="mr-2" />
              <LTag variant="accent" size="small">{{ currentlyProcessing.model }}</LTag>
              <span class="streaming-item-name">{{ currentlyProcessing.itemName }}</span>
            </div>
            <div ref="streamingContentRef" class="streaming-content">
              {{ streamingContent || t('generation.detail.waitingForResponse') }}
              <span class="cursor">|</span>
            </div>
          </div>

          <!-- Outputs List -->
          <div v-if="isLoadingOutputs" class="loading-state">
            <v-progress-circular indeterminate color="primary" />
          </div>

          <div v-else-if="outputs.length > 0 || currentlyProcessing" ref="outputsListRef" class="outputs-list">
            <div
              v-for="output in outputs"
              :key="output.id"
              class="output-item"
              :class="{ 'is-failed': output.status === 'failed' }"
              @click="selectOutput(output)"
            >
              <div class="output-status">
                <LIcon :color="getOutputStatusColor(output.status)" size="18">
                  {{ getOutputStatusIcon(output.status) }}
                </LIcon>
              </div>
              <div class="output-content">
                <div class="output-meta">
                  <LTag variant="secondary" size="x-small">{{ output.llm_model_name }}</LTag>
                  <span class="output-item-name">
                    {{ output.prompt_variant_name || `Item #${output.source_item_id || output.id}` }}
                  </span>
                </div>
                <p class="output-preview">
                  {{ output.content_preview || output.error_message || '-' }}
                </p>
              </div>
              <div class="output-tokens">
                <span v-if="output.tokens?.output">{{ output.tokens.output }} tok</span>
              </div>
            </div>
          </div>

          <div v-else class="empty-outputs">
            <LIcon size="48" color="grey">mdi-text-box-remove</LIcon>
            <p>{{ $t('generation.detail.noOutputs') }}</p>
          </div>

          <!-- Pagination -->
          <div v-if="outputsPagination.pages > 1" class="outputs-pagination">
            <v-pagination
              v-model="outputsPage"
              :length="outputsPagination.pages"
              :total-visible="5"
              density="compact"
              @update:model-value="handlePageChange"
            />
          </div>
        </LCard>
      </div>
    </div>

    <!-- Output Detail Dialog -->
    <v-dialog v-model="showOutputDialog" max-width="900">
      <LCard v-if="selectedOutput">
        <template #title>
          <LIcon color="primary" class="mr-2">mdi-text-box-outline</LIcon>
          {{ $t('generation.detail.outputDetail') }}
        </template>

        <div class="output-detail">
          <!-- Loading indicator -->
          <div v-if="isLoadingOutput" class="text-center py-4">
            <v-progress-circular indeterminate color="primary" />
            <p class="mt-2 text-medium-emphasis">{{ $t('common.loading') }}</p>
          </div>

          <template v-else>
            <div class="output-detail-meta">
              <div class="meta-item">
                <span class="meta-label">Model:</span>
                <LTag variant="accent">{{ selectedOutput.llm_model_name }}</LTag>
              </div>
              <div class="meta-item">
                <span class="meta-label">Status:</span>
                <LTag :variant="getOutputStatusVariant(selectedOutput.status)">
                  {{ selectedOutput.status }}
                </LTag>
              </div>
              <div v-if="selectedOutput.tokens?.total" class="meta-item">
                <span class="meta-label">Tokens:</span>
                <span>{{ selectedOutput.tokens.input }} in / {{ selectedOutput.tokens.output }} out</span>
              </div>
              <div v-if="selectedOutput.cost_usd" class="meta-item">
                <span class="meta-label">Cost:</span>
                <span>${{ selectedOutput.cost_usd.toFixed(6) }}</span>
              </div>
            </div>

            <v-divider class="my-4" />

            <!-- Two-column layout: Prompt | Generated Content -->
            <div class="output-columns">
              <!-- Left: Input Prompts -->
              <div class="output-column">
                <h4 class="column-title">
                  <LIcon size="18" class="mr-1">mdi-arrow-right-circle</LIcon>
                  {{ $t('generation.detail.inputPrompt') }}
                </h4>
                <div v-if="selectedOutput.rendered_system_prompt" class="prompt-section">
                  <span class="prompt-label">System:</span>
                  <pre class="prompt-pre">{{ selectedOutput.rendered_system_prompt }}</pre>
                </div>
                <div v-if="selectedOutput.rendered_user_prompt" class="prompt-section">
                  <span class="prompt-label">User:</span>
                  <pre class="prompt-pre">{{ selectedOutput.rendered_user_prompt }}</pre>
                </div>
                <div v-if="!selectedOutput.rendered_system_prompt && !selectedOutput.rendered_user_prompt" class="text-medium-emphasis">
                  {{ $t('generation.detail.noPromptData') }}
                </div>
              </div>

              <!-- Right: Generated Content -->
              <div class="output-column">
                <h4 class="column-title">
                  <LIcon size="18" class="mr-1">mdi-arrow-left-circle</LIcon>
                  {{ $t('generation.detail.generatedContent') }}
                </h4>
                <div v-if="selectedOutput.generated_content" class="output-full-content">
                  <pre class="content-pre">{{ selectedOutput.generated_content }}</pre>
                </div>
                <div v-else-if="selectedOutput.error_message" class="output-error">
                  <pre class="error-pre">{{ selectedOutput.error_message }}</pre>
                </div>
                <div v-else class="text-medium-emphasis">
                  {{ $t('generation.detail.noContent') }}
                </div>
              </div>
            </div>
          </template>
        </div>

        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showOutputDialog = false">
            {{ $t('common.close') }}
          </LBtn>
        </v-card-actions>
      </LCard>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMobile } from '@/composables/useMobile'
import { useGeneration, JOB_STATUS, OUTPUT_STATUS } from '@/composables/useGeneration'
import { getSocket } from '@/services/socketService'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isMobile } = useMobile()

// Socket.IO instance
let socket = null

// Generation composable
const {
  currentJob,
  outputs,
  outputsPagination,
  isLoading,
  isLoadingOutputs,
  loadJob,
  loadOutputs,
  loadOutput,
  startJob,
  pauseJob,
  cancelJob,
  downloadCsv,
  downloadJson
} = useGeneration()

// Local state
const outputFilter = ref(null)
const outputsPage = ref(1)
const showOutputDialog = ref(false)
const selectedOutput = ref(null)
const isLoadingOutput = ref(false)

// Real-time streaming state
const currentlyProcessing = ref(null)  // { model: 'gpt-4', outputId: 123, content: 'Streaming...' }
const streamingContent = ref('')  // Current streaming content

// Auto-scroll refs
const streamingContentRef = ref(null)
const outputsListRef = ref(null)

// Computed
const jobId = computed(() => Number(route.params.jobId))

const jobConfig = computed(() => currentJob.value?.config || {})

const progressPercent = computed(() => {
  if (!currentJob.value?.progress?.total) return 0
  return Math.round(((currentJob.value.progress.completed || 0) / currentJob.value.progress.total) * 100)
})

const statusConfig = computed(() => {
  const status = currentJob.value?.status
  const configs = {
    [JOB_STATUS.CREATED]: { icon: 'mdi-clock-outline', color: 'grey', label: t('generation.status.created') },
    [JOB_STATUS.QUEUED]: { icon: 'mdi-timer-sand', color: 'info', label: t('generation.status.queued') },
    [JOB_STATUS.RUNNING]: { icon: 'mdi-play-circle', color: 'primary', label: t('generation.status.running') },
    [JOB_STATUS.PAUSED]: { icon: 'mdi-pause-circle', color: 'warning', label: t('generation.status.paused') },
    [JOB_STATUS.COMPLETED]: { icon: 'mdi-check-circle', color: 'success', label: t('generation.status.completed') },
    [JOB_STATUS.FAILED]: { icon: 'mdi-alert-circle', color: 'error', label: t('generation.status.failed') },
    [JOB_STATUS.CANCELLED]: { icon: 'mdi-cancel', color: 'grey', label: t('generation.status.cancelled') }
  }
  return configs[status] || configs[JOB_STATUS.CREATED]
})

const statusIcon = computed(() => statusConfig.value.icon)
const statusColor = computed(() => statusConfig.value.color)
const statusLabel = computed(() => statusConfig.value.label)

// Source info
const sourceType = computed(() => jobConfig.value?.sources?.type || 'unknown')

const sourceLabel = computed(() => {
  const labels = {
    scenario: t('generation.wizard.step1.scenarioSource'),
    manual: t('generation.wizard.step1.manualSource'),
    prompt_only: t('generation.wizard.step1.promptOnlySource')
  }
  return labels[sourceType.value] || sourceType.value
})

const sourceIcon = computed(() => {
  const icons = {
    scenario: 'mdi-clipboard-text-outline',
    manual: 'mdi-file-upload-outline',
    prompt_only: 'mdi-text-box-multiple-outline'
  }
  return icons[sourceType.value] || 'mdi-help'
})

const sourceVariant = computed(() => {
  const variants = {
    scenario: 'primary',
    manual: 'accent',
    prompt_only: 'secondary'
  }
  return variants[sourceType.value] || 'info'
})

// Action availability
const canStart = computed(() =>
  currentJob.value?.status === JOB_STATUS.CREATED ||
  currentJob.value?.status === JOB_STATUS.PAUSED
)

const canPause = computed(() =>
  currentJob.value?.status === JOB_STATUS.RUNNING
)

// Check if job is actively running
const isJobRunning = computed(() =>
  currentJob.value?.status === JOB_STATUS.RUNNING ||
  currentJob.value?.status === JOB_STATUS.QUEUED
)

const canCancel = computed(() =>
  currentJob.value?.status === JOB_STATUS.RUNNING ||
  currentJob.value?.status === JOB_STATUS.PAUSED
)

const canCreateScenario = computed(() =>
  currentJob.value?.status === JOB_STATUS.COMPLETED &&
  (currentJob.value?.progress?.completed || 0) > 0
)

// Methods
function goBack() {
  router.push({ name: 'GenerationHub' })
}

async function handleStart() {
  await startJob(jobId.value)
  await loadJob(jobId.value)
}

async function handlePause() {
  await pauseJob(jobId.value)
  await loadJob(jobId.value)
}

async function handleCancel() {
  await cancelJob(jobId.value)
  await loadJob(jobId.value)
}

function handleExportCsv() {
  downloadCsv(jobId.value, { include_prompts: false })
}

function handleExportJson() {
  downloadJson(jobId.value, { include_prompts: true })
}

function handlePageChange(page) {
  loadOutputs(jobId.value, { page, status: outputFilter.value })
}

async function selectOutput(output) {
  showOutputDialog.value = true
  isLoadingOutput.value = true
  selectedOutput.value = output  // Show basic info immediately

  // Load full details with prompts
  const fullOutput = await loadOutput(output.id)
  if (fullOutput) {
    selectedOutput.value = fullOutput
  }
  isLoadingOutput.value = false
}

function getOutputStatusIcon(status) {
  const icons = {
    [OUTPUT_STATUS.PENDING]: 'mdi-clock-outline',
    [OUTPUT_STATUS.PROCESSING]: 'mdi-loading',
    [OUTPUT_STATUS.COMPLETED]: 'mdi-check',
    [OUTPUT_STATUS.FAILED]: 'mdi-alert',
    [OUTPUT_STATUS.RETRYING]: 'mdi-refresh',
    [OUTPUT_STATUS.SKIPPED]: 'mdi-skip-next'
  }
  return icons[status] || 'mdi-help'
}

function getOutputStatusColor(status) {
  const colors = {
    [OUTPUT_STATUS.PENDING]: 'grey',
    [OUTPUT_STATUS.PROCESSING]: 'primary',
    [OUTPUT_STATUS.COMPLETED]: 'success',
    [OUTPUT_STATUS.FAILED]: 'error',
    [OUTPUT_STATUS.RETRYING]: 'warning',
    [OUTPUT_STATUS.SKIPPED]: 'grey'
  }
  return colors[status] || 'grey'
}

function getOutputStatusVariant(status) {
  const variants = {
    [OUTPUT_STATUS.COMPLETED]: 'success',
    [OUTPUT_STATUS.FAILED]: 'danger',
    [OUTPUT_STATUS.RETRYING]: 'warning'
  }
  return variants[status] || 'info'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function openScenarioWizard() {
  // Navigate to Scenario Manager with the generation job ID
  // The wizard will open automatically and load the generated outputs
  router.push({
    name: 'ScenarioManager',
    query: { fromGeneration: jobId.value }
  })
}

// Watch for filter changes
watch(outputFilter, () => {
  outputsPage.value = 1
  loadOutputs(jobId.value, { page: 1, status: outputFilter.value })
})

// Auto-scroll streaming content when new tokens arrive
watch(streamingContent, () => {
  if (streamingContentRef.value) {
    // Use nextTick to ensure DOM is updated before scrolling
    // Store ref locally to avoid null issues in setTimeout callback
    const el = streamingContentRef.value
    setTimeout(() => {
      if (el) el.scrollTop = el.scrollHeight
    }, 0)
  }
})

// Auto-scroll outputs list when new items are added
watch(outputs, () => {
  if (outputsListRef.value) {
    const el = outputsListRef.value
    setTimeout(() => {
      if (el) el.scrollTop = el.scrollHeight
    }, 100)
  }
}, { deep: true })

// =============================================================================
// Socket.IO Event Handlers
// =============================================================================

function setupSocketListeners() {
  socket = getSocket()
  console.log('[Generation] Setting up socket listeners for job', jobId.value, 'socket connected:', socket.connected)

  // Debug: log all incoming events
  socket.onAny((eventName, ...args) => {
    if (eventName.startsWith('generation:')) {
      console.log('[Generation] Received event:', eventName, args)
    }
  })

  // Job started
  socket.on('generation:job:started', (data) => {
    console.log('[Generation] job:started', data)
    if (data.job_id === jobId.value) {
      loadJob(jobId.value)
    }
  })

  // Progress update (no full reload, just update progress values)
  socket.on('generation:job:progress', (data) => {
    console.log('[Generation] job:progress', data)
    if (data.job_id === jobId.value && currentJob.value) {
      // Update progress without full reload
      currentJob.value.progress = {
        total: data.total,
        completed: data.completed,
        failed: data.failed,
        percent: data.percent
      }
      currentJob.value.cost = {
        ...currentJob.value.cost,
        total_cost_usd: data.cost_usd
      }
    }
  })

  // Item started processing
  socket.on('generation:item:started', (data) => {
    console.log('[Generation] item:started', data)
    if (data.job_id === jobId.value) {
      const itemLabel = data.prompt_variant
        ? `${data.prompt_variant} (Item #${data.source_item_id || data.output_id})`
        : `Item #${data.source_item_id || data.output_id}`
      currentlyProcessing.value = {
        model: data.model_name,
        outputId: data.output_id,
        itemName: itemLabel
      }
      streamingContent.value = ''
    }
  })

  // Streaming token received
  socket.on('generation:item:token', (data) => {
    // Don't log every token, just append
    if (data.job_id === jobId.value && data.output_id === currentlyProcessing.value?.outputId) {
      streamingContent.value += data.token
    }
  })

  // Item completed
  socket.on('generation:item:completed', (data) => {
    if (data.job_id === jobId.value) {
      // Clear processing state if this was the current item
      if (currentlyProcessing.value?.outputId === data.output_id) {
        currentlyProcessing.value = null
        streamingContent.value = ''
      }
      // Update the output locally if it exists in the list
      const output = outputs.value.find(o => o.id === data.output_id)
      if (output) {
        output.status = 'COMPLETED'
        output.generated_content = data.content_preview
        output.input_tokens = data.tokens?.input || 0
        output.output_tokens = data.tokens?.output || 0
        output.total_cost_usd = data.cost_usd || 0
      }
      // Don't reload - just update locally to avoid page refresh
    }
  })

  // Item failed
  socket.on('generation:item:failed', (data) => {
    if (data.job_id === jobId.value) {
      if (currentlyProcessing.value?.outputId === data.output_id) {
        currentlyProcessing.value = null
        streamingContent.value = ''
      }
      // Update the output locally if it exists in the list
      const output = outputs.value.find(o => o.id === data.output_id)
      if (output) {
        output.status = 'FAILED'
        output.error_message = data.error || 'Unknown error'
      }
      // Don't reload - just update locally to avoid page refresh
    }
  })

  // Job completed
  socket.on('generation:job:completed', (data) => {
    if (data.job_id === jobId.value) {
      currentlyProcessing.value = null
      streamingContent.value = ''
      loadJob(jobId.value)
      loadOutputs(jobId.value)
    }
  })

  // Job failed
  socket.on('generation:job:failed', (data) => {
    if (data.job_id === jobId.value) {
      currentlyProcessing.value = null
      streamingContent.value = ''
      loadJob(jobId.value)
    }
  })

  // Budget exceeded
  socket.on('generation:job:budget_exceeded', (data) => {
    if (data.job_id === jobId.value) {
      currentlyProcessing.value = null
      loadJob(jobId.value)
    }
  })
}

function cleanupSocketListeners() {
  if (socket) {
    socket.offAny()  // Remove the debug listener
    socket.off('generation:job:started')
    socket.off('generation:job:progress')
    socket.off('generation:item:started')
    socket.off('generation:item:token')
    socket.off('generation:item:completed')
    socket.off('generation:item:failed')
    socket.off('generation:job:completed')
    socket.off('generation:job:failed')
    socket.off('generation:job:budget_exceeded')
  }
}

// =============================================================================
// Lifecycle
// =============================================================================

onMounted(async () => {
  // Setup Socket.IO listeners FIRST to capture any events during data loading
  // This prevents missing streaming events if the job is already running
  setupSocketListeners()

  await loadJob(jobId.value)
  await loadOutputs(jobId.value)

  // Check if there's a currently processing item (for reconnection support)
  if (currentJob.value?.currently_processing) {
    const cp = currentJob.value.currently_processing
    currentlyProcessing.value = {
      model: cp.model_name,
      outputId: cp.output_id,
      itemName: cp.item_name
    }
    // Load partial content that was streamed before reconnection
    // New tokens will be appended via Socket.IO
    streamingContent.value = cp.partial_content || ''
  }
})

onUnmounted(() => {
  cleanupSocketListeners()
})
</script>

<style scoped>
.job-detail {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

/* Header */
.detail-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.header-info {
  flex: 1;
}

.header-info h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.header-info p {
  margin: 4px 0 0 0;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Content */
.detail-content {
  flex: 1;
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 24px;
  padding: 24px;
  overflow: hidden;
}

/* Info Panel */
.info-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.progress-card {
  padding: 20px;
}

.progress-section {
  margin-top: 16px;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-text {
  font-size: 0.9rem;
  font-weight: 500;
}

.progress-percent {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--llars-primary, #b0ca97);
}

.failed-info {
  display: flex;
  align-items: center;
  margin-top: 8px;
  font-size: 0.85rem;
  color: var(--llars-danger, #e8a087);
}

.processing-info {
  margin-top: 12px;
  padding: 12px;
  background: rgba(var(--v-theme-primary), 0.08);
  border-radius: 8px 3px 8px 3px;
  border-left: 3px solid var(--llars-primary, #b0ca97);
}

.processing-header {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--llars-primary, #b0ca97);
  margin-bottom: 8px;
}

.processing-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  padding: 4px 0;
}

.processing-item .model-name {
  font-weight: 600;
  color: var(--llars-accent, #88c4c8);
}

.processing-item .item-name {
  opacity: 0.7;
  font-size: 0.75rem;
}

/* Streaming Preview */
.streaming-preview {
  margin-bottom: 16px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.08), rgba(var(--v-theme-secondary), 0.05));
  border-radius: 12px 4px 12px 4px;
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.streaming-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.streaming-item-name {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-left: auto;
}

.streaming-content {
  font-family: monospace;
  font-size: 0.85rem;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.streaming-content .cursor {
  animation: blink 1s infinite;
  color: var(--llars-primary, #b0ca97);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 0.9rem;
  font-weight: 500;
}

.stat-value.cost {
  font-family: monospace;
  color: var(--llars-secondary, #d1bc8a);
}

/* Config Card */
.config-card {
  padding: 20px;
}

.config-section {
  margin-top: 16px;
}

.config-section:first-of-type {
  margin-top: 0;
}

.config-section h4 {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
}

.config-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.params-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Outputs Panel */
.outputs-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.outputs-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.outputs-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}

.output-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  cursor: pointer;
  transition: background 0.2s ease;
}

.output-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.02);
  margin: 0 -8px;
  padding: 12px 8px;
}

.output-item:last-child {
  border-bottom: none;
}

.output-item.is-failed {
  background: rgba(var(--v-theme-error), 0.05);
}

.output-status {
  flex-shrink: 0;
  padding-top: 2px;
}

.output-content {
  flex: 1;
  min-width: 0;
}

.output-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.output-item-name {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.output-preview {
  font-size: 0.85rem;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.output-tokens {
  flex-shrink: 0;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-family: monospace;
}

.empty-outputs {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.outputs-pagination {
  padding: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Loading State */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

/* Output Detail */
.output-detail {
  padding: 16px;
}

.output-detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.output-full-content,
.output-error {
  margin-top: 16px;
}

.output-full-content h4,
.output-error h4 {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.content-pre,
.error-pre {
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  font-size: 0.85rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.error-pre {
  background: rgba(var(--v-theme-error), 0.05);
  color: var(--llars-danger, #e8a087);
}

/* Two-column output layout */
.output-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.output-column {
  display: flex;
  flex-direction: column;
  min-width: 0;  /* Prevent overflow */
}

.column-title {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.prompt-section {
  margin-bottom: 12px;
}

.prompt-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 4px;
}

.prompt-pre {
  padding: 12px;
  background: rgba(var(--v-theme-primary), 0.05);
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
  border-radius: 8px 3px 8px 3px;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
}

.output-column .output-full-content {
  margin-top: 0;
}

.output-column .content-pre {
  max-height: 350px;
}

/* Mobile Styles */
.job-detail.is-mobile .detail-header {
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
}

.job-detail.is-mobile .header-info h1 {
  font-size: 1.25rem;
}

.job-detail.is-mobile .header-actions {
  width: 100%;
  flex-wrap: wrap;
}

.job-detail.is-mobile .detail-content {
  grid-template-columns: 1fr;
  padding: 16px;
  overflow-y: auto;
}

.job-detail.is-mobile .info-panel {
  overflow: visible;
}
</style>
