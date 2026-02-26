<template>
  <div class="score-chart-wrapper">
    <LChart
      v-if="chartData"
      type="line"
      :data="chartData"
      :options="chartOptions"
    />
    <div v-else class="no-data">
      {{ $t('pipeline.noScoresYet') }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import LChart from '@/components/common/LChart.vue'

const { t } = useI18n()

const props = defineProps({
  scoreHistory: { type: Array, default: () => [] },
  thresholds: { type: Object, default: () => ({}) },
})

const chartData = computed(() => {
  if (!props.scoreHistory.length) return null

  const labels = props.scoreHistory.map(h => `Iter ${h.iteration}`)

  // Collect all dimension IDs
  const allDimIds = new Set()
  props.scoreHistory.forEach(h => {
    if (h.scores?.dimensions) {
      Object.keys(h.scores.dimensions).forEach(d => allDimIds.add(d))
    }
  })

  const colors = ['#b0ca97', '#88c4c8', '#D1BC8A', '#e8a087', '#98d4bb', '#c4a5de']

  const datasets = []

  // One dataset per dimension
  Array.from(allDimIds).forEach((dimId, idx) => {
    datasets.push({
      label: dimId,
      data: props.scoreHistory.map(h => h.scores?.dimensions?.[dimId] ?? null),
      borderColor: colors[idx % colors.length],
      backgroundColor: colors[idx % colors.length] + '20',
      tension: 0.3,
      pointRadius: 4,
      fill: false,
    })
  })

  // Average score dataset
  datasets.push({
    label: t('pipeline.avgScore'),
    data: props.scoreHistory.map(h => h.avgScore),
    borderColor: '#666',
    borderDash: [5, 5],
    tension: 0.3,
    pointRadius: 3,
    fill: false,
  })

  // Threshold line
  const globalThreshold = props.thresholds?.global_threshold
  if (globalThreshold) {
    datasets.push({
      label: t('pipeline.threshold'),
      data: labels.map(() => globalThreshold),
      borderColor: '#e8a087',
      borderDash: [10, 5],
      pointRadius: 0,
      fill: false,
    })
  }

  return { labels, datasets }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { boxWidth: 12, font: { size: 11 } },
    },
  },
  scales: {
    y: {
      beginAtZero: false,
      min: 0,
      max: 5,
      title: { display: true, text: 'Score' },
    },
  },
}))
</script>

<style scoped>
.score-chart-wrapper {
  height: 250px;
  width: 100%;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.85rem;
}
</style>
