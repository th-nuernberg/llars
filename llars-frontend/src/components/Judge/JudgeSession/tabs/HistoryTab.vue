<template>
  <div class="history-tab">
    <!-- Header with Filters -->
    <div class="history-header">
      <div class="header-left">
        <LIcon size="20" class="mr-2">mdi-history</LIcon>
        <span class="header-title">Verlauf</span>
        <v-chip size="x-small" color="success" class="ml-2">
          {{ comparisons.length }} Vergleiche
        </v-chip>
      </div>
      <div class="header-right">
        <v-btn
          icon="mdi-filter-variant"
          variant="text"
          size="small"
          @click="showFilters = !showFilters"
          :color="hasActiveFilters ? 'primary' : undefined"
        ></v-btn>
        <v-btn
          icon="mdi-refresh"
          variant="text"
          size="small"
          @click="$emit('refresh')"
          :loading="loading"
        ></v-btn>
      </div>
    </div>

    <!-- Filter Bar (collapsible) -->
    <v-expand-transition>
      <div v-if="showFilters" class="filter-bar">
        <div class="filter-row">
          <div class="filter-group">
            <span class="filter-label">Gewinner:</span>
            <v-btn-toggle v-model="filterWinner" density="compact">
              <v-btn value="" size="x-small" variant="text">Alle</v-btn>
              <v-btn value="A" size="x-small" variant="text" color="blue">A</v-btn>
              <v-btn value="B" size="x-small" variant="text" color="green">B</v-btn>
              <v-btn value="TIE" size="x-small" variant="text" color="warning">TIE</v-btn>
            </v-btn-toggle>
          </div>
          <div class="filter-group">
            <span class="filter-label">Säule:</span>
            <v-select
              v-model="filterPillar"
              :items="pillarOptions"
              density="compact"
              variant="outlined"
              hide-details
              clearable
              class="filter-select"
            ></v-select>
          </div>
          <v-btn
            v-if="hasActiveFilters"
            size="x-small"
            variant="text"
            color="grey"
            @click="clearFilters"
          >
            Filter löschen
          </v-btn>
        </div>
      </div>
    </v-expand-transition>

    <!-- Comparison List -->
    <div class="history-content">
      <div v-if="filteredComparisons.length === 0" class="empty-state">
        <LIcon size="48" color="grey">mdi-clipboard-text-off</LIcon>
        <p>{{ hasActiveFilters ? 'Keine Vergleiche mit diesen Filtern' : 'Noch keine abgeschlossenen Vergleiche' }}</p>
      </div>

      <div v-else class="comparison-list">
        <div
          v-for="comparison in filteredComparisons"
          :key="comparison.comparison_id"
          class="comparison-item"
          :class="{ 'is-selected': selectedId === comparison.comparison_id }"
          @click="selectComparison(comparison)"
        >
          <!-- Main Row -->
          <div class="item-main">
            <div class="item-index">#{{ (comparison.comparison_index ?? comparison.queue_position ?? 0) + 1 }}</div>

            <div class="item-pillars">
              <span class="pillar-chip pillar-a">{{ comparison.pillar_a_name || 'S' + comparison.pillar_a }}</span>
              <LIcon size="12">mdi-arrow-left-right</LIcon>
              <span class="pillar-chip pillar-b">{{ comparison.pillar_b_name || 'S' + comparison.pillar_b }}</span>
            </div>

            <div class="item-winner">
              <v-chip
                :color="getWinnerColor(comparison.winner)"
                size="x-small"
                :prepend-icon="comparison.winner === 'TIE' ? 'mdi-equal' : 'mdi-trophy'"
              >
                {{ comparison.winner || '?' }}
              </v-chip>
            </div>

            <div class="item-confidence">
              <div class="confidence-bar-mini">
                <div
                  class="confidence-fill"
                  :style="{ width: (comparison.confidence_score || 0) * 100 + '%' }"
                  :class="getConfidenceClass(comparison.confidence_score)"
                ></div>
              </div>
              <span class="confidence-value">
                {{ comparison.confidence_score ? Math.round(comparison.confidence_score * 100) + '%' : '-' }}
              </span>
            </div>

            <div class="item-time">
              {{ formatTime(comparison.completed_at || comparison.evaluated_at) }}
            </div>

            <v-btn
              icon="mdi-fullscreen"
              variant="text"
              size="x-small"
              @click.stop="$emit('view-fullscreen', comparison)"
              title="Im Vollbild anzeigen"
            ></v-btn>
          </div>

          <!-- Preview Row (when selected) -->
          <v-expand-transition>
            <div v-if="selectedId === comparison.comparison_id" class="item-preview">
              <div class="preview-content">
                <div class="preview-scores" v-if="comparison.scores">
                  <div v-for="(score, key) in comparison.scores" :key="key" class="score-mini">
                    <span class="score-label">{{ formatCriterionShort(key) }}</span>
                    <span class="score-a">{{ score.a }}</span>
                    <span class="score-vs">:</span>
                    <span class="score-b">{{ score.b }}</span>
                  </div>
                </div>
                <div v-if="comparison.reasoning" class="preview-reasoning">
                  <LIcon size="14" class="mr-1">mdi-message-text</LIcon>
                  {{ truncate(comparison.reasoning, 150) }}
                </div>
                <v-btn
                  variant="tonal"
                  size="small"
                  color="primary"
                  class="mt-2"
                  @click="$emit('view-detail', comparison)"
                >
                  <LIcon start size="16">mdi-eye</LIcon>
                  Vollständig anzeigen
                </v-btn>
              </div>
            </div>
          </v-expand-transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  comparisons: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
});

