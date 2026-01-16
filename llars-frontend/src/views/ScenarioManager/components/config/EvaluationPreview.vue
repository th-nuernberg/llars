<template>
  <div class="evaluation-preview">
    <!-- Rating Preview -->
    <div v-if="evalType === 'rating'" class="preview-rating">
      <div class="preview-label">{{ $t('scenarioManager.evalConfig.preview.ratingDemo') }}</div>

      <!-- Stars Preview -->
      <div v-if="config?.type === 'stars'" class="stars-preview">
        <v-rating
          v-model="demoRating"
          :length="config.max - config.min + 1"
          :half-increments="config.allowHalf"
          color="warning"
          active-color="warning"
          hover
        />
        <span class="rating-value">{{ demoRating }} / {{ config.max }}</span>
      </div>

      <!-- Likert Preview -->
      <div v-else-if="config?.type === 'likert'" class="likert-preview">
        <div class="likert-scale">
          <div
            v-for="val in scaleValues"
            :key="val"
            class="likert-option"
            :class="{ selected: demoRating === val }"
            @click="demoRating = val"
          >
            <div class="option-circle">{{ val }}</div>
            <span v-if="config.showLabels && getLabel(val)" class="option-label">
              {{ getLabel(val) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Slider Preview -->
      <div v-else-if="config?.type === 'slider'" class="slider-preview">
        <v-slider
          v-model="demoRating"
          :min="config.min"
          :max="config.max"
          :step="config.step"
          thumb-label
          color="primary"
        />
        <span class="slider-value">{{ demoRating }}{{ config.unit || '' }}</span>
      </div>

      <!-- Numeric Preview -->
      <div v-else class="numeric-preview">
        <v-btn-toggle v-model="demoRating" mandatory color="primary">
          <v-btn v-for="val in scaleValues" :key="val" :value="val" variant="outlined">
            {{ val }}
          </v-btn>
        </v-btn-toggle>
      </div>

      <!-- Dimensions Preview (optional, for multi-dimensional rating) -->
      <div v-if="config?.dimensions?.length" class="dimensions-preview mt-3">
        <div v-for="dim in config.dimensions" :key="dim.id" class="dimension-item">
          <span class="dim-name">{{ getDimensionName(dim) }}</span>
          <v-rating
            :model-value="3"
            :length="config.max - config.min + 1"
            density="compact"
            color="warning"
            active-color="warning"
            readonly
            size="small"
          />
        </div>
      </div>
    </div>

    <!-- Ranking Preview -->
    <div v-else-if="evalType === 'ranking'" class="preview-ranking">
      <div class="preview-label">{{ $t('scenarioManager.evalConfig.preview.rankingDemo') }}</div>

      <!-- Buckets Preview -->
      <div v-if="config?.type === 'buckets' && config?.buckets?.length" class="buckets-preview">
        <div
          v-for="bucket in config.buckets"
          :key="bucket.id"
          class="bucket-box"
          :style="{ borderColor: bucket.color, backgroundColor: bucket.color + '15' }"
        >
          <div class="bucket-header" :style="{ backgroundColor: bucket.color }">
            {{ getBucketName(bucket) }}
          </div>
          <div class="bucket-content">
            <div class="demo-item">Item 1</div>
            <div class="demo-item">Item 2</div>
          </div>
        </div>
      </div>

      <!-- Ordered Preview -->
      <div v-else class="ordered-preview">
        <div class="ordered-list">
          <div v-for="i in 3" :key="i" class="ordered-item">
            <span class="position">{{ i }}</span>
            <span class="item-text">Demo Item {{ i }}</span>
            <LIcon class="drag-icon" size="18">mdi-drag-vertical</LIcon>
          </div>
        </div>
        <div v-if="config?.labels" class="order-labels">
          <span class="label-first">{{ config.labels.first }}</span>
          <span class="label-last">{{ config.labels.last }}</span>
        </div>
      </div>
    </div>

    <!-- Labeling Preview -->
    <div v-else-if="evalType === 'labeling'" class="preview-labeling">
      <div class="preview-label">{{ $t('scenarioManager.evalConfig.preview.labelingDemo') }}</div>

      <div class="labels-preview">
        <div
          v-for="cat in config?.categories || []"
          :key="cat.id"
          class="label-chip"
          :class="{ selected: selectedLabels.includes(cat.id), multiselect: config?.multiLabel }"
          :style="{
            '--chip-color': cat.color,
            backgroundColor: selectedLabels.includes(cat.id) ? cat.color + '25' : 'transparent',
            borderColor: cat.color
          }"
          @click="toggleLabel(cat.id)"
        >
          <LIcon v-if="cat.icon" :color="cat.color" size="18">{{ cat.icon }}</LIcon>
          <span>{{ getCategoryName(cat) }}</span>
          <LIcon v-if="config?.multiLabel && selectedLabels.includes(cat.id)" size="16" color="primary">
            mdi-check
          </LIcon>
        </div>

        <!-- Unsure option -->
        <div
          v-if="config?.allowUnsure && config?.unsureOption"
          class="label-chip unsure"
          :class="{ selected: selectedLabels.includes('unsure') }"
          :style="{
            '--chip-color': config.unsureOption.color,
            backgroundColor: selectedLabels.includes('unsure') ? config.unsureOption.color + '25' : 'transparent',
            borderColor: config.unsureOption.color
          }"
          @click="toggleLabel('unsure')"
        >
          <LIcon :color="config.unsureOption.color" size="18">{{ config.unsureOption.icon }}</LIcon>
          <span>{{ getCategoryName(config.unsureOption) }}</span>
        </div>
      </div>
    </div>

    <!-- Comparison Preview -->
    <div v-else-if="evalType === 'comparison'" class="preview-comparison">
      <div class="preview-label">{{ $t('scenarioManager.evalConfig.preview.comparisonDemo') }}</div>

      <div class="comparison-layout">
        <div class="compare-item" :class="{ winner: selectedWinner === 'A' }" @click="selectedWinner = 'A'">
          <div class="item-header">Option A</div>
          <div class="item-content">
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
          </div>
          <div v-if="selectedWinner === 'A'" class="winner-badge">
            <LIcon color="success">mdi-trophy</LIcon>
          </div>
        </div>

        <div class="vs-divider">
          <span>VS</span>
          <v-btn
            v-if="config?.allowTie"
            size="small"
            variant="outlined"
            :color="selectedWinner === 'tie' ? 'warning' : 'grey'"
            @click="selectedWinner = 'tie'"
          >
            {{ $t('scenarioManager.evalConfig.preview.tie') }}
          </v-btn>
        </div>

        <div class="compare-item" :class="{ winner: selectedWinner === 'B' }" @click="selectedWinner = 'B'">
          <div class="item-header">Option B</div>
          <div class="item-content">
            <p>Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          </div>
          <div v-if="selectedWinner === 'B'" class="winner-badge">
            <LIcon color="success">mdi-trophy</LIcon>
          </div>
        </div>
      </div>

      <!-- Criteria display -->
      <div v-if="config?.criteria?.length > 1" class="criteria-preview mt-3">
        <span class="criteria-label">{{ $t('scenarioManager.evalConfig.preview.criteriaUsed') }}:</span>
        <div class="criteria-tags">
          <LTag v-for="crit in config.criteria" :key="crit.id" variant="info" size="small">
            {{ getCriterionName(crit) }} ({{ (crit.weight * 100).toFixed(0) }}%)
          </LTag>
        </div>
      </div>

      <!-- Confidence display -->
      <div v-if="config?.showConfidence" class="confidence-preview mt-3">
        <span class="confidence-label">{{ $t('scenarioManager.evalConfig.preview.confidence') }}:</span>
        <v-rating
          v-model="demoConfidence"
          :length="config.confidenceScale?.max - config.confidenceScale?.min + 1"
          color="warning"
          active-color="warning"
          density="compact"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  evalType: {
    type: String,
    required: true
  },
  config: {
    type: Object,
    default: () => ({})
  }
})

