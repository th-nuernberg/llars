<template>
  <div class="l-skeleton" :class="containerClass">
    <!-- Stat Card Skeleton -->
    <template v-if="type === 'stat-card'">
      <div v-for="n in count" :key="n" class="l-skeleton__stat-card">
        <div class="l-skeleton__stat-icon skeleton-pulse" />
        <div class="l-skeleton__stat-value skeleton-pulse" />
        <div class="l-skeleton__stat-label skeleton-pulse" />
        <div class="l-skeleton__stat-accent skeleton-pulse" />
      </div>
    </template>

    <!-- Activity List Skeleton -->
    <template v-else-if="type === 'activity-list'">
      <div v-for="n in count" :key="n" class="l-skeleton__activity-item">
        <div class="l-skeleton__activity-icon skeleton-pulse" />
        <div class="l-skeleton__activity-content">
          <div class="l-skeleton__activity-title skeleton-pulse" />
          <div class="l-skeleton__activity-meta skeleton-pulse" />
        </div>
        <div class="l-skeleton__activity-time skeleton-pulse" />
      </div>
    </template>

    <!-- Table Skeleton -->
    <template v-else-if="type === 'table'">
      <div class="l-skeleton__table">
        <div class="l-skeleton__table-header">
          <div v-for="col in columns" :key="col" class="l-skeleton__table-th skeleton-pulse" />
        </div>
        <div v-for="row in count" :key="row" class="l-skeleton__table-row">
          <div v-for="col in columns" :key="col" class="l-skeleton__table-td skeleton-pulse" />
        </div>
      </div>
    </template>

    <!-- Card Skeleton -->
    <template v-else-if="type === 'card'">
      <div v-for="n in count" :key="n" class="l-skeleton__card">
        <div class="l-skeleton__card-header">
          <div class="l-skeleton__card-avatar skeleton-pulse" />
          <div class="l-skeleton__card-titles">
            <div class="l-skeleton__card-title skeleton-pulse" />
            <div class="l-skeleton__card-subtitle skeleton-pulse" />
          </div>
        </div>
        <div class="l-skeleton__card-content">
          <div class="l-skeleton__card-line skeleton-pulse" />
          <div class="l-skeleton__card-line skeleton-pulse" style="width: 80%" />
        </div>
      </div>
    </template>

    <!-- Button Grid Skeleton -->
    <template v-else-if="type === 'button-grid'">
      <div class="l-skeleton__button-grid">
        <div v-for="n in count" :key="n" class="l-skeleton__button skeleton-pulse" />
      </div>
    </template>

    <!-- Panel Skeleton (header + content) -->
    <template v-else-if="type === 'panel'">
      <div class="l-skeleton__panel">
        <div class="l-skeleton__panel-header">
          <div class="l-skeleton__panel-icon skeleton-pulse" />
          <div class="l-skeleton__panel-title skeleton-pulse" />
        </div>
        <div class="l-skeleton__panel-content">
          <div v-for="n in count" :key="n" class="l-skeleton__panel-line skeleton-pulse" />
        </div>
      </div>
    </template>

    <!-- Health Bar Skeleton -->
    <template v-else-if="type === 'health-bar'">
      <div class="l-skeleton__health-bar">
        <div v-for="n in count" :key="n" class="l-skeleton__health-item skeleton-pulse" />
      </div>
    </template>

    <!-- Text Lines Skeleton -->
    <template v-else-if="type === 'text'">
      <div class="l-skeleton__text">
        <div
          v-for="n in count"
          :key="n"
          class="l-skeleton__text-line skeleton-pulse"
          :style="{ width: getRandomWidth(n) }"
        />
      </div>
    </template>

    <!-- Avatar Skeleton -->
    <template v-else-if="type === 'avatar'">
      <div v-for="n in count" :key="n" class="l-skeleton__avatar skeleton-pulse" :style="avatarStyle" />
    </template>

    <!-- Tag Skeleton -->
    <template v-else-if="type === 'tag'">
      <div class="l-skeleton__tags">
        <div v-for="n in count" :key="n" class="l-skeleton__tag skeleton-pulse" />
      </div>
    </template>

    <!-- Chart Skeleton -->
    <template v-else-if="type === 'chart'">
      <div class="l-skeleton__chart">
        <div class="l-skeleton__chart-bars">
          <div v-for="n in 7" :key="n" class="l-skeleton__chart-bar skeleton-pulse" :style="{ height: getRandomHeight() }" />
        </div>
        <div class="l-skeleton__chart-axis skeleton-pulse" />
      </div>
    </template>

    <!-- Generic Box Skeleton -->
    <template v-else>
      <div
        v-for="n in count"
        :key="n"
        class="l-skeleton__box skeleton-pulse"
        :style="{ height: height, width: width }"
      />
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'box',
    validator: (v) => [
      'stat-card', 'activity-list', 'table', 'card', 'button-grid',
      'panel', 'health-bar', 'text', 'avatar', 'tag', 'chart', 'box'
    ].includes(v)
  },
  count: {
    type: Number,
    default: 1
  },
  columns: {
    type: Number,
    default: 4
  },
  height: {
    type: String,
    default: '100px'
  },
  width: {
    type: String,
    default: '100%'
  },
  avatarSize: {
    type: Number,
    default: 40
  },
  inline: {
    type: Boolean,
    default: false
  }
})

