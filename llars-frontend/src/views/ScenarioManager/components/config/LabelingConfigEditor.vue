<template>
  <div class="labeling-config">
    <!-- Labeling Type -->
    <v-select
      v-model="localConfig.type"
      :items="labelingTypes"
      :label="$t('scenarioManager.evalConfig.labeling.labelingType')"
      variant="outlined"
      density="compact"
      class="mb-3"
      @update:modelValue="handleTypeChange"
    />

    <!-- Options -->
    <div class="config-options mb-4">
      <LSwitch
        v-if="localConfig.type !== 'binary'"
        v-model="localConfig.multiLabel"
        :label="$t('scenarioManager.evalConfig.labeling.multiLabel')"
        @update:modelValue="emitUpdate"
      />
      <LSwitch
        v-model="localConfig.allowUnsure"
        :label="$t('scenarioManager.evalConfig.labeling.allowUnsure')"
        @update:modelValue="emitUpdate"
      />
    </div>

    <!-- Categories Editor -->
    <div class="categories-section">
      <div class="section-header">
        <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.labeling.categories') }}</h5>
        <v-btn
          size="small"
          variant="text"
          color="primary"
          prepend-icon="mdi-plus"
          @click="addCategory"
        >
          {{ $t('scenarioManager.evalConfig.labeling.addCategory') }}
        </v-btn>
      </div>

      <draggable
        v-model="localConfig.categories"
        item-key="id"
        handle=".drag-handle"
        class="categories-list"
        @change="emitUpdate"
      >
        <template #item="{ element, index }">
          <div class="category-row">
            <LIcon class="drag-handle" size="18">mdi-drag-vertical</LIcon>
            <div
              class="category-color"
              :style="{ backgroundColor: element.color }"
              @click="openColorPicker(index)"
            />
            <v-text-field
              v-model="element.name.de"
              :placeholder="$t('scenarioManager.evalConfig.labeling.categoryName')"
              variant="outlined"
              density="compact"
              hide-details
              class="flex-grow-1"
              @update:modelValue="updateCategoryName(index, $event)"
            />
            <v-select
              v-model="element.icon"
              :items="availableIcons"
              variant="outlined"
              density="compact"
              hide-details
              class="icon-select"
              @update:modelValue="emitUpdate"
            >
              <template v-slot:selection="{ item }">
                <LIcon size="18">{{ item.value }}</LIcon>
              </template>
              <template v-slot:item="{ item, props }">
                <v-list-item v-bind="props">
                  <template v-slot:prepend>
                    <LIcon size="18">{{ item.value }}</LIcon>
                  </template>
                </v-list-item>
              </template>
            </v-select>
            <v-btn
              icon
              size="x-small"
              variant="text"
              color="error"
              :disabled="localConfig.categories.length <= 2"
              @click="removeCategory(index)"
            >
              <LIcon size="18">mdi-delete-outline</LIcon>
            </v-btn>
          </div>
        </template>
      </draggable>

      <p v-if="localConfig.categories.length < 2" class="hint-text">
        {{ $t('scenarioManager.evalConfig.labeling.minCategoriesHint') }}
      </p>
    </div>

    <!-- Unsure Option Configuration -->
    <div v-if="localConfig.allowUnsure" class="unsure-section mt-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.labeling.unsureOption') }}</h5>
      <div class="unsure-row">
        <div
          class="category-color"
          :style="{ backgroundColor: localConfig.unsureOption?.color || '#D1BC8A' }"
          @click="openUnsureColorPicker"
        />
        <v-text-field
          v-model="unsureLabel"
          :placeholder="$t('scenarioManager.evalConfig.labeling.unsureName')"
          variant="outlined"
          density="compact"
          hide-details
          class="flex-grow-1"
          @update:modelValue="updateUnsureLabel"
        />
      </div>
    </div>

    <!-- Multi-label constraints -->
    <div v-if="localConfig.multiLabel" class="multilabel-options mt-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.labeling.constraints') }}</h5>
      <v-row>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.minLabels"
            :label="$t('scenarioManager.evalConfig.labeling.minLabels')"
            type="number"
            variant="outlined"
            density="compact"
            :min="1"
            @update:modelValue="emitUpdate"
          />
        </v-col>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.maxLabels"
            :label="$t('scenarioManager.evalConfig.labeling.maxLabels')"
            type="number"
            variant="outlined"
            density="compact"
            :placeholder="$t('scenarioManager.evalConfig.labeling.unlimited')"
            @update:modelValue="emitUpdate"
          />
        </v-col>
      </v-row>
    </div>

    <!-- Color picker dialog -->
    <v-dialog v-model="colorPickerOpen" max-width="300">
      <v-card>
        <v-card-title>{{ $t('scenarioManager.evalConfig.labeling.selectColor') }}</v-card-title>
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

const labelingTypes = computed(() => [
  { title: t('scenarioManager.evalConfig.labeling.typeOptions.binary'), value: 'binary' },
  { title: t('scenarioManager.evalConfig.labeling.typeOptions.multiclass'), value: 'multiclass' },
  { title: t('scenarioManager.evalConfig.labeling.typeOptions.multilabel'), value: 'multilabel' }
])

