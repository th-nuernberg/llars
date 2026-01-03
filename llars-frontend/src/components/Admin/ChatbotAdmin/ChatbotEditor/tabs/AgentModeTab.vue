<!--
  ChatbotEditor - Agent Mode Tab

  Advanced agent configuration with mode selection, task types, and tool settings.
-->
<template>
  <v-form ref="formAgent">
    <v-row>
      <!-- Comprehensive Explanation Card -->
      <v-col cols="12">
        <v-card variant="outlined" class="agent-explanation-card mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon start color="primary">mdi-robot-outline</v-icon>
            <span>Agent-Modi verstehen</span>
            <v-spacer />
            <v-btn
              :icon="showExplanation ? 'mdi-chevron-up' : 'mdi-chevron-down'"
              variant="text"
              size="small"
              @click="showExplanation = !showExplanation"
            />
          </v-card-title>

          <v-expand-transition>
            <div v-show="showExplanation">
              <v-divider />
              <v-card-text>
                <!-- What are Agent Modes -->
                <div class="mb-4">
                  <div class="text-subtitle-2 mb-2">
                    <v-icon start size="small" color="info">mdi-help-circle</v-icon>
                    Was sind Agent-Modi?
                  </div>
                  <p class="text-body-2 text-medium-emphasis">
                    Agent-Modi steuern, <strong>wie</strong> der Chatbot Fragen beantwortet. Statt einer einfachen Anfrage-Antwort
                    kann der Agent mehrere Schritte durchlaufen: nachdenken, Werkzeuge nutzen (z.B. Dokumentensuche),
                    Ergebnisse auswerten und erst dann antworten.
                  </p>
                </div>

                <!-- Mode Comparison -->
                <div class="mb-4">
                  <div class="text-subtitle-2 mb-2">
                    <v-icon start size="small" color="success">mdi-compare</v-icon>
                    Ablauf-Vergleich
                  </div>
                  <div class="agent-flow-comparison">
                    <div v-for="flow in flowComparison" :key="flow.label" class="flow-item">
                      <div class="flow-label">{{ flow.label }}</div>
                      <div class="flow-steps">
                        <template v-for="(step, idx) in flow.steps" :key="idx">
                          <span :class="['flow-step', step.class]">{{ step.text }}</span>
                          <span v-if="idx < flow.steps.length - 1" class="flow-arrow">{{ flow.arrows?.[idx] || '→' }}</span>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- When to use which -->
                <div>
                  <div class="text-subtitle-2 mb-2">
                    <v-icon start size="small" color="warning">mdi-lightbulb</v-icon>
                    Empfehlungen
                  </div>
                  <v-table density="compact" class="agent-recommendations-table">
                    <thead>
                      <tr>
                        <th>Anwendungsfall</th>
                        <th>Empfohlener Modus</th>
                        <th>Grund</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="rec in recommendations" :key="rec.useCase">
                        <td>{{ rec.useCase }}</td>
                        <td><LTag :variant="rec.variant" size="sm">{{ rec.mode }}</LTag></td>
                        <td class="text-caption">{{ rec.reason }}</td>
                      </tr>
                    </tbody>
                  </v-table>
                </div>
              </v-card-text>
            </div>
          </v-expand-transition>

          <!-- Collapsed summary -->
          <v-card-text v-if="!showExplanation" class="pt-0">
            <div class="text-body-2 text-medium-emphasis">
              Agent-Modi steuern wie der Chatbot Fragen beantwortet: von einfacher Antwort (Standard)
              bis zu mehrstufigem Reasoning mit Tool-Nutzung (ReflAct).
              <a href="#" class="text-primary" @click.prevent="showExplanation = true">Mehr erfahren...</a>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Agent Mode Selection Cards -->
      <v-col cols="12">
        <div class="d-flex align-center mb-2">
          <div class="text-subtitle-2">Agent-Modus wählen</div>
        </div>
        <div class="agent-mode-grid">
          <v-card
            v-for="mode in agentModes"
            :key="mode.value"
            :class="['agent-mode-card', { 'agent-mode-card--selected': formData.prompt_settings.agent_mode === mode.value }]"
            variant="outlined"
            @click="formData.prompt_settings.agent_mode = mode.value"
          >
            <v-card-text>
              <!-- Header -->
              <div class="d-flex align-center mb-2">
                <v-icon :color="mode.color" size="28" class="mr-2">{{ mode.icon }}</v-icon>
                <span class="text-h6 font-weight-bold">{{ mode.label }}</span>
                <LTag v-if="mode.badge" :variant="mode.badgeColor" size="sm" class="ml-auto">
                  {{ mode.badge }}
                </LTag>
              </div>

              <!-- Description -->
              <div class="text-body-2 mb-3">{{ mode.description }}</div>

              <!-- Details (shown on selection) -->
              <v-expand-transition>
                <div v-if="formData.prompt_settings.agent_mode === mode.value" class="mode-details mb-3">
                  <div class="text-caption text-medium-emphasis mb-2">{{ mode.details }}</div>
                  <div class="mode-example">
                    <v-icon size="small" class="mr-1">mdi-code-tags</v-icon>
                    <code class="text-caption">{{ mode.example }}</code>
                  </div>
                </div>
              </v-expand-transition>

              <!-- Tags -->
              <div class="d-flex align-center flex-wrap ga-2">
                <LTag variant="info" size="sm" prepend-icon="mdi-api">
                  {{ mode.calls }}
                </LTag>
                <LTag v-if="mode.tools" variant="success" size="sm" prepend-icon="mdi-tools">
                  Tools
                </LTag>
                <LTag v-if="mode.value === 'standard'" variant="gray" size="sm" prepend-icon="mdi-speedometer">
                  Schnell
                </LTag>
                <LTag v-if="mode.value === 'reflact'" variant="warning" size="sm" prepend-icon="mdi-brain">
                  Komplex
                </LTag>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </v-col>

      <!-- Task Type Selection (for non-standard modes) -->
      <v-col v-if="formData.prompt_settings.agent_mode !== 'standard'" cols="12">
        <div class="d-flex align-center mb-2">
          <div class="text-subtitle-2">Task-Typ</div>
          <LInfoTooltip title="Task-Typen" :max-width="420" class="ml-2">
            <ul>
              <li>Look Up: einfache Fakten-Suche mit wenigen Tool-Aufrufen.</li>
              <li>Multi-hop: mehrschrittige Fragen, mehr Iterationen und Tokens.</li>
            </ul>
          </LInfoTooltip>
        </div>
        <div class="task-type-grid">
          <v-card
            v-for="task in taskTypes"
            :key="task.value"
            :class="['task-type-card', { 'task-type-card--selected': formData.prompt_settings.task_type === task.value }]"
            variant="outlined"
            @click="formData.prompt_settings.task_type = task.value"
          >
            <v-card-text class="pa-3">
              <div class="d-flex align-center mb-1">
                <v-icon color="primary" size="20" class="mr-2">{{ task.icon }}</v-icon>
                <span class="font-weight-medium">{{ task.label }}</span>
                <LTag v-if="task.badge" :variant="task.badgeColor" size="sm" class="ml-auto">
                  {{ task.badge }}
                </LTag>
              </div>
              <div class="text-caption text-medium-emphasis">{{ task.description }}</div>
            </v-card-text>
          </v-card>
        </div>
      </v-col>

      <!-- Configuration Matrix Info -->
      <v-col v-if="formData.prompt_settings.agent_mode !== 'standard'" cols="12">
        <v-alert type="success" variant="tonal" density="compact">
          <div class="d-flex align-center">
            <v-icon start>mdi-information</v-icon>
            <span>
              Aktuelle Konfiguration:
              <strong>{{ agentModes.find(m => m.value === formData.prompt_settings.agent_mode)?.label }}</strong>
              +
              <strong>{{ taskTypes.find(t => t.value === formData.prompt_settings.task_type)?.label }}</strong>
            </span>
          </div>
        </v-alert>
      </v-col>

      <!-- Max Iterations (for agent modes) -->
      <v-col v-if="isAgentMode" cols="12" md="6">
        <v-text-field
          v-model.number="formData.prompt_settings.agent_max_iterations"
          label="Max. Iterationen"
          type="number"
          :min="1"
          :max="10"
          hint="Maximale Anzahl an Agent-Zyklen"
          persistent-hint
          variant="outlined"
          density="comfortable"
        />
      </v-col>

      <!-- Tools Configuration -->
      <v-col v-if="isAgentMode" cols="12" md="6">
        <v-select
          v-model="formData.prompt_settings.tools_enabled"
          :items="availableAgentTools"
          label="Aktivierte Tools"
          multiple
          chips
          closable-chips
          hint="Welche Tools der Agent nutzen darf"
          persistent-hint
          variant="outlined"
          density="comfortable"
        />
      </v-col>

      <!-- Web Search Configuration -->
      <v-col v-if="isAgentMode" cols="12">
        <v-card variant="outlined">
          <v-card-title class="text-subtitle-1 d-flex align-center">
            <v-icon start color="info">mdi-web</v-icon>
            Web-Suche (Tavily)
            <LTag v-if="formData.prompt_settings.web_search_enabled" variant="success" size="sm" class="ml-2">
              Aktiv
            </LTag>
          </v-card-title>
          <v-card-text>
            <v-switch
              v-model="formData.prompt_settings.web_search_enabled"
              label="Web-Suche aktivieren"
              color="info"
              hide-details
              class="mb-3"
            />
            <div v-if="formData.prompt_settings.web_search_enabled" class="mt-3">
              <v-text-field
                v-model.number="formData.prompt_settings.web_search_max_results"
                label="Max. Web-Ergebnisse"
                type="number"
                :min="1"
                :max="10"
                hint="Anzahl der Web-Suchergebnisse pro Anfrage"
                persistent-hint
                variant="outlined"
                density="comfortable"
              />
              <v-alert type="info" variant="tonal" density="compact" class="mt-3">
                <v-icon start size="small">mdi-key</v-icon>
                Der Tavily API-Key wird über Umgebungsvariablen konfiguriert (TAVILY_API_KEY)
              </v-alert>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ACT Settings -->
      <v-col v-if="formData.prompt_settings.agent_mode === 'act'" cols="12">
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon start>mdi-play</v-icon>
              ACT System-Prompt anpassen
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-textarea
                v-model="formData.prompt_settings.act_system_prompt"
                label="ACT System-Prompt"
                hint="Instruktionen für den Action-only Prozess"
                persistent-hint
                rows="8"
                variant="outlined"
                density="comfortable"
              />
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>

      <!-- ReAct Settings -->
      <v-col v-if="formData.prompt_settings.agent_mode === 'react'" cols="12">
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon start>mdi-thought-bubble</v-icon>
              ReAct System-Prompt anpassen
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-textarea
                v-model="formData.prompt_settings.react_system_prompt"
                label="ReAct System-Prompt"
                hint="Instruktionen für den THOUGHT → ACTION → OBSERVATION Prozess"
                persistent-hint
                rows="12"
                variant="outlined"
                density="comfortable"
              />
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>

      <!-- ReflAct Settings -->
      <v-col v-if="formData.prompt_settings.agent_mode === 'reflact'" cols="12">
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon start>mdi-target</v-icon>
              ReflAct System-Prompt anpassen
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-textarea
                v-model="formData.prompt_settings.reflact_system_prompt"
                label="ReflAct System-Prompt"
                hint="Instruktionen für den GOAL → REFLECTION → ACTION Prozess"
                persistent-hint
                rows="14"
                variant="outlined"
                density="comfortable"
              />
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>

      <!-- Reflection Prompt (cross-mode) -->
      <v-col v-if="formData.prompt_settings.agent_mode !== 'standard'" cols="12">
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon start>mdi-check-decagram</v-icon>
              Reflection Prompt anpassen
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-textarea
                v-model="formData.prompt_settings.reflection_prompt"
                label="Reflection Prompt"
                hint="Instruktionen fuer die kritische Selbstpruefung der Antwort"
                persistent-hint
                rows="10"
                variant="outlined"
                density="comfortable"
              />
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </v-form>
</template>

