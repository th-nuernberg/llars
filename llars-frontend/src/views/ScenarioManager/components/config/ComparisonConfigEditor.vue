<template>
  <div class="comparison-config">
    <!-- Comparison Type -->
    <v-select
      v-model="localConfig.type"
      :items="comparisonTypes"
      :label="$t('scenarioManager.evalConfig.comparison.comparisonType')"
      variant="outlined"
      density="compact"
      class="mb-3"
      @update:modelValue="emitUpdate"
    />

    <!-- Options -->
    <div class="config-options mb-4">
      <LSwitch
        v-model="localConfig.allowTie"
        :label="$t('scenarioManager.evalConfig.comparison.allowTie')"
        @update:modelValue="emitUpdate"
      />
      <LSwitch
        v-model="localConfig.showConfidence"
        :label="$t('scenarioManager.evalConfig.comparison.showConfidence')"
        @update:modelValue="emitUpdate"
      />
    </div>

    <!-- Items per comparison -->
    <v-text-field
      v-model.number="localConfig.itemsPerComparison"
      :label="$t('scenarioManager.evalConfig.comparison.itemsPerComparison')"
      type="number"
      variant="outlined"
      density="compact"
      :min="2"
      :max="5"
      class="mb-3"
      @update:modelValue="emitUpdate"
    />

    <!-- Confidence Scale (when enabled) -->
    <div v-if="localConfig.showConfidence" class="confidence-section mb-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.comparison.confidenceScale') }}</h5>
      <v-row>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.confidenceScale.min"
            :label="$t('scenarioManager.evalConfig.comparison.confidenceMin')"
            type="number"
            variant="outlined"
            density="compact"
            @update:modelValue="emitUpdate"
          />
        </v-col>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.confidenceScale.max"
            :label="$t('scenarioManager.evalConfig.comparison.confidenceMax')"
            type="number"
            variant="outlined"
            density="compact"
            @update:modelValue="emitUpdate"
          />
        </v-col>
      </v-row>
    </div>

    <!-- Criteria Editor -->
    <div class="criteria-section">
      <div class="section-header">
        <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.comparison.criteria') }}</h5>
        <v-btn
          size="small"
          variant="text"
          color="primary"
          prepend-icon="mdi-plus"
          @click="addCriterion"
        >
          {{ $t('scenarioManager.evalConfig.comparison.addCriterion') }}
        </v-btn>
      </div>

      <draggable
        v-model="localConfig.criteria"
        item-key="id"
        handle=".drag-handle"
        class="criteria-list"
        @change="emitUpdate"
      >
        <template #item="{ element, index }">
          <div class="criterion-row">
            <LIcon class="drag-handle" size="18">mdi-drag-vertical</LIcon>
            <v-text-field
              v-model="element.name.de"
              :placeholder="$t('scenarioManager.evalConfig.comparison.criterionName')"
              variant="outlined"
              density="compact"
              hide-details
              class="flex-grow-1"
              @update:modelValue="updateCriterionName(index, $event)"
            />
            <v-text-field
              v-model.number="element.weight"
              :label="$t('scenarioManager.evalConfig.comparison.weight')"
              type="number"
              variant="outlined"
              density="compact"
              hide-details
              class="weight-input"
              :min="0"
              :max="1"
              :step="0.1"
              @update:modelValue="emitUpdate"
            />
            <v-btn
              icon
              size="x-small"
              variant="text"
              color="error"
              :disabled="localConfig.criteria.length <= 1"
              @click="removeCriterion(index)"
            >
              <LIcon size="18">mdi-delete-outline</LIcon>
            </v-btn>
          </div>
        </template>
      </draggable>

      <div class="weight-info mt-2">
        <span class="weight-label">{{ $t('scenarioManager.evalConfig.comparison.totalWeight') }}:</span>
        <span :class="['weight-value', { invalid: totalWeight !== 1 }]">
          {{ totalWeight.toFixed(2) }}
        </span>
        <span v-if="totalWeight !== 1" class="weight-warning">
          ({{ $t('scenarioManager.evalConfig.comparison.shouldBeOne') }})
        </span>
      </div>

      <p v-if="localConfig.criteria.length === 0" class="hint-text">
        {{ $t('scenarioManager.evalConfig.comparison.minCriteriaHint') }}
      </p>
    </div>

    <!-- Tournament Options (when tournament type) -->
    <div v-if="localConfig.type === 'tournament'" class="tournament-section mt-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.comparison.tournamentOptions') }}</h5>
      <v-select
        v-model="localConfig.rounds"
        :items="roundOptions"
        :label="$t('scenarioManager.evalConfig.comparison.rounds')"
        variant="outlined"
        density="compact"
        @update:modelValue="emitUpdate"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import draggable from 'vuedraggable'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()

const comparisonTypes = computed(() => [
  { title: t('scenarioManager.evalConfig.comparison.typeOptions.pairwise'), value: 'pairwise' },
  { title: t('scenarioManager.evalConfig.comparison.typeOptions.tournament'), value: 'tournament' }
])

const roundOptions = computed(() => [
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.auto'), value: 'auto' },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round1'), value: 1 },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round2'), value: 2 },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round3'), value: 3 }
])

const localConfig = ref({
  type: 'pairwise',
  itemsPerComparison: 2,
  allowTie: true,
  showConfidence: false,
  confidenceScale: { min: 1, max: 5 },
  criteria: [],
  rounds: 'auto'
})

const totalWeight = computed(() => {
  return localConfig.value.criteria.reduce((sum, c) => sum + (c.weight || 0), 0)
})

function addCriterion() {
  const remainingWeight = Math.max(0, 1 - totalWeight.value)
  localConfig.value.criteria.push({
    id: `crit_${Date.now()}`,
    name: { de: '', en: '' },
    weight: Math.round(remainingWeight * 10) / 10
  })
  emitUpdate()
}

function removeCriterion(index) {
  if (localConfig.value.criteria.length > 1) {
    localConfig.value.criteria.splice(index, 1)
    emitUpdate()
  }
}

function updateCriterionName(index, value) {
  localConfig.value.criteria[index].name = { de: value, en: value }
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', { ...localConfig.value })
}

function initFromProps() {
  if (props.modelValue) {
    localConfig.value = {
      ...localConfig.value,
      ...props.modelValue,
      criteria: props.modelValue.criteria ? [...props.modelValue.criteria] : [],
      confidenceScale: props.modelValue.confidenceScale || { min: 1, max: 5 }
    }
  }
}

watch(() => props.modelValue, initFromProps, { deep: true })

onMounted(initFromProps)
</script>

<style scoped>
.comparison-config {
  padding: 8px 0;
}

.subsection-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.config-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

/* Confidence */
.confidence-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

/* Criteria */
.criteria-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

.criteria-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.criterion-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background-color: rgba(var(--v-theme-surface), 1);
  border-radius: 6px;
}

.drag-handle {
  cursor: grab;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.drag-handle:hover {
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.weight-input {
  width: 90px;
  flex-shrink: 0;
}

.weight-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.weight-label {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.weight-value {
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.weight-value.invalid {
  color: rgb(var(--v-theme-error));
}

.weight-warning {
  font-size: 0.75rem;
  color: rgb(var(--v-theme-error));
}

.hint-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 8px;
  font-style: italic;
}

/* Tournament */
.tournament-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}
</style>
