<template>
  <LCard :title="$t('evaluationAssistant.progress.title')" icon="mdi-chart-donut">
    <!-- Status Badge -->
    <template #actions>
      <LTag :variant="statusVariant" size="sm">
        <LIcon size="14" class="mr-1">{{ statusIcon }}</LIcon>
        {{ statusText }}
      </LTag>
    </template>

    <!-- Progress Bar -->
    <div class="progress-bar-container">
      <v-progress-linear
        :model-value="progress.percent"
        :color="progressColor"
        height="8"
        rounded
      />
      <div class="progress-labels">
        <span class="text-caption">{{ progress.completed }} / {{ progress.total }}</span>
        <span class="text-caption font-weight-bold">{{ progress.percent }}%</span>
      </div>
    </div>

    <!-- Statistics -->
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value text-success">{{ progress.completed }}</div>
        <div class="stat-label">{{ $t('evaluationAssistant.progress.completed') }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-warning">{{ progress.pending }}</div>
        <div class="stat-label">{{ $t('evaluationAssistant.progress.pending') }}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-error">{{ progress.failed }}</div>
        <div class="stat-label">{{ $t('evaluationAssistant.progress.failed') }}</div>
      </div>
    </div>

    <!-- Current Evaluation -->
    <div v-if="currentEvaluation" class="current-eval">
      <div class="current-eval-header">
        <LIcon size="16" color="primary" class="mr-2">mdi-robot</LIcon>
        <span class="text-caption font-weight-medium">{{ $t('evaluationAssistant.progress.currentlyEvaluating') }}</span>
      </div>
      <div class="current-eval-info">
        <span class="text-body-2">{{ currentEvaluation.thread_name || `Thread #${currentEvaluation.thread_id}` }}</span>
        <v-progress-circular
          indeterminate
          size="16"
          width="2"
          color="primary"
        />
      </div>
    </div>

    <!-- Token Usage -->
    <div v-if="tokenUsage.total_tokens > 0" class="token-usage">
      <div class="token-usage-header">
        <LIcon size="16" class="mr-2">mdi-currency-usd</LIcon>
        <span class="text-caption font-weight-medium">{{ $t('evaluationAssistant.progress.tokenUsage') }}</span>
      </div>
      <div class="token-usage-stats">
        <div class="token-stat">
          <span class="token-value">{{ formatNumber(tokenUsage.total_tokens) }}</span>
          <span class="token-label">{{ $t('evaluationAssistant.progress.tokens') }}</span>
        </div>
        <div class="token-stat">
          <span class="token-value">${{ tokenUsage.total_cost_usd.toFixed(4) }}</span>
          <span class="token-label">{{ $t('evaluationAssistant.progress.cost') }}</span>
        </div>
      </div>
    </div>
  </LCard>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { EVAL_STATUS } from '@/composables/useLLMEvaluation'

const { t } = useI18n()

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  progress: {
    type: Object,
    default: () => ({ total: 0, completed: 0, pending: 0, failed: 0, percent: 0 })
  },
  currentEvaluation: {
    type: Object,
    default: null
  },
  tokenUsage: {
    type: Object,
    default: () => ({ total_tokens: 0, total_cost_usd: 0, by_model: [] })
  }
})

const statusVariant = computed(() => {
  switch (props.status) {
    case EVAL_STATUS.RUNNING: return 'success'
    case EVAL_STATUS.COMPLETED: return 'info'
    case EVAL_STATUS.ERROR: return 'danger'
    default: return 'gray'
  }
})

const statusIcon = computed(() => {
  switch (props.status) {
    case EVAL_STATUS.RUNNING: return 'mdi-play-circle'
    case EVAL_STATUS.COMPLETED: return 'mdi-check-circle'
    case EVAL_STATUS.ERROR: return 'mdi-alert-circle'
    default: return 'mdi-pause-circle'
  }
})

const statusText = computed(() => {
  return t(`evaluationAssistant.status.${props.status}`)
})

const progressColor = computed(() => {
  if (props.status === EVAL_STATUS.ERROR) return 'error'
  if (props.status === EVAL_STATUS.COMPLETED) return 'success'
  return 'primary'
})

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}
</script>

<style scoped>
.progress-bar-container {
  margin-bottom: 16px;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
}

.current-eval {
  padding: 12px;
  background: rgba(var(--v-theme-primary), 0.08);
  border-radius: 8px;
  border-left: 3px solid rgb(var(--v-theme-primary));
  margin-bottom: 16px;
}

.current-eval-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.current-eval-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.token-usage {
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
}

.token-usage-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.token-usage-stats {
  display: flex;
  gap: 24px;
}

.token-stat {
  display: flex;
  flex-direction: column;
}

.token-value {
  font-size: 1.1rem;
  font-weight: 600;
}

.token-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
</style>