const { t, locale } = useI18n()

// Demo state
const demoRating = ref(3)
const demoConfidence = ref(3)
const selectedLabels = ref([])
const selectedWinner = ref(null)

// Computed
const scaleValues = computed(() => {
  if (!props.config) return []
  const values = []
  const min = props.config.min || 1
  const max = props.config.max || 5
  const step = props.config.step || 1
  for (let v = min; v <= max; v += step) {
    values.push(v)
  }
  return values
})

// Methods
function getLabel(value) {
  if (!props.config?.labels?.[value]) return null
  const label = props.config.labels[value]
  if (typeof label === 'string') return label
  return label[locale.value] || label.de || label.en || ''
}

function getBucketName(bucket) {
  if (!bucket?.name) return ''
  if (typeof bucket.name === 'string') return bucket.name
  return bucket.name[locale.value] || bucket.name.de || bucket.name.en || ''
}

function getCategoryName(category) {
  if (!category?.name) return ''
  if (typeof category.name === 'string') return category.name
  return category.name[locale.value] || category.name.de || category.name.en || ''
}

function getCriterionName(criterion) {
  if (!criterion?.name) return ''
  if (typeof criterion.name === 'string') return criterion.name
  return criterion.name[locale.value] || criterion.name.de || criterion.name.en || ''
}

