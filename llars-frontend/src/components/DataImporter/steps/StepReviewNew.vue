<template>
  <div class="step-review pa-6">
    <!-- Configuration Grid -->
    <div class="config-grid">
      <!-- Left: Scenario Config -->
      <div class="config-section">
        <div class="section-header">
          <LIcon size="20" class="mr-2" color="primary">mdi-folder-cog</LIcon>
          <span>Szenario-Einstellungen</span>
        </div>

        <div class="config-form">
          <!-- Scenario Name -->
          <div class="form-field">
            <label class="field-label">Name *</label>
            <input
              v-model="localScenarioConfig.name"
              type="text"
              class="text-input"
              placeholder="z.B. Chatbot-Evaluation Q1 2026"
            />
          </div>

          <!-- Task Type -->
          <div class="form-field">
            <label class="field-label">Evaluationstyp</label>
            <div class="task-type-grid">
              <button
                v-for="taskType in taskTypes"
                :key="taskType.value"
                class="task-type-btn"
                :class="{ 'task-type-btn--selected': localScenarioConfig.taskType === taskType.value }"
                @click="localScenarioConfig.taskType = taskType.value"
              >
                <LIcon size="20" class="mb-1">{{ taskType.icon }}</LIcon>
                <span class="task-type-label">{{ taskType.label }}</span>
              </button>
            </div>
          </div>

          <!-- Date Range -->
          <div class="form-field">
            <label class="field-label">Zeitraum</label>
            <div class="date-inputs">
              <input
                v-model="localScenarioConfig.beginDate"
                type="date"
                class="text-input text-input--small"
              />
              <span class="date-separator">bis</span>
              <input
                v-model="localScenarioConfig.endDate"
                type="date"
                class="text-input text-input--small"
                :min="localScenarioConfig.beginDate"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Analysis Summary -->
      <div class="config-section">
        <div class="section-header">
          <LIcon size="20" class="mr-2" color="success">mdi-check-decagram</LIcon>
          <span>KI-Analyse</span>
        </div>

        <div v-if="analysisResult" class="analysis-summary">
          <!-- Task Description -->
          <div class="summary-item">
            <div class="summary-label">Erkanntes Ziel</div>
            <div class="summary-value">{{ analysisResult.task_description || 'Daten bewerten' }}</div>
          </div>

          <!-- Field Mapping -->
          <div v-if="Object.keys(analysisResult.field_mapping || {}).length" class="summary-item">
            <div class="summary-label">Feld-Mapping</div>
            <div class="mapping-preview">
              <div
                v-for="(target, source) in analysisResult.field_mapping"
                :key="source"
                class="mapping-item"
              >
                <code>{{ source }}</code>
                <LIcon size="12" class="mx-1">mdi-arrow-right</LIcon>
                <span>{{ target }}</span>
              </div>
            </div>
          </div>

          <!-- Role Mapping -->
          <div v-if="analysisResult.role_mapping" class="summary-item">
            <div class="summary-label">Rollen</div>
            <div class="role-chips">
              <div
                v-for="(llarsRole, dataRole) in analysisResult.role_mapping"
                :key="dataRole"
                class="role-chip"
              >
                {{ dataRole }} → {{ llarsRole }}
              </div>
            </div>
          </div>

          <!-- Evaluation Criteria -->
          <div v-if="analysisResult.evaluation_criteria?.length" class="summary-item">
            <div class="summary-label">Bewertungskriterien</div>
            <div class="criteria-chips">
              <span
                v-for="criterion in analysisResult.evaluation_criteria"
                :key="criterion"
                class="criterion-chip"
              >
                {{ criterion }}
              </span>
            </div>
          </div>

          <!-- Confidence -->
          <div class="confidence-bar">
            <div class="confidence-label">Konfidenz: {{ Math.round((analysisResult.confidence || 0.7) * 100) }}%</div>
            <v-progress-linear
              :model-value="(analysisResult.confidence || 0.7) * 100"
              color="success"
              height="6"
              rounded
            />
          </div>
        </div>

        <div v-else class="no-analysis">
          <LIcon size="48" color="grey-lighten-1">mdi-robot-confused</LIcon>
          <span class="text-body-2 text-medium-emphasis mt-2">
            Keine KI-Analyse durchgeführt
          </span>
        </div>
      </div>
    </div>

    <!-- Data Overview -->
    <div class="data-overview mt-6">
      <div class="section-header">
        <LIcon size="20" class="mr-2" color="accent">mdi-database</LIcon>
        <span>Daten-Übersicht</span>
        <v-spacer />
        <span class="data-count">{{ sessions.length }} Dateien</span>
      </div>

      <div class="data-stats">
        <div class="stat-item">
          <div class="stat-value">{{ totalFiles }}</div>
          <div class="stat-label">Dateien</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ totalItems.toLocaleString() }}</div>
          <div class="stat-label">Einträge</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ detectedFormat }}</div>
          <div class="stat-label">Format</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  session: { type: Object, default: null },
  sessions: { type: Array, default: () => [] },
  analysisResult: { type: Object, default: null },
  scenarioConfig: { type: Object, required: true },
  userConfig: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

