<template>
  <div class="rating-config">
    <!-- Scale Type -->
    <v-select
      v-model="localConfig.type"
      :items="scaleTypes"
      :label="$t('scenarioManager.evalConfig.rating.scaleType')"
      variant="outlined"
      density="compact"
      class="mb-3"
      @update:modelValue="emitUpdate"
    />

    <!-- Scale Range -->
    <v-row class="mb-3">
      <v-col cols="6">
        <v-text-field
          v-model.number="localConfig.min"
          :label="$t('scenarioManager.evalConfig.rating.minValue')"
          type="number"
          variant="outlined"
          density="compact"
          @update:modelValue="emitUpdate"
        />
      </v-col>
      <v-col cols="6">
        <v-text-field
          v-model.number="localConfig.max"
          :label="$t('scenarioManager.evalConfig.rating.maxValue')"
          type="number"
          variant="outlined"
          density="compact"
          @update:modelValue="emitUpdate"
        />
      </v-col>
    </v-row>

    <!-- Step Size -->
    <v-text-field
      v-model.number="localConfig.step"
      :label="$t('scenarioManager.evalConfig.rating.stepSize')"
      type="number"
      variant="outlined"
      density="compact"
      class="mb-3"
      :min="0.5"
      :step="0.5"
      @update:modelValue="emitUpdate"
    />

    <!-- Options -->
    <div class="config-options mb-4">
      <LSwitch
        v-model="localConfig.showLabels"
        :label="$t('scenarioManager.evalConfig.rating.showLabels')"
        @update:modelValue="emitUpdate"
      />
      <LSwitch
        v-if="localConfig.type === 'stars'"
        v-model="localConfig.allowHalf"
        :label="$t('scenarioManager.evalConfig.rating.allowHalfSteps')"
        @update:modelValue="emitUpdate"
      />
    </div>

    <!-- Labels Editor -->
    <div v-if="localConfig.showLabels" class="labels-section">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.rating.scaleLabels') }}</h5>
      <div class="labels-list">
        <div
          v-for="value in scaleValues"
          :key="value"
          class="label-row"
        >
          <span class="label-value">{{ value }}</span>
          <v-text-field
            v-model="localConfig.labels[value]"
            :placeholder="$t('scenarioManager.evalConfig.rating.labelPlaceholder')"
            variant="outlined"
            density="compact"
            hide-details
            class="label-input"
            @update:modelValue="handleLabelUpdate(value, $event)"
          />
        </div>
      </div>
    </div>

    <!-- Dimensions (optional multi-dimensional rating) -->
    <div v-if="showDimensions" class="dimensions-section mt-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.rating.dimensions') }}</h5>
      <p class="section-hint mb-3">{{ $t('scenarioManager.evalConfig.rating.dimensionsHint') }}</p>
      <v-btn
        size="small"
        variant="text"
        color="primary"
        prepend-icon="mdi-plus"
        class="mb-3"
        @click="addDimension"
      >
        {{ $t('scenarioManager.evalConfig.rating.addDimension') }}
      </v-btn>
      <draggable
        v-model="localConfig.dimensions"
        item-key="id"
        handle=".drag-handle"
        @change="emitUpdate"
      >
        <template #item="{ element, index }">
          <div class="dimension-card">
            <div class="dimension-header">
              <LIcon class="drag-handle" size="18">mdi-drag-vertical</LIcon>
              <v-text-field
                :model-value="getDimensionName(element.name)"
                :placeholder="$t('scenarioManager.evalConfig.rating.dimensionName')"
                variant="outlined"
                density="compact"
                hide-details
                class="dimension-name-input"
                @update:modelValue="updateDimensionName(index, $event)"
              />
              <v-btn
                icon
                size="x-small"
                variant="text"
                color="error"
                @click="removeDimension(index)"
              >
                <LIcon size="18">mdi-delete-outline</LIcon>
              </v-btn>
            </div>
            <div class="dimension-details">
              <v-textarea
                :model-value="getDimensionDescription(element.description)"
                :placeholder="$t('scenarioManager.evalConfig.rating.dimensionDescription')"
                variant="outlined"
                density="compact"
                rows="2"
                hide-details
                class="dimension-description-input"
                @update:modelValue="updateDimensionDescription(index, $event)"
              />
              <v-text-field
                :model-value="element.weight"
                :label="$t('scenarioManager.evalConfig.rating.dimensionWeight')"
                type="number"
                variant="outlined"
                density="compact"
                hide-details
                class="dimension-weight-input"
                :min="0"
                :max="1"
                :step="0.05"
                @update:modelValue="updateDimensionWeight(index, $event)"
              />
            </div>
          </div>
        </template>
      </draggable>

      <!-- Weight Summary -->
      <div v-if="localConfig.dimensions?.length > 0" class="weight-summary mt-3">
        <span class="weight-label">{{ $t('scenarioManager.evalConfig.rating.totalWeight') }}:</span>
        <span class="weight-value" :class="{ 'weight-warning': totalWeight !== 1 }">
          {{ (totalWeight * 100).toFixed(0) }}%
        </span>
        <span v-if="totalWeight !== 1" class="weight-hint">
          ({{ $t('scenarioManager.evalConfig.rating.shouldBe100') }})
        </span>
      </div>
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
  },
  showDimensions: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])
