<template>
  <div class="pipeline-session">
    <!-- Header -->
    <div class="session-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goBack">
        {{ $t('pipeline.backToHub') }}
      </LBtn>

      <div class="header-info" v-if="currentRun">
        <h1 class="header-title">{{ currentRun.name }}</h1>
        <div class="header-meta">
          <LStatusChip :status="statusChipValue" size="small" />
          <span class="meta-text">
            {{ $t('pipeline.iterationLabel', { n: currentRun.current_iteration }) }}
            / {{ currentRun.max_iterations }}
          </span>
          <span class="meta-text">
            {{ $t('pipeline.budget') }}:
            <strong>{{ budgetPercent }}%</strong>
          </span>
        </div>
      </div>

      <div class="header-actions" v-if="currentRun">
        <LBtn
          v-if="currentRun.can_pause"
          variant="secondary"
          size="small"
          @click="pauseRun(currentRun.id)"
        >
          <v-icon start size="16">mdi-pause</v-icon>
          {{ $t('pipeline.pause') }}
        </LBtn>
        <LBtn
          v-if="currentRun.can_start"
          variant="primary"
          size="small"
          @click="startRun(currentRun.id)"
        >
          <v-icon start size="16">mdi-play</v-icon>
          {{ $t('pipeline.start') }}
        </LBtn>
        <LBtn
          v-if="currentRun.can_cancel"
          variant="danger"
          size="small"
          @click="cancelRun(currentRun.id)"
        >
          <v-icon start size="16">mdi-stop</v-icon>
          {{ $t('pipeline.cancel') }}
        </LBtn>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="session-loading">
      <v-skeleton-loader type="card" class="mb-4" />
      <v-skeleton-loader type="card" class="mb-4" />
      <v-skeleton-loader type="card" />
    </div>

    <!-- Content -->
    <div v-else-if="currentRun" class="session-content">
      <!-- Review Panel -->
      <PipelineReviewPanel
        v-if="currentRun.status === RUN_STATUS.WAITING_FOR_REVIEW"
        :best-config="bestConfig"
        class="mb-4"
        @review="handleReview"
      />

      <!-- Configuration Section (collapsible) -->
      <div class="config-section mb-4">
        <div class="section-toggle" @click="configExpanded = !configExpanded">
          <h3 class="section-title mb-0">
            <v-icon size="20" class="mr-2">mdi-cog-outline</v-icon>
            {{ $t('pipeline.session.config') }}
          </h3>
          <v-icon size="20">{{ configExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
        </div>
        <div v-if="configExpanded" class="config-body">
          <!-- Task Spec -->
          <div class="config-row">
            <span class="config-key">{{ $t('pipeline.session.taskSpec') }}</span>
            <span class="config-val">{{ currentRun.config?.task_spec || $t('pipeline.session.noTaskSpec') }}</span>
          </div>

          <!-- Candidate Models -->
          <div v-if="currentRun.candidate_models?.length" class="config-row">
            <span class="config-key">{{ $t('pipeline.session.candidateModels') }}</span>
            <div class="config-tags">
              <LTag v-for="m in currentRun.candidate_models" :key="m" variant="info" size="sm">{{ m }}</LTag>
            </div>
          </div>

          <!-- Eval Model + Meta Model -->
          <div class="config-row-grid">
            <div v-if="configEvalModel" class="config-row">
              <span class="config-key">{{ $t('pipeline.session.evalModel') }}</span>
              <LTag variant="info" size="sm">{{ configEvalModel }}</LTag>
            </div>
            <div v-if="configMetaModel" class="config-row">
              <span class="config-key">{{ $t('pipeline.session.metaModel') }}</span>
              <LTag variant="info" size="sm">{{ configMetaModel }}</LTag>
            </div>
          </div>

          <!-- Thresholds -->
          <div v-if="currentRun.config?.thresholds" class="config-row">
            <span class="config-key">{{ $t('pipeline.session.thresholds') }}</span>
            <div class="threshold-list">
              <div v-if="configGlobalThreshold != null" class="threshold-item">
                <span class="threshold-dim">{{ $t('pipeline.session.globalThreshold') }}</span>
                <span class="threshold-val">{{ configGlobalThreshold }}</span>
              </div>
              <div
                v-for="(val, dimId) in configDimThresholds"
                :key="dimId"
                class="threshold-item"
              >
                <span class="threshold-dim">{{ dimId }}</span>
                <span class="threshold-val">{{ val }}</span>
              </div>
            </div>
          </div>

          <!-- Token Budget + Max Iterations -->
          <div class="config-row-grid">
            <div v-if="currentRun.config?.budget_tokens" class="config-row">
              <span class="config-key">{{ $t('pipeline.session.tokenBudget') }}</span>
              <span class="config-val">{{ currentRun.config.budget_tokens.toLocaleString() }}</span>
            </div>
            <div class="config-row">
              <span class="config-key">{{ $t('pipeline.session.maxIterations') }}</span>
              <span class="config-val">{{ currentRun.max_iterations }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Live Phase -->
      <PipelineLivePhase
        v-if="livePhase"
        :live-phase="livePhase"
        class="mb-4"
      />

      <!-- Timeline of iterations -->
      <div class="timeline-section">
        <h3 class="section-title">
          <v-icon size="20" class="mr-2">mdi-timeline-text</v-icon>
          {{ $t('pipeline.iterations') }}
        </h3>
        <div class="timeline">
          <PipelineIterationCard
            v-for="it in sortedIterations"
            :key="it.iteration_number"
            :iteration="it"
            :is-live="livePhase && livePhase.iteration === it.iteration_number"
            :live-phase="livePhase && livePhase.iteration === it.iteration_number ? livePhase : null"
            :thresholds="currentRun.config?.thresholds"
          />
        </div>
        <div v-if="!iterations.length && !livePhase" class="no-iterations">
          {{ $t('pipeline.noIterationsYet') }}
        </div>
      </div>

      <!-- Score Chart -->
      <div v-if="scoreHistory.length > 0" class="chart-section">
        <h3 class="section-title">
          <v-icon size="20" class="mr-2">mdi-chart-line</v-icon>
          {{ $t('pipeline.scoreChart') }}
        </h3>
        <PipelineScoreChart
          :score-history="scoreHistory"
          :thresholds="currentRun.config?.thresholds"
        />
      </div>

      <!-- Best Config -->
      <div v-if="bestConfig" class="best-section">
        <h3 class="section-title">
          <v-icon size="20" class="mr-2" color="success">mdi-trophy</v-icon>
          {{ $t('pipeline.bestSetup') }}
        </h3>
        <div class="best-card">
          <!-- Stats row -->
          <div class="best-stats-row">
            <div class="best-stat">
              <span class="best-label">{{ $t('pipeline.avgScore') }}</span>
              <span class="best-value">{{ bestConfig.avg_score?.toFixed(2) || '—' }} / 5.00</span>
            </div>
            <div class="best-stat">
              <span class="best-label">{{ $t('pipeline.iteration') }}</span>
              <span class="best-value">{{ bestConfig.iteration || '—' }}</span>
            </div>
          </div>

          <!-- Dimension scores with threshold comparison -->
          <div v-if="bestConfig.dimension_scores && Object.keys(bestConfig.dimension_scores).length" class="best-dimensions">
            <div class="best-dim-header">{{ $t('pipeline.session.dimensions') }}</div>
            <table class="dim-table">
              <thead>
                <tr>
                  <th>{{ $t('pipeline.session.dimension') }}</th>
                  <th>{{ $t('pipeline.session.score') }}</th>
                  <th>{{ $t('pipeline.threshold') }}</th>
                  <th>{{ $t('pipeline.session.status') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(score, dimId) in bestConfig.dimension_scores" :key="dimId">
                  <td>{{ dimId }}</td>
                  <td class="score-cell">{{ score.toFixed(2) }}</td>
                  <td class="threshold-cell">{{ getDimThreshold(dimId) ?? '—' }}</td>
                  <td>
                    <v-icon
                      v-if="getDimThreshold(dimId) != null"
                      :color="score >= getDimThreshold(dimId) ? 'success' : 'error'"
                      size="18"
                    >
                      {{ score >= getDimThreshold(dimId) ? 'mdi-check-circle' : 'mdi-close-circle' }}
                    </v-icon>
                    <span v-else class="dim-na">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Best prompt variants -->
          <div v-if="bestConfig.prompt_variants?.length" class="best-prompts">
            <div class="best-dim-header">{{ $t('pipeline.session.bestPrompts') }}</div>
            <div v-for="(pv, idx) in bestConfig.prompt_variants" :key="idx" class="prompt-variant-block">
              <div class="prompt-variant-name">{{ pv.variant_name || pv.name || `Variant ${idx + 1}` }}</div>
              <div v-if="pv.system_prompt" class="prompt-section">
                <span class="prompt-label">{{ $t('pipeline.session.systemPrompt') }}</span>
                <pre class="prompt-code">{{ pv.system_prompt }}</pre>
              </div>
              <div v-if="pv.user_prompt_template || pv.user_template" class="prompt-section">
                <span class="prompt-label">{{ $t('pipeline.session.userTemplate') }}</span>
                <pre class="prompt-code">{{ pv.user_prompt_template || pv.user_template }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-else class="session-error">
      <v-icon size="48" color="error">mdi-alert-circle-outline</v-icon>
      <p>{{ error || $t('pipeline.notFound') }}</p>
      <LBtn variant="primary" @click="goBack">{{ $t('pipeline.backToHub') }}</LBtn>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePipeline, RUN_STATUS } from './composables/usePipeline'
import PipelineIterationCard from './components/PipelineIterationCard.vue'
import PipelineScoreChart from './components/PipelineScoreChart.vue'
import PipelineLivePhase from './components/PipelineLivePhase.vue'
import PipelineReviewPanel from './components/PipelineReviewPanel.vue'
import LBtn from '@/components/common/LBtn.vue'
import LStatusChip from '@/components/common/LStatusChip.vue'
import LTag from '@/components/common/LTag.vue'

const props = defineProps({
  runId: { type: [Number, String], required: true },
})

const router = useRouter()
const { t } = useI18n()

const configExpanded = ref(true)

const {
  currentRun,
  iterations,
  livePhase,
  isLoading,
  error,
  isRunActive,
  budgetPercent,
  bestConfig,
  scoreHistory,
  startRun,
  pauseRun,
  cancelRun,
  submitReview,
} = usePipeline({ watchRunId: Number(props.runId) })

const sortedIterations = computed(() => {
  return [...iterations.value].sort((a, b) => a.iteration_number - b.iteration_number)
})

const statusChipValue = computed(() => {
  if (!currentRun.value) return 'pending'
  const map = {
    created: 'pending',
    running: 'active',
    paused: 'warning',
    waiting_for_review: 'warning',
    completed: 'done',
    failed: 'error',
    cancelled: 'inactive',
  }
  return map[currentRun.value.status] || 'pending'
})

// Config field helpers — support both naming conventions
const configEvalModel = computed(() => {
  const c = currentRun.value?.config
  return c?.eval_model_id || c?.eval_model || null
})

const configMetaModel = computed(() => {
  const c = currentRun.value?.config
  return c?.meta_model_id || c?.meta_model || null
})

const configGlobalThreshold = computed(() => {
  const t = currentRun.value?.config?.thresholds
  if (!t) return null
  return t.global_threshold ?? t.global ?? null
})

const configDimThresholds = computed(() => {
  const t = currentRun.value?.config?.thresholds
  if (!t) return {}
  return t.dimension_thresholds || t.dimensions || {}
})

function getDimThreshold(dimId) {
  const t = currentRun.value?.config?.thresholds
  if (!t) return null
  const dims = t.dimension_thresholds || t.dimensions || {}
  return dims[dimId] ?? t.global_threshold ?? t.global ?? null
}

function goBack() {
  router.push({ name: 'PipelineHub' })
}

function handleReview(decision) {
  submitReview(Number(props.runId), decision)
}
</script>

<style scoped>
.pipeline-session {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.session-header {
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

.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.meta-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.session-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.session-loading {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.timeline-section {
  margin-bottom: 24px;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.no-iterations {
  padding: 32px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.85rem;
}

.chart-section {
  margin-bottom: 24px;
}

.best-section {
  margin-bottom: 24px;
}

/* Configuration Section */
.config-section {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 3px 12px 3px;
  overflow: hidden;
}

.section-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.section-toggle:hover {
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.config-body {
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  padding-top: 12px;
}

.config-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-row-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.config-key {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  font-weight: 600;
}

.config-val {
  font-size: 0.85rem;
  line-height: 1.4;
}

.config-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.threshold-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.threshold-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 4px;
  font-size: 0.8rem;
}

.threshold-dim {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.threshold-val {
  font-weight: 600;
}

/* Best Config */
.best-card {
  padding: 16px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-success), 0.2);
  border-radius: 12px 3px 12px 3px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.best-stats-row {
  display: flex;
  gap: 24px;
}

.best-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.best-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.best-value {
  font-size: 1rem;
  font-weight: 700;
}

.best-dimensions {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  padding-top: 12px;
}

.best-dim-header {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  font-weight: 600;
  margin-bottom: 8px;
}

.dim-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

.dim-table th {
  text-align: left;
  font-weight: 600;
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  padding: 4px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.dim-table td {
  padding: 6px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.score-cell {
  font-weight: 600;
}

.threshold-cell {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.dim-na {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.best-prompts {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  padding-top: 12px;
}

.prompt-variant-block {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.prompt-variant-name {
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.prompt-section {
  margin-bottom: 8px;
}

.prompt-section:last-child {
  margin-bottom: 0;
}

.prompt-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  font-weight: 600;
  display: block;
  margin-bottom: 4px;
}

.prompt-code {
  font-size: 0.75rem;
  line-height: 1.5;
  background: rgba(var(--v-theme-on-surface), 0.04);
  padding: 8px 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}

.session-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  text-align: center;
}

@media (max-width: 768px) {
  .session-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .best-stats-row {
    flex-direction: column;
    gap: 12px;
  }

  .config-row-grid {
    grid-template-columns: 1fr;
  }
}
</style>
