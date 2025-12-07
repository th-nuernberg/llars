<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    fullscreen
    transition="dialog-bottom-transition"
    class="fullscreen-dialog"
  >
    <v-card class="fullscreen-card d-flex flex-column">
      <!-- Header -->
      <v-toolbar color="primary" density="compact">
        <v-btn icon @click="$emit('close')">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>
          <v-icon class="mr-2" :class="{ 'pulse-icon': isStreaming }">mdi-broadcast</v-icon>
          Live Vergleich #{{ (currentComparison?.comparison_index || 0) + 1 }}
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <v-chip
          :color="isStreaming ? 'error' : 'success'"
          class="mr-2"
          variant="flat"
        >
          <v-icon start size="small" :class="{ 'rotating': isStreaming }">
            {{ isStreaming ? 'mdi-loading' : 'mdi-check-circle' }}
          </v-icon>
          {{ isStreaming ? 'Streamt...' : 'Abgeschlossen' }}
        </v-chip>
        <v-chip color="white" variant="outlined" class="mr-2">
          {{ currentComparison?.pillar_a_name }} vs {{ currentComparison?.pillar_b_name }}
        </v-chip>
      </v-toolbar>

      <!-- Main Content -->
      <v-container fluid class="flex-grow-1 pa-4 fullscreen-content">
        <v-row class="h-100">
          <!-- Left: Thread A -->
          <v-col cols="12" md="3" class="d-flex flex-column">
            <v-card class="flex-grow-1 d-flex flex-column" variant="outlined">
              <v-card-title class="bg-blue py-2">
                <v-icon class="mr-2">mdi-alpha-a-circle</v-icon>
                Thread A - {{ currentComparison?.pillar_a_name }}
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="flex-grow-1 overflow-y-auto thread-scroll">
                <div v-for="(msg, idx) in currentComparison?.thread_a_messages" :key="idx" class="message-item mb-3">
                  <div class="message-role text-caption font-weight-bold mb-1" :class="msg.role === 'assistant' ? 'text-primary' : 'text-secondary'">
                    <v-icon size="small" class="mr-1">
                      {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
                    </v-icon>
                    {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                  </div>
                  <div class="message-content text-body-2">{{ msg.content }}</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Center: Live Stream -->
          <v-col cols="12" md="6" class="d-flex flex-column">
            <v-card class="flex-grow-1 d-flex flex-column" variant="outlined">
              <v-card-title class="bg-primary py-2 d-flex align-center">
                <v-icon class="mr-2" :class="{ 'rotating': isStreaming }">
                  {{ isStreaming ? 'mdi-loading' : 'mdi-robot' }}
                </v-icon>
                LLM Live Output
                <v-spacer></v-spacer>
                <!-- Display Mode Toggle -->
                <v-btn-toggle
                  :model-value="streamDisplayMode"
                  @update:model-value="$emit('update:streamDisplayMode', $event)"
                  density="compact"
                  mandatory
                  class="mr-2"
                  color="white"
                  variant="outlined"
                >
                  <v-btn value="raw" size="small">
                    <v-icon start size="small">mdi-code-braces</v-icon>
                    Raw
                  </v-btn>
                  <v-btn value="formatted" size="small">
                    <v-icon start size="small">mdi-format-list-bulleted</v-icon>
                    Formatiert
                  </v-btn>
                </v-btn-toggle>
                <v-chip size="small" color="white" variant="outlined" class="mr-2">
                  {{ llmStreamContent.length }} Zeichen
                </v-chip>
                <v-btn
                  icon="mdi-content-copy"
                  size="small"
                  variant="text"
                  @click="$emit('copy-stream')"
                  :disabled="!llmStreamContent"
                ></v-btn>
              </v-card-title>
              <v-divider></v-divider>

              <!-- Result Display - ALWAYS VISIBLE with Likert Scales -->
              <div class="pa-3 result-display-header">
                <v-row dense>
                  <!-- Side A with Name -->
                  <v-col cols="4" class="text-center">
                    <v-card
                      :color="parsedStreamJson?.winner === 'A' ? 'success' : (isStreaming ? 'grey-darken-1' : 'grey-lighten-2')"
                      variant="tonal"
                      class="pa-3 winner-card-fullscreen"
                      :class="{ 'winner-highlight': parsedStreamJson?.winner === 'A' }"
                    >
                      <div class="text-h4 font-weight-bold">A</div>
                      <div class="text-caption">{{ currentComparison?.pillar_a_name }}</div>
                    </v-card>
                  </v-col>

                  <!-- Center: Winner + Confidence -->
                  <v-col cols="4" class="d-flex flex-column align-center justify-center">
                    <v-chip
                      :color="parsedStreamJson?.winner ? 'primary' : 'grey'"
                      size="x-large"
                      class="mb-2"
                      :class="{ 'pulse-chip': isStreaming && !parsedStreamJson?.winner }"
                    >
                      <v-icon start :class="{ 'rotating': isStreaming && !parsedStreamJson?.winner }">
                        {{ isStreaming && !parsedStreamJson?.winner ? 'mdi-loading' : 'mdi-trophy' }}
                      </v-icon>
                      {{ parsedStreamJson?.winner || (isStreaming ? '...' : '?') }}
                    </v-chip>
                    <div class="text-center">
                      <div class="text-caption text-medium-emphasis">Konfidenz</div>
                      <div class="text-h6 font-weight-bold">
                        {{ parsedStreamJson?.confidence ? Math.round(parsedStreamJson.confidence * 100) + '%' : (isStreaming ? '...' : '-') }}
                      </div>
                    </div>
                  </v-col>

                  <!-- Side B with Name -->
                  <v-col cols="4" class="text-center">
                    <v-card
                      :color="parsedStreamJson?.winner === 'B' ? 'success' : (isStreaming ? 'grey-darken-1' : 'grey-lighten-2')"
                      variant="tonal"
                      class="pa-3 winner-card-fullscreen"
                      :class="{ 'winner-highlight': parsedStreamJson?.winner === 'B' }"
                    >
                      <div class="text-h4 font-weight-bold">B</div>
                      <div class="text-caption">{{ currentComparison?.pillar_b_name }}</div>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- Likert Scales for all criteria - ALWAYS visible with placeholders -->
                <v-row dense class="mt-3">
                  <v-col cols="12">
                    <div class="likert-scales-container">
                      <div
                        v-for="criterion in scoreCriteria"
                        :key="criterion.key"
                        class="likert-row"
                      >
                        <!-- Criterion Label -->
                        <div class="likert-label text-caption">{{ criterion.label }}</div>

                        <!-- A Score Likert -->
                        <div class="likert-scale likert-a">
                          <div
                            v-for="n in 5"
                            :key="`a-${n}`"
                            class="likert-dot"
                            :class="{
                              'likert-active': parsedStreamJson?.scores?.A?.[criterion.key] >= n,
                              'likert-pending': !parsedStreamJson?.scores?.A?.[criterion.key] && isStreaming,
                              'likert-a-color': parsedStreamJson?.scores?.A?.[criterion.key] >= n
                            }"
                          >
                            <span v-if="n === parsedStreamJson?.scores?.A?.[criterion.key]" class="likert-value">{{ n }}</span>
                          </div>
                        </div>

                        <!-- VS Divider -->
                        <div class="likert-vs text-caption text-medium-emphasis">vs</div>

                        <!-- B Score Likert -->
                        <div class="likert-scale likert-b">
                          <div
                            v-for="n in 5"
                            :key="`b-${n}`"
                            class="likert-dot"
                            :class="{
                              'likert-active': parsedStreamJson?.scores?.B?.[criterion.key] >= n,
                              'likert-pending': !parsedStreamJson?.scores?.B?.[criterion.key] && isStreaming,
                              'likert-b-color': parsedStreamJson?.scores?.B?.[criterion.key] >= n
                            }"
                          >
                            <span v-if="n === parsedStreamJson?.scores?.B?.[criterion.key]" class="likert-value">{{ n }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </v-col>
                </v-row>
              </div>

              <v-divider></v-divider>

              <!-- Stream Output - Raw or Formatted -->
              <v-card-text
                class="flex-grow-1 overflow-y-auto stream-scroll position-relative"
                ref="streamOutputRef"
                @scroll="$emit('stream-scroll', $event)"
              >
                <!-- Empty State -->
                <div v-if="!llmStreamContent" class="d-flex flex-column align-center justify-center h-100 text-medium-emphasis">
                  <v-progress-circular v-if="isStreaming" indeterminate size="64" color="primary" class="mb-4"></v-progress-circular>
                  <v-icon v-else size="64" class="mb-4">mdi-text-box-outline</v-icon>
                  <div class="text-h6">{{ isStreaming ? 'Warte auf LLM-Ausgabe...' : 'Stream startet wenn der Vergleich beginnt' }}</div>
                </div>

                <!-- RAW Mode -->
                <pre v-else-if="streamDisplayMode === 'raw'" class="stream-pre-fullscreen">{{ llmStreamContent }}<span v-if="isStreaming" class="cursor-blink">|</span></pre>

                <!-- FORMATTED Mode -->
                <div v-else class="formatted-stream-view">
                  <!-- Pre-structured Step Areas - ALL 6 steps always visible -->
                  <div class="structured-steps-container">
                    <div
                      v-for="(stepDef, stepKey) in stepDefinitions"
                      :key="stepKey"
                      class="structured-step"
                      :class="{
                        'step-active': getStepByKey(stepKey),
                        'step-streaming': getStepByKey(stepKey)?.isStreaming,
                        'step-pending': !getStepByKey(stepKey) && isStreaming
                      }"
                    >
                      <!-- Step Header - Always visible -->
                      <div class="step-header d-flex align-center">
                        <v-avatar
                          size="28"
                          :color="getStepByKey(stepKey) ? 'primary' : 'grey'"
                          class="mr-2"
                        >
                          <v-icon size="16" :class="{ 'rotating': getStepByKey(stepKey)?.isStreaming }">
                            {{ getStepByKey(stepKey)?.isStreaming ? 'mdi-loading' : stepDef.icon }}
                          </v-icon>
                        </v-avatar>
                        <span class="step-title" :class="{ 'text-medium-emphasis': !getStepByKey(stepKey) }">
                          {{ stepDef.title }}
                        </span>
                        <v-spacer></v-spacer>
                        <v-icon
                          v-if="getStepByKey(stepKey) && !getStepByKey(stepKey)?.isStreaming"
                          size="small"
                          color="success"
                        >
                          mdi-check-circle
                        </v-icon>
                        <v-progress-circular
                          v-else-if="getStepByKey(stepKey)?.isStreaming"
                          indeterminate
                          size="16"
                          width="2"
                          color="warning"
                        ></v-progress-circular>
                      </div>

                      <!-- Step Content - Shows when step is active -->
                      <div class="step-content" v-if="getStepByKey(stepKey)">
                        <div class="step-text">
                          {{ getStepByKey(stepKey).content }}<span v-if="getStepByKey(stepKey)?.isStreaming" class="cursor-blink">|</span>
                        </div>
                      </div>

                      <!-- Placeholder when waiting -->
                      <div class="step-placeholder" v-else-if="isStreaming">
                        <span class="text-caption text-medium-emphasis">Warte auf Analyse...</span>
                      </div>
                    </div>
                  </div>

                  <!-- Final Justification - at the bottom -->
                  <div v-if="parsedStreamJson?.final_justification" class="justification-section mt-4">
                    <div class="d-flex align-center mb-2">
                      <v-icon size="small" color="primary" class="mr-2">mdi-text-box-check</v-icon>
                      <span class="text-subtitle-2 font-weight-bold">Abschließende Begründung</span>
                    </div>
                    <v-card variant="tonal" color="primary" class="pa-3">
                      <div class="text-body-2">{{ parsedStreamJson.final_justification }}</div>
                    </v-card>
                  </div>

                  <!-- Raw JSON Preview (collapsed) -->
                  <v-expansion-panels class="mt-4" variant="accordion">
                    <v-expansion-panel>
                      <v-expansion-panel-title class="py-2">
                        <v-icon size="small" class="mr-2">mdi-code-json</v-icon>
                        <span class="text-caption">Raw JSON anzeigen</span>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <pre class="stream-pre-fullscreen text-caption">{{ llmStreamContent }}</pre>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </div>

                <!-- Follow Button - shows when auto-scroll is disabled -->
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
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Right: Thread B -->
          <v-col cols="12" md="3" class="d-flex flex-column">
            <v-card class="flex-grow-1 d-flex flex-column" variant="outlined">
              <v-card-title class="bg-green py-2">
                <v-icon class="mr-2">mdi-alpha-b-circle</v-icon>
                Thread B - {{ currentComparison?.pillar_b_name }}
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="flex-grow-1 overflow-y-auto thread-scroll">
                <div v-for="(msg, idx) in currentComparison?.thread_b_messages" :key="idx" class="message-item mb-3">
                  <div class="message-role text-caption font-weight-bold mb-1" :class="msg.role === 'assistant' ? 'text-primary' : 'text-secondary'">
                    <v-icon size="small" class="mr-1">
                      {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
                    </v-icon>
                    {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                  </div>
                  <div class="message-content text-body-2">{{ msg.content }}</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>

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
defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  currentComparison: {
    type: Object,
    default: null
  },
  session: {
    type: Object,
    default: null
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
  streamDisplayMode: {
    type: String,
    default: 'raw'
  },
  autoScrollEnabled: {
    type: Boolean,
    default: true
  },
  progress: {
    type: Number,
    default: 0
  },
  scoreCriteria: {
    type: Array,
    required: true
  },
  stepDefinitions: {
    type: Object,
    required: true
  },
  getStepByKey: {
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
  }
});

defineEmits([
  'update:modelValue',
  'update:streamDisplayMode',
  'close',
  'copy-stream',
  'stream-scroll',
  'enable-auto-scroll'
]);
</script>

<style scoped>
/* Import relevant styles from parent component */
.fullscreen-card {
  height: 100vh;
  overflow: hidden;
}

.fullscreen-content {
  overflow: hidden;
}

.fullscreen-content .h-100 {
  height: 100%;
}

.thread-scroll {
  max-height: calc(100vh - 250px);
}

.stream-scroll {
  max-height: calc(100vh - 400px);
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

.stream-pre-fullscreen {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
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

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pulse-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

.result-display-header {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.8) 0%, rgba(var(--v-theme-surface-variant), 0.4) 100%);
  min-height: 120px;
}

.winner-card-fullscreen {
  transition: all 0.3s ease;
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

.likert-scales-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 12px;
}

.likert-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.likert-label {
  width: 140px;
  flex-shrink: 0;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.likert-scale {
  display: flex;
  gap: 4px;
  align-items: center;
}

.likert-vs {
  width: 30px;
  text-align: center;
  flex-shrink: 0;
}

.likert-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border: 2px solid rgba(var(--v-theme-on-surface), 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  position: relative;
}

.likert-dot.likert-pending {
  animation: likert-pulse 1.5s ease-in-out infinite;
}

.likert-dot.likert-active {
  transform: scale(1.1);
}

.likert-dot.likert-a-color {
  background: rgba(33, 150, 243, 0.8);
  border-color: rgb(33, 150, 243);
}

.likert-dot.likert-b-color {
  background: rgba(76, 175, 80, 0.8);
  border-color: rgb(76, 175, 80);
}

.likert-value {
  color: white;
  font-size: 10px;
  font-weight: bold;
}

@keyframes likert-pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.05);
  }
}