const { t, locale } = useI18n()

const scaleTypes = [
  { title: 'Multi-Dimensional (LLM-as-Judge)', value: 'multi-dimensional' },
  { title: 'Likert', value: 'likert' },
  { title: 'Sterne', value: 'stars' },
  { title: 'Numerisch', value: 'numeric' },
  { title: 'Slider', value: 'slider' }
]

const localConfig = ref({
  type: 'likert',
  min: 1,
  max: 5,
  step: 1,
  labels: {},
  showLabels: true,
  allowHalf: false,
  dimensions: []
})

const scaleValues = computed(() => {
  const values = []
  for (let v = localConfig.value.min; v <= localConfig.value.max; v += localConfig.value.step) {
    values.push(v)
  }
  return values
})

function getDimensionName(name) {
  if (!name) return ''
  if (typeof name === 'string') return name
  return name[locale.value] || name.de || name.en || ''
}

function getDimensionDescription(description) {
  if (!description) return ''
  if (typeof description === 'string') return description
  return description[locale.value] || description.de || description.en || ''
}

function updateDimensionName(index, value) {
  const dimension = localConfig.value.dimensions?.[index]
  if (!dimension) return
  if (dimension.name && typeof dimension.name === 'object') {
    dimension.name[locale.value] = value
  } else {
    dimension.name = value
  }
  emitUpdate()
}

function updateDimensionDescription(index, value) {
  const dimension = localConfig.value.dimensions?.[index]
  if (!dimension) return
  if (dimension.description && typeof dimension.description === 'object') {
    dimension.description[locale.value] = value
  } else {
    dimension.description = { de: value, en: value }
  }
  emitUpdate()
}

function updateDimensionWeight(index, value) {
  const dimension = localConfig.value.dimensions?.[index]
  if (!dimension) return
  dimension.weight = parseFloat(value) || 0
  emitUpdate()
}

const totalWeight = computed(() => {
  if (!localConfig.value.dimensions?.length) return 0
  return localConfig.value.dimensions.reduce((sum, dim) => sum + (dim.weight || 0), 0)
})

function handleLabelUpdate(value, label) {
  if (!localConfig.value.labels) {
    localConfig.value.labels = {}
  }
  // Store as simple string or locale object
  if (typeof label === 'string') {
    localConfig.value.labels[value] = { de: label, en: label }
  }
  emitUpdate()
}

function addDimension() {
  if (!localConfig.value.dimensions) {
    localConfig.value.dimensions = []
  }
  // Calculate default weight to make total = 1
  const existingCount = localConfig.value.dimensions.length
  const defaultWeight = existingCount === 0 ? 1 : Math.round((1 / (existingCount + 1)) * 100) / 100

  localConfig.value.dimensions.push({
    id: `dim_${Date.now()}`,
    name: { de: '', en: '' },
    description: { de: '', en: '' },
    weight: defaultWeight
  })

  // Optionally redistribute weights evenly
  const newCount = localConfig.value.dimensions.length
  const evenWeight = Math.round((1 / newCount) * 100) / 100
  localConfig.value.dimensions.forEach(dim => {
    dim.weight = evenWeight
  })

  emitUpdate()
}

function removeDimension(index) {
  localConfig.value.dimensions.splice(index, 1)
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', { ...localConfig.value })
}

function initFromProps() {
  if (props.modelValue) {
    localConfig.value = { ...localConfig.value, ...props.modelValue }
    // Ensure labels object exists
    if (!localConfig.value.labels) {
      localConfig.value.labels = {}
    }
    if (!localConfig.value.dimensions) {
      localConfig.value.dimensions = []
    }
  }
}

watch(() => props.modelValue, initFromProps, { deep: true })

onMounted(initFromProps)
</script>

<style scoped>
.rating-config {
  padding: 8px 0;
}

.subsection-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 8px;
}

.config-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

/* Labels */
.labels-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

.labels-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.label-value {
  width: 32px;
  text-align: center;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.label-input {
  flex: 1;
}

/* Dimensions */
.dimensions-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

.section-hint {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.dimension-card {
  background-color: rgba(var(--v-theme-surface), 1);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.dimension-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.dimension-name-input {
  flex: 1;
}

.dimension-details {
  display: flex;
  gap: 12px;
  padding-left: 26px;
}

.dimension-description-input {
  flex: 1;
}

.dimension-weight-input {
  width: 100px;
  flex-shrink: 0;
}

.drag-handle {
  cursor: grab;
  color: rgba(var(--v-theme-on-surface), 0.4);
  flex-shrink: 0;
}

.drag-handle:hover {
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Weight Summary */
.weight-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 6px;
  font-size: 0.85rem;
}

.weight-label {
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.weight-value {
  font-weight: 600;
  color: rgb(var(--v-theme-success));
}

.weight-value.weight-warning {
  color: rgb(var(--v-theme-warning));
}

.weight-hint {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.8rem;
}
</style>