<script setup>
/**
 * @component AgentModeTab
 * @description Advanced agent configuration with mode selection, task types, and tool settings.
 */
import { ref, computed } from 'vue';
import { AGENT_MODES, TASK_TYPES, AVAILABLE_AGENT_TOOLS } from '../constants';

const props = defineProps({
  /** Form data object */
  formData: {
    type: Object,
    required: true
  }
});

// Re-export constants for template
const agentModes = AGENT_MODES;
const taskTypes = TASK_TYPES;
const availableAgentTools = AVAILABLE_AGENT_TOOLS;

// Local state
const showExplanation = ref(false);

// Computed
const isAgentMode = computed(() =>
  ['act', 'react', 'reflact'].includes(props.formData.prompt_settings?.agent_mode)
);

// Flow comparison data for explanation
const flowComparison = [
  {
    label: 'Standard',
    steps: [
      { text: 'Frage', class: 'step-query' },
      { text: 'LLM', class: 'step-llm' },
      { text: 'Antwort', class: 'step-answer' }
    ]
  },
  {
    label: 'ACT',
    steps: [
      { text: 'Frage', class: 'step-query' },
      { text: 'ACTION', class: 'step-action' },
      { text: 'OBSERVATION', class: 'step-observation' },
      { text: 'Antwort', class: 'step-answer' }
    ]
  },
  {
    label: 'ReAct',
    steps: [
      { text: 'Frage', class: 'step-query' },
      { text: 'THOUGHT', class: 'step-thought' },
      { text: 'ACTION', class: 'step-action' },
      { text: 'OBSERVATION', class: 'step-observation' },
      { text: 'Antwort', class: 'step-answer' }
    ],
    arrows: ['→', '→', '→', '↺']
  },
  {
    label: 'ReflAct',
    steps: [
      { text: 'Aufgabe', class: 'step-query' },
      { text: 'REFLECTION', class: 'step-reflection' },
      { text: 'ACTION', class: 'step-action' },
      { text: 'OBSERVATION', class: 'step-observation' },
      { text: 'Antwort', class: 'step-answer' }
    ],
    arrows: ['→', '→', '→', '↺']
  }
];

