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
          <div class="best-stat">
            <span class="best-label">{{ $t('pipeline.avgScore') }}</span>
            <span class="best-value">{{ bestConfig.avg_score?.toFixed(2) || '—' }} / 5.00</span>
          </div>
          <div class="best-stat">
            <span class="best-label">{{ $t('pipeline.iteration') }}</span>
            <span class="best-value">{{ bestConfig.iteration || '—' }}</span>
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePipeline, RUN_STATUS } from './composables/usePipeline'
import PipelineIterationCard from './components/PipelineIterationCard.vue'
import PipelineScoreChart from './components/PipelineScoreChart.vue'
import PipelineLivePhase from './components/PipelineLivePhase.vue'
import PipelineReviewPanel from './components/PipelineReviewPanel.vue'
import LBtn from '@/components/common/LBtn.vue'
import LStatusChip from '@/components/common/LStatusChip.vue'

const props = defineProps({
  runId: { type: [Number, String], required: true },
})

const router = useRouter()
const { t } = useI18n()

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

.best-card {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-success), 0.2);
  border-radius: 12px 3px 12px 3px;
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

  .best-card {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
