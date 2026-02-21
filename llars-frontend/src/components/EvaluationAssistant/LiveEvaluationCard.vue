<template>
  <LCard class="live-evaluation-card">
    <!-- Header -->
    <div class="live-header">
      <div class="live-indicator">
        <span class="pulse-dot"></span>
        <span class="live-label">{{ $t('evaluationAssistant.live.evaluating') }}</span>
      </div>
      <LTag variant="info" size="sm">
        {{ displayModelName }}
      </LTag>
    </div>

    <!-- Thread Info -->
    <div class="thread-info">
      <LIcon size="20" class="mr-2">mdi-email-outline</LIcon>
      <div>
        <div class="thread-name">{{ evaluation.thread_name || `Thread #${evaluation.thread_id}` }}</div>
        <div class="thread-type text-caption text-medium-emphasis">
          {{ $t(`evaluationAssistant.taskTypes.${evaluation.task_type}`) }}
        </div>
      </div>
    </div>

    <!-- Progress Animation -->
    <div class="progress-animation">
      <div class="progress-steps">
        <div
          v-for="(step, index) in progressSteps"
          :key="index"
          class="progress-step"
          :class="{ active: currentStep >= index, done: currentStep > index }"
        >
          <div class="step-icon">
            <LIcon v-if="currentStep > index" size="16">mdi-check</LIcon>
            <v-progress-circular
              v-else-if="currentStep === index"
              indeterminate
              size="16"
              width="2"
            />
            <span v-else class="step-number">{{ index + 1 }}</span>
          </div>
          <div class="step-label">{{ step }}</div>
        </div>
      </div>
    </div>

    <!-- Streaming Output (if available) -->
    <div v-if="evaluation.streaming_output" class="streaming-output">
      <div class="output-header">
        <LIcon size="16" class="mr-1">mdi-text</LIcon>
        <span>{{ $t('evaluationAssistant.live.output') }}</span>
      </div>
      <div class="output-content">
        {{ evaluation.streaming_output }}
        <span class="cursor-blink">|</span>
      </div>
    </div>

    <!-- Elapsed Time -->
    <div class="elapsed-time">
      <LIcon size="14" class="mr-1">mdi-clock-outline</LIcon>
      <span>{{ formatElapsed(evaluation.started_at) }}</span>
    </div>
  </LCard>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { parseUserProviderModelId } from '@/utils/formatters'

const { t } = useI18n()

const props = defineProps({
  evaluation: {
    type: Object,
    required: true
  }
})

const currentStep = ref(1)
const elapsedSeconds = ref(0)
let stepInterval = null
let elapsedInterval = null

const progressSteps = computed(() => {
  return [
    t('evaluationAssistant.live.steps.preparing'),
    t('evaluationAssistant.live.steps.processing'),
    t('evaluationAssistant.live.steps.analyzing'),
    t('evaluationAssistant.live.steps.completing')
  ]
})

const displayModelName = computed(() => {
  const parsed = parseUserProviderModelId(props.evaluation?.model_id)
  return parsed?.displayName || props.evaluation?.model_id || 'LLM'
})

function formatElapsed(startTime) {
  if (!startTime) return '0s'
  const start = new Date(startTime)
  const now = new Date()
  const seconds = Math.floor((now - start) / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

onMounted(() => {
  // Animate through steps
  stepInterval = setInterval(() => {
    if (currentStep.value < progressSteps.value.length - 1) {
      currentStep.value++
    }
  }, 2000)

  // Update elapsed time
  elapsedInterval = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)
})

onUnmounted(() => {
  if (stepInterval) clearInterval(stepInterval)
  if (elapsedInterval) clearInterval(elapsedInterval)
})
</script>

<style scoped>
.live-evaluation-card {
  border: 2px solid rgb(var(--v-theme-primary));
  animation: borderPulse 2s infinite;
}

@keyframes borderPulse {
  0%, 100% { border-color: rgb(var(--v-theme-primary)); }
  50% { border-color: rgba(var(--v-theme-primary), 0.5); }
}

.live-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pulse-dot {
  width: 10px;
  height: 10px;
  background: rgb(var(--v-theme-success));
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.7; }
}

.live-label {
  font-weight: 600;
  color: rgb(var(--v-theme-success));
}

.thread-info {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  margin-bottom: 16px;
}

.thread-name {
  font-weight: 500;
}

.progress-animation {
  margin-bottom: 16px;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.progress-step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 12px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.progress-step.active:not(:last-child)::after {
  background: rgb(var(--v-theme-primary));
}

.step-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--v-theme-on-surface), 0.1);
  font-size: 0.75rem;
  z-index: 1;
  margin-bottom: 4px;
}

.progress-step.active .step-icon {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.progress-step.done .step-icon {
  background: rgb(var(--v-theme-success));
  color: white;
}

.step-label {
  font-size: 0.625rem;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
  max-width: 60px;
}

.progress-step.active .step-label {
  color: rgb(var(--v-theme-primary));
  font-weight: 500;
}

.streaming-output {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.output-header {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 8px;
}

.output-content {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
}

.cursor-blink {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.elapsed-time {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
</style>
