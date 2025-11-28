<template>
  <v-row class="mb-4">
    <v-col cols="12">
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
    </v-col>
  </v-row>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  session: {
    type: Object,
    required: true,
    default: () => ({})
  },
  workerCount: {
    type: Number,
    default: 1
  }
});

// Compute progress percentage
const progress = computed(() => {
  if (!props.session || !props.session.total_comparisons) return 0;
  return (props.session.completed_comparisons / props.session.total_comparisons) * 100;
});

// Format date to German locale
const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};
</script>
