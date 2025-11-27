<template>
  <div class="transition-heatmap" :style="{ '--cell-size': cellSize + 'px', '--label-width': labelWidth + 'px' }">
    <div class="heatmap-container" ref="heatmapContainer">
      <!-- Labels on Y-axis (left) -->
      <div class="y-labels">
        <div class="corner-cell"></div>
        <div
          v-for="label in sortedLabels"
          :key="'y-' + label"
          class="y-label"
          :class="{ 'highlighted-label': highlightedCell?.from === label }"
          :title="labelDisplays[label]"
        >
          {{ getShortLabel(label) }}
        </div>
      </div>

      <!-- Main grid -->
      <div class="heatmap-grid">
        <!-- X-axis labels (top) -->
        <div class="x-labels">
          <div
            v-for="label in sortedLabels"
            :key="'x-' + label"
            class="x-label"
            :class="{ 'highlighted-label': highlightedCell?.to === label }"
            :title="labelDisplays[label]"
          >
            {{ getShortLabel(label) }}
          </div>
        </div>

        <!-- Heatmap cells -->
        <div class="cells-container">
          <div
            v-for="fromLabel in sortedLabels"
            :key="'row-' + fromLabel"
            class="heatmap-row"
          >
            <div
              v-for="toLabel in sortedLabels"
              :key="fromLabel + '-' + toLabel"
              class="heatmap-cell"
              :class="{
                'highlighted-cell': highlightedCell?.from === fromLabel && highlightedCell?.to === toLabel,
                'highlighted-row': highlightedCell?.from === fromLabel,
                'highlighted-col': highlightedCell?.to === toLabel
              }"
              :style="getCellStyle(fromLabel, toLabel)"
              @mouseenter="onCellHover(fromLabel, toLabel)"
              @mouseleave="onCellLeave"
            >
              <span v-if="showValues && getCellValue(fromLabel, toLabel) > 0" class="cell-value">
                {{ formatCellValue(fromLabel, toLabel) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Hover Info Panel - shows for both local hover and external highlight (synced across heatmaps) -->
    <div v-if="highlightedCell" class="hover-info-panel mt-2">
      <div class="text-caption font-weight-bold">
        {{ labelDisplays[highlightedCell.from] || highlightedCell.from }}
        <v-icon size="x-small" class="mx-1">mdi-arrow-right</v-icon>
        {{ labelDisplays[highlightedCell.to] || highlightedCell.to }}
      </div>
      <div class="d-flex justify-space-between text-caption mt-1">
        <span>Anzahl:</span>
        <span class="font-weight-bold">{{ getCellValue(highlightedCell.from, highlightedCell.to) }}</span>
      </div>
      <div class="d-flex justify-space-between text-caption">
        <span>Wahrsch.:</span>
        <span class="font-weight-bold">{{ (getCellProbability(highlightedCell.from, highlightedCell.to) * 100).toFixed(1) }}%</span>
      </div>
    </div>

    <!-- Color legend -->
    <div class="heatmap-legend mt-2">
      <span class="text-caption mr-2">0</span>
      <div class="legend-gradient"></div>
      <span class="text-caption ml-2">{{ maxValueDisplay }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  counts: {
    type: Object,
    required: true
  },
  probabilities: {
    type: Object,
    default: () => ({})
  },
  labels: {
    type: Array,
    default: () => []
  },
  labelDisplays: {
    type: Object,
    default: () => ({})
  },
  showValues: {
    type: Boolean,
    default: false
  },
  colorMode: {
    type: String,
    default: 'count' // 'count' or 'probability'
  },
  pillarName: {
    type: String,
    default: ''
  },
  pillarNumber: {
    type: [Number, String],
    default: null
  },
  // External highlight from parent (for sync across heatmaps)
  externalHighlight: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['cell-hover', 'cell-leave']);

const heatmapContainer = ref(null);
const localHighlight = ref(null);
const isHoveredLocally = ref(false);

// Combine local and external highlight
const highlightedCell = computed(() => {
  return localHighlight.value || props.externalHighlight;
});

// Sort labels: CO- first, then CL-
const sortedLabels = computed(() => {
  const coLabels = props.labels.filter(l => l.startsWith('CO-')).sort();
  const clLabels = props.labels.filter(l => l.startsWith('CL-')).sort();
  return [...coLabels, ...clLabels];
});

// Dynamic cell size based on number of labels
const cellSize = computed(() => {
  const numLabels = sortedLabels.value.length;
  if (numLabels <= 10) return 28;
  if (numLabels <= 15) return 22;
  if (numLabels <= 20) return 18;
  return 14;
});

const labelWidth = computed(() => {
  return cellSize.value <= 18 ? 50 : 60;
});

// Get max value for color scaling
const maxValue = computed(() => {
  let max = 0;
  for (const fromLabel in props.counts) {
    for (const toLabel in props.counts[fromLabel]) {
      const val = props.colorMode === 'probability'
        ? (props.probabilities[fromLabel]?.[toLabel] || 0)
        : (props.counts[fromLabel]?.[toLabel] || 0);
      if (val > max) max = val;
    }
  }
  return max;
});

const maxValueDisplay = computed(() => {
  return props.colorMode === 'probability' ? Math.round(maxValue.value * 100) + '%' : maxValue.value;
});

const getCellValue = (fromLabel, toLabel) => {
  return props.counts[fromLabel]?.[toLabel] || 0;
};

const getCellProbability = (fromLabel, toLabel) => {
  return props.probabilities[fromLabel]?.[toLabel] || 0;
};

const formatCellValue = (fromLabel, toLabel) => {
  if (props.colorMode === 'probability') {
    const prob = getCellProbability(fromLabel, toLabel);
    return prob > 0 ? Math.round(prob * 100) : '';
  }
  return getCellValue(fromLabel, toLabel);
};

const getCellStyle = (fromLabel, toLabel) => {
  const value = props.colorMode === 'probability'
    ? getCellProbability(fromLabel, toLabel)
    : getCellValue(fromLabel, toLabel);

  const maxVal = props.colorMode === 'probability' ? 1 : maxValue.value;
  const intensity = maxVal > 0 ? value / maxVal : 0;

  // Color gradient from white to deep blue
  const r = Math.round(255 - intensity * 200);
  const g = Math.round(255 - intensity * 150);
  const b = Math.round(255 - intensity * 50);

  return {
    backgroundColor: value > 0 ? `rgb(${r}, ${g}, ${b})` : 'var(--v-theme-surface, #f5f5f5)',
    color: intensity > 0.5 ? 'white' : 'inherit'
  };
};

const getShortLabel = (label) => {
  // Shorten labels for display
  return label.replace('CO-IF-', '').replace('CL-IF-', '').replace('CO-', '').replace('CL-', '');
};

const onCellHover = (fromLabel, toLabel) => {
  localHighlight.value = { from: fromLabel, to: toLabel };
  isHoveredLocally.value = true;
  emit('cell-hover', {
    from: fromLabel,
    to: toLabel,
    pillar: props.pillarNumber,
    count: getCellValue(fromLabel, toLabel),
    probability: getCellProbability(fromLabel, toLabel)
  });
};

const onCellLeave = () => {
  localHighlight.value = null;
  isHoveredLocally.value = false;
  emit('cell-leave');
};

// Watch external highlight changes
watch(() => props.externalHighlight, (newVal) => {
  if (!newVal) {
    localHighlight.value = null;
  }
});
</script>

<style scoped>
.transition-heatmap {
  --cell-size: 24px;
  --label-width: 60px;
  overflow-x: auto;
  overflow-y: visible;
  max-width: 100%;
}

.heatmap-container {
  display: flex;
  width: fit-content;
  min-width: min-content;
}

.y-labels {
  display: flex;
  flex-direction: column;
}

.corner-cell {
  height: 50px;
  width: var(--label-width);
}

.y-label {
  height: var(--cell-size);
  width: var(--label-width);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 4px;
  font-size: 8px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background-color 0.15s;
}

.y-label.highlighted-label {
  background-color: rgba(var(--v-theme-primary), 0.15);
  font-weight: 700;
}

.heatmap-grid {
  display: flex;
  flex-direction: column;
}

.x-labels {
  display: flex;
  height: 50px;
}

.x-label {
  width: var(--cell-size);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  font-size: 8px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-bottom: 4px;
  transition: background-color 0.15s;
}

.x-label.highlighted-label {
  background-color: rgba(var(--v-theme-primary), 0.15);
  font-weight: 700;
}

.cells-container {
  display: flex;
  flex-direction: column;
}

.heatmap-row {
  display: flex;
}

.heatmap-cell {
  width: var(--cell-size);
  height: var(--cell-size);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
}

.heatmap-cell.highlighted-row,
.heatmap-cell.highlighted-col {
  opacity: 0.7;
}

.heatmap-cell.highlighted-cell {
  opacity: 1;
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -1px;
  z-index: 10;
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.cell-value {
  font-size: 6px;
  font-weight: bold;
  line-height: 1;
}

.hover-info-panel {
  background: rgba(var(--v-theme-surface-variant), 0.95);
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  border-radius: 4px;
  padding: 6px 10px;
  min-width: 140px;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: center;
}

.legend-gradient {
  width: 80px;
  height: 10px;
  background: linear-gradient(to right, var(--v-theme-surface, #f5f5f5), #37a5eb);
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}
</style>
