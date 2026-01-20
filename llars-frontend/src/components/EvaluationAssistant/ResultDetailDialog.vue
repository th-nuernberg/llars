<template>
  <v-card class="result-detail-dialog">
    <!-- Header -->
    <v-card-title class="dialog-header">
      <div class="header-content">
        <div class="evaluator-info">
          <div class="evaluator-icon" :class="result.is_llm_evaluation ? 'llm' : 'human'">
            <LIcon size="24">{{ result.is_llm_evaluation ? 'mdi-robot' : 'mdi-account' }}</LIcon>
          </div>
          <div>
            <div class="evaluator-name">
              {{ result.evaluator_name || (result.is_llm_evaluation ? result.model_id : `User #${result.user_id}`) }}
            </div>
            <div class="evaluation-meta">
              {{ $t(`evaluationAssistant.taskTypes.${result.task_type}`) }} |
              {{ formatDate(result.created_at) }}
            </div>
          </div>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="$emit('close')" />
      </div>
    </v-card-title>

    <v-divider />

    <v-card-text class="dialog-content">
      <!-- Thread Info -->
      <div class="section">
        <div class="section-title">
          <LIcon size="18" class="mr-2">mdi-email-outline</LIcon>
          {{ $t('evaluationAssistant.detail.thread') }}
        </div>
        <div class="thread-info-card">
          <div class="thread-name">{{ result.thread_name || `Thread #${result.thread_id}` }}</div>
          <div class="thread-id">ID: {{ result.thread_id }}</div>
        </div>
      </div>

      <!-- Confidence -->
      <div v-if="result.confidence" class="section">
        <div class="section-title">
          <LIcon size="18" class="mr-2">mdi-brain</LIcon>
          {{ $t('evaluationAssistant.detail.confidence') }}
        </div>
        <div class="confidence-display">
          <v-progress-linear
            :model-value="result.confidence * 100"
            color="primary"
            height="12"
            rounded
          />
          <span class="confidence-value">{{ (result.confidence * 100).toFixed(1) }}%</span>
        </div>
      </div>

      <!-- Main Result -->
      <div class="section">
        <div class="section-title">
          <LIcon size="18" class="mr-2">mdi-clipboard-check</LIcon>
          {{ $t('evaluationAssistant.detail.result') }}
        </div>
        <div class="result-content">
          <!-- Task-specific result rendering -->
          <component :is="resultComponent" :result="result" />
        </div>
      </div>

      <!-- Reasoning -->
      <div v-if="result.reasoning" class="section">
        <div class="section-title">
          <LIcon size="18" class="mr-2">mdi-lightbulb</LIcon>
          {{ $t('evaluationAssistant.detail.reasoning') }}
        </div>
        <div class="reasoning-content">{{ result.reasoning }}</div>
      </div>

      <!-- Meta Information -->
      <div v-if="result.is_llm_evaluation" class="section">
        <div class="section-title">
          <LIcon size="18" class="mr-2">mdi-information</LIcon>
          {{ $t('evaluationAssistant.detail.meta') }}
        </div>
        <div class="meta-grid">
          <div class="meta-item">
            <span class="meta-label">{{ $t('evaluationAssistant.detail.model') }}</span>
            <span class="meta-value">{{ result.model_id }}</span>
          </div>
          <div v-if="result.prompt_template_id" class="meta-item">
            <span class="meta-label">{{ $t('evaluationAssistant.detail.template') }}</span>
            <span class="meta-value">Template #{{ result.prompt_template_id }}</span>
          </div>
          <div v-if="result.token_usage" class="meta-item">
            <span class="meta-label">{{ $t('evaluationAssistant.detail.tokens') }}</span>
            <span class="meta-value">
              {{ result.token_usage.input_tokens }} + {{ result.token_usage.output_tokens }}
            </span>
          </div>
          <div v-if="result.token_usage?.cost_usd" class="meta-item">
            <span class="meta-label">{{ $t('evaluationAssistant.detail.cost') }}</span>
            <span class="meta-value">${{ result.token_usage.cost_usd.toFixed(6) }}</span>
          </div>
          <div v-if="result.processing_time_ms" class="meta-item">
            <span class="meta-label">{{ $t('evaluationAssistant.detail.processingTime') }}</span>
            <span class="meta-value">{{ (result.processing_time_ms / 1000).toFixed(2) }}s</span>
          </div>
        </div>
      </div>

      <!-- Raw JSON (for debugging) -->
      <v-expansion-panels variant="accordion" class="mt-4">
        <v-expansion-panel>
          <v-expansion-panel-title>
            <LIcon size="18" class="mr-2">mdi-code-json</LIcon>
            {{ $t('evaluationAssistant.detail.rawData') }}
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <pre class="json-display">{{ JSON.stringify(result, null, 2) }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card-text>

    <v-divider />

    <v-card-actions>
      <v-spacer />
      <LBtn variant="text" @click="$emit('close')">
        {{ $t('common.close') }}
      </LBtn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

defineEmits(['close'])

// Lazy load task-specific result components
const RankingResult = defineAsyncComponent(() => import('./detail/RankingResult.vue'))
const RatingResult = defineAsyncComponent(() => import('./detail/RatingResult.vue'))
const AuthenticityResult = defineAsyncComponent(() => import('./detail/AuthenticityResult.vue'))
const ComparisonResult = defineAsyncComponent(() => import('./detail/ComparisonResult.vue'))
const ClassificationResult = defineAsyncComponent(() => import('./detail/ClassificationResult.vue'))
const MailRatingResult = defineAsyncComponent(() => import('./detail/MailRatingResult.vue'))
const GenericResult = defineAsyncComponent(() => import('./detail/GenericResult.vue'))

const resultComponent = computed(() => {
  switch (props.result.task_type) {
    case 'ranking': return RankingResult
    case 'rating': return RatingResult
    case 'authenticity': return AuthenticityResult
    case 'comparison': return ComparisonResult
    case 'text_classification':
    case 'labeling':
      return ClassificationResult
    case 'mail_rating': return MailRatingResult
    default: return GenericResult
  }
})

function formatDate(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString()
}
</script>

<style scoped>
.result-detail-dialog {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  flex-shrink: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.evaluator-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.evaluator-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.evaluator-icon.llm {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.evaluator-icon.human {
  background: rgba(var(--v-theme-secondary), 0.15);
  color: rgb(var(--v-theme-secondary));
}

.evaluator-name {
  font-weight: 600;
  font-size: 1.1rem;
}

.evaluation-meta {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 8px;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.thread-info-card {
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
}

.thread-name {
  font-weight: 500;
}

.thread-id {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.confidence-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.confidence-value {
  font-weight: 600;
  min-width: 50px;
}

.result-content {
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
}

.reasoning-content {
  padding: 16px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-left: 3px solid rgb(var(--v-theme-primary));
  border-radius: 0 8px 8px 0;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px;
}

.meta-label {
  font-size: 0.625rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  margin-bottom: 2px;
}

.meta-value {
  font-weight: 500;
  font-size: 0.875rem;
}

.json-display {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px;
  overflow-x: auto;
  white-space: pre-wrap;
}
</style>
