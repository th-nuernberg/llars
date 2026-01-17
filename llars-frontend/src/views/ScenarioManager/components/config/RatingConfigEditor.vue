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
      <v-btn
        size="small"
        variant="text"
        color="primary"
        prepend-icon="mdi-plus"
        class="mb-2"
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
          <div class="dimension-row">
            <LIcon class="drag-handle" size="18">mdi-drag-vertical</LIcon>
            <v-text-field
              :model-value="getDimensionName(element.name)"
              :placeholder="$t('scenarioManager.evalConfig.rating.dimensionName')"
              variant="outlined"
              density="compact"
              hide-details
              class="flex-grow-1"
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
        </template>
      </draggable>
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
  localConfig.value.dimensions.push({
    id: `dim_${Date.now()}`,
    name: ''
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

.dimension-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background-color: rgba(var(--v-theme-surface), 1);
  border-radius: 6px;
  margin-bottom: 4px;
}

.drag-handle {
  cursor: grab;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.drag-handle:hover {
  color: rgba(var(--v-theme-on-surface), 0.7);
}
</style>