const emit = defineEmits(['view-detail', 'view-fullscreen', 'refresh']);

const showFilters = ref(false);
const filterWinner = ref('');
const filterPillar = ref(null);
const selectedId = ref(null);

// Pillar options
const pillarOptions = computed(() => {
  const pillars = new Set();
  props.comparisons.forEach(c => {
    pillars.add(c.pillar_a);
    pillars.add(c.pillar_b);
  });
  return Array.from(pillars).sort().map(p => ({
    title: `Säule ${p}`,
    value: p
  }));
});

// Filtered comparisons
const filteredComparisons = computed(() => {
  return props.comparisons.filter(c => {
    if (filterWinner.value && c.winner !== filterWinner.value) return false;
    if (filterPillar.value && c.pillar_a !== filterPillar.value && c.pillar_b !== filterPillar.value) return false;
    return true;
  });
});

const hasActiveFilters = computed(() => filterWinner.value || filterPillar.value);

// Methods
const clearFilters = () => {
  filterWinner.value = '';
  filterPillar.value = null;
};

const selectComparison = (comparison) => {
  if (selectedId.value === comparison.comparison_id) {
    selectedId.value = null;
  } else {
    selectedId.value = comparison.comparison_id;
  }
};

const getWinnerColor = (winner) => {
  if (winner === 'A') return 'blue';
  if (winner === 'B') return 'green';
  if (winner === 'TIE') return 'warning';
  return 'grey';
};

const getConfidenceClass = (confidence) => {
  if (confidence >= 0.8) return 'high';
  if (confidence >= 0.6) return 'medium';
  return 'low';
};

const formatTime = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return 'gerade eben';
  if (diffMin < 60) return `vor ${diffMin} Min`;

  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `vor ${diffHours} Std`;

  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
};

const formatCriterionShort = (key) => {
  const names = {
    counsellor_coherence: 'KB',
    client_coherence: 'KK',
    quality: 'QL',
    empathy: 'EM',
    authenticity: 'AU',
    solution_orientation: 'LÖ'
  };
  return names[key] || key.substring(0, 2);
};

const truncate = (text, length) => {
  if (!text) return '';
  return text.length > length ? text.substring(0, length) + '...' : text;
};
</script>

<style scoped>
.history-tab {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

/* Header */
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-title {
  font-weight: 600;
  font-size: 14px;
}

/* Filter Bar */
.filter-bar {
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.filter-select {
  width: 120px;
}

.filter-select :deep(.v-field) {
  font-size: 12px;
}

/* Content */
.history-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Comparison List */
.comparison-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.comparison-item {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
}

.comparison-item:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background: rgba(var(--v-theme-primary), 0.02);
}

.comparison-item.is-selected {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.05);
}

/* Main Row */
.item-main {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  gap: 12px;
}

.item-index {
  width: 36px;
  font-weight: 600;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.item-pillars {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.pillar-chip {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

.pillar-chip.pillar-a {
  background: rgba(33, 150, 243, 0.15);
  color: #2196F3;
}

.pillar-chip.pillar-b {
  background: rgba(76, 175, 80, 0.15);
  color: #4CAF50;
}

.item-winner {
  width: 60px;
}

.item-confidence {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 80px;
}

.confidence-bar-mini {
  width: 40px;
  height: 4px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.confidence-fill.high {
  background: rgb(var(--v-theme-success));
}

.confidence-fill.medium {
  background: rgb(var(--v-theme-warning));
}

.confidence-fill.low {
  background: rgb(var(--v-theme-error));
}

.confidence-value {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-weight: 500;
}

.item-time {
  width: 70px;
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-align: right;
}

/* Preview Row */
.item-preview {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.preview-content {
  padding: 12px;
}

.preview-scores {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.score-mini {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(var(--v-theme-surface), 0.8);
  border-radius: 4px;
  font-size: 11px;
}

.score-label {
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 600;
}

.score-a {
  color: #2196F3;
  font-weight: 600;
}

.score-b {
  color: #4CAF50;
  font-weight: 600;
}

.score-vs {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.preview-reasoning {
  font-size: 12px;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.7);
  padding: 8px;
  background: rgba(var(--v-theme-surface), 0.6);
  border-radius: 4px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}
</style>
