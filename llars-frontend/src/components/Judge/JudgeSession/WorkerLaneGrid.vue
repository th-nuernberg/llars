<template>
  <v-card class="worker-pool-card">
    <!-- Enhanced Dashboard Header -->
    <div class="worker-pool-header">
      <div class="header-main">
        <div class="header-title-section">
          <div class="header-icon-badge">
            <v-icon size="24">mdi-account-group</v-icon>
          </div>
          <div class="header-title-text">
            <span class="header-title">Worker-Pool Live View</span>
            <span class="header-subtitle">{{ activeWorkerCount }}/{{ workerCount }} Worker aktiv</span>
          </div>
        </div>

        <v-spacer></v-spacer>

        <!-- Session Stats -->
        <div class="header-stats">
          <div class="stat-item">
            <v-icon size="16">mdi-check-circle-outline</v-icon>
            <span class="stat-value">{{ displayCompleted }}</span>
            <span class="stat-label">/{{ displayTotal }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <v-icon size="16">mdi-percent</v-icon>
            <span class="stat-value">{{ Math.round(Math.min(progress, 100)) }}%</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="header-actions">
          <v-btn
            color="white"
            variant="tonal"
            size="small"
            class="mr-2"
            @click="$emit('open-fullscreen')"
          >
            <v-icon start size="18">mdi-fullscreen</v-icon>
            Vollbild
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="$emit('refresh')"
            color="white"
          >
            <v-icon size="20">mdi-refresh</v-icon>
          </v-btn>
        </div>
      </div>

      <!-- Pillar Overview Bar -->
      <div v-if="sessionPillars.length > 0" class="pillars-overview">
        <div class="pillars-label">
          <v-icon size="14">mdi-pillar</v-icon>
          <span>Säulen im Vergleich:</span>
        </div>
        <div class="pillars-chips">
          <div
            v-for="pillar in sessionPillars"
            :key="pillar.id"
            class="pillar-badge"
            :style="{ '--pillar-color': getPillarColor(pillar.id) }"
          >
            <v-icon size="14">{{ getPillarIcon(pillar.id) }}</v-icon>
            <span>{{ pillar.short }}</span>
          </div>
        </div>
        <div class="pairs-info">
          <span class="pairs-label">Paare:</span>
          <div class="pairs-progress">
            <div
              v-for="pair in pillarPairs"
              :key="pair.key"
              class="pair-chip"
              :class="{ 'pair-active': isPairActive(pair) }"
            >
              <span>{{ pair.a }}{{ pair.b }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <v-divider></v-divider>

    <!-- Worker Grid -->
    <v-card-text class="worker-grid-container">
      <v-row>
        <v-col
          v-for="i in workerCount"
          :key="i - 1"
          :cols="workerCount <= 2 ? 6 : (workerCount <= 3 ? 4 : 3)"
        >
          <WorkerLane
            :worker-id="i - 1"
            :current-comparison="workerStreams[i - 1]?.comparison"
            :stream-content="workerStreams[i - 1]?.content || ''"
            :is-streaming="workerStreams[i - 1]?.isStreaming || false"
            @open-fullscreen="$emit('open-worker-fullscreen', $event)"
          />
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed } from 'vue';
import WorkerLane from '../WorkerLane.vue';

const props = defineProps({
  workerCount: {
    type: Number,
    required: true
  },
  activeWorkerCount: {
    type: Number,
    required: true
  },
  session: {
    type: Object,
    default: null
  },
  progress: {
    type: Number,
    default: 0
  },
  sessionPillars: {
    type: Array,
    default: () => []
  },
  pillarPairs: {
    type: Array,
    default: () => []
  },
  workerStreams: {
    type: Object,
    required: true
  },
  getPillarColor: {
    type: Function,
    required: true
  },
  getPillarIcon: {
    type: Function,
    required: true
  },
  isPairActive: {
    type: Function,
    required: true
  },
  // Event-based counting values (optional)
  completedCount: {
    type: Number,
    default: null
  },
  confirmedTotal: {
    type: Number,
    default: null
  }
});

defineEmits(['open-fullscreen', 'refresh', 'open-worker-fullscreen']);

// Use event-based counting if available, otherwise fall back to session values
const displayCompleted = computed(() => {
  if (props.completedCount !== null && props.completedCount >= 0) {
    return props.completedCount;
  }
  return props.session?.completed_comparisons || 0;
});

const displayTotal = computed(() => {
  if (props.confirmedTotal !== null && props.confirmedTotal > 0) {
    return props.confirmedTotal;
  }
  return props.session?.total_comparisons || 0;
});
</script>

<style scoped>
.worker-pool-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  background: linear-gradient(135deg,
    rgba(var(--v-theme-surface), 0.95) 0%,
    rgba(var(--v-theme-surface-variant), 0.5) 100%);
}

.worker-pool-header {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.08) 0%,
    rgba(var(--v-theme-surface-variant), 0.3) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.1);
  padding: 16px 20px;
}

.header-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.header-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.2) 0%,
    rgba(var(--v-theme-primary), 0.1) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.header-title-text {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.header-subtitle {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(var(--v-theme-surface), 0.6);
  padding: 8px 12px;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pillars-overview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 8px;
  flex-wrap: wrap;
}

.pillars-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.pillars-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pillar-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
  background: color-mix(in srgb, var(--pillar-color) 15%, transparent);
  color: var(--pillar-color);
  border: 1px solid var(--pillar-color);
}

.pillar-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: color-mix(in srgb, var(--pillar-color) 25%, transparent);
}

.pairs-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.pairs-label {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.pairs-progress {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pair-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  color: rgba(var(--v-theme-on-surface), 0.7);
  transition: all 0.2s ease;
}

.pair-chip.pair-active {
  background: rgba(var(--v-theme-success), 0.15);
  color: rgb(var(--v-theme-success));
  animation: pair-pulse 2s ease-in-out infinite;
}

@keyframes pair-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(var(--v-theme-success), 0.3);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(var(--v-theme-success), 0);
  }
}

.worker-grid-container {
  padding: 16px;
}

@media (max-width: 960px) {
  .header-main {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-stats {
    width: 100%;
    justify-content: space-around;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .pillars-overview {
    flex-direction: column;
    align-items: flex-start;
  }

  .pairs-info {
    margin-left: 0;
    margin-top: 8px;
  }
}
</style>
