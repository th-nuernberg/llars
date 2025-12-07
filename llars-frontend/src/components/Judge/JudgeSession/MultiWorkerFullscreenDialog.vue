<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    fullscreen
    transition="dialog-bottom-transition"
    class="multi-worker-fullscreen-dialog"
  >
    <v-card class="fullscreen-card d-flex flex-column">
      <!-- Enhanced Fullscreen Header -->
      <div class="fullscreen-header">
        <div class="fullscreen-header-main">
          <div class="fullscreen-header-left">
            <v-btn icon variant="text" @click="$emit('close')" class="mr-2">
              <v-icon>mdi-close</v-icon>
            </v-btn>
            <div class="fullscreen-title-section">
              <div class="fullscreen-icon-badge">
                <v-icon size="24">mdi-account-group</v-icon>
              </div>
              <div class="fullscreen-title-text">
                <span class="fullscreen-title">Worker-Pool Live View</span>
                <span class="fullscreen-subtitle">{{ session?.session_name }}</span>
              </div>
            </div>
          </div>

          <div class="fullscreen-header-stats">
            <div class="fullscreen-stat">
              <span class="fullscreen-stat-value">{{ activeWorkerCount }}</span>
              <span class="fullscreen-stat-label">Aktiv</span>
            </div>
            <div class="fullscreen-stat-divider"></div>
            <div class="fullscreen-stat">
              <span class="fullscreen-stat-value">{{ session?.completed_comparisons || 0 }}</span>
              <span class="fullscreen-stat-label">Fertig</span>
            </div>
            <div class="fullscreen-stat-divider"></div>
            <div class="fullscreen-stat">
              <span class="fullscreen-stat-value">{{ session?.total_comparisons || 0 }}</span>
              <span class="fullscreen-stat-label">Total</span>
            </div>
          </div>

          <div class="fullscreen-header-right">
            <!-- Session Status -->
            <v-chip
              :color="session?.status === 'running' ? 'success' : 'warning'"
              variant="flat"
              class="mr-2"
            >
              <v-icon start size="small" :class="{ 'rotating': session?.status === 'running' }">
                {{ session?.status === 'running' ? 'mdi-loading' : 'mdi-pause-circle' }}
              </v-icon>
              {{ getStatusText(session?.status) }}
            </v-chip>

            <!-- Display Mode Toggle -->
            <v-btn-toggle
              :model-value="displayMode"
              @update:model-value="$emit('update:displayMode', $event)"
              density="compact"
              mandatory
              class="fullscreen-mode-toggle"
              variant="outlined"
            >
              <v-btn value="grid" size="small" title="Grid-Ansicht">
                <v-icon size="small">mdi-view-grid</v-icon>
              </v-btn>
              <v-btn value="focus" size="small" title="Fokus-Ansicht">
                <v-icon size="small">mdi-card-outline</v-icon>
              </v-btn>
            </v-btn-toggle>
          </div>
        </div>

        <!-- Pillar Progress Bar -->
        <div class="fullscreen-pillars-bar">
          <div class="fullscreen-pillars-chips">
            <div
              v-for="pillar in sessionPillars"
              :key="pillar.id"
              class="fullscreen-pillar-badge"
              :style="{
                '--pillar-color': getPillarColor(pillar.id),
                '--pillar-bg': getPillarColor(pillar.id) + '20'
              }"
            >
              <v-icon size="14">{{ getPillarIcon(pillar.id) }}</v-icon>
              <span>{{ pillar.short }}</span>
            </div>
          </div>
          <div class="fullscreen-progress-container">
            <v-progress-linear
              :model-value="progress"
              height="8"
              rounded
              :color="progress === 100 ? 'success' : 'primary'"
            ></v-progress-linear>
            <span class="fullscreen-progress-text">{{ Math.round(progress) }}%</span>
          </div>
        </div>
      </div>

      <!-- Main Content - Grid View -->
      <MultiWorkerGridView
        v-if="displayMode === 'grid'"
        :worker-count="workerCount"
        :worker-streams="workerStreams"
        :worker-colors="workerColors"
        :score-criteria="scoreCriteria"
        :step-definitions="stepDefinitions"
        :get-multi-worker-col-size="getMultiWorkerColSize"
        :get-worker-parsed-result="getWorkerParsedResult"
        :get-worker-score-a="getWorkerScoreA"
        :get-worker-score-b="getWorkerScoreB"
        :get-worker-step="getWorkerStep"
        :get-confidence-color="getConfidenceColor"
      />

      <!-- Focus View - Shows one worker large with selector -->
      <MultiWorkerFocusView
        v-else
        :worker-count="workerCount"
        :focused-worker-id="focusedWorkerId"
        :worker-streams="workerStreams"
        :worker-colors="workerColors"
        :score-criteria="scoreCriteria"
        :step-definitions="stepDefinitions"
        :get-worker-parsed-result="getWorkerParsedResult"
        :get-worker-score-a="getWorkerScoreA"
        :get-worker-score-b="getWorkerScoreB"
        :get-worker-step="getWorkerStep"
        @update:focused-worker-id="$emit('update:focusedWorkerId', $event)"
      />

      <!-- Footer with Progress -->
      <v-footer class="bg-surface-variant pa-2">
        <v-container fluid>
          <v-row align="center">
            <v-col cols="12" md="8">
              <v-progress-linear
                :model-value="progress"
                height="20"
                rounded
                :color="progress === 100 ? 'success' : 'primary'"
                striped
              >
                <template v-slot:default="{ value }">
                  <strong>{{ session?.completed_comparisons || 0 }} / {{ session?.total_comparisons || 0 }} ({{ Math.round(value) }}%)</strong>
                </template>
              </v-progress-linear>
            </v-col>
            <v-col cols="12" md="4" class="text-right">
              <v-chip size="small" :color="getStatusColor(session?.status)" class="mr-2">
                <v-icon start size="small">{{ getStatusIcon(session?.status) }}</v-icon>
                {{ getStatusText(session?.status) }}
              </v-chip>
              <span class="text-caption">Session: {{ session?.session_name }}</span>
            </v-col>
          </v-row>
        </v-container>
      </v-footer>
    </v-card>
  </v-dialog>
