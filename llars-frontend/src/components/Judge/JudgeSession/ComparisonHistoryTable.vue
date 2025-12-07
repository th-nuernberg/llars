<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-history</v-icon>
      Verlauf ({{ completedComparisons.length }} abgeschlossene Vergleiche)
    </v-card-title>
    <v-divider></v-divider>

    <v-data-table
      :headers="headers"
      :items="completedComparisons"
      :items-per-page="10"
      class="history-table"
    >
      <!-- Index -->
      <template v-slot:item.comparison_index="{ item }">
        <span class="font-weight-bold">#{{ item.comparison_index + 1 }}</span>
      </template>

      <!-- Pillars -->
      <template v-slot:item.pillars="{ item }">
        <div class="d-flex gap-1">
          <v-chip size="small" color="blue" variant="outlined">{{ item.pillar_a_name }}</v-chip>
          <v-icon size="small">mdi-arrow-left-right</v-icon>
          <v-chip size="small" color="green" variant="outlined">{{ item.pillar_b_name }}</v-chip>
        </div>
      </template>

      <!-- Winner -->
      <template v-slot:item.winner="{ item }">
        <v-chip
          size="small"
          :color="item.winner === 'A' ? 'blue' : item.winner === 'B' ? 'green' : 'grey'"
          variant="flat"
        >
          <v-icon start size="small">mdi-trophy</v-icon>
          {{ item.winner || 'TBD' }}
        </v-chip>
      </template>

      <!-- Confidence -->
      <template v-slot:item.confidence_score="{ item }">
        <v-chip
          v-if="item.confidence_score"
          size="small"
          :color="getConfidenceColor(item.confidence_score)"
          variant="outlined"
        >
          {{ Math.round(item.confidence_score * 100) }}%
        </v-chip>
        <span v-else>-</span>
      </template>

      <!-- Timestamp -->
      <template v-slot:item.evaluated_at="{ item }">
        {{ formatDate(item.evaluated_at) }}
      </template>

      <!-- Actions -->
      <template v-slot:item.actions="{ item }">
        <v-btn
          icon="mdi-eye"
          size="small"
          variant="text"
          @click="$emit('view-comparison', item)"
        ></v-btn>
      </template>
    </v-data-table>
  </v-card>
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
</script>

<style scoped>
.history-table :deep(tbody tr) {
  cursor: pointer;
}

.history-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
