<template>
  <div class="data-quality-card" :class="{ 'is-loading': loading }">
    <!-- Header -->
    <div class="card-header">
      <v-icon size="18" class="mr-2">mdi-check-circle</v-icon>
      <span>{{ $t('scenarioWizard.analysis.dataQuality') }}</span>
    </div>

    <!-- Content -->
    <div class="card-content">
      <!-- Loading State -->
      <template v-if="loading">
        <div class="skeleton-bar"></div>
        <div class="skeleton-line" style="width: 60%"></div>
        <div class="skeleton-line" style="width: 80%"></div>
      </template>

      <!-- Content State -->
      <template v-else>
        <!-- Completeness Bar -->
        <div class="completeness-section">
          <div class="completeness-bar-container">
            <div
              class="completeness-bar"
              :style="{ width: `${completenessPercent}%`, backgroundColor: completenessColor }"
            ></div>
          </div>
          <div class="completeness-value" :style="{ color: completenessColor }">
            {{ completenessPercent }}%
          </div>
        </div>

        <!-- Issues -->
        <div v-if="issues && issues.length > 0" class="issues-section">
          <div class="section-title">
            <v-icon size="16" color="#e8a087" class="mr-1">mdi-alert</v-icon>
            {{ $t('scenarioWizard.analysis.issues') }}
          </div>
          <div class="issues-list">
            <div v-for="(issue, idx) in issues" :key="idx" class="issue-item">
              <span class="issue-bullet">•</span>
              <span>{{ issue }}</span>
            </div>
          </div>
        </div>

        <!-- Recommendations -->
        <div v-if="recommendations && recommendations.length > 0" class="recommendations-section">
          <div class="section-title">
            <v-icon size="16" color="#b0ca97" class="mr-1">mdi-lightbulb</v-icon>
            {{ $t('scenarioWizard.analysis.recommendations') }}
          </div>
          <div class="recommendations-list">
            <div v-for="(rec, idx) in recommendations" :key="idx" class="recommendation-item">
              <span class="rec-bullet">•</span>
              <span>{{ rec }}</span>
            </div>
          </div>
        </div>

        <!-- All good message -->
        <div v-if="(!issues || issues.length === 0) && completenessPercent >= 90" class="all-good">
          <v-icon size="24" color="#98d4bb">mdi-check-circle</v-icon>
          <span>{{ $t('scenarioWizard.analysis.dataLooksGood') }}</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  completeness: {
    type: Number,
    default: null
  },
  issues: {
    type: Array,
    default: () => []
  },
  recommendations: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const completenessPercent = computed(() => {
  if (props.completeness === null) return 0
  return Math.round(props.completeness * 100)
})

const completenessColor = computed(() => {
  if (completenessPercent.value >= 80) return '#98d4bb' // Success green
  if (completenessPercent.value >= 50) return '#D1BC8A' // Warning yellow
  return '#e8a087' // Danger red
})
</script>

<style scoped>
.data-quality-card {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(152, 212, 187, 0.3);
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
  height: 200px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: rgba(152, 212, 187, 0.1);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #98d4bb;
  flex-shrink: 0;
}

.card-content {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  overflow-y: auto;
}

/* Loading Skeleton */
.skeleton-bar {
  width: 100%;
  height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-line {
  height: 12px;
  background: rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* Completeness */
.completeness-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.completeness-bar-container {
  flex: 1;
  height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.completeness-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease-out;
}

.completeness-value {
  font-size: 16px;
  font-weight: 700;
  min-width: 45px;
  text-align: right;
}

/* Issues */
.issues-section,
.recommendations-section {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding-top: 10px;
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 8px;
}

.issues-list,
.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.issue-item,
.recommendation-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.4;
}

.issue-bullet {
  color: #e8a087;
  font-weight: bold;
}

.rec-bullet {
  color: #b0ca97;
  font-weight: bold;
}

/* All Good */
.all-good {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: rgba(152, 212, 187, 0.1);
  border-radius: 8px;
  color: #98d4bb;
  font-size: 14px;
  font-weight: 500;
}
</style>