</template>

<script setup>
import MultiWorkerGridView from './MultiWorkerGridView.vue';
import MultiWorkerFocusView from './MultiWorkerFocusView.vue';

defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  displayMode: {
    type: String,
    default: 'grid'
  },
  session: {
    type: Object,
    default: null
  },
  activeWorkerCount: {
    type: Number,
    default: 0
  },
  sessionPillars: {
    type: Array,
    default: () => []
  },
  progress: {
    type: Number,
    default: 0
  },
  workerCount: {
    type: Number,
    default: 1
  },
  workerStreams: {
    type: Object,
    default: () => ({})
  },
  workerColors: {
    type: Array,
    required: true
  },
  scoreCriteria: {
    type: Array,
    required: true
  },
  stepDefinitions: {
    type: Object,
    required: true
  },
  focusedWorkerId: {
    type: Number,
    default: 0
  },
  getMultiWorkerColSize: {
    type: Number,
    default: 6
  },
  getPillarColor: {
    type: Function,
    required: true
  },
  getPillarIcon: {
    type: Function,
    required: true
  },
  getStatusColor: {
    type: Function,
    required: true
  },
  getStatusIcon: {
    type: Function,
    required: true
  },
  getStatusText: {
    type: Function,
    required: true
  },
  getWorkerParsedResult: {
    type: Function,
    required: true
  },
  getWorkerScoreA: {
    type: Function,
    required: true
  },
  getWorkerScoreB: {
    type: Function,
    required: true
  },
  getWorkerStep: {
    type: Function,
    required: true
  },
  getConfidenceColor: {
    type: Function,
    required: true
  }
});

defineEmits([
  'update:modelValue',
  'update:displayMode',
  'update:focusedWorkerId',
  'close'
]);
</script>

<style scoped>
.fullscreen-card {
  height: 100vh;
  overflow: hidden;
}

.fullscreen-header {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.15) 0%,
    rgba(var(--v-theme-surface-variant), 0.5) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.2);
  padding: 0;
}

.fullscreen-header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  gap: 16px;
}

.fullscreen-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fullscreen-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.fullscreen-icon-badge {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.25) 0%,
    rgba(var(--v-theme-primary), 0.1) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
}

.fullscreen-title-text {
  display: flex;
  flex-direction: column;
}

.fullscreen-title {
  font-size: 16px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.fullscreen-subtitle {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.fullscreen-header-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(var(--v-theme-surface), 0.7);
  padding: 8px 16px;
  border-radius: 8px;
}

.fullscreen-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.fullscreen-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.fullscreen-stat-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.fullscreen-stat-divider {
  width: 1px;
  height: 30px;
  background: rgba(var(--v-theme-on-surface), 0.15);
}

.fullscreen-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fullscreen-mode-toggle {
  border-color: rgba(var(--v-theme-on-surface), 0.3);
}

.fullscreen-pillars-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: rgba(var(--v-theme-surface), 0.5);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  gap: 16px;
}

.fullscreen-pillars-chips {
  display: flex;
  gap: 8px;
}

.fullscreen-pillar-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  background: var(--pillar-bg);
  color: var(--pillar-color);
  border: 1px solid var(--pillar-color);
  transition: all 0.2s ease;
}

.fullscreen-pillar-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.fullscreen-progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  max-width: 400px;
}

.fullscreen-progress-text {
  font-size: 14px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  min-width: 40px;
  text-align: right;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Responsive Fullscreen Header */
@media (max-width: 1200px) {
  .fullscreen-header-main {
    flex-wrap: wrap;
  }

  .fullscreen-header-stats {
    order: 3;
    width: 100%;
    justify-content: center;
    margin-top: 8px;
  }
}

@media (max-width: 768px) {
  .fullscreen-pillars-bar {
    flex-direction: column;
    gap: 12px;
  }

  .fullscreen-progress-container {
    max-width: 100%;
    width: 100%;
  }
}
</style>
