<template>
  <div v-if="visible" class="agent-panel" :class="[`mode-${mode}`, { expanded, processing: isProcessing }]">
    <!-- Header Bar -->
    <div class="agent-header" @click="expanded = !expanded">
      <div class="header-left">
        <div class="mode-badge">
          <div class="mode-icon-wrapper" :class="{ pulse: isProcessing }">
            <v-icon size="16">{{ modeIcon }}</v-icon>
          </div>
          <span class="mode-name">{{ modeLabel }}</span>
        </div>
        <span v-if="taskType" class="task-badge">{{ taskType === 'multihop' ? 'MULTI-HOP' : 'LOOKUP' }}</span>
      </div>

      <div class="header-right">
        <span v-if="currentStatus" class="status-pill">{{ currentStatus }}</span>
        <span v-if="iteration" class="iter-pill">Schritt {{ iteration }}</span>
        <v-icon size="18" class="chevron">{{ expanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
      </div>
    </div>

    <!-- Activity Indicator (while processing) -->
    <div v-if="isProcessing" class="activity-bar">
      <div class="activity-pulse"></div>
    </div>

    <!-- Expanded Content -->
    <v-expand-transition>
      <div v-show="expanded" ref="contentRef" class="agent-content">
        <!-- Timeline -->
        <div v-if="steps.length > 0" class="timeline">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="timeline-item"
            :class="[`type-${step.type}`, { active: index === steps.length - 1 && isProcessing }]"
          >
            <!-- Vertical line + dot -->
            <div class="timeline-rail">
              <div class="rail-line top" :class="{ hidden: index === 0 }"></div>
              <div class="rail-dot">
                <v-icon size="12">{{ getStepIcon(step.type) }}</v-icon>
              </div>
              <div class="rail-line bottom" :class="{ hidden: index === steps.length - 1 }"></div>
            </div>

            <!-- Content card -->
            <div class="timeline-card">
              <div class="card-header">
                <span class="card-label">{{ getStepLabel(step.type) }}</span>
                <span v-if="step.action" class="card-action">{{ step.action }}</span>
              </div>
              <div class="card-body">
                <template v-if="step.expanded || step.content.length <= 200">
                  {{ step.content }}
                </template>
                <template v-else>
                  {{ step.content.substring(0, 200) }}...
                  <button class="show-more" @click.stop="step.expanded = true">mehr</button>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-else class="loading-state">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
          <span>Agent denkt nach...</span>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

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

const expanded = ref(false);
const steps = ref([]);
const contentRef = ref(null);

// Auto-scroll to bottom when new steps are added
function scrollToBottom() {
  nextTick(() => {
    if (contentRef.value) {
      contentRef.value.scrollTop = contentRef.value.scrollHeight;
    }
  });
}
const currentStatus = ref('');
const iteration = ref(0);
const maxIterations = ref(0);
const mode = ref('standard');
const taskType = ref('lookup');

const visible = computed(() => {
  // Only render for agent modes (act/react/reflact) when we have steps or are processing
  return mode.value && mode.value !== 'standard' && (props.isProcessing || steps.value.length > 0 || !!props.agentStatus);
});

const modeLabel = computed(() => {
  const labels = {
    'act': 'ACT Agent',
    'react': 'ReAct Agent',
    'reflact': 'ReflAct Agent'
  };
  return labels[mode.value] || mode.value;
});

const modeIcon = computed(() => {
  const icons = {
    'act': 'mdi-play-circle',
    'react': 'mdi-head-cog',
    'reflact': 'mdi-head-sync'
  };
  return icons[mode.value] || 'mdi-robot';
});

function getStepIcon(type) {
  const icons = {
    'goal': 'mdi-flag',
    'reflection': 'mdi-mirror',
    'thought': 'mdi-lightbulb',
    'action': 'mdi-cog',
    'observation': 'mdi-eye',
    'search': 'mdi-magnify',
    'respond': 'mdi-message-reply'
  };
  return icons[type] || 'mdi-circle-small';
}

function getStepLabel(type) {
  const labels = {
    'goal': 'GOAL',
    'reflection': 'REFLECT',
    'thought': 'THOUGHT',
    'action': 'ACTION',
    'observation': 'OBSERVATION',
    'search': 'SEARCH',
    'respond': 'RESPOND'
  };
  return labels[type] || type?.toUpperCase();
}

// Parse action content to extract clean action name and parameter
function parseActionContent(action, param) {
  if (param) {
    return `${action}("${param}")`;
  }
  return action || '';
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
      currentStatus.value = 'Initialisiere...';
      expanded.value = true;
      break;

    case 'starting':
      mode.value = status.mode;
      currentStatus.value = 'Starte...';
      expanded.value = true;
      break;

    case 'iteration':
      iteration.value = status.iteration;
      maxIterations.value = status.max || maxIterations.value;
      currentStatus.value = `Iteration ${status.iteration}`;
      break;

    case 'context':
      currentStatus.value = `${status.sources_count} Quellen`;
      break;

    case 'defining_goal':
      currentStatus.value = 'Definiere Ziel...';
      break;

    case 'goal':
      steps.value.push({ type: 'goal', content: status.goal, expanded: false });
      currentStatus.value = 'Ziel definiert';
      scrollToBottom();
      break;

    case 'reflecting':
      currentStatus.value = 'Reflektiere...';
      break;

    case 'reflection':
      steps.value.push({ type: 'reflection', content: status.content, expanded: false });
      currentStatus.value = 'Reflexion';
      scrollToBottom();
      break;

    case 'thinking':
      currentStatus.value = 'Denke nach...';
      break;

    case 'thought':
      steps.value.push({ type: 'thought', content: status.content, expanded: false });
      currentStatus.value = 'Gedanke';
      scrollToBottom();
      break;

    case 'getting_action':
      currentStatus.value = 'Wähle Aktion...';
      break;

    case 'action':
      steps.value.push({
        type: 'action',
        action: status.action,
        content: parseActionContent(status.action, status.param),
        expanded: false
      });
      currentStatus.value = status.action;
      scrollToBottom();
      break;

    case 'observation':
      steps.value.push({ type: 'observation', content: status.content, expanded: false });
      currentStatus.value = 'Beobachtung';
      scrollToBottom();
      break;

    case 'generating':
      currentStatus.value = 'Generiere...';
      break;

    case 'final_answer':
      currentStatus.value = 'Fertig';
      // Keep expanded - let user close manually
      break;

    case 'max_iterations':
      currentStatus.value = 'Max. Iterationen';
      break;
  }
}, { immediate: true, flush: 'sync' });

