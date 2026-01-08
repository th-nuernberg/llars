<template>
  <v-container fluid class="flex-grow-1 pa-4 fullscreen-content">
    <v-row class="h-100">
      <!-- Worker Selector Sidebar -->
      <v-col cols="2" class="d-flex flex-column">
        <div class="worker-selector">
          <div
            v-for="i in workerCount"
            :key="i - 1"
            class="worker-selector-item mb-2"
            :class="{
              'selected': focusedWorkerId === (i - 1),
              'streaming': workerStreams[i - 1]?.isStreaming
            }"
            @click="$emit('update:focusedWorkerId', i - 1)"
          >
            <v-avatar size="36" :color="workerColors[(i - 1) % workerColors.length]" class="mr-2">
              <span class="font-weight-bold">W{{ i }}</span>
            </v-avatar>
            <div class="worker-mini-info">
              <div class="text-caption font-weight-bold">Worker {{ i }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ getWorkerParsedResult(i - 1)?.winner ? `Sieger: ${getWorkerParsedResult(i - 1).winner}` : (workerStreams[i - 1]?.isStreaming ? 'Streamt...' : 'Wartet') }}
              </div>
            </div>
            <LIcon v-if="workerStreams[i - 1]?.isStreaming" size="small" color="warning" class="rotating ml-auto">mdi-loading</LIcon>
          </div>
        </div>
      </v-col>

      <!-- Focused Worker Display -->
      <v-col cols="10" class="d-flex flex-column">
        <v-card class="flex-grow-1 d-flex flex-column" variant="outlined">
          <v-card-title
            class="py-3 px-4 d-flex align-center"
            :class="`bg-${workerColors[focusedWorkerId % workerColors.length]}`"
          >
            <v-avatar size="40" :color="workerColors[focusedWorkerId % workerColors.length]" variant="flat" class="mr-3">
              <span class="text-h6 font-weight-bold">W{{ focusedWorkerId + 1 }}</span>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">Worker {{ focusedWorkerId + 1 }}</div>
              <div v-if="workerStreams[focusedWorkerId]?.comparison" class="text-caption">
                {{ workerStreams[focusedWorkerId]?.comparison?.pillar_a_name }} vs {{ workerStreams[focusedWorkerId]?.comparison?.pillar_b_name }}
              </div>
            </div>
            <v-spacer></v-spacer>
            <v-chip
              :color="workerStreams[focusedWorkerId]?.isStreaming ? 'warning' : (workerStreams[focusedWorkerId]?.comparison ? 'success' : 'grey')"
              variant="flat"
              size="large"
            >
              <LIcon start :class="{ 'rotating': workerStreams[focusedWorkerId]?.isStreaming }">
                {{ workerStreams[focusedWorkerId]?.isStreaming ? 'mdi-loading' : (workerStreams[focusedWorkerId]?.comparison ? 'mdi-check-circle' : 'mdi-sleep') }}
              </LIcon>
              {{ workerStreams[focusedWorkerId]?.isStreaming ? 'Streamt...' : (workerStreams[focusedWorkerId]?.comparison ? 'Aktiv' : 'Wartet') }}
            </v-chip>
          </v-card-title>

          <v-divider></v-divider>

          <!-- Large Result Display for Focused Worker -->
          <v-card-text class="flex-grow-1 overflow-y-auto pa-4">
            <!-- Empty State -->
            <div v-if="!workerStreams[focusedWorkerId]?.content && !workerStreams[focusedWorkerId]?.comparison" class="d-flex flex-column align-center justify-center h-100 text-medium-emphasis">
              <LIcon size="64" class="mb-4">mdi-robot-off</LIcon>
              <span class="text-h6">Wartet auf Aufgabe...</span>
            </div>

            <!-- Full Result Display -->
            <div v-else>
              <!-- Winner Display - Large -->
              <v-row class="mb-4">
                <v-col cols="4" class="text-center">
                  <v-card
                    :color="getWorkerParsedResult(focusedWorkerId)?.winner === 'A' ? 'success' : 'grey-lighten-2'"
                    variant="tonal"
                    class="pa-4"
                    :class="{ 'winner-glow': getWorkerParsedResult(focusedWorkerId)?.winner === 'A' }"
                  >
                    <div class="text-h3 font-weight-bold">A</div>
                    <div class="text-body-2">{{ workerStreams[focusedWorkerId]?.comparison?.pillar_a_name }}</div>
                  </v-card>
                </v-col>
                <v-col cols="4" class="d-flex flex-column align-center justify-center">
                  <v-chip
                    :color="getWorkerParsedResult(focusedWorkerId)?.winner ? 'primary' : 'grey'"
                    size="x-large"
                    class="mb-3"
                    :class="{ 'pulse-chip': workerStreams[focusedWorkerId]?.isStreaming && !getWorkerParsedResult(focusedWorkerId)?.winner }"
                  >
                    <LIcon start size="large" :class="{ 'rotating': workerStreams[focusedWorkerId]?.isStreaming && !getWorkerParsedResult(focusedWorkerId)?.winner }">
                      {{ workerStreams[focusedWorkerId]?.isStreaming && !getWorkerParsedResult(focusedWorkerId)?.winner ? 'mdi-loading' : 'mdi-trophy' }}
                    </LIcon>
                    {{ getWorkerParsedResult(focusedWorkerId)?.winner || (workerStreams[focusedWorkerId]?.isStreaming ? '...' : '?') }}
                  </v-chip>
                  <div class="text-center">
                    <div class="text-caption text-medium-emphasis">Konfidenz</div>
                    <div class="text-h5 font-weight-bold">
                      {{ getWorkerParsedResult(focusedWorkerId)?.confidence ? Math.round(getWorkerParsedResult(focusedWorkerId).confidence * 100) + '%' : '-' }}
                    </div>
                  </div>
                </v-col>
                <v-col cols="4" class="text-center">
                  <v-card
                    :color="getWorkerParsedResult(focusedWorkerId)?.winner === 'B' ? 'success' : 'grey-lighten-2'"
                    variant="tonal"
                    class="pa-4"
                    :class="{ 'winner-glow': getWorkerParsedResult(focusedWorkerId)?.winner === 'B' }"
                  >
                    <div class="text-h3 font-weight-bold">B</div>
                    <div class="text-body-2">{{ workerStreams[focusedWorkerId]?.comparison?.pillar_b_name }}</div>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Likert Scales - Large -->
              <v-card variant="outlined" class="mb-4 pa-4">
                <div class="text-subtitle-1 font-weight-bold mb-3">Kriterien-Bewertung</div>
                <div class="likert-scales-large">
                  <div
                    v-for="criterion in scoreCriteria"
                    :key="criterion.key"
                    class="likert-row-large"
                  >
                    <span class="criterion-label-large">{{ criterion.label }}</span>
                    <div class="likert-visual-large">
                      <!-- A Score -->
                      <div class="score-side score-a-side">
                        <div
                          v-for="n in 5"
                          :key="`a-${n}`"
                          class="score-dot-large"
                          :class="{
                            'filled': getWorkerScoreA(focusedWorkerId, criterion.key) >= n,
                            'pending': !getWorkerScoreA(focusedWorkerId, criterion.key) && workerStreams[focusedWorkerId]?.isStreaming
                          }"
                        ></div>
                        <span class="score-value">{{ getWorkerScoreA(focusedWorkerId, criterion.key) || '-' }}</span>
                      </div>
                      <span class="vs-label">vs</span>
                      <!-- B Score -->
                      <div class="score-side score-b-side">
                        <span class="score-value">{{ getWorkerScoreB(focusedWorkerId, criterion.key) || '-' }}</span>
                        <div
                          v-for="n in 5"
                          :key="`b-${n}`"
                          class="score-dot-large"
                          :class="{
                            'filled': getWorkerScoreB(focusedWorkerId, criterion.key) >= n,
                            'pending': !getWorkerScoreB(focusedWorkerId, criterion.key) && workerStreams[focusedWorkerId]?.isStreaming
                          }"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </v-card>

              <!-- Analysis Steps with Content -->
              <v-card variant="outlined" class="mb-4 pa-4">
                <div class="text-subtitle-1 font-weight-bold mb-3">Analyse-Schritte</div>
                <div class="steps-detailed">
                  <div
                    v-for="(stepDef, stepKey) in stepDefinitions"
                    :key="stepKey"
                    class="step-detailed"
                    :class="{
                      'active': getWorkerStep(focusedWorkerId, stepKey),
                      'streaming': getWorkerStep(focusedWorkerId, stepKey)?.isStreaming
                    }"
                  >
                    <div class="step-header-detailed d-flex align-center">
                      <v-avatar size="28" :color="getWorkerStep(focusedWorkerId, stepKey) ? 'primary' : 'grey'" class="mr-2">
                        <LIcon size="16" :class="{ 'rotating': getWorkerStep(focusedWorkerId, stepKey)?.isStreaming }">
                          {{ getWorkerStep(focusedWorkerId, stepKey)?.isStreaming ? 'mdi-loading' : stepDef.icon }}
                        </LIcon>
                      </v-avatar>
                      <span :class="{ 'text-medium-emphasis': !getWorkerStep(focusedWorkerId, stepKey) }">{{ stepDef.title }}</span>
                      <v-spacer></v-spacer>
                      <LIcon v-if="getWorkerStep(focusedWorkerId, stepKey) && !getWorkerStep(focusedWorkerId, stepKey)?.isStreaming" size="small" color="success">mdi-check</LIcon>
                    </div>
                    <div v-if="getWorkerStep(focusedWorkerId, stepKey)" class="step-content-detailed mt-2">
                      {{ getWorkerStep(focusedWorkerId, stepKey).content }}<span v-if="getWorkerStep(focusedWorkerId, stepKey)?.isStreaming" class="cursor-blink">|</span>
                    </div>
                  </div>
                </div>
              </v-card>

              <!-- Final Justification -->
              <v-card v-if="getWorkerParsedResult(focusedWorkerId)?.final_justification" variant="tonal" color="primary" class="pa-4">
                <div class="text-subtitle-1 font-weight-bold mb-2">Abschließende Begründung</div>
                <div class="text-body-1">{{ getWorkerParsedResult(focusedWorkerId).final_justification }}</div>
              </v-card>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
