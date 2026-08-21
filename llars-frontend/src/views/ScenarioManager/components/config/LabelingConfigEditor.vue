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

    <!-- Co-Pilot: LLM pre-annotation suggestions during labeling -->
    <div class="copilot-section mt-4">
      <div class="section-header">
        <h5 class="subsection-title">
          <LIcon size="16" class="mr-1">mdi-robot-outline</LIcon>
          {{ $t('scenarioManager.evalConfig.labeling.copilot.title') }}
        </h5>
        <LSwitch
          v-model="copilotConfig.enabled"
          :label="$t('scenarioManager.evalConfig.labeling.copilot.enable')"
          @update:modelValue="handleCopilotToggle"
        />
      </div>
      <p class="hint-text">{{ $t('scenarioManager.evalConfig.labeling.copilot.description') }}</p>

      <template v-if="copilotConfig.enabled">
        <LlmModelSelect
          v-model="copilotConfig.model_id"
          :label="$t('scenarioManager.evalConfig.labeling.copilot.model')"
          class="mt-3"
          @update:modelValue="emitUpdate"
        />

        <v-select
          v-model="copilotConfig.top_k"
          :items="topKOptions"
          :label="$t('scenarioManager.evalConfig.labeling.copilot.topK')"
          variant="outlined"
          density="compact"
          class="mt-2"
          @update:modelValue="emitUpdate"
        />

        <div class="d-flex align-center justify-space-between mt-2 mb-1">
          <span class="field-label">{{ $t('scenarioManager.evalConfig.labeling.copilot.prompt') }}</span>
          <div class="placeholder-chips">
            <LTag
              v-for="ph in promptPlaceholders"
              :key="ph"
              size="small"
              variant="info"
              class="placeholder-chip"
              @click="insertPlaceholder(ph)"
            >
              {{ ph }}
            </LTag>
          </div>
        </div>
        <v-textarea
          v-model="copilotConfig.prompt"
          :placeholder="$t('scenarioManager.evalConfig.labeling.copilot.promptPlaceholder')"
          variant="outlined"
          density="compact"
          rows="8"
          auto-grow
          class="prompt-textarea"
          @update:modelValue="emitUpdate"
        />
        <p class="hint-text">{{ $t('scenarioManager.evalConfig.labeling.copilot.promptHint') }}</p>

        <v-textarea
          v-model="copilotConfig.codebook"
          :label="$t('scenarioManager.evalConfig.labeling.copilot.codebook')"
          :placeholder="$t('scenarioManager.evalConfig.labeling.copilot.codebookPlaceholder')"
          variant="outlined"
          density="compact"
          rows="4"
          auto-grow
          class="mt-2"
          @update:modelValue="emitUpdate"
        />

        <div class="mt-2">
          <span class="field-label">
            {{ $t('scenarioManager.evalConfig.labeling.copilot.hiddenControl') }}:
            {{ Math.round((copilotConfig.hidden_control_ratio || 0) * 100) }}%
          </span>
          <v-slider
            v-model="copilotConfig.hidden_control_ratio"
            :min="0"
            :max="0.3"
            :step="0.05"
            density="compact"
            hide-details
            color="primary"
            @update:modelValue="emitUpdate"
          />
          <p class="hint-text">{{ $t('scenarioManager.evalConfig.labeling.copilot.hiddenControlHint') }}</p>
        </div>
      </template>
    </div>

    <!-- Parts / Phases: optional partitioning for calibration studies.
         The wizard emits size boundary specs; the SERVER resolves them into
         item_ids on import and keeps the partition invisible to assessors. -->
    <div class="parts-section mt-4">
      <div class="section-header">
        <h5 class="subsection-title">
          <LIcon size="16" class="mr-1">mdi-format-list-group</LIcon>
          {{ $t('scenarioManager.evalConfig.labeling.parts.title') }}
        </h5>
        <LSwitch
          v-model="partsConfig.enabled"
          :label="$t('scenarioManager.evalConfig.labeling.parts.enable')"
          @update:modelValue="handlePartsToggle"
        />
      </div>
      <p class="hint-text">{{ $t('scenarioManager.evalConfig.labeling.parts.description') }}</p>

      <template v-if="partsConfig.enabled">
        <div
          v-for="(part, index) in partsConfig.list"
          :key="index"
          class="part-row"
        >
          <div class="part-row-head">
            <LTag size="small" variant="info">{{ index + 1 }}</LTag>
            <v-text-field
              v-model="part.name"
              :placeholder="$t('scenarioManager.evalConfig.labeling.parts.partName', { n: index + 1 })"
              variant="outlined"
              density="compact"
              hide-details
              class="flex-grow-1"
              @update:modelValue="emitUpdate"
            />
            <v-text-field
              v-if="index < partsConfig.list.length - 1"
              v-model.number="part.size"
              :label="$t('scenarioManager.evalConfig.labeling.parts.partSize')"
              type="number"
              variant="outlined"
              density="compact"
              hide-details
              :min="1"
              class="part-size-field"
              @update:modelValue="emitUpdate"
            />
            <v-text-field
              v-else
              :model-value="$t('scenarioManager.evalConfig.labeling.parts.rest')"
              variant="outlined"
              density="compact"
              hide-details
              disabled
              class="part-size-field"
            />
            <v-btn
              icon
              size="x-small"
              variant="text"
              color="error"
              :disabled="partsConfig.list.length <= 2"
              @click="removePart(index)"
            >
              <LIcon size="18">mdi-delete-outline</LIcon>
            </v-btn>
          </div>
          <div class="part-row-options">
            <v-select
              v-model="part.order"
              :items="partOrderOptions"
              :label="$t('scenarioManager.evalConfig.labeling.parts.order')"
              variant="outlined"
              density="compact"
              hide-details
              class="part-order-select"
              @update:modelValue="emitUpdate"
            />
            <LSwitch
              v-if="copilotConfig.enabled"
              v-model="part.copilot"
              :label="$t('scenarioManager.evalConfig.labeling.parts.copilotSwitch')"
              @update:modelValue="emitUpdate"
            />
            <LSwitch
              v-model="part.locked"
              :label="$t('scenarioManager.evalConfig.labeling.parts.startLocked')"
              @update:modelValue="emitUpdate"
            />
          </div>
        </div>

        <v-btn
          size="small"
          variant="text"
          color="primary"
          prepend-icon="mdi-plus"
          class="mt-2"
          @click="addPart"
        >
          {{ $t('scenarioManager.evalConfig.labeling.parts.addPart') }}
        </v-btn>

        <p v-if="itemCount > 0" class="hint-text">
          {{ $t('scenarioManager.evalConfig.labeling.parts.itemsInfo', {
            total: itemCount,
            assigned: assignedSizeSum,
            rest: Math.max(0, itemCount - assignedSizeSum)
          }) }}
        </p>
        <p v-if="partsSizeError" class="parts-error-text">
          <LIcon size="14" class="mr-1">mdi-alert-circle-outline</LIcon>
          {{ partsSizeError }}
        </p>
      </template>
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
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  // Number of uploaded items (from the wizard's analysis step) — only used
  // for the parts-section assignment hint; 0 = unknown.
  itemCount: {
    type: Number,
    default: 0
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

// Co-Pilot (LLM pre-annotation): lives inside the labeling config as
// `copilot`. Prompt versioning + hidden-control salt are stamped SERVER-side
// on save (LabelingCopilotService.normalize_config_on_write) — the editor
// only manages the user-facing fields.
const defaultCopilot = () => ({
  enabled: false,
  model_id: null,
  prompt: '',
  codebook: '',
  top_k: 1,
  hidden_control_ratio: 0.15
})
const copilotConfig = ref(defaultCopilot())

const promptPlaceholders = ['{item}', '{context}', '{labels}', '{codebook}']

// Kept as a JS constant (NOT i18n): the literal {item}/{labels} braces would
// be parsed as interpolation slots by the vue-i18n message compiler.
// Mirrors DEFAULT_COPILOT_PROMPT in app/services/evaluation/labeling_copilot_service.py.
const DEFAULT_COPILOT_PROMPT = [
  'Du bist ein sorgfältiger Annotations-Assistent für kategorisches Labeling.',
  'Deine Aufgabe: Ordne das folgende Item einer der erlaubten Kategorien zu und begründe deinen Vorschlag knapp mit Textbelegen.',
  '',
  'Erlaubte Kategorien:',
  '{labels}',
  '',
  'Kodierregeln / Codebook:',
  '{codebook}',
  '',
  'Kontext:',
  '{context}',
  '',
  'Zu labelndes Item:',
  '{item}',
  '',
  'Stütze dich ausschließlich auf den Text. Wenn die Evidenz dünn ist, wähle konservativ und benenne die Unsicherheit in der Begründung.'
].join('\n')

const topKOptions = computed(() => [
  { title: t('scenarioManager.evalConfig.labeling.copilot.topKOptions.one'), value: 1 },
  { title: t('scenarioManager.evalConfig.labeling.copilot.topKOptions.two'), value: 2 }
])

function handleCopilotToggle(enabled) {
  if (enabled && !copilotConfig.value.prompt) {
    copilotConfig.value.prompt = DEFAULT_COPILOT_PROMPT
  }
  emitUpdate()
}

// Parts / Phases (calibration studies): the editor manages size boundary
// specs ("part 1: next N items, last part: rest"); the server resolves them
// into internal item_ids on import (ScenarioPartsService) and never exposes
// the partition to assessors.
const defaultParts = () => ({ enabled: false, list: [] })
const partsConfig = ref(defaultParts())

const partOrderOptions = computed(() => [
  { title: t('scenarioManager.evalConfig.labeling.parts.orderSequential'), value: 'sequential' },
  { title: t('scenarioManager.evalConfig.labeling.parts.orderRandom'), value: 'random' }
])

// Sum of the explicit sizes (all parts except the trailing "rest" part)
const assignedSizeSum = computed(() =>
  partsConfig.value.list
    .slice(0, -1)
    .reduce((sum, p) => sum + (Number(p.size) || 0), 0)
)

const partsSizeError = computed(() => {
  if (!partsConfig.value.enabled) return ''
  const sizedParts = partsConfig.value.list.slice(0, -1)
  if (sizedParts.some(p => !Number(p.size) || Number(p.size) < 1)) {
    return t('scenarioManager.evalConfig.labeling.parts.sizeMissing')
  }
  if (props.itemCount > 0 && assignedSizeSum.value >= props.itemCount) {
    return t('scenarioManager.evalConfig.labeling.parts.sizeExceeds', { total: props.itemCount })
  }
  return ''
})

function makePart(index) {
  return {
    name: t('scenarioManager.evalConfig.labeling.parts.partName', { n: index + 1 }),
    size: null,
    order: 'sequential',
    copilot: false,
    locked: index > 0
  }
}

function handlePartsToggle(enabled) {
  if (enabled && partsConfig.value.list.length === 0) {
    // Seed a sensible two-phase default: a sized first part, the rest after.
    const first = makePart(0)
    first.size = props.itemCount > 1 ? Math.ceil(props.itemCount / 2) : 1
    partsConfig.value.list = [first, makePart(1)]
  }
  emitUpdate()
}

function addPart() {
  // Insert BEFORE the trailing rest part so the invariant "last part = rest"
  // holds without re-shuffling sizes.
  const list = partsConfig.value.list
  const insertAt = Math.max(0, list.length - 1)
  const part = makePart(list.length)
  part.size = 1
  list.splice(insertAt, 0, part)
  emitUpdate()
}

function removePart(index) {
  if (partsConfig.value.list.length > 2) {
    partsConfig.value.list.splice(index, 1)
    emitUpdate()
  }
}

function buildPartsPayload() {
  const list = partsConfig.value.list
  return {
    enabled: true,
    list: list.map((part, index) => {
      const out = {
        id: part.id || `p${index + 1}`,
        name: (part.name || '').trim() || `Teil ${index + 1}`,
        order: part.order === 'random' ? 'random' : 'sequential',
        copilot: Boolean(copilotConfig.value.enabled && part.copilot),
        locked: Boolean(part.locked)
      }
      // Server-resolved assignments (existing scenarios) win over size specs
      if (Array.isArray(part.item_ids) && part.item_ids.length) {
        out.item_ids = [...part.item_ids]
      } else if (index < list.length - 1) {
        out.size = Math.max(1, Number(part.size) || 1)
      }
      return out
    })
  }
}

function insertPlaceholder(placeholder) {
  const current = copilotConfig.value.prompt || ''
  copilotConfig.value.prompt = current + (current.endsWith('\n') || !current ? '' : '\n') + placeholder
  emitUpdate()
}

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
  const payload = { ...localConfig.value, copilot: { ...copilotConfig.value } }
  // Opt-in contract: toggle off → NO parts field in the payload at all
  // (a scenario without parts must be byte-identical to today's configs).
  if (partsConfig.value.enabled && partsConfig.value.list.length) {
    payload.parts = buildPartsPayload()
  } else {
    delete payload.parts
  }
  emit('update:modelValue', payload)
}