// Recommendations data
const recommendations = [
  { useCase: 'Einfache FAQ, Smalltalk', mode: 'Standard', variant: 'gray', reason: 'Schnell, keine Tool-Nutzung nötig' },
  { useCase: 'Fakten aus Dokumenten', mode: 'ReAct', variant: 'success', reason: 'Nachvollziehbarer Suchprozess' },
  { useCase: 'Schnelle Tool-Nutzung', mode: 'ACT', variant: 'primary', reason: 'Weniger Tokens, schneller' },
  { useCase: 'Komplexe Multi-Hop Fragen', mode: 'ReflAct', variant: 'warning', reason: 'Selbstkorrektur durch Ziel-Reflexion' }
];
</script>

<style scoped>
/* Agent Mode Grid */
.agent-mode-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 600px) {
  .agent-mode-grid {
    grid-template-columns: 1fr;
  }
}

.agent-mode-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.agent-mode-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.5);
  background-color: rgba(var(--v-theme-primary), 0.04);
}

.agent-mode-card--selected {
  border-color: rgb(var(--v-theme-primary)) !important;
  background-color: rgba(var(--v-theme-primary), 0.08) !important;
}

/* Mode Details */
.mode-details {
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px 2px 8px 2px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.mode-example {
  display: flex;
  align-items: flex-start;
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 4px;
  overflow-x: auto;
}

.mode-example code {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  word-break: break-word;
  white-space: pre-wrap;
}

/* Agent Explanation Card */
.agent-explanation-card {
  border-radius: 12px 4px 12px 4px;
}

/* Flow Comparison Visualization */
.agent-flow-comparison {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.flow-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px 2px 8px 2px;
}

.flow-label {
  min-width: 70px;
  font-weight: 600;
  font-size: 13px;
}

.flow-steps {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.flow-step {
  padding: 4px 8px;
  border-radius: 6px 2px 6px 2px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.flow-arrow {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 14px;
}

/* Flow Step Colors */
.step-query {
  background: rgba(var(--v-theme-info), 0.2);
  color: rgb(var(--v-theme-info));
}

.step-llm {
  background: rgba(var(--v-theme-primary), 0.2);
  color: rgb(var(--v-theme-primary));
}

.step-answer {
  background: rgba(var(--v-theme-success), 0.2);
  color: rgb(var(--v-theme-success));
}

.step-thought {
  background: rgba(103, 58, 183, 0.2);
  color: #673ab7;
}

.step-action {
  background: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.step-observation {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.step-reflection {
  background: rgba(0, 188, 212, 0.2);
  color: #00bcd4;
}

/* Recommendations Table */
.agent-recommendations-table {
  font-size: 13px;
}

.agent-recommendations-table th {
  font-weight: 600 !important;
  background: rgba(var(--v-theme-surface-variant), 0.5) !important;
}

.agent-recommendations-table td {
  padding: 8px 12px !important;
}

/* Task Type Grid */
.task-type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

@media (max-width: 600px) {
  .task-type-grid {
    grid-template-columns: 1fr;
  }
}

.task-type-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.task-type-card:hover {
  border-color: rgba(var(--v-theme-info), 0.5);
  background-color: rgba(var(--v-theme-info), 0.04);
}

.task-type-card--selected {
  border-color: rgb(var(--v-theme-info)) !important;
  background-color: rgba(var(--v-theme-info), 0.08) !important;
}

.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}
</style>
