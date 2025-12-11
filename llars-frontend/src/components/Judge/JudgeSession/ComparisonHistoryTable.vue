<template>
  <div class="history-table-container">
    <v-data-table
      :headers="headers"
      :items="completedComparisons"
      :items-per-page="5"
      density="compact"
      class="history-table"
      hide-default-footer
      v-if="completedComparisons.length > 0"
    >
      <!-- Index -->
      <template v-slot:item.comparison_index="{ item }">
        <span class="font-weight-bold text-caption">#{{ item.comparison_index + 1 }}</span>
      </template>

      <!-- Pillars -->
      <template v-slot:item.pillars="{ item }">
        <div class="d-flex align-center gap-1">
          <span class="pillar-badge pillar-a">{{ item.pillar_a_name?.substring(0, 8) || 'A' }}</span>
          <v-icon size="12" color="grey">mdi-arrow-left-right</v-icon>
          <span class="pillar-badge pillar-b">{{ item.pillar_b_name?.substring(0, 8) || 'B' }}</span>
        </div>
      </template>

      <!-- Winner -->
      <template v-slot:item.winner="{ item }">
        <v-chip
          size="x-small"
          :color="item.winner === 'A' ? 'blue' : item.winner === 'B' ? 'green' : 'grey'"
          variant="flat"
        >
          {{ item.winner || '?' }}
        </v-chip>
      </template>

      <!-- Confidence -->
      <template v-slot:item.confidence_score="{ item }">
        <span v-if="item.confidence_score" class="confidence-badge" :class="getConfidenceClass(item.confidence_score)">
          {{ Math.round(item.confidence_score * 100) }}%
        </span>
        <span v-else class="text-medium-emphasis">-</span>
      </template>

      <!-- Timestamp -->
      <template v-slot:item.evaluated_at="{ item }">
        <span class="text-caption text-medium-emphasis">{{ formatDate(item.evaluated_at) }}</span>
      </template>

      <!-- Actions -->
      <template v-slot:item.actions="{ item }">
        <v-btn
          icon="mdi-eye"
          size="x-small"
          variant="text"
          density="compact"
          @click="$emit('view-comparison', item)"
        ></v-btn>
      </template>
    </v-data-table>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <v-icon size="24" color="grey">mdi-history</v-icon>
      <span class="text-caption text-medium-emphasis">Noch keine Vergleiche abgeschlossen</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  completedComparisons: {
    type: Array,
    default: () => []
  },
  headers: {
    type: Array,
    required: true
  },
  getConfidenceColor: {
    type: Function,
    required: true
  },
  formatDate: {
    type: Function,
    required: true
  }
});

defineEmits(['view-comparison']);

const getConfidenceClass = (score) => {
  if (score >= 0.8) return 'confidence-high';
  if (score >= 0.6) return 'confidence-mid';
  return 'confidence-low';
};
</script>

<style scoped>
.history-table-container {
  height: 100%;
  overflow-y: auto;
}

.history-table {
  background: transparent !important;
}

.history-table :deep(thead th) {
  font-size: 10px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 6px 8px !important;
  background: rgba(var(--v-theme-surface-variant), 0.3) !important;
}

.history-table :deep(tbody td) {
  padding: 4px 8px !important;
  font-size: 12px;
}

.history-table :deep(tbody tr) {
  cursor: pointer;
}

.history-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05) !important;
}

.pillar-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.pillar-a {
  background: rgba(33, 150, 243, 0.15);
  color: rgb(33, 150, 243);
}

.pillar-b {
  background: rgba(76, 175, 80, 0.15);
  color: rgb(76, 175, 80);
}

.confidence-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.confidence-high {
  background: rgba(76, 175, 80, 0.15);
  color: rgb(76, 175, 80);
}

.confidence-mid {
  background: rgba(255, 152, 0, 0.15);
  color: rgb(255, 152, 0);
}

.confidence-low {
  background: rgba(244, 67, 54, 0.15);
  color: rgb(244, 67, 54);
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
</style>