function initFromProps() {
  if (props.modelValue) {
    localConfig.value = {
      ...localConfig.value,
      ...props.modelValue,
      categories: props.modelValue.categories ? [...props.modelValue.categories] : []
    }
    if (props.modelValue.copilot) {
      copilotConfig.value = { ...defaultCopilot(), ...props.modelValue.copilot }
    }
    if (props.modelValue.parts) {
      partsConfig.value = {
        enabled: Boolean(props.modelValue.parts.enabled),
        list: Array.isArray(props.modelValue.parts.list)
          ? props.modelValue.parts.list.map(p => ({ ...p }))
          : []
      }
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

/* Co-Pilot */
.copilot-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

/* Parts / Phases */
.parts-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

.part-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  margin-bottom: 8px;
  background-color: rgba(var(--v-theme-surface), 1);
  border-radius: 6px;
}

.part-row-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.part-row-options {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.part-size-field {
  width: 130px;
  flex-shrink: 0;
}

.part-order-select {
  width: 200px;
  flex-shrink: 0;
}

.parts-error-text {
  font-size: 0.75rem;
  color: rgb(var(--v-theme-error));
  margin-top: 8px;
  display: flex;
  align-items: center;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.placeholder-chips {
  display: flex;
  gap: 6px;
}

.placeholder-chip {
  cursor: pointer;
  font-family: monospace;
}

.prompt-textarea :deep(textarea) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.82rem;
}
</style>
