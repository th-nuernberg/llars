<template>
  <div class="stats-grid">
    <!-- Total Comparisons -->
    <div class="stat-card">
      <v-skeleton-loader v-if="loading" type="avatar, text" />
      <template v-else>
        <div class="stat-icon stat-icon--primary">
          <LIcon size="28">mdi-compare</LIcon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ totalComparisons }}</div>
          <div class="stat-label">{{ $t('judge.results.stats.totalComparisons') }}</div>
        </div>
      </template>
    </div>

    <!-- Top Pillar -->
    <div class="stat-card">
      <v-skeleton-loader v-if="loading" type="avatar, text" />
      <template v-else>
        <div class="stat-icon stat-icon--success">
          <LIcon size="28">mdi-trophy</LIcon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ topPillar?.name || '-' }}</div>
          <div class="stat-label">{{ $t('judge.results.stats.topPillar') }}</div>
        </div>
      </template>
    </div>

    <!-- Average Confidence -->
    <div class="stat-card">
      <v-skeleton-loader v-if="loading" type="avatar, text" />
      <template v-else>
        <div class="stat-icon stat-icon--info">
          <LIcon size="28">mdi-percent</LIcon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ averageConfidence }}%</div>
          <div class="stat-label">{{ $t('judge.results.stats.avgConfidence') }}</div>
        </div>
      </template>
    </div>

    <!-- Duration -->
    <div class="stat-card">
      <v-skeleton-loader v-if="loading" type="avatar, text" />
      <template v-else>
        <div class="stat-icon stat-icon--warning">
          <LIcon size="28">mdi-clock-outline</LIcon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ duration }}</div>
          <div class="stat-label">{{ $t('judge.results.stats.duration') }}</div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  totalComparisons: { type: Number, default: 0 },
  topPillar: { type: Object, default: null },
  averageConfidence: { type: Number, default: 0 },
  duration: { type: String, default: '-' }
});
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--llars-spacing-md);
  margin-bottom: var(--llars-spacing-lg);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--llars-spacing-md);
  padding: var(--llars-spacing-md) var(--llars-spacing-lg);
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  box-shadow: var(--llars-shadow-sm);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  min-height: 90px;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--llars-shadow-md);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--llars-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon--primary {
  background: rgba(176, 202, 151, 0.2);
  color: var(--llars-primary-active);
}

.stat-icon--success {
  background: rgba(152, 212, 187, 0.2);
  color: var(--llars-success-active);
}

.stat-icon--info {
  background: rgba(168, 197, 226, 0.2);
  color: var(--llars-info-active);
}

.stat-icon--warning {
  background: rgba(232, 200, 122, 0.2);
  color: var(--llars-warning-active);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-label {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 2px;
}
</style>