.winner-highlight {
  animation: winner-glow 2s ease-in-out infinite;
}

@keyframes winner-glow {
  0%, 100% {
    box-shadow: 0 0 5px rgba(var(--v-theme-success), 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(var(--v-theme-success), 0.6);
  }
}

.structured-steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.structured-step {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 8px;
  border-left: 4px solid rgba(var(--v-theme-on-surface), 0.2);
  overflow: hidden;
  transition: all 0.3s ease;
}

.structured-step.step-active {
  border-left-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.08);
}

.structured-step.step-streaming {
  border-left-color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.1);
  box-shadow: 0 2px 8px rgba(var(--v-theme-warning), 0.2);
}

.structured-step.step-pending {
  opacity: 0.6;
}

.step-header {
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.step-title {
  font-weight: 600;
  font-size: 14px;
}

.step-content {
  padding: 0 16px 16px 16px;
}

.step-text {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.9);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.step-placeholder {
  padding: 8px 16px 12px 16px;
  min-height: 32px;
}

.justification-section {
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 8px;
  padding: 16px;
}

.formatted-stream-view {
  padding: 8px;
}

.follow-btn {
  position: sticky;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: bounce-in 0.3s ease-out;
}

@keyframes bounce-in {
  0% {
    transform: translateX(-50%) translateY(20px);
    opacity: 0;
  }
  100% {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

.position-relative {
  position: relative;
}
</style>
