<template>
  <div v-if="visible" class="agent-reasoning">
    <!-- Agent Mode Badge -->
    <div class="agent-header">
      <v-chip
        size="small"
        :color="modeColor"
        variant="flat"
        class="mr-2"
      >
        <v-icon start size="small">{{ modeIcon }}</v-icon>
        {{ modeLabel }}
      </v-chip>
      <v-chip
        v-if="taskType"
        size="x-small"
        variant="tonal"
      >
        {{ taskType === 'multihop' ? 'Multi-hop' : 'Look Up' }}
      </v-chip>
      <v-spacer />
      <v-btn
        icon
        variant="text"
        size="x-small"
        @click="expanded = !expanded"
      >
        <v-icon>{{ expanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
      </v-btn>
    </div>

    <!-- Reasoning Steps (Collapsible) -->
    <v-expand-transition>
      <div v-show="expanded" class="reasoning-steps">
        <!-- Current Status -->
        <div v-if="currentStatus" class="status-item">
          <v-progress-circular
            v-if="isProcessing"
            indeterminate
            size="16"
            width="2"
            color="primary"
            class="mr-2"
          />
          <span class="status-text">{{ currentStatus }}</span>
        </div>

        <!-- Steps Timeline -->
        <div v-if="steps.length > 0" class="steps-timeline">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-item"
            :class="`step-${step.type}`"
          >
            <div class="step-icon">
              <v-icon size="16" :color="getStepColor(step.type)">
                {{ getStepIcon(step.type) }}
              </v-icon>
            </div>
            <div class="step-content">
              <div class="step-label">{{ getStepLabel(step.type) }}</div>
              <div class="step-text">{{ truncateText(step.content, 200) }}</div>
            </div>
          </div>
        </div>

        <!-- Iteration Progress -->
        <div v-if="iteration && maxIterations" class="iteration-progress">
          <v-progress-linear
            :model-value="(iteration / maxIterations) * 100"
            color="primary"
            height="4"
            rounded
          />
          <div class="iteration-label">
            Iteration {{ iteration }} / {{ maxIterations }}
          </div>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  agentStatus: {
    type: Object,
    default: null
  },
  isProcessing: {
    type: Boolean,
    default: false
  }
});

const expanded = ref(true);
const steps = ref([]);
const currentStatus = ref('');
const iteration = ref(0);
const maxIterations = ref(0);
const mode = ref('standard');
const taskType = ref('lookup');

const visible = computed(() => {
  return mode.value && mode.value !== 'standard';
});

const modeLabel = computed(() => {
  const labels = {
    'act': 'ACT',
    'react': 'ReAct',
    'reflact': 'ReflAct'
  };
  return labels[mode.value] || mode.value;
});

const modeIcon = computed(() => {
  const icons = {
    'act': 'mdi-play',
    'react': 'mdi-thought-bubble',
    'reflact': 'mdi-target'
  };
  return icons[mode.value] || 'mdi-robot';
});

const modeColor = computed(() => {
  const colors = {
    'act': 'primary',
    'react': 'success',
    'reflact': 'warning'
  };
  return colors[mode.value] || 'grey';
});

function getStepIcon(type) {
  const icons = {
    'goal': 'mdi-flag',
    'reflection': 'mdi-mirror',
    'thought': 'mdi-lightbulb',
    'action': 'mdi-play-circle',
    'observation': 'mdi-eye'
  };
  return icons[type] || 'mdi-circle';
}

function getStepColor(type) {
  const colors = {
    'goal': 'info',
    'reflection': 'purple',
    'thought': 'warning',
    'action': 'success',
    'observation': 'primary'
  };
  return colors[type] || 'grey';
}

function getStepLabel(type) {
  const labels = {
    'goal': 'Ziel',
    'reflection': 'Reflexion',
    'thought': 'Gedanke',
    'action': 'Aktion',
    'observation': 'Beobachtung'
  };
  return labels[type] || type;
}

