<template>
  <div class="progress-panel">
    <!-- Progress Header -->
    <div class="progress-header">
      <span class="progress-label">Fortschritt</span>
      <span class="progress-count">
        {{ displayCompleted }} / {{ displayTotal }}
      </span>
    </div>

    <!-- Progress Bar -->
    <div class="progress-bar-container">
      <div class="progress-bar-bg">
        <div
          class="progress-bar-fill"
          :class="{ 'progress-complete': progress >= 100 }"
          :style="{ width: Math.min(progress, 100) + '%' }"
        ></div>
      </div>
      <span class="progress-percent">{{ Math.round(Math.min(progress, 100)) }}%</span>
    </div>

    <!-- Session Meta (compact row) -->
    <div class="progress-meta">
      <span class="meta-item">
        <v-icon size="12" class="mr-1">mdi-pillar</v-icon>
        {{ session?.pillar_count }} Säulen
      </span>
      <span class="meta-item">
        <v-icon size="12" class="mr-1">mdi-file-document-multiple</v-icon>
        {{ session?.samples_per_pillar }} Samples
      </span>
      <span v-if="workerCount > 1" class="meta-item">
        <v-icon size="12" class="mr-1">mdi-account-group</v-icon>
        {{ workerCount }} Worker
      </span>
      <span v-if="session?.position_swap" class="meta-item meta-swap">
        <v-icon size="12" class="mr-1">mdi-swap-horizontal</v-icon>
        Swap
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, watchEffect } from 'vue';

const props = defineProps({
  session: {
    type: Object,
    default: null
  },
  progress: {
    type: Number,
    default: 0
  },
  workerCount: {
    type: Number,
    default: 1
  },
  formatDate: {
    type: Function,
    required: true
  },
  // Event-based counting values (optional - falls back to session values)
  completedCount: {
    type: Number,
    default: null
  },
  confirmedTotal: {
    type: Number,
    default: null
  }
});

// Debug: Watch props to see what we receive on each change
watchEffect(() => {
  console.log('[SessionProgressBar] Props:', {
    progress: props.progress,
    completedCount: props.completedCount,
    confirmedTotal: props.confirmedTotal,
    sessionCompleted: props.session?.completed_comparisons,
    sessionTotal: props.session?.total_comparisons
  });
});

// Use event-based counting if available, otherwise fall back to session values
const displayCompleted = computed(() => {
  // Prefer completedCount if available and valid
  if (props.completedCount !== null && props.completedCount >= 0) {
    return props.completedCount;
  }
  return props.session?.completed_comparisons || 0;
});

const displayTotal = computed(() => {
  // Prefer confirmedTotal if available and valid
  if (props.confirmedTotal !== null && props.confirmedTotal > 0) {
    return props.confirmedTotal;
  }
  return props.session?.total_comparisons || 0;
});
</script>

<style scoped>
.progress-panel {
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  padding: 12px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.progress-count {
  font-size: 12px;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.progress-bar-bg {
  flex: 1;
  height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: rgb(var(--v-theme-primary));
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-bar-fill.progress-complete {
  background: rgb(var(--v-theme-success));
}

.progress-percent {
  font-size: 11px;
  font-weight: 700;
  min-width: 32px;
  text-align: right;
}

.progress-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

.meta-swap {
  background: rgba(var(--v-theme-info), 0.15);
  color: rgb(var(--v-theme-info));
}
</style>