const availableIcons = [
  { title: 'Check', value: 'mdi-check-circle' },
  { title: 'Alert', value: 'mdi-alert-circle' },
  { title: 'Info', value: 'mdi-information' },
  { title: 'Tag', value: 'mdi-tag' },
  { title: 'Star', value: 'mdi-star' },
  { title: 'Heart', value: 'mdi-heart' },
  { title: 'Flag', value: 'mdi-flag' },
  { title: 'Shield', value: 'mdi-shield' },
  { title: 'Help', value: 'mdi-help-circle' },
  { title: 'Happy', value: 'mdi-emoticon-happy' },
  { title: 'Sad', value: 'mdi-emoticon-sad' },
  { title: 'Neutral', value: 'mdi-emoticon-neutral' }
]

const colorSwatches = [
  ['#98d4bb', '#6bc48f', '#4a9d6e'],
  ['#D1BC8A', '#c4a55e', '#a68b3d'],
  ['#e8a087', '#d46b6b', '#b54545'],
  ['#88c4c8', '#5ba9ae', '#3d8c91'],
  ['#c4a0d4', '#a87cc4', '#8a5aad']
]

const localConfig = ref({
  type: 'binary',
  multiLabel: false,
  categories: [],
  allowUnsure: true,
  unsureOption: null,
  minLabels: 1,
  maxLabels: null
})

const unsureLabel = ref('')
const colorPickerOpen = ref(false)
const selectedColor = ref('#98d4bb')
const editingIndex = ref(null)
const editingUnsure = ref(false)

function handleTypeChange(type) {
  if (type === 'binary' && localConfig.value.categories.length > 2) {
    localConfig.value.categories = localConfig.value.categories.slice(0, 2)
  }
  if (type === 'multilabel') {
    localConfig.value.multiLabel = true
  } else {
    localConfig.value.multiLabel = false
  }
  emitUpdate()
}

function addCategory() {
  const colors = ['#98d4bb', '#e8a087', '#88c4c8', '#c4a0d4', '#D1BC8A']
  const icons = ['mdi-check-circle', 'mdi-alert-circle', 'mdi-tag', 'mdi-star', 'mdi-flag']
  const idx = localConfig.value.categories.length
  localConfig.value.categories.push({
    id: `cat_${Date.now()}`,
    name: { de: '', en: '' },
    color: colors[idx % colors.length],
    icon: icons[idx % icons.length]
  })
  emitUpdate()
}

function removeCategory(index) {
  if (localConfig.value.categories.length > 2) {
    localConfig.value.categories.splice(index, 1)
    emitUpdate()
  }
}

function updateCategoryName(index, value) {
  localConfig.value.categories[index].name = { de: value, en: value }
  emitUpdate()
}

function updateUnsureLabel(value) {
  if (!localConfig.value.unsureOption) {
    localConfig.value.unsureOption = {
      id: 'unsure',
      name: { de: value, en: value },
      color: '#D1BC8A',
      icon: 'mdi-help-circle'
    }
  } else {
    localConfig.value.unsureOption.name = { de: value, en: value }
  }
  emitUpdate()
}

function openColorPicker(index) {
  editingIndex.value = index
  editingUnsure.value = false
  selectedColor.value = localConfig.value.categories[index].color
  colorPickerOpen.value = true
}

function openUnsureColorPicker() {
  editingIndex.value = null
  editingUnsure.value = true
  selectedColor.value = localConfig.value.unsureOption?.color || '#D1BC8A'
  colorPickerOpen.value = true
}

function applyColor() {
  if (editingUnsure.value) {
    if (!localConfig.value.unsureOption) {
      localConfig.value.unsureOption = { id: 'unsure', name: { de: '', en: '' }, color: selectedColor.value, icon: 'mdi-help-circle' }
    } else {
      localConfig.value.unsureOption.color = selectedColor.value
    }
  } else if (editingIndex.value !== null) {
    localConfig.value.categories[editingIndex.value].color = selectedColor.value
  }
  emitUpdate()
  colorPickerOpen.value = false
}

function emitUpdate() {
  emit('update:modelValue', { ...localConfig.value })
}

function initFromProps() {
  if (props.modelValue) {
    localConfig.value = {
      ...localConfig.value,
      ...props.modelValue,
      categories: props.modelValue.categories ? [...props.modelValue.categories] : []
    }
    if (localConfig.value.unsureOption?.name) {
      unsureLabel.value = localConfig.value.unsureOption.name.de || localConfig.value.unsureOption.name.en || ''
    }
  }
}

watch(() => props.modelValue, initFromProps, { deep: true })

onMounted(initFromProps)
</script>

<style scoped>
.labeling-config {
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
  flex-direction: column;
  gap: 8px;
}

/* Categories */
.categories-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-row,
.unsure-row {
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

.category-color {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid rgba(0, 0, 0, 0.1);
  transition: transform 0.15s;
  flex-shrink: 0;
}

.category-color:hover {
  transform: scale(1.1);
}

.icon-select {
  width: 70px;
  flex-shrink: 0;
}

.hint-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 8px;
  font-style: italic;
}

/* Unsure */
.unsure-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

/* Multi-label */
.multilabel-options {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}
</style>
