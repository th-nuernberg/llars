<template>
  <div class="overall-score-display" :class="{ 'has-score': score !== null }">
    <div class="score-header">
      <v-icon size="20" class="score-icon">mdi-chart-box</v-icon>
      <span class="score-label">{{ $t('evaluation.rating.overallScore') }}</span>
    </div>

    <div class="score-content">
      <!-- Star Display -->
      <div class="stars-row">
        <v-icon
          v-for="star in maxScore"
          :key="star"
          :size="starSize"
          :color="getStarColor(star)"
          class="star-icon"
        >
          {{ getStarIcon(star) }}
        </v-icon>
      </div>

      <!-- Numeric Display -->
      <div class="numeric-row">
        <span class="score-value" :class="getScoreClass()">
          {{ formattedScore }}
        </span>
        <span class="score-max">/{{ maxScore }}</span>
      </div>

      <!-- Label -->
      <div v-if="scoreLabel" class="score-interpretation">
        {{ scoreLabel }}
      </div>
    </div>

    <!-- Progress toward completion -->
    <div v-if="showProgress" class="completion-progress">
      <v-progress-linear
        :model-value="completionPercent"
        height="4"
        :color="completionPercent === 100 ? 'success' : 'primary'"
        rounded
      />
      <span class="completion-text">
        {{ ratedCount }}/{{ totalDimensions }} {{ $t('evaluation.rating.dimensionsRated') }}
      </span>
    </div>
  </div>
</template>

<script setup>
/**
 * OverallScoreDisplay - Shows the calculated overall score
 *
 * Displays the weighted average as stars and numeric value.
 * Also shows completion progress for dimensions.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const props = defineProps({
  score: {
    type: Number,
    default: null
  },
  maxScore: {
    type: Number,
    default: 5
  },
  labels: {
    type: Object,
    default: () => ({})
    // Expected: { 1: {de, en}, 2: {de, en}, ... }
  },
  ratedCount: {
    type: Number,
    default: 0
  },
  totalDimensions: {
    type: Number,
    default: 0
  },
  showProgress: {
    type: Boolean,
    default: true
  },
  starSize: {
    type: [Number, String],
    default: 28
  }
})

// Formatted score (rounded to 1 decimal)
const formattedScore = computed(() => {
  if (props.score === null || props.score === undefined) return '-'
  return props.score.toFixed(1)
})

// Completion percentage
const completionPercent = computed(() => {
  if (props.totalDimensions === 0) return 0
  return Math.round((props.ratedCount / props.totalDimensions) * 100)
})

// Get label for current score
const scoreLabel = computed(() => {
  if (props.score === null) return null

  // Find closest label
  const roundedScore = Math.round(props.score)
  const label = props.labels[roundedScore] || props.labels[String(roundedScore)]

  if (!label) return null
  return typeof label === 'string' ? label : (label[locale.value] || label.de)
})

// Get star icon (full, half, or empty)
function getStarIcon(position) {
  if (props.score === null) return 'mdi-star-outline'

  const diff = props.score - position + 1

  if (diff >= 1) return 'mdi-star'
  if (diff >= 0.5) return 'mdi-star-half-full'
  return 'mdi-star-outline'
}

// Get star color based on fill state
function getStarColor(position) {
  if (props.score === null) return 'grey-lighten-1'

  const diff = props.score - position + 1

  if (diff >= 0.5) return '#FFB300' // Amber
  return 'grey-lighten-1'
}

// Get CSS class for score value based on position
function getScoreClass() {
  if (props.score === null) return ''

  const position = props.score / props.maxScore

  if (position <= 0.4) return 'score-low'
  if (position >= 0.7) return 'score-high'
  return 'score-mid'
}
</script>

<style scoped>
.overall-score-display {
  padding: 16px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px 4px 12px 4px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  transition: all 0.3s ease;
}

.overall-score-display.has-score {
  border-color: var(--llars-primary, #b0ca97);
  background: rgba(176, 202, 151, 0.08);
}

/* Header */
.score-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.score-icon {
  color: var(--llars-secondary, #D1BC8A);
}

.score-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Content */
.score-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

/* Stars */
.stars-row {
  display: flex;
  gap: 4px;
}

.star-icon {
  transition: transform 0.2s ease;
}

.has-score .star-icon:hover {
  transform: scale(1.1);
}

/* Numeric Display */
.numeric-row {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.score-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  color: rgb(var(--v-theme-on-surface));
  transition: color 0.3s ease;
}

.score-value.score-low {
  color: var(--llars-danger, #e8a087);
}

.score-value.score-mid {
  color: var(--llars-secondary, #D1BC8A);
}

.score-value.score-high {
  color: var(--llars-success, #98d4bb);
}

.score-max {
  font-size: 1rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Interpretation Label */
.score-interpretation {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-style: italic;
  margin-top: 4px;
}

/* Completion Progress */
.completion-progress {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.completion-text {
  display: block;
  text-align: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 6px;
}

/* Responsive */
@media (max-width: 600px) {
  .overall-score-display {
    padding: 12px;
  }

  .score-value {
    font-size: 1.75rem;
  }
}
</style>