// Keep expanded while processing
watch(() => props.isProcessing, (processing) => {
  if (processing && mode.value !== 'standard') {
    expanded.value = true;
  }
}, { immediate: true });

// Reset method
function reset() {
  steps.value = [];
  currentStatus.value = '';
  iteration.value = 0;
  mode.value = 'standard';
  taskType.value = 'lookup';
  expanded.value = false;
}

defineExpose({ reset });
</script>

<style scoped>
/* === Panel Container === */
.agent-panel {
  background: rgb(var(--v-theme-surface));
  border-radius: 16px;
  margin-bottom: 16px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Mode Themes */
.agent-panel.mode-act {
  --mode-color: var(--v-theme-primary);
  --mode-rgb: var(--v-theme-primary);
}

.agent-panel.mode-react {
  --mode-color: 76, 175, 80; /* green */
  --mode-rgb: 76, 175, 80;
}

.agent-panel.mode-reflact {
  --mode-color: 156, 39, 176; /* purple */
  --mode-rgb: 156, 39, 176;
}

.agent-panel.processing {
  box-shadow: 0 2px 12px rgba(var(--mode-rgb), 0.15);
}

/* === Header === */
.agent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.15s ease;
  user-select: none;
}

.agent-header:hover {
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mode-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-icon-wrapper {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--mode-rgb), 0.12);
  color: rgb(var(--mode-rgb));
}

.mode-icon-wrapper.pulse {
  animation: icon-pulse 1.5s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(var(--mode-rgb), 0.3); }
  50% { transform: scale(1.02); box-shadow: 0 0 0 4px rgba(var(--mode-rgb), 0); }
}