defineProps({
  workerCount: {
    type: Number,
    required: true
  },
  focusedWorkerId: {
    type: Number,
    required: true
  },
  workerStreams: {
    type: Object,
    required: true
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
  }
});

defineEmits(['update:focusedWorkerId']);
</script>

<style scoped>
.worker-selector {
  display: flex;
  flex-direction: column;
}

.worker-selector-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.worker-selector-item:hover {
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

.worker-selector-item.selected {
  background: rgba(var(--v-theme-primary), 0.15);
  border: 2px solid rgb(var(--v-theme-primary));
}

.worker-selector-item.streaming {
  background: rgba(var(--v-theme-warning), 0.15);
  border: 2px solid rgb(var(--v-theme-warning));
}

.worker-mini-info {
  flex: 1;
  min-width: 0;
}

.winner-glow {
  box-shadow: 0 0 20px rgba(var(--v-theme-success), 0.4);
}

.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.likert-scales-large {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.likert-row-large {
  display: flex;
  align-items: center;
  gap: 16px;
}

.criterion-label-large {
  width: 160px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.likert-visual-large {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
  gap: 8px;
}

.score-side {
  display: flex;
  align-items: center;
  gap: 4px;
}

.score-side.score-a-side {
  flex-direction: row;
}

.score-side.score-b-side {
  flex-direction: row-reverse;
}

.score-dot-large {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.15);
  transition: all 0.2s ease;
}

.score-side.score-a-side .score-dot-large.filled {
  background: rgb(33, 150, 243);
}

.score-side.score-b-side .score-dot-large.filled {
  background: rgb(76, 175, 80);
}

.score-dot-large.pending {
  animation: dot-pulse 1s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.score-value {
  font-weight: bold;
  font-size: 16px;
  min-width: 24px;
  text-align: center;
}

.score-side.score-a-side .score-value {
  color: rgb(33, 150, 243);
}

.score-side.score-b-side .score-value {
  color: rgb(76, 175, 80);
}

.vs-label {
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 14px;
  padding: 0 8px;
}

.steps-detailed {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-detailed {
  padding: 12px;
  border-radius: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  transition: all 0.2s ease;
}

.step-detailed.active {
  background: rgba(var(--v-theme-primary), 0.1);
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.step-detailed.streaming {
  background: rgba(var(--v-theme-warning), 0.15);
  border-left: 3px solid rgb(var(--v-theme-warning));
}

.step-content-detailed {
  padding-left: 36px;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.85);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
  font-weight: bold;
}

@keyframes blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}
</style>
