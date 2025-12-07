<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-playlist-play</v-icon>
      Vergleichs-Warteschlange
      <v-spacer></v-spacer>
      <v-chip size="small" color="info" class="mr-2">
        {{ queue.stats?.pending || 0 }} ausstehend
      </v-chip>
      <v-chip size="small" color="warning" class="mr-2" v-if="queue.stats?.running > 0">
        {{ queue.stats?.running || 0 }} läuft
      </v-chip>
      <v-chip size="small" color="success" class="mr-2" v-if="queue.stats?.completed > 0">
        {{ queue.stats?.completed || 0 }} fertig
      </v-chip>
      <v-btn
        icon="mdi-refresh"
        variant="text"
        size="small"
        @click="$emit('refresh')"
        :loading="loading"
      ></v-btn>
    </v-card-title>
    <v-divider></v-divider>

    <!-- Queue Table -->
    <v-data-table
      v-if="queue.pending?.length > 0 || queue.current"
      :headers="headers"
      :items="allQueueItems"
      :items-per-page="20"
      class="queue-table"
      density="compact"
    >
      <!-- Position -->
      <template v-slot:item.queue_position="{ item }">
        <span class="font-weight-bold">#{{ item.queue_position + 1 }}</span>
      </template>

      <!-- Status -->
      <template v-slot:item.status="{ item }">
        <v-chip
          size="x-small"
          :color="getQueueStatusColor(item.status)"
          variant="flat"
        >
          <v-icon start size="x-small" :class="{ 'mdi-spin': item.status === 'running' }">
            {{ getQueueStatusIcon(item.status) }}
          </v-icon>
          {{ getQueueStatusText(item.status) }}
        </v-chip>
      </template>

      <!-- Pillar A -->
      <template v-slot:item.pillar_a="{ item }">
        <v-chip size="small" color="blue" variant="outlined">
          {{ item.pillar_a_name }}
        </v-chip>
      </template>

      <!-- VS -->
      <template v-slot:item.vs="{ item }">
        <v-icon size="small">mdi-arrow-left-right</v-icon>
      </template>

      <!-- Pillar B -->
      <template v-slot:item.pillar_b="{ item }">
        <v-chip size="small" color="green" variant="outlined">
          {{ item.pillar_b_name }}
        </v-chip>
      </template>

      <!-- Result (if completed) -->
      <template v-slot:item.result="{ item }">
        <template v-if="item.winner">
          <v-chip size="x-small" :color="item.winner === 'A' ? 'blue' : 'green'" variant="flat">
            <v-icon start size="x-small">mdi-trophy</v-icon>
            {{ item.winner }}
          </v-chip>
        </template>
        <span v-else class="text-medium-emphasis">-</span>
      </template>
    </v-data-table>

    <!-- Empty State -->
    <v-card-text v-else class="text-center py-8 text-medium-emphasis">
      <v-icon size="48" class="mb-2">mdi-playlist-remove</v-icon>
      <div>Keine Vergleiche in der Warteschlange</div>
      <div class="text-caption mt-1">
        Konfigurieren Sie die Session um Vergleiche zu erstellen
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
defineProps({
  queue: {
    type: Object,
    required: true
  },
  allQueueItems: {
    type: Array,
    default: () => []
  },
  headers: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  getQueueStatusColor: {
    type: Function,
    required: true
  },
  getQueueStatusIcon: {
    type: Function,
    required: true
  },
  getQueueStatusText: {
    type: Function,
    required: true
  }
});

defineEmits(['refresh']);
</script>

<style scoped>
.queue-table :deep(tbody tr) {
  cursor: pointer;
}

.queue-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
