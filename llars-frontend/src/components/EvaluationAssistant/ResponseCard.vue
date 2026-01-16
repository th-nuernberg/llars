<template>
  <div class="response-card" :class="{ expanded }">
    <!-- Card Header -->
    <div class="card-header" @click="$emit('toggle')">
      <div class="header-left">
        <!-- Evaluator Type Icon -->
        <div class="evaluator-icon" :class="evaluatorClass">
          <LIcon size="20">{{ result.is_llm_evaluation ? 'mdi-robot' : 'mdi-account' }}</LIcon>
        </div>

        <!-- Basic Info -->
        <div class="header-info">
          <div class="evaluator-name">
            {{ result.evaluator_name || (result.is_llm_evaluation ? result.model_id : `User #${result.user_id}`) }}
          </div>
          <div class="thread-name text-caption text-medium-emphasis">
            {{ result.thread_name || `Thread #${result.thread_id}` }}
          </div>
        </div>
      </div>

      <div class="header-right">
        <!-- Result Summary -->
        <div class="result-summary">
          <ResultBadge :result="result" />
        </div>

        <!-- Confidence -->
        <div v-if="result.confidence" class="confidence">
          <LTooltip :text="$t('evaluationAssistant.responseCard.confidenceTooltip')">
            <div class="confidence-value">
              <LIcon size="14" class="mr-1">mdi-brain</LIcon>
              {{ (result.confidence * 100).toFixed(0) }}%
            </div>
          </LTooltip>
        </div>

        <!-- Timestamp -->
        <div class="timestamp text-caption text-medium-emphasis">
          {{ formatTime(result.created_at) }}
        </div>

        <!-- Expand Icon -->
        <LIcon class="expand-icon" :class="{ rotated: expanded }">
          mdi-chevron-down
        </LIcon>
      </div>
    </div>

    <!-- Expanded Content -->
    <v-expand-transition>
      <div v-show="expanded" class="card-content">
        <!-- Reasoning Section -->
        <div v-if="result.reasoning" class="content-section">
          <div class="section-header">
            <LIcon size="16" class="mr-2">mdi-lightbulb-outline</LIcon>
            <span>{{ $t('evaluationAssistant.responseCard.reasoning') }}</span>
          </div>
          <div class="reasoning-text">{{ result.reasoning }}</div>
        </div>

        <!-- Detailed Result based on task type -->
        <div class="content-section">
          <div class="section-header">
            <LIcon size="16" class="mr-2">mdi-format-list-bulleted</LIcon>
            <span>{{ $t('evaluationAssistant.responseCard.detailedResult') }}</span>
          </div>

          <!-- Ranking Result -->
          <div v-if="result.task_type === 'ranking'" class="result-detail ranking-detail">
            <div v-for="(bucket, name) in result.buckets" :key="name" class="bucket">
              <div class="bucket-header" :class="`bucket-${name}`">
                <LIcon size="16" class="mr-1">{{ getBucketIcon(name) }}</LIcon>
                {{ $t(`evaluationAssistant.buckets.${name}`) }}
                <span class="bucket-count">({{ bucket.feature_ids?.length || 0 }})</span>
              </div>
              <div v-if="bucket.reasoning" class="bucket-reasoning">
                {{ bucket.reasoning }}
              </div>
            </div>
          </div>

          <!-- Rating Result -->
          <div v-else-if="result.task_type === 'rating'" class="result-detail rating-detail">
            <div v-for="rating in result.ratings" :key="rating.feature_id" class="rating-item">
              <div class="rating-header">
                <span class="feature-label">Feature #{{ rating.feature_id }}</span>
                <div class="rating-stars">
                  <LIcon
                    v-for="star in 5"
                    :key="star"
                    size="16"
                    :color="star <= rating.rating ? '#FFB300' : 'grey'"
                  >
                    {{ star <= rating.rating ? 'mdi-star' : 'mdi-star-outline' }}
                  </LIcon>
                </div>
              </div>
              <div v-if="rating.reasoning" class="rating-reasoning">
                {{ rating.reasoning }}
              </div>
              <div v-if="rating.strengths?.length" class="rating-attributes">
                <span class="attr-label text-success">+</span>
                <span v-for="(s, i) in rating.strengths" :key="i" class="attr-item">{{ s }}</span>
              </div>
              <div v-if="rating.weaknesses?.length" class="rating-attributes">
                <span class="attr-label text-error">-</span>
                <span v-for="(w, i) in rating.weaknesses" :key="i" class="attr-item">{{ w }}</span>
              </div>
            </div>
          </div>

          <!-- Authenticity Result -->
          <div v-else-if="result.task_type === 'authenticity'" class="result-detail authenticity-detail">
            <div class="vote-display">
              <LTag :variant="result.vote === 'real' ? 'success' : 'danger'" size="lg">
                <LIcon size="18" class="mr-1">{{ result.vote === 'real' ? 'mdi-check-circle' : 'mdi-alert-circle' }}</LIcon>
                {{ $t(`evaluationAssistant.votes.${result.vote}`) }}
              </LTag>
              <div class="confidence-score">
                {{ $t('evaluationAssistant.responseCard.confidenceScore') }}: {{ result.confidence_score }}/5
              </div>
            </div>
            <div v-if="result.indicators?.length" class="indicators-list">
              <div class="section-subheader">{{ $t('evaluationAssistant.responseCard.indicators') }}</div>
              <div v-for="(ind, i) in result.indicators" :key="i" class="indicator-item">
                <LIcon size="14" :color="ind.supports === 'real' ? 'success' : 'error'" class="mr-1">
                  {{ ind.supports === 'real' ? 'mdi-thumb-up' : 'mdi-thumb-down' }}
                </LIcon>
                <span>{{ ind.indicator }}</span>
                <span class="indicator-weight">({{ (ind.weight * 100).toFixed(0) }}%)</span>
              </div>
            </div>
            <div v-if="result.linguistic_analysis" class="analysis-section">
              <div class="section-subheader">{{ $t('evaluationAssistant.responseCard.linguisticAnalysis') }}</div>
              <p>{{ result.linguistic_analysis }}</p>
            </div>
            <div v-if="result.behavioral_analysis" class="analysis-section">
              <div class="section-subheader">{{ $t('evaluationAssistant.responseCard.behavioralAnalysis') }}</div>
              <p>{{ result.behavioral_analysis }}</p>
            </div>
          </div>

          <!-- Comparison Result -->
          <div v-else-if="result.task_type === 'comparison'" class="result-detail comparison-detail">
            <div class="winner-display">
              <LTag :variant="result.winner === 'TIE' ? 'info' : 'primary'" size="lg">
                <LIcon size="18" class="mr-1">mdi-trophy</LIcon>
                {{ result.winner === 'TIE' ? $t('evaluationAssistant.comparison.tie') : $t('evaluationAssistant.comparison.winner', { winner: result.winner }) }}
              </LTag>
            </div>
            <div v-if="result.comparison_aspects?.length" class="aspects-list">
              <div v-for="(asp, i) in result.comparison_aspects" :key="i" class="aspect-item">
                <span class="aspect-name">{{ asp.aspect }}</span>
                <span class="aspect-winner">{{ asp.winner }}</span>
                <span class="aspect-reasoning text-caption">{{ asp.reasoning }}</span>
              </div>
            </div>
          </div>

          <!-- Classification Result -->
          <div v-else-if="result.task_type === 'text_classification'" class="result-detail classification-detail">
            <div class="label-display">
              <LTag variant="primary" size="lg">{{ result.label }}</LTag>
              <div class="confidence-score">
                {{ $t('evaluationAssistant.responseCard.confidenceScore') }}: {{ result.confidence_score }}/5
              </div>
            </div>
            <div v-if="result.key_phrases?.length" class="key-phrases">
              <div class="section-subheader">{{ $t('evaluationAssistant.responseCard.keyPhrases') }}</div>
              <div class="phrases-list">
                <LTag v-for="(phrase, i) in result.key_phrases" :key="i" variant="gray" size="sm">
                  {{ phrase }}
                </LTag>
              </div>
            </div>
          </div>

          <!-- Mail Rating Result -->
          <div v-else-if="result.task_type === 'mail_rating'" class="result-detail mail-rating-detail">
            <div class="overall-rating">
              <span class="rating-label">{{ $t('evaluationAssistant.responseCard.overallRating') }}</span>
              <div class="rating-stars-large">
                <LIcon
                  v-for="star in 5"
                  :key="star"
                  size="24"
                  :color="star <= result.overall_rating ? '#FFB300' : 'grey'"
                >
                  {{ star <= result.overall_rating ? 'mdi-star' : 'mdi-star-outline' }}
                </LIcon>
              </div>
            </div>
            <div v-if="result.criteria?.length" class="criteria-list">
              <div v-for="(crit, i) in result.criteria" :key="i" class="criteria-item">
                <span class="criteria-name">{{ crit.name }}</span>
                <span class="criteria-score">{{ crit.score }}/5</span>
                <span v-if="crit.reasoning" class="criteria-reasoning">{{ crit.reasoning }}</span>
              </div>
            </div>
            <div v-if="result.summary" class="summary-section">
              <div class="section-subheader">{{ $t('evaluationAssistant.responseCard.summary') }}</div>
              <p>{{ result.summary }}</p>
            </div>
          </div>

          <!-- Generic/Unknown Result -->
          <div v-else class="result-detail generic-detail">
            <pre class="json-output">{{ JSON.stringify(result.result_data || result, null, 2) }}</pre>
          </div>
        </div>

        <!-- Token Usage (for LLM evaluations) -->
        <div v-if="result.is_llm_evaluation && result.token_usage" class="content-section token-section">
          <div class="section-header">
            <LIcon size="16" class="mr-2">mdi-currency-usd</LIcon>
            <span>{{ $t('evaluationAssistant.responseCard.tokenUsage') }}</span>
          </div>
          <div class="token-stats">
            <span>{{ result.token_usage.input_tokens }} + {{ result.token_usage.output_tokens }} tokens</span>
            <span class="token-cost">${{ result.token_usage.cost_usd?.toFixed(6) }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="card-actions">
          <LBtn variant="text" size="small" @click="$emit('view-details')">
            <LIcon start size="16">mdi-open-in-new</LIcon>
            {{ $t('evaluationAssistant.responseCard.viewDetails') }}
          </LBtn>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ResultBadge from './ResultBadge.vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  },
  expanded: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle', 'view-details'])

const evaluatorClass = computed(() => {
  return props.result.is_llm_evaluation ? 'evaluator-llm' : 'evaluator-human'
})

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function getBucketIcon(bucket) {
  const icons = {
    gut: 'mdi-thumb-up',
    mittel: 'mdi-minus',
    schlecht: 'mdi-thumb-down',
    neutral: 'mdi-help-circle'
  }
  return icons[bucket] || 'mdi-circle'
}
</script>

<style scoped>
.response-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.response-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.response-card.expanded {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.evaluator-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.evaluator-llm {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.evaluator-human {
  background: rgba(var(--v-theme-secondary), 0.15);
  color: rgb(var(--v-theme-secondary));
}

.evaluator-name {
  font-weight: 600;
  font-size: 0.875rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.confidence-value {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.expand-icon {
  transition: transform 0.2s;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.card-content {
  padding: 0 16px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.05);
}

.content-section {
  margin-top: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 8px;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.section-subheader {
  font-weight: 500;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 8px 0 4px;
  text-transform: uppercase;
}

.reasoning-text {
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* Bucket styles for ranking */
.bucket {
  margin-bottom: 8px;
}

.bucket-header {
  display: flex;
  align-items: center;
  font-weight: 500;
  font-size: 0.875rem;
  padding: 6px 10px;
  border-radius: 6px;
}

.bucket-gut { background: rgba(76, 175, 80, 0.15); color: #4CAF50; }
.bucket-mittel { background: rgba(255, 193, 7, 0.15); color: #FFC107; }
.bucket-schlecht { background: rgba(244, 67, 54, 0.15); color: #F44336; }
.bucket-neutral { background: rgba(158, 158, 158, 0.15); color: #9E9E9E; }

.bucket-count {
  margin-left: auto;
  font-size: 0.75rem;
  opacity: 0.7;
}

.bucket-reasoning {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  padding: 4px 10px 4px 32px;
}

/* Rating styles */
.rating-item {
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 6px;
  margin-bottom: 6px;
}

.rating-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rating-reasoning {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-top: 4px;
}

.rating-attributes {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
  font-size: 0.75rem;
}

.attr-label {
  font-weight: 700;
}

.attr-item {
  padding: 2px 6px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 4px;
}

/* Authenticity styles */
.vote-display {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.confidence-score {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.indicators-list {
  margin-top: 12px;
}

.indicator-item {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  padding: 4px 0;
}

.indicator-weight {
  margin-left: auto;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.analysis-section {
  margin-top: 12px;
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 6px;
}

.analysis-section p {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

/* Comparison styles */
.winner-display {
  margin-bottom: 12px;
}

.aspects-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.aspect-item {
  display: grid;
  grid-template-columns: 1fr auto 2fr;
  gap: 8px;
  align-items: center;
  padding: 6px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 4px;
}

.aspect-name {
  font-weight: 500;
}

.aspect-winner {
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

/* Classification styles */
.label-display {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.phrases-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

/* Mail rating styles */
.overall-rating {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.rating-label {
  font-weight: 500;
}

.criteria-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.criteria-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  padding: 6px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 4px;
}

.criteria-reasoning {
  grid-column: 1 / -1;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.summary-section {
  margin-top: 12px;
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 6px;
}

.summary-section p {
  margin: 0;
  font-size: 0.875rem;
}

/* Generic JSON output */
.json-output {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px;
  overflow-x: auto;
  white-space: pre-wrap;
}

/* Token section */
.token-section {
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.05);
}

.token-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Actions */
.card-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  display: flex;
  justify-content: flex-end;
}
</style>
