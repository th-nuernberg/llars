<template>
  <div class="ranking-config">
    <!-- Ranking Type -->
    <v-select
      v-model="localConfig.type"
      :items="rankingTypes"
      :label="$t('scenarioManager.evalConfig.ranking.rankingType')"
      variant="outlined"
      density="compact"
      class="mb-3"
      @update:modelValue="emitUpdate"
    />

    <!-- Options -->
    <div class="config-options mb-4">
      <LSwitch
        v-model="localConfig.allowTies"
        :label="$t('scenarioManager.evalConfig.ranking.allowTies')"
        @update:modelValue="emitUpdate"
      />
      <LSwitch
        v-model="localConfig.dragDrop"
        :label="$t('scenarioManager.evalConfig.ranking.enableDragDrop')"
        @update:modelValue="emitUpdate"
      />
      <LSwitch
        v-if="localConfig.type === 'ordered'"
        v-model="localConfig.showPosition"
        :label="$t('scenarioManager.evalConfig.ranking.showPositions')"
        @update:modelValue="emitUpdate"
      />
    </div>

    <!-- Buckets Editor (for bucket-based ranking) -->
    <div v-if="localConfig.type === 'buckets'" class="buckets-section">
      <div class="section-header">
        <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.ranking.buckets') }}</h5>
        <v-btn
          size="small"
          variant="text"
          color="primary"
          prepend-icon="mdi-plus"
          @click="addBucket"
        >
          {{ $t('scenarioManager.evalConfig.ranking.addBucket') }}
        </v-btn>
      </div>

      <draggable
        v-model="localConfig.buckets"
        item-key="id"
        handle=".drag-handle"
        class="buckets-list"
        @change="emitUpdate"
      >
        <template #item="{ element, index }">
          <div class="bucket-row">
            <LIcon class="drag-handle" size="18">mdi-drag-vertical</LIcon>
            <div
              class="bucket-color"
              :style="{ backgroundColor: element.color }"
              @click="openColorPicker(index)"
            />
            <v-text-field
              v-model="element.name.de"
              :placeholder="$t('scenarioManager.evalConfig.ranking.bucketName')"
              variant="outlined"
              density="compact"
              hide-details
              class="flex-grow-1"
              @update:modelValue="updateBucketName(index, $event)"
            />
            <v-btn
              icon
              size="x-small"
              variant="text"
              color="error"
              :disabled="localConfig.buckets.length <= 2"
              @click="removeBucket(index)"
            >
              <LIcon size="18">mdi-delete-outline</LIcon>
            </v-btn>
          </div>
        </template>
      </draggable>

      <p v-if="localConfig.buckets.length < 2" class="hint-text">
        {{ $t('scenarioManager.evalConfig.ranking.minBucketsHint') }}
      </p>
    </div>

    <!-- Labels for ordered ranking -->
    <div v-if="localConfig.type === 'ordered'" class="ordered-labels mt-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.ranking.orderLabels') }}</h5>
      <v-row>
        <v-col cols="6">
          <v-text-field
            v-model="localConfig.labels.first"
            :label="$t('scenarioManager.evalConfig.ranking.firstLabel')"
            :placeholder="$t('scenarioManager.evalConfig.ranking.firstPlaceholder')"
            variant="outlined"
            density="compact"
            @update:modelValue="emitUpdate"
          />
        </v-col>
        <v-col cols="6">
          <v-text-field
            v-model="localConfig.labels.last"
            :label="$t('scenarioManager.evalConfig.ranking.lastLabel')"
            :placeholder="$t('scenarioManager.evalConfig.ranking.lastPlaceholder')"
            variant="outlined"
            density="compact"
            @update:modelValue="emitUpdate"
          />
        </v-col>
      </v-row>
    </div>

    <!-- Hidden color picker dialog -->
    <v-dialog v-model="colorPickerOpen" max-width="300">
      <v-card>
        <v-card-title>{{ $t('scenarioManager.evalConfig.ranking.selectColor') }}</v-card-title>
        <v-card-text>
          <v-color-picker
            v-model="selectedColor"
            :modes="['hexa']"
            hide-inputs
            show-swatches
            :swatches="colorSwatches"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="colorPickerOpen = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="primary" @click="applyColor">
            {{ $t('common.apply') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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

const rankingTypes = computed(() => [
  { title: t('scenarioManager.evalConfig.ranking.typeOptions.buckets'), value: 'buckets' },
  { title: t('scenarioManager.evalConfig.ranking.typeOptions.ordered'), value: 'ordered' }
])

const colorSwatches = [
  ['#98d4bb', '#6bc48f', '#4a9d6e'],
  ['#D1BC8A', '#c4a55e', '#a68b3d'],
  ['#e8a087', '#d46b6b', '#b54545'],
  ['#88c4c8', '#5ba9ae', '#3d8c91'],
  ['#c4a0d4', '#a87cc4', '#8a5aad']
]

const localConfig = ref({
  type: 'buckets',
  buckets: [
    { id: 1, name: { de: 'Gut', en: 'Good' }, color: '#98d4bb' },
    { id: 2, name: { de: 'Mittel', en: 'Medium' }, color: '#D1BC8A' },
    { id: 3, name: { de: 'Schlecht', en: 'Poor' }, color: '#e8a087' }
  ],
  allowTies: false,
  dragDrop: true,
  showPosition: true,
  labels: { first: '', last: '' }
})

const colorPickerOpen = ref(false)
const selectedColor = ref('#98d4bb')
const editingBucketIndex = ref(null)

function addBucket() {
  const colors = ['#98d4bb', '#D1BC8A', '#e8a087', '#88c4c8', '#c4a0d4']
  const colorIndex = localConfig.value.buckets.length % colors.length
  localConfig.value.buckets.push({
    id: Date.now(),
    name: { de: '', en: '' },
    color: colors[colorIndex]
  })
  emitUpdate()
}

function removeBucket(index) {
  if (localConfig.value.buckets.length > 2) {
    localConfig.value.buckets.splice(index, 1)
    emitUpdate()
  }
}

function updateBucketName(index, value) {
  localConfig.value.buckets[index].name = { de: value, en: value }
  emitUpdate()
}

function openColorPicker(index) {
  editingBucketIndex.value = index
  selectedColor.value = localConfig.value.buckets[index].color
  colorPickerOpen.value = true
}

function applyColor() {
  if (editingBucketIndex.value !== null) {
    localConfig.value.buckets[editingBucketIndex.value].color = selectedColor.value
    emitUpdate()
  }
  colorPickerOpen.value = false
}

function emitUpdate() {
  emit('update:modelValue', { ...localConfig.value })
}

function initFromProps() {
  if (props.modelValue) {
    const hasBuckets = Object.prototype.hasOwnProperty.call(props.modelValue, 'buckets')
    localConfig.value = {
      ...localConfig.value,
      ...props.modelValue,
      buckets: hasBuckets ? [...(props.modelValue.buckets || [])] : localConfig.value.buckets,
      labels: props.modelValue.labels || { first: '', last: '' }
    }
  }
}

watch(() => props.modelValue, initFromProps, { deep: true })

onMounted(initFromProps)
</script>

<style scoped>
.ranking-config {
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

/* Buckets */
.buckets-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

.buckets-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bucket-row {
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

.bucket-color {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid rgba(0, 0, 0, 0.1);
  transition: transform 0.15s;
}

.bucket-color:hover {
  transform: scale(1.1);
}

.hint-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 8px;
  font-style: italic;
}

/* Ordered labels */
.ordered-labels {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}
</style>