const emit = defineEmits(['update:scenarioConfig', 'update:userConfig'])

// Local state for two-way binding
const localScenarioConfig = ref({ ...props.scenarioConfig })
const localUserConfig = ref({ ...props.userConfig })

// Task types
const taskTypes = [
  { value: 'mail_rating', label: 'Mail Rating', icon: 'mdi-email-star' },
  { value: 'rating', label: 'Rating', icon: 'mdi-star' },
  { value: 'ranking', label: 'Ranking', icon: 'mdi-sort' },
  { value: 'comparison', label: 'Vergleich', icon: 'mdi-compare' },
  { value: 'authenticity', label: 'Echt/Fake', icon: 'mdi-shield-check' },
  { value: 'classification', label: 'Labels', icon: 'mdi-tag-multiple' }
]

// Computed
const totalFiles = computed(() => props.sessions?.length || 0)

const totalItems = computed(() => {
  return props.sessions?.reduce((sum, s) => sum + (s.item_count || s.structure?.item_count || 0), 0) || 0
})

const detectedFormat = computed(() => {
  if (props.sessions?.length) {
    return props.sessions[0]?.detected_format || 'JSON'
  }
  return props.session?.detected_format || 'Unbekannt'
})

// Watchers for two-way binding
watch(localScenarioConfig, (newVal) => {
  emit('update:scenarioConfig', { ...newVal })
}, { deep: true })

watch(localUserConfig, (newVal) => {
  emit('update:userConfig', { ...newVal })
}, { deep: true })

watch(() => props.scenarioConfig, (newVal) => {
  localScenarioConfig.value = { ...newVal }
}, { deep: true })

// Apply analysis result task type
watch(() => props.analysisResult?.task_type, (newType) => {
  if (newType && !localScenarioConfig.value.taskType) {
    localScenarioConfig.value.taskType = newType
  }
})

onMounted(() => {
  // Initialize from props
  localScenarioConfig.value = { ...props.scenarioConfig }
  localUserConfig.value = { ...props.userConfig }
})
</script>

<style scoped>
.step-review {
  max-width: 900px;
  margin: 0 auto;
}

.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 800px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
}

.config-section {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  background: rgba(var(--v-theme-surface-variant), 0.4);
  font-weight: 600;
  font-size: 0.9rem;
}

/* Form Styles */
.config-form {
  padding: 18px;
}

.form-field {
  margin-bottom: 18px;
}

.form-field:last-child {
  margin-bottom: 0;
}

.field-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 8px;
}

.text-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid rgba(var(--v-border-color), 0.3);
  border-radius: 8px 2px 8px 2px;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.5);
  transition: border-color 0.2s;
}

.text-input:focus {
  outline: none;
  border-color: #b0ca97;
}

.text-input--small {
  padding: 8px 10px;
  font-size: 0.85rem;
}

.date-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-separator {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.85rem;
}

/* Task Type Grid */
.task-type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.task-type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border: 1px solid rgba(var(--v-border-color), 0.2);
  border-radius: 8px 2px 8px 2px;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
}

.task-type-btn:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.task-type-btn--selected {
  background: rgba(176, 202, 151, 0.2);
  border-color: #b0ca97;
}

.task-type-label {
  font-size: 0.7rem;
  font-weight: 500;
  margin-top: 2px;
}

/* Analysis Summary */
.analysis-summary {
  padding: 18px;
}

.summary-item {
  margin-bottom: 16px;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.summary-value {
  font-size: 0.95rem;
  color: rgb(var(--v-theme-on-surface));
}

.mapping-preview {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mapping-item {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
}

.mapping-item code {
  font-size: 0.75rem;
  padding: 2px 6px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border-radius: 4px;
}

.role-chips,
.criteria-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.role-chip {
  padding: 4px 10px;
  background: rgba(136, 196, 200, 0.15);
  border-radius: 12px;
  font-size: 0.8rem;
  color: #5a9a9e;
}

.criterion-chip {
  padding: 4px 10px;
  background: rgba(209, 188, 138, 0.2);
  border-radius: 6px 2px 6px 2px;
  font-size: 0.8rem;
  color: #8a7a52;
}

.confidence-bar {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-border-color), 0.1);
}

.confidence-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 6px;
}

.no-analysis {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

/* Data Overview */
.data-overview {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
}

.data-count {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.data-stats {
  display: flex;
  gap: 24px;
  padding: 20px;
  justify-content: center;
}

.stat-item {
  text-align: center;
  min-width: 100px;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #6a8a52;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}
</style>
