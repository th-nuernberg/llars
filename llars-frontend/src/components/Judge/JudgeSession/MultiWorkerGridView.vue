<template>
  <v-container fluid class="flex-grow-1 pa-4 fullscreen-content multi-worker-grid">
    <v-row class="h-100">
      <v-col
        v-for="i in workerCount"
        :key="i - 1"
        :cols="getMultiWorkerColSize"
        class="worker-col"
      >
        <!-- Enhanced Worker Card for Fullscreen -->
        <v-card
          variant="outlined"
          class="worker-fullscreen-card h-100 d-flex flex-column"
          :class="{
            'worker-streaming': workerStreams[i - 1]?.isStreaming,
            'worker-active': workerStreams[i - 1]?.comparison
          }"
        >
          <!-- Worker Header -->
          <v-card-title
            class="py-2 px-3 d-flex align-center"
            :class="`bg-${workerColors[(i - 1) % workerColors.length]}`"
          >
            <v-avatar size="32" :color="workerColors[(i - 1) % workerColors.length]" variant="flat" class="mr-2">
              <span class="font-weight-bold">W{{ i }}</span>
            </v-avatar>
            <span class="text-subtitle-1 font-weight-bold">Worker {{ i }}</span>
            <v-spacer></v-spacer>
            <v-chip
              size="small"
              :color="workerStreams[i - 1]?.isStreaming ? 'warning' : (workerStreams[i - 1]?.comparison ? 'info' : 'grey')"
              variant="flat"
            >
              <LIcon start size="small" :class="{ 'rotating': workerStreams[i - 1]?.isStreaming }">
                {{ workerStreams[i - 1]?.isStreaming ? 'mdi-loading' : (workerStreams[i - 1]?.comparison ? 'mdi-play-circle' : 'mdi-sleep') }}
              </LIcon>
              {{ workerStreams[i - 1]?.isStreaming ? 'Streamt' : (workerStreams[i - 1]?.comparison ? 'Arbeitet' : 'Wartet') }}
            </v-chip>
          </v-card-title>

          <!-- Comparison Info -->
          <div v-if="workerStreams[i - 1]?.comparison" class="comparison-info pa-2 bg-surface-variant">
            <div class="d-flex justify-space-between align-center">
              <v-chip size="small" color="blue" variant="outlined">
                {{ workerStreams[i - 1]?.comparison?.pillar_a_name || 'A' }}
              </v-chip>
              <LIcon size="small">mdi-arrow-left-right</LIcon>
              <v-chip size="small" color="green" variant="outlined">
                {{ workerStreams[i - 1]?.comparison?.pillar_b_name || 'B' }}
              </v-chip>
            </div>
          </div>

          <v-divider></v-divider>

          <!-- Worker Content -->
          <v-card-text class="flex-grow-1 overflow-y-auto pa-3">
            <!-- Empty State -->
            <div v-if="!workerStreams[i - 1]?.content && !workerStreams[i - 1]?.comparison" class="d-flex flex-column align-center justify-center h-100 text-medium-emphasis">
              <LIcon size="48" class="mb-2">mdi-robot-off</LIcon>
              <span>Wartet auf Aufgabe...</span>
            </div>

            <!-- Result Display -->
            <div v-else class="worker-result-display">
              <!-- Winner and Confidence -->
              <div class="result-summary mb-3">
                <div class="d-flex justify-space-between align-center mb-2">
                  <div class="thread-badge thread-a" :class="{ 'is-winner': getWorkerParsedResult(i - 1)?.winner === 'A' }">A</div>
                  <v-chip
                    :color="getWorkerParsedResult(i - 1)?.winner ? 'primary' : 'grey'"
                    size="large"
                    :class="{ 'pulse-chip': workerStreams[i - 1]?.isStreaming && !getWorkerParsedResult(i - 1)?.winner }"
                  >
                    <LIcon start :class="{ 'rotating': workerStreams[i - 1]?.isStreaming && !getWorkerParsedResult(i - 1)?.winner }">
                      {{ workerStreams[i - 1]?.isStreaming && !getWorkerParsedResult(i - 1)?.winner ? 'mdi-loading' : 'mdi-trophy' }}
                    </LIcon>
                    {{ getWorkerParsedResult(i - 1)?.winner || (workerStreams[i - 1]?.isStreaming ? '...' : '-') }}
                  </v-chip>
                  <div class="thread-badge thread-b" :class="{ 'is-winner': getWorkerParsedResult(i - 1)?.winner === 'B' }">B</div>
                </div>

                <!-- Confidence Bar -->
                <v-progress-linear
                  :model-value="getWorkerParsedResult(i - 1)?.confidence ? getWorkerParsedResult(i - 1).confidence * 100 : 0"
                  :indeterminate="workerStreams[i - 1]?.isStreaming && !getWorkerParsedResult(i - 1)?.confidence"
                  :color="getConfidenceColor(getWorkerParsedResult(i - 1)?.confidence || 0)"
                  height="20"
                  rounded
                >
                  <template v-slot:default>
                    <span class="text-caption font-weight-bold">
                      {{ getWorkerParsedResult(i - 1)?.confidence ? Math.round(getWorkerParsedResult(i - 1).confidence * 100) + '%' : '' }}
                    </span>
                  </template>
                </v-progress-linear>
              </div>

              <!-- Likert Scale Scores -->
              <div class="likert-scores-fullscreen mb-3">
                <div
                  v-for="criterion in scoreCriteria"
                  :key="criterion.key"
                  class="likert-row-fullscreen"
                >
                  <span class="criterion-label-full">{{ criterion.label }}</span>
                  <div class="likert-dots-full">
                    <!-- A Score dots -->
                    <div class="dots-group-full dots-a">
                      <div
                        v-for="n in 5"
                        :key="`a-${n}`"
                        class="dot-full"
                        :class="{
                          'dot-filled': getWorkerScoreA(i - 1, criterion.key) >= n,
                          'dot-pending': !getWorkerScoreA(i - 1, criterion.key) && workerStreams[i - 1]?.isStreaming
                        }"
                      ></div>
                    </div>
                    <span class="score-divider-full">|</span>
                    <!-- B Score dots -->
                    <div class="dots-group-full dots-b">
                      <div
                        v-for="n in 5"
                        :key="`b-${n}`"
                        class="dot-full"
                        :class="{
                          'dot-filled': getWorkerScoreB(i - 1, criterion.key) >= n,
                          'dot-pending': !getWorkerScoreB(i - 1, criterion.key) && workerStreams[i - 1]?.isStreaming
                        }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Analysis Steps Progress -->
              <div class="analysis-steps-progress mb-3">
                <div class="steps-row">
                  <div
                    v-for="(stepDef, stepKey) in stepDefinitions"
                    :key="stepKey"
                    class="step-indicator"
                    :class="{
                      'step-complete': getWorkerStep(i - 1, stepKey) && !getWorkerStep(i - 1, stepKey)?.isStreaming,
                      'step-active': getWorkerStep(i - 1, stepKey)?.isStreaming
                    }"
                    :title="stepDef.title"
                  >
                    <LIcon size="16" :class="{ 'rotating': getWorkerStep(i - 1, stepKey)?.isStreaming }">
                      {{ getWorkerStep(i - 1, stepKey)?.isStreaming ? 'mdi-loading' : (getWorkerStep(i - 1, stepKey) ? 'mdi-check-circle' : 'mdi-circle-outline') }}
                    </LIcon>
                  </div>
                </div>
              </div>

              <!-- Final Justification -->
              <div v-if="getWorkerParsedResult(i - 1)?.final_justification" class="justification-fullscreen">
                <div class="text-caption text-medium-emphasis mb-1">Begründung:</div>
                <div class="text-body-2">{{ getWorkerParsedResult(i - 1).final_justification }}</div>
              </div>

              <!-- Raw Stream Toggle -->
              <v-expansion-panels class="mt-3" variant="accordion">
                <v-expansion-panel>
                  <v-expansion-panel-title class="py-2">
                    <LIcon size="small" class="mr-2" :class="{ 'rotating': workerStreams[i - 1]?.isStreaming }">
                      {{ workerStreams[i - 1]?.isStreaming ? 'mdi-loading' : 'mdi-code-json' }}
                    </LIcon>
                    <span class="text-caption">Raw Stream ({{ (workerStreams[i - 1]?.content || '').length }} Zeichen)</span>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <pre class="stream-pre-fullscreen">{{ workerStreams[i - 1]?.content || '' }}<span v-if="workerStreams[i - 1]?.isStreaming" class="cursor-blink">|</span></pre>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
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
  getMultiWorkerColSize: {
    type: Number,
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
</script>

<style scoped>
.multi-worker-grid {
  overflow-y: auto;
}

.worker-col {
  display: flex;
  flex-direction: column;
}

.worker-fullscreen-card {
  transition: all 0.3s ease;
  min-height: 400px;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid transparent;
}

.worker-fullscreen-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.worker-fullscreen-card.worker-streaming {
  border-color: rgb(var(--v-theme-warning));
  box-shadow: 0 0 20px rgba(var(--v-theme-warning), 0.3);
}

.worker-fullscreen-card.worker-active {
  border-color: rgba(var(--v-theme-primary), 0.5);
}

.comparison-info {
  font-size: 12px;
}

.thread-badge {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  transition: all 0.3s ease;
}

.thread-badge.thread-a {
  background: rgba(33, 150, 243, 0.2);
  color: rgb(33, 150, 243);
  border: 2px solid rgba(33, 150, 243, 0.3);
}

.thread-badge.thread-b {
  background: rgba(76, 175, 80, 0.2);
  color: rgb(76, 175, 80);
  border: 2px solid rgba(76, 175, 80, 0.3);
}

.thread-badge.is-winner {
  transform: scale(1.2);
  box-shadow: 0 0 15px currentColor;
}

.thread-badge.thread-a.is-winner {
  background: rgb(33, 150, 243);
  color: white;
}

.thread-badge.thread-b.is-winner {
  background: rgb(76, 175, 80);
  color: white;
}

.likert-scores-fullscreen {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 12px;
  border-radius: 8px;
}

.likert-row-fullscreen {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.likert-row-fullscreen:last-child {
  margin-bottom: 0;
}

.criterion-label-full {
  width: 120px;
  font-size: 11px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.likert-dots-full {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
  gap: 3px;
}

.dots-group-full {
  display: flex;
  gap: 3px;
}

.dot-full {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.15);
  transition: all 0.2s ease;
}

.dots-group-full.dots-a .dot-full.dot-filled {
  background: rgb(33, 150, 243);
}

.dots-group-full.dots-b .dot-full.dot-filled {
  background: rgb(76, 175, 80);
}

.dot-full.dot-pending {
  animation: dot-pulse 1s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.score-divider-full {
  color: rgba(var(--v-theme-on-surface), 0.3);
  font-size: 12px;
  margin: 0 6px;
}

.analysis-steps-progress {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  padding: 8px;
  border-radius: 6px;
}

.steps-row {
  display: flex;
  justify-content: space-between;
  gap: 4px;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.4);
  transition: all 0.2s ease;
}

.step-indicator.step-complete {
  background: rgba(var(--v-theme-success), 0.15);
  color: rgb(var(--v-theme-success));
}

.step-indicator.step-active {
  background: rgba(var(--v-theme-warning), 0.2);
  color: rgb(var(--v-theme-warning));
}

.justification-fullscreen {
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.result-summary {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 16px;
  border-radius: 8px;
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

.stream-pre-fullscreen {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 11px;
  line-height: 1.4;
  color: rgb(var(--v-theme-on-surface));
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
