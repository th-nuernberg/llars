<template>
  <v-card>
    <v-card-text>
      <div class="d-flex justify-space-between mb-2">
        <span class="text-subtitle-2">Fortschritt</span>
        <span class="text-subtitle-2 font-weight-bold">
          {{ session?.completed_comparisons || 0 }} / {{ session?.total_comparisons || 0 }} Vergleiche
        </span>
      </div>
      <v-progress-linear
        :model-value="progress"
        height="25"
        rounded
        :color="progress === 100 ? 'success' : 'primary'"
        striped
      >
        <template v-slot:default="{ value }">
          <strong>{{ Math.round(value) }}%</strong>
        </template>
      </v-progress-linear>

      <!-- Session Info -->
      <div class="d-flex justify-space-between mt-4 text-caption text-medium-emphasis">
        <span>Säulen: {{ session?.pillar_count }}</span>
        <span>Samples: {{ session?.samples_per_pillar }}</span>
        <span>Position-Swap: {{ session?.position_swap ? 'Ja' : 'Nein' }}</span>
        <span v-if="workerCount > 1">Worker: {{ workerCount }}</span>
        <span v-if="session?.created_at">Erstellt: {{ formatDate(session.created_at) }}</span>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
defineProps({
  session: {
    type: Object,
    default: null
  },
  progress: {
    type: Number,
    default: 0
  },
  workerCount: {
    type: Number,
    default: 1
  },
  formatDate: {
    type: Function,
    required: true
  }
});
</script>
