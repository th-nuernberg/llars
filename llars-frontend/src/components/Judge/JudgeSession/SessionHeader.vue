<template>
  <v-row class="mb-4">
    <v-col cols="12">
      <div class="d-flex align-center">
        <!-- Back Button -->
        <v-btn
          icon="mdi-arrow-left"
          variant="text"
          @click="$emit('back')"
        ></v-btn>

        <!-- Session Name and Status -->
        <div class="ml-2">
          <h1 class="text-h4 font-weight-bold">{{ session?.session_name || 'Judge Session' }}</h1>
          <div class="d-flex align-center mt-1">
            <v-chip
              :color="getStatusColor(session?.status)"
              :prepend-icon="getStatusIcon(session?.status)"
              size="small"
              class="mr-2"
            >
              {{ getStatusText(session?.status) }}
            </v-chip>
            <span class="text-caption text-medium-emphasis">
              Session ID: {{ sessionId }}
            </span>
          </div>
        </div>

        <v-spacer></v-spacer>

        <!-- Action Buttons - Intelligent State-Based -->
        <div class="d-flex gap-2 align-center">
          <!-- Recovery Warning Badge -->
          <v-chip
            v-if="sessionHealth?.needs_recovery"
            color="warning"
            size="small"
            prepend-icon="mdi-alert"
            class="mr-2"
          >
            Wiederherstellung nötig
          </v-chip>

          <!-- START: Only for created/queued sessions -->
          <v-btn
            v-if="session?.status === 'created' || session?.status === 'queued'"
            color="success"
            prepend-icon="mdi-play"
            @click="$emit('start')"
            :loading="actionLoading"
          >
            Starten
          </v-btn>

          <!-- PAUSE: Only when workers are actually running -->
          <v-btn
            v-if="isActuallyRunning"
            color="warning"
            prepend-icon="mdi-pause"
            @click="$emit('pause')"
            :loading="actionLoading"
          >
            Pause
          </v-btn>

          <!-- RESUME/RECOVER: When session needs recovery or is paused -->
          <v-btn
            v-if="showResumeButton"
            :color="sessionHealth?.needs_recovery ? 'error' : 'info'"
            :prepend-icon="sessionHealth?.needs_recovery ? 'mdi-restart-alert' : 'mdi-play'"
            @click="$emit('resume')"
            :loading="actionLoading"
          >
            {{ sessionHealth?.needs_recovery ? 'Wiederherstellen' : 'Fortsetzen' }}
          </v-btn>

          <!-- RESULTS: Completed sessions -->
          <v-btn
            v-if="session?.status === 'completed'"
            color="primary"
            prepend-icon="mdi-chart-box"
            @click="$emit('navigate-results')"
          >
            Ergebnisse
          </v-btn>

          <!-- Refresh -->
          <v-btn
            icon="mdi-refresh"
            variant="text"
            @click="$emit('refresh')"
            :loading="loading"
            title="Seite aktualisieren"
          ></v-btn>
        </div>
      </div>
    </v-col>
  </v-row>
</template>

<script setup>
// Props
const props = defineProps({
  session: {
    type: Object,
    default: null
  },
  sessionId: {
    type: [String, Number],
    required: true
  },
  sessionHealth: {
    type: Object,
    default: null
  },
  isActuallyRunning: {
    type: Boolean,
    default: false
  },
  showResumeButton: {
    type: Boolean,
    default: false
  },
  actionLoading: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  }
});

// Events
defineEmits([
  'start',
  'pause',
  'resume',
  'refresh',
  'navigate-results',
  'back'
]);

// Helper Functions
const getStatusColor = (status) => {
  const colors = {
    created: 'grey',
    queued: 'warning',
    running: 'info',
    paused: 'orange',
    completed: 'success',
    failed: 'error'
  };
  return colors[status] || 'grey';
};

const getStatusIcon = (status) => {
  const icons = {
    created: 'mdi-file-document',
    queued: 'mdi-clock-outline',
    running: 'mdi-play-circle',
    paused: 'mdi-pause-circle',
    completed: 'mdi-check-circle',
    failed: 'mdi-alert-circle'
  };
  return icons[status] || 'mdi-help-circle';
};

const getStatusText = (status) => {
  const texts = {
    created: 'Erstellt',
    queued: 'In Warteschlange',
    running: 'Läuft',
    paused: 'Pausiert',
    completed: 'Abgeschlossen',
    failed: 'Fehlgeschlagen'
  };
  return texts[status] || status;
};
</script>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}
</style>
