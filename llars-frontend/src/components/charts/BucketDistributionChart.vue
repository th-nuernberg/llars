<template>
  <div class="bucket-distribution-chart">
    <div v-if="title" class="chart-title">{{ title }}</div>

    <div v-if="distribution.length > 0" class="chart-container">
      <!-- Bars -->
      <div class="bars-container">
        <div
          v-for="bucket in distribution"
          :key="bucket.bucket"
          class="bar-wrapper"
        >
          <div class="bar-label">{{ bucket.label }}</div>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{
                width: bucket.percentage + '%',
                backgroundColor: bucket.color
              }"
            >
              <span v-if="bucket.percentage > 15" class="bar-value-inside">
                {{ bucket.count }}
              </span>
            </div>
            <span v-if="bucket.percentage <= 15" class="bar-value-outside">
              {{ bucket.count }}
            </span>
          </div>
          <div class="bar-percentage">{{ bucket.percentage }}%</div>
        </div>
      </div>

      <!-- Legend -->
      <div class="chart-legend">
        <div
          v-for="bucket in distribution"
          :key="'legend-' + bucket.bucket"
          class="legend-item"
        >
          <span class="legend-color" :style="{ backgroundColor: bucket.color }"></span>
          <span class="legend-label">{{ bucket.label }}: {{ bucket.count }}</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <LIcon size="32" color="grey-lighten-1">mdi-chart-bar</LIcon>
      <span>{{ $t('scenarioManager.evaluation.noRankingData') || 'Keine Ranking-Daten verfügbar' }}</span>
    </div>
  </div>
</template>

<script setup>import { i18n } from '@/i18n'

/**
 * BucketDistributionChart - Horizontal bar chart for ranking bucket distribution
 *
 * Shows how items are distributed across ranking buckets (gut/mittel/schlecht).
 *
 * Usage:
 *   <BucketDistributionChart
 *     :distribution="[
 *       { bucket: 'gut', label: i18n.global.t('auto.988d10abb9'), count: 10, percentage: 50, color: '#b0ca97' },
 *       { bucket: 'mittel', label: i18n.global.t('auto.f7b252956581b9a5'), count: 6, percentage: 30, color: '#e8c87a' },
 *       { bucket: 'schlecht', label: i18n.global.t('auto.7d1ca93ec76ef187'), count: 4, percentage: 20, color: '#e8a087' }
 *     ]"
 *     title="Bucket-Verteilung"
 *   />
 */
defineProps({
  /** Distribution data with bucket, label, count, percentage, color */
  distribution: {
    type: Array,
    default: () => []
  },
  /** Chart title */
  title: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.bucket-distribution-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  min-height: 280px;
}

.chart-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 16px;
  text-align: center;
}

.chart-container {
  width: 100%;
  max-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bars-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-label {
  width: 70px;
  font-size: 0.8rem;
  font-weight: 500;
  text-align: right;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.bar-track {
  flex: 1;
  height: 28px;
  background-color: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.bar-fill {
  height: 100%;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  transition: width 0.5s ease-out;
  min-width: 2px;
}

.bar-value-inside {
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.bar-value-outside {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-left: 6px;
}

.bar-percentage {
  width: 40px;
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-align: right;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.8rem;
  flex: 1;
  min-height: 200px;
}
</style>