function getDimensionName(dimension) {
  if (!dimension?.name) return ''
  if (typeof dimension.name === 'string') return dimension.name
  return dimension.name[locale.value] || dimension.name.de || dimension.name.en || ''
}

function toggleLabel(labelId) {
  if (props.config?.multiLabel) {
    const idx = selectedLabels.value.indexOf(labelId)
    if (idx >= 0) {
      selectedLabels.value.splice(idx, 1)
    } else {
      selectedLabels.value.push(labelId)
    }
  } else {
    selectedLabels.value = [labelId]
  }
}
</script>

<style scoped>
.evaluation-preview {
  padding: 8px 0;
}

.preview-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Rating Preview */
.stars-preview {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rating-value {
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.likert-preview {
  overflow-x: auto;
}

.likert-scale {
  display: flex;
  gap: 8px;
  min-width: max-content;
}

.likert-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s;
}

.likert-option:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.likert-option.selected {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.option-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.2);
  transition: all 0.2s;
}

.likert-option.selected .option-circle {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgb(var(--v-theme-primary));
  color: white;
}

.option-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-align: center;
  max-width: 80px;
}

.slider-preview {
  display: flex;
  align-items: center;
  gap: 16px;
}

.slider-value {
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  min-width: 50px;
}

.dimensions-preview {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  padding-top: 12px;
}

.dimension-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.dim-name {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Ranking Preview */
.buckets-preview {
  display: flex;
  gap: 12px;
  overflow-x: auto;
}

.bucket-box {
  flex: 1;
  min-width: 120px;
  border: 2px solid;
  border-radius: 8px;
  overflow: hidden;
}

.bucket-header {
  padding: 8px 12px;
  font-weight: 600;
  font-size: 0.85rem;
  color: white;
  text-align: center;
}

.bucket-content {
  padding: 12px;
  min-height: 60px;
}

.demo-item {
  padding: 6px 10px;
  background-color: rgba(var(--v-theme-surface), 1);
  border-radius: 4px;
  font-size: 0.8rem;
  margin-bottom: 4px;
}

.ordered-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ordered-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background-color: rgba(var(--v-theme-surface), 1);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 6px;
}

.position {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgb(var(--v-theme-primary));
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
}

.item-text {
  flex: 1;
  font-size: 0.85rem;
}

.drag-icon {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.order-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Labeling Preview */
.labels-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.label-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: 2px solid;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.label-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.label-chip.selected {
  font-weight: 600;
}

/* Comparison Preview */
.comparison-layout {
  display: flex;
  gap: 16px;
  align-items: stretch;
}

.compare-item {
  flex: 1;
  position: relative;
  padding: 16px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.compare-item:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.compare-item.winner {
  border-color: rgb(var(--v-theme-success));
  background-color: rgba(var(--v-theme-success), 0.05);
}

.item-header {
  font-weight: 600;
  margin-bottom: 8px;
  color: rgb(var(--v-theme-on-surface));
}

.item-content p {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0;
}

.winner-badge {
  position: absolute;
  top: -8px;
  right: -8px;
}

.vs-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 8px;
}

.vs-divider span:first-child {
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.criteria-preview,
.confidence-preview {
  display: flex;
  align-items: center;
  gap: 8px;
}

.criteria-label,
.confidence-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.criteria-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