function truncateText(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// Watch for agent status updates
watch(() => props.agentStatus, (status) => {
  if (!status) return;

  const type = status.type;

  switch (type) {
    case 'init':
      mode.value = status.mode;
      taskType.value = status.task_type;
      maxIterations.value = status.max_iterations;
      steps.value = [];
      currentStatus.value = 'Agent wird initialisiert...';
      break;

    case 'starting':
      mode.value = status.mode;
      currentStatus.value = `${modeLabel.value} Agent startet...`;
      break;

    case 'iteration':
      iteration.value = status.iteration;
      maxIterations.value = status.max || maxIterations.value;
      currentStatus.value = `Iteration ${status.iteration}/${status.max}`;
      break;

    case 'context':
      currentStatus.value = `${status.sources_count} Quellen gefunden`;
      break;

    case 'defining_goal':
      currentStatus.value = 'Definiere Ziel...';
      break;

    case 'goal':
      steps.value.push({ type: 'goal', content: status.goal });
      currentStatus.value = 'Ziel definiert';
      break;

    case 'reflecting':
      currentStatus.value = 'Reflektiere...';
      break;

    case 'reflection':
      steps.value.push({ type: 'reflection', content: status.content });
      currentStatus.value = 'Reflexion abgeschlossen';
      break;

    case 'thinking':
      currentStatus.value = 'Denke nach...';
      break;

    case 'thought':
      steps.value.push({ type: 'thought', content: status.content });
      currentStatus.value = 'Gedanke formuliert';
      break;

    case 'getting_action':
      currentStatus.value = 'Wähle Aktion...';
      break;

    case 'action':
      steps.value.push({
        type: 'action',
        content: `${status.action}(${status.param || ''})`
      });
      currentStatus.value = `Führe ${status.action} aus...`;
      break;

    case 'observation':
      steps.value.push({ type: 'observation', content: status.content });
      currentStatus.value = 'Beobachtung erfasst';
      break;

    case 'generating':
      currentStatus.value = 'Generiere Antwort...';
      break;

    case 'final_answer':
      currentStatus.value = 'Finale Antwort erstellt';
      expanded.value = false; // Collapse after completion
      break;

    case 'max_iterations':
      currentStatus.value = 'Max. Iterationen erreicht';
      break;
  }
}, { immediate: true });

// Reset when processing starts
watch(() => props.isProcessing, (processing) => {
  if (processing) {
    // Keep existing steps for context
  } else {
    currentStatus.value = '';
  }
});

// Expose reset method
function reset() {
  steps.value = [];
  currentStatus.value = '';
  iteration.value = 0;
  mode.value = 'standard';
  taskType.value = 'lookup';
  expanded.value = true;
}

defineExpose({ reset });
</script>

<style scoped>
.agent-reasoning {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.agent-header {
  display: flex;
  align-items: center;
}

.reasoning-steps {
  margin-top: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  padding: 8px;
  background: rgba(var(--v-theme-primary), 0.08);
  border-radius: 4px;
  margin-bottom: 8px;
}

.status-text {
  font-size: 13px;
  color: rgb(var(--v-theme-on-surface));
}

.steps-timeline {
  margin-top: 8px;
  padding-left: 8px;
  border-left: 2px solid rgba(var(--v-theme-on-surface), 0.1);
}

.step-item {
  display: flex;
  align-items: flex-start;
  padding: 8px 0;
  margin-left: -9px;
}

.step-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgb(var(--v-theme-surface));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 2px;
}

.step-text {
  font-size: 13px;
  line-height: 1.4;
  color: rgb(var(--v-theme-on-surface));
  word-break: break-word;
}

.step-goal .step-icon {
  border-color: rgb(var(--v-theme-info));
}

.step-reflection .step-icon {
  border-color: #9c27b0;
}

.step-thought .step-icon {
  border-color: rgb(var(--v-theme-warning));
}

.step-action .step-icon {
  border-color: rgb(var(--v-theme-success));
}

.step-observation .step-icon {
  border-color: rgb(var(--v-theme-primary));
}

.iteration-progress {
  margin-top: 12px;
}

.iteration-label {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-align: center;
  margin-top: 4px;
}
</style>