.mode-name {
  font-weight: 600;
  font-size: 14px;
  color: rgb(var(--v-theme-on-surface));
}

.task-badge {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.5px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-pill {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.iter-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(var(--mode-rgb), 0.1);
  color: rgb(var(--mode-rgb));
}

.chevron {
  color: rgba(var(--v-theme-on-surface), 0.4);
  transition: transform 0.2s ease;
}

.expanded .chevron {
  transform: rotate(180deg);
}

/* === Activity Bar (replaces progress bar) === */
.activity-bar {
  height: 3px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  overflow: hidden;
}

.activity-pulse {
  height: 100%;
  width: 30%;
  background: linear-gradient(90deg, transparent, rgb(var(--mode-rgb)), transparent);
  animation: activity-slide 1.5s ease-in-out infinite;
}

@keyframes activity-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(400%); }
}

/* === Content Area === */
.agent-content {
  padding: 0 16px 16px;
  max-height: 60vh;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--mode-rgb), 0.3) transparent;
}

.agent-content::-webkit-scrollbar {
  width: 6px;
}

.agent-content::-webkit-scrollbar-track {
  background: transparent;
}

.agent-content::-webkit-scrollbar-thumb {
  background: rgba(var(--mode-rgb), 0.3);
  border-radius: 3px;
}

.agent-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--mode-rgb), 0.5);
}

/* === Timeline === */
.timeline {
  display: flex;
  flex-direction: column;
  padding-top: 8px;
}

.timeline-item {
  display: flex;
  gap: 12px;
}

/* Rail (vertical line + dot) */
.timeline-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.rail-line {
  width: 2px;
  flex: 1;
  min-height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  transition: background 0.2s ease;
}

.rail-line.hidden {
  background: transparent;
}

.rail-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgb(var(--v-theme-surface));
  border: 2px solid rgba(var(--v-theme-on-surface), 0.15);
  color: rgba(var(--v-theme-on-surface), 0.5);
  z-index: 1;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

/* Active step animation */
.timeline-item.active .rail-dot {
  animation: dot-glow 1.2s ease-in-out infinite;
}

@keyframes dot-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--mode-rgb), 0.3); }
  50% { box-shadow: 0 0 0 6px rgba(var(--mode-rgb), 0); }
}

/* Step type colors */
.type-goal .rail-dot { border-color: #2196f3; color: #2196f3; }
.type-reflection .rail-dot { border-color: #9c27b0; color: #9c27b0; }
.type-thought .rail-dot { border-color: #ff9800; color: #ff9800; }
.type-action .rail-dot { border-color: #4caf50; color: #4caf50; }
.type-observation .rail-dot { border-color: #00bcd4; color: #00bcd4; }
.type-search .rail-dot { border-color: #3f51b5; color: #3f51b5; }
.type-respond .rail-dot { border-color: #8bc34a; color: #8bc34a; }

/* Timeline Card */
.timeline-card {
  flex: 1;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 8px;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.card-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.card-action {
  font-size: 11px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  background: rgba(76, 175, 80, 0.12);
  color: #4caf50;
  padding: 2px 8px;
  border-radius: 4px;
}

.card-body {
  font-size: 13px;
  line-height: 1.55;
  color: rgba(var(--v-theme-on-surface), 0.85);
  word-break: break-word;
}

.show-more {
  background: none;
  border: none;
  color: rgb(var(--v-theme-primary));
  font-size: 12px;
  cursor: pointer;
  padding: 0;
  margin-left: 4px;
  font-weight: 500;
}

.show-more:hover {
  text-decoration: underline;
}

/* === Loading State === */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 13px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(var(--mode-rgb), 0.5);
  animation: dot-bounce 1.2s ease-in-out infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.15s; }
.loading-dots span:nth-child(3) { animation-delay: 0.3s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(1); opacity: 0.5; }
  40% { transform: scale(1.3); opacity: 1; }
}

/* === Responsive === */
@media (max-width: 600px) {
  .agent-header {
    padding: 10px 12px;
  }

  .mode-name {
    font-size: 13px;
  }

  .task-badge {
    display: none;
  }

  .timeline-card {
    padding: 8px 10px;
  }
}
</style>