const containerClass = computed(() => ({
  'l-skeleton--inline': props.inline,
  [`l-skeleton--${props.type}`]: true
}))

const avatarStyle = computed(() => ({
  width: `${props.avatarSize}px`,
  height: `${props.avatarSize}px`
}))

const getRandomWidth = (seed) => {
  const widths = ['100%', '90%', '95%', '85%', '75%', '80%']
  return widths[seed % widths.length]
}

const getRandomHeight = () => {
  return `${30 + Math.random() * 60}%`
}
</script>

<style scoped>
/* Base skeleton styles */
.l-skeleton {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.l-skeleton--inline {
  flex-direction: row;
}

/* Pulse animation */
.skeleton-pulse {
  background: linear-gradient(
    90deg,
    rgba(var(--v-theme-on-surface), 0.06) 25%,
    rgba(var(--v-theme-on-surface), 0.12) 50%,
    rgba(var(--v-theme-on-surface), 0.06) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
  border-radius: 4px;
}

@keyframes skeleton-pulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Stat Card Skeleton */
.l-skeleton--stat-card {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.l-skeleton__stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  gap: 6px;
}

.l-skeleton__stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
}

.l-skeleton__stat-value {
  width: 50px;
  height: 24px;
  border-radius: 4px;
}

.l-skeleton__stat-label {
  width: 70px;
  height: 12px;
  border-radius: 2px;
}

.l-skeleton__stat-accent {
  width: 100%;
  height: 4px;
  border-radius: 0;
  margin-top: auto;
}

/* Activity List Skeleton */
.l-skeleton--activity-list {
  gap: 6px;
}

.l-skeleton__activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
}

.l-skeleton__activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
}

.l-skeleton__activity-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.l-skeleton__activity-title {
  height: 14px;
  width: 80%;
}

.l-skeleton__activity-meta {
  height: 10px;
  width: 50%;
}

.l-skeleton__activity-time {
  width: 60px;
  height: 20px;
  border-radius: 10px;
  flex-shrink: 0;
}

/* Table Skeleton */
.l-skeleton__table {
  width: 100%;
}

.l-skeleton__table-header {
  display: flex;
  gap: 16px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.l-skeleton__table-th {
  flex: 1;
  height: 12px;
}

.l-skeleton__table-row {
  display: flex;
  gap: 16px;
  padding: 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.l-skeleton__table-td {
  flex: 1;
  height: 16px;
}

/* Card Skeleton */
.l-skeleton--card {
  gap: 12px;
}

.l-skeleton__card {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  padding: 16px;
}

.l-skeleton__card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.l-skeleton__card-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
}

.l-skeleton__card-titles {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.l-skeleton__card-title {
  height: 16px;
  width: 60%;
}

.l-skeleton__card-subtitle {
  height: 12px;
  width: 40%;
}

.l-skeleton__card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.l-skeleton__card-line {
  height: 14px;
  width: 100%;
}

/* Button Grid Skeleton */
.l-skeleton__button-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.l-skeleton__button {
  height: 56px;
  border-radius: 8px;
}

/* Panel Skeleton */
.l-skeleton__panel {
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.l-skeleton__panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.l-skeleton__panel-icon {
  width: 18px;
  height: 18px;
  border-radius: 4px;
}

.l-skeleton__panel-title {
  width: 120px;
  height: 14px;
}

.l-skeleton__panel-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.l-skeleton__panel-line {
  height: 14px;
  width: 100%;
}

.l-skeleton__panel-line:nth-child(2) { width: 90%; }
.l-skeleton__panel-line:nth-child(3) { width: 75%; }

/* Health Bar Skeleton */
.l-skeleton__health-bar {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.l-skeleton__health-item {
  flex: 1;
  height: 32px;
  border-radius: 6px;
}

/* Text Skeleton */
.l-skeleton__text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.l-skeleton__text-line {
  height: 14px;
}

/* Avatar Skeleton */
.l-skeleton--avatar {
  flex-direction: row;
  gap: 8px;
}

.l-skeleton__avatar {
  border-radius: 50%;
}

/* Tag Skeleton */
.l-skeleton__tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.l-skeleton__tag {
  width: 60px;
  height: 22px;
  border-radius: 11px;
}

/* Chart Skeleton */
.l-skeleton__chart {
  height: 150px;
  display: flex;
  flex-direction: column;
}

.l-skeleton__chart-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 0 8px;
}

.l-skeleton__chart-bar {
  flex: 1;
  border-radius: 4px 4px 0 0;
}

.l-skeleton__chart-axis {
  height: 2px;
  margin-top: 4px;
}

/* Box Skeleton */
.l-skeleton__box {
  border-radius: 8px;
}

/* Responsive */
@media (max-width: 900px) {
  .l-skeleton--stat-card {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
