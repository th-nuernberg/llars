<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-eye</v-icon>
      Aktueller Vergleich
      <v-spacer></v-spacer>
      <!-- Live Stream Button -->
      <v-btn
        v-if="session?.status === 'running'"
        color="error"
        variant="tonal"
        size="small"
        class="mr-2"
        :loading="reconnecting"
        @click="$emit('reconnect')"
      >
        <v-icon start :class="{ 'pulse-icon': isStreaming }">mdi-broadcast</v-icon>
        {{ isStreaming ? 'Live' : 'Verbinden' }}
      </v-btn>
      <!-- Fullscreen Button -->
      <v-btn
        color="primary"
        variant="tonal"
        size="small"
        class="mr-2"
        @click="$emit('open-fullscreen')"
      >
        <v-icon start>mdi-fullscreen</v-icon>
        Vollbild
      </v-btn>
      <v-chip size="small" variant="outlined">
        Vergleich {{ (currentComparison.comparison_index || 0) + 1 }} von {{ session?.total_comparisons }}
      </v-chip>
    </v-card-title>
    <v-divider></v-divider>

    <v-card-text>
      <v-row>
        <!-- Thread A -->
        <v-col cols="12" md="5">
          <div class="thread-container">
            <div class="thread-header">
              <v-chip color="blue" variant="flat" prepend-icon="mdi-alpha-a-circle">
                Thread A - {{ currentComparison.pillar_a_name }}
              </v-chip>
            </div>
            <v-card variant="outlined" class="mt-2 thread-card">
              <v-card-text class="pa-3">
                <div v-for="(msg, idx) in currentComparison.thread_a_messages" :key="idx" class="message-item mb-3">
                  <div class="message-role text-caption font-weight-bold mb-1" :class="msg.role === 'assistant' ? 'text-primary' : 'text-secondary'">
                    <v-icon size="small" class="mr-1">
                      {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
                    </v-icon>
                    {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                  </div>
                  <div class="message-content">{{ msg.content }}</div>
                </div>
              </v-card-text>
            </v-card>
          </div>
        </v-col>

        <!-- Center: LLM Evaluation -->
        <v-col cols="12" md="2">
          <div class="evaluation-center">
            <!-- LLM Status -->
            <v-card variant="outlined" class="text-center mb-3">
              <v-card-text class="pa-2">
                <v-icon
                  :color="currentComparison.llm_status === 'completed' ? 'success' : 'info'"
                  size="32"
                  :class="{ 'rotating': currentComparison.llm_status === 'running' }"
                >
                  {{ currentComparison.llm_status === 'completed' ? 'mdi-check-circle' : 'mdi-loading' }}
                </v-icon>
                <div class="text-caption mt-1">
                  {{ currentComparison.llm_status === 'completed' ? 'Bewertet' : 'Bewertet...' }}
                </div>
              </v-card-text>
            </v-card>

            <!-- Winner Display -->
            <v-card
              v-if="currentComparison.winner"
              variant="outlined"
              :color="currentComparison.winner === 'A' ? 'blue' : 'green'"
              class="text-center winner-card"
            >
              <v-card-text class="pa-3">
                <v-icon size="48" color="warning">mdi-trophy</v-icon>
                <div class="text-h5 font-weight-bold mt-2">
                  {{ currentComparison.winner }}
                </div>
                <div class="text-caption">Gewinner</div>
              </v-card-text>
            </v-card>

            <!-- Confidence Score -->
            <v-card v-if="currentComparison.confidence_score" variant="outlined" class="text-center mt-3">
              <v-card-text class="pa-2">
                <div class="text-caption text-medium-emphasis">Konfidenz</div>
                <div class="text-h6 font-weight-bold">
                  {{ Math.round(currentComparison.confidence_score * 100) }}%
                </div>
              </v-card-text>
            </v-card>
          </div>
        </v-col>

        <!-- Thread B -->
        <v-col cols="12" md="5">
          <div class="thread-container">
            <div class="thread-header">
              <v-chip color="green" variant="flat" prepend-icon="mdi-alpha-b-circle">
                Thread B - {{ currentComparison.pillar_b_name }}
              </v-chip>
            </div>
            <v-card variant="outlined" class="mt-2 thread-card">
              <v-card-text class="pa-3">
                <div v-for="(msg, idx) in currentComparison.thread_b_messages" :key="idx" class="message-item mb-3">
                  <div class="message-role text-caption font-weight-bold mb-1" :class="msg.role === 'assistant' ? 'text-primary' : 'text-secondary'">
                    <v-icon size="small" class="mr-1">
                      {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
                    </v-icon>
                    {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                  </div>
                  <div class="message-content">{{ msg.content }}</div>
                </div>
              </v-card-text>
            </v-card>
          </div>
        </v-col>
      </v-row>

      <!-- LLM Prompt Display -->
      <v-expansion-panels class="mt-4" :model-value="expandedPanels" @update:model-value="$emit('update:expanded-panels', $event)">
        <v-expansion-panel value="prompt">
          <v-expansion-panel-title>
            <v-icon class="mr-2">mdi-message-text</v-icon>
            LLM Prompt (an das Modell gesendet)
            <v-chip size="x-small" class="ml-2" color="info">{{ currentComparison.llm_prompt?.length || 0 }} Zeichen</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert type="info" variant="tonal" density="compact" class="mb-3">
              <strong>System Prompt:</strong> {{ currentComparison.llm_system_prompt }}
            </v-alert>
            <pre class="prompt-preview">{{ currentComparison.llm_prompt }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- LLM Stream Output - Live Formatted -->
        <v-expansion-panel value="stream">
          <v-expansion-panel-title>
            <v-icon class="mr-2" :class="{ 'rotating': isStreaming }">
              {{ isStreaming ? 'mdi-loading' : 'mdi-robot' }}
            </v-icon>
            LLM Ausgabe (Live Stream)
            <v-chip size="x-small" class="ml-2" :color="isStreaming ? 'warning' : (llmStreamContent ? 'success' : 'grey')">
              {{ isStreaming ? 'Streamt...' : (llmStreamContent ? 'Fertig' : 'Warte...') }}
            </v-chip>
            <v-chip size="x-small" class="ml-1" color="info" v-if="llmStreamContent">
              {{ llmStreamContent.length }} Zeichen
            </v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text class="stream-panel-content">
            <!-- Stream Status Header -->
            <v-alert
              :type="isStreaming ? 'warning' : 'info'"
              variant="tonal"
              density="compact"
              class="mb-3"
            >
              <div class="d-flex align-center justify-space-between">
                <span>
                  <strong>Vergleich #{{ currentComparison.comparison_index + 1 }}:</strong>
                  {{ currentComparison.pillar_a_name }} vs {{ currentComparison.pillar_b_name }}
                </span>
                <v-chip
                  size="x-small"
                  :color="isStreaming ? 'warning' : 'success'"
                  class="ml-2"
                >
                  <v-icon start size="x-small" :class="{ 'rotating': isStreaming }">
                    {{ isStreaming ? 'mdi-loading' : 'mdi-check' }}
                  </v-icon>
                  {{ isStreaming ? 'LLM generiert...' : 'Abgeschlossen' }}
                </v-chip>
              </div>
            </v-alert>

            <!-- Formatted JSON Output (when valid JSON detected) -->
            <div v-if="parsedStreamJson" class="formatted-json-output mb-3">
              <v-card variant="outlined" class="pa-3">
                <div class="text-subtitle-2 font-weight-bold mb-2 d-flex align-center">
                  <v-icon class="mr-1" size="small" color="success">mdi-check-circle</v-icon>
                  Strukturierte Bewertung
                </div>

                <!-- Winner Display -->
                <v-row class="mb-3">
                  <v-col cols="4">
                    <v-card
                      :color="parsedStreamJson.winner === 'A' ? 'success' : 'grey-lighten-3'"
                      variant="tonal"
                      class="text-center pa-2"
                    >
                      <div class="text-h5 font-weight-bold">A</div>
                      <div class="text-caption">{{ currentComparison.pillar_a_name }}</div>
                    </v-card>
                  </v-col>
                  <v-col cols="4" class="d-flex align-center justify-center">
                    <v-chip
                      :color="parsedStreamJson.winner === 'TIE' ? 'warning' : 'primary'"
                      size="large"
                    >
                      <v-icon start>mdi-trophy</v-icon>
                      {{ parsedStreamJson.winner || '?' }}
                    </v-chip>
                  </v-col>
                  <v-col cols="4">
                    <v-card
                      :color="parsedStreamJson.winner === 'B' ? 'success' : 'grey-lighten-3'"
                      variant="tonal"
                      class="text-center pa-2"
                    >
                      <div class="text-h5 font-weight-bold">B</div>
                      <div class="text-caption">{{ currentComparison.pillar_b_name }}</div>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- Confidence -->
                <div v-if="parsedStreamJson.confidence" class="mb-3">
                  <div class="text-caption text-medium-emphasis">Konfidenz</div>
                  <v-progress-linear
                    :model-value="parsedStreamJson.confidence * 100"
                    :color="parsedStreamJson.confidence >= 0.8 ? 'success' : parsedStreamJson.confidence >= 0.6 ? 'info' : 'warning'"
                    height="20"
                    rounded
                  >
                    <template v-slot:default="{ value }">
                      <strong>{{ Math.round(value) }}%</strong>
                    </template>
                  </v-progress-linear>
                </div>

                <!-- Criteria Scores -->
                <div v-if="parsedStreamJson.criteria_scores" class="criteria-scores">
                  <div class="text-subtitle-2 font-weight-bold mb-2">Kriterien-Bewertungen</div>
                  <v-table density="compact">
                    <thead>
                      <tr>
                        <th>Kriterium</th>
                        <th class="text-center">A</th>
                        <th class="text-center">B</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(scores, criterion) in parsedStreamJson.criteria_scores" :key="criterion">
                        <td>{{ formatCriterionName(criterion) }}</td>
                        <td class="text-center">
                          <v-chip size="x-small" :color="getScoreColor(scores.score_a)">
                            {{ scores.score_a }}/5
                          </v-chip>
                        </td>
                        <td class="text-center">
                          <v-chip size="x-small" :color="getScoreColor(scores.score_b)">
                            {{ scores.score_b }}/5
                          </v-chip>
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </div>

                <!-- Final Justification -->
                <div v-if="parsedStreamJson.final_justification" class="mt-3">
                  <div class="text-subtitle-2 font-weight-bold mb-1">Begründung</div>
                  <div class="text-body-2 justification-text">{{ parsedStreamJson.final_justification }}</div>
                </div>
              </v-card>
            </div>

            <!-- Raw Stream Output -->
            <div class="stream-output-container">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-subtitle-2">Raw Stream Output</span>
                <v-btn
                  size="x-small"
                  variant="text"
                  @click="$emit('copy-stream')"
                  :disabled="!llmStreamContent"
                >
                  <v-icon start size="small">mdi-content-copy</v-icon>
                  Kopieren
                </v-btn>
              </div>
              <div class="stream-output" ref="streamOutput" @scroll="$emit('stream-scroll', $event)">
                <pre v-if="llmStreamContent" class="stream-pre">{{ llmStreamContent }}<span v-if="isStreaming" class="cursor-blink">|</span></pre>
                <div v-else class="text-center text-medium-emphasis py-4">
                  <v-progress-circular v-if="isStreaming" indeterminate color="primary" class="mb-2"></v-progress-circular>
                  <v-icon v-else size="32" class="mb-2">mdi-text-box-outline</v-icon>
                  <div>{{ isStreaming ? 'Warte auf LLM-Ausgabe...' : 'Stream startet wenn der Vergleich beginnt' }}</div>
                </div>
                <!-- Follow Button (appears when user scrolls up) -->
                <v-btn
                  v-if="!autoScrollEnabled && isStreaming"
                  class="follow-btn"
                  color="primary"
                  size="small"
                  rounded
                  @click="$emit('enable-auto-scroll')"
                >
                  <v-icon start>mdi-arrow-down</v-icon>
                  Folgen
                </v-btn>
              </div>
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Chain of Thought -->
        <v-expansion-panel v-if="currentComparison.chain_of_thought" value="cot">
          <v-expansion-panel-title>
            <v-icon class="mr-2">mdi-brain</v-icon>
            Chain-of-Thought Reasoning
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div v-for="(step, idx) in currentComparison.chain_of_thought" :key="idx" class="cot-step mb-3">
              <div class="text-subtitle-2 font-weight-bold">{{ step.step_name }}</div>
              <div class="text-body-2 mt-1">{{ step.reasoning }}</div>
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- JSON Preview -->
        <v-expansion-panel value="json">
          <v-expansion-panel-title>
            <v-icon class="mr-2">mdi-code-json</v-icon>
            JSON Rohdaten
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <pre class="json-preview">{{ JSON.stringify(currentComparison, null, 2) }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card-text>
  </v-card>
</template>

<script setup>
defineProps({
  currentComparison: {
    type: Object,
    required: true
  },
  session: {
    type: Object,
    default: null
  },
  reconnecting: {
    type: Boolean,
    default: false
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  llmStreamContent: {
    type: String,
    default: ''
  },
  parsedStreamJson: {
    type: Object,
    default: null
  },
  expandedPanels: {
    type: Array,
    default: () => []
  },
  autoScrollEnabled: {
    type: Boolean,
    default: true
  },
  formatCriterionName: {
    type: Function,
    required: true
  },
  getScoreColor: {
    type: Function,
    required: true
  }
});

defineEmits(['reconnect', 'open-fullscreen', 'copy-stream', 'stream-scroll', 'enable-auto-scroll', 'update:expanded-panels']);
</script>

<style scoped>
.thread-container {
  height: 100%;
}

.thread-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.message-item {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.message-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.message-role {
  color: rgb(var(--v-theme-primary));
  text-transform: uppercase;
}

.message-content {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.evaluation-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  height: 100%;
}

.winner-card {
  animation: winnerPulse 1s ease-in-out;
}

@keyframes winnerPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.cot-step {
  padding: 12px;
  background-color: rgba(var(--v-theme-surface), 0.5);
  border-left: 3px solid rgb(var(--v-theme-primary));
  border-radius: 4px;
}

.json-preview {
  background-color: rgba(var(--v-theme-surface), 0.5);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.prompt-preview {
  background-color: rgba(var(--v-theme-info), 0.08);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 500px;
  overflow-y: auto;
}

.stream-output {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  position: relative;
}

.stream-output pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.thread-card {
  max-height: 500px;
  overflow-y: auto;
}

.stream-panel-content :deep(.v-expansion-panel-text__wrapper) {
  max-height: 500px;
  overflow-y: auto;
}

.stream-output-container {
  margin-top: 16px;
  position: relative;
}

.stream-pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
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

.formatted-json-output {
  border: 1px solid rgba(var(--v-theme-success), 0.3);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(var(--v-theme-success), 0.05) 0%, rgba(var(--v-theme-success), 0.02) 100%);
  max-height: 350px;
  overflow-y: auto;
}

.justification-text {
  background-color: rgba(var(--v-theme-surface), 0.8);
  padding: 12px;
  border-radius: 6px;
  font-style: italic;
  line-height: 1.6;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.follow-btn {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.pulse-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
