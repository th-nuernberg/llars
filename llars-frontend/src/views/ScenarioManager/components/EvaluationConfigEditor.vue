<template>
  <div class="eval-config-editor">
    <!-- Preset Selection -->
    <div class="preset-section" v-if="showPresets">
      <h4 class="section-title">{{ $t('scenarioManager.evalConfig.selectPreset') }}</h4>
      <div class="preset-grid">
        <div
          v-for="preset in availablePresets"
          :key="preset.id"
          class="preset-card"
          :class="{ selected: selectedPresetId === preset.id }"
          @click="selectPreset(preset)"
        >
          <div class="preset-icon" v-if="preset.id !== 'custom'">
            <LIcon color="primary" size="24">{{ presetIcon }}</LIcon>
          </div>
          <div class="preset-icon custom" v-else>
            <LIcon color="grey" size="24">mdi-cog-outline</LIcon>
          </div>
          <div class="preset-info">
            <span class="preset-name">{{ preset.name }}</span>
            <span class="preset-desc">{{ preset.description }}</span>
          </div>
          <LIcon v-if="selectedPresetId === preset.id" color="primary" class="preset-check">
            mdi-check-circle
          </LIcon>
        </div>
      </div>
    </div>

    <v-divider v-if="showPresets && showCustomConfig" class="my-4" />

    <!-- Custom Configuration -->
    <div class="custom-config" v-if="showCustomConfig">
      <h4 class="section-title">{{ $t('scenarioManager.evalConfig.customizeConfig') }}</h4>

      <!-- Rating Configuration -->
      <template v-if="editorType === 'rating'">
        <RatingConfigEditor
          v-model="localConfig"
          :show-dimensions="showDimensions"
          @update:modelValue="emitUpdate"
        />
      </template>

      <!-- Ranking Configuration -->
      <template v-else-if="editorType === 'ranking'">
        <RankingConfigEditor
          v-model="localConfig"
          @update:modelValue="emitUpdate"
        />
      </template>

      <!-- Labeling Configuration -->
      <template v-else-if="editorType === 'labeling'">
        <LabelingConfigEditor
          v-model="localConfig"
          @update:modelValue="emitUpdate"
        />
      </template>

      <!-- Comparison Configuration -->
      <template v-else-if="editorType === 'comparison'">
        <ComparisonConfigEditor
          v-model="localConfig"
          @update:modelValue="emitUpdate"
        />
      </template>
    </div>

    <!-- Config Preview -->
    <div class="config-preview" v-if="showPreview">
      <h4 class="section-title">{{ $t('scenarioManager.evalConfig.preview') }}</h4>
      <EvaluationPreview :eval-type="evalType" :config="localConfig" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  EVAL_TYPES,
  PRESETS_BY_TYPE,
  getBaseType,
  getPresetsArray,
  getDefaultConfig,
  cloneConfig,
  TYPE_INFO
} from '../config/evaluationPresets'
import RatingConfigEditor from './config/RatingConfigEditor.vue'
import RankingConfigEditor from './config/RankingConfigEditor.vue'
import LabelingConfigEditor from './config/LabelingConfigEditor.vue'
import ComparisonConfigEditor from './config/ComparisonConfigEditor.vue'
import EvaluationPreview from './config/EvaluationPreview.vue'

const props = defineProps({
  evalType: {
    type: String,
    required: true,
    validator: (v) => ['rating', 'ranking', 'labeling', 'comparison', 'mail_rating', 'authenticity'].includes(v)
  },
  modelValue: {
    type: Object,
    default: null
  },
  showPresets: {
    type: Boolean,
    default: true
  },
  showPreview: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

const { t } = useI18n()

// Local state
const selectedPresetId = ref(null)
const localConfig = ref(null)

// Computed
const availablePresets = computed(() => {
  return getPresetsArray(props.evalType)
})

const showCustomConfig = computed(() => {
  if (!editorType.value) return false
  return selectedPresetId.value === 'custom' || !props.showPresets
})

const presetIcon = computed(() => {
  return TYPE_INFO[props.evalType]?.icon || 'mdi-cog'
})

const resolvedType = computed(() => getBaseType(props.evalType))

const editorType = computed(() => {
  if (props.evalType === EVAL_TYPES.MAIL_RATING) return null
  return resolvedType.value
})

const showDimensions = computed(() => {
  if (resolvedType.value !== EVAL_TYPES.RATING) return false
  if (props.evalType === EVAL_TYPES.MAIL_RATING) return true
  return Array.isArray(localConfig.value?.dimensions) && localConfig.value.dimensions.length > 0
})

// Methods
function selectPreset(preset) {
  selectedPresetId.value = preset.id
  localConfig.value = cloneConfig(preset.config)
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', {
    presetId: selectedPresetId.value,
    config: localConfig.value
  })
}

function initFromValue() {
  if (props.modelValue?.config) {
    localConfig.value = cloneConfig(props.modelValue.config)
    selectedPresetId.value = props.modelValue.presetId || 'custom'
  } else {
    // Set default preset
    const presets = availablePresets.value
    if (presets.length > 0) {
      selectPreset(presets[0])
    }
  }
}

// Watchers
watch(() => props.evalType, () => {
  // Reset when type changes
  const presets = availablePresets.value
  if (presets.length > 0) {
    selectPreset(presets[0])
  }
})

watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.config !== localConfig.value) {
    initFromValue()
  }
}, { deep: true })

// Lifecycle
onMounted(() => {
  initFromValue()
})
</script>

<style scoped>
.eval-config-editor {
  padding: 8px 0;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 12px;
}

/* Preset Grid */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.preset-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background-color: rgba(var(--v-theme-primary), 0.02);
}

.preset-card.selected {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.preset-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.preset-icon.custom {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.preset-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.preset-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
}

.preset-desc {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.3;
}

.preset-check {
  position: absolute;
  top: 8px;
  right: 8px;
}

/* Custom Config */
.custom-config {
  margin-top: 16px;
}

/* Preview */
.config-preview {
  margin-top: 20px;
  padding: 16px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 10px;
}
</style>
