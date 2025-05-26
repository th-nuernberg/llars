<template>
  <div class="comparison-footer-wrapper">
    <v-card color="secondary" class="comparison-footer" elevation="8">
      <v-container fluid>
        <v-row align="center" justify="space-between" no-gutters>
          <v-col cols="auto" class="d-flex align-center">
            <v-btn
              variant="text"
              color="white"
              @click="navigateToPreviousSession"
              :disabled="isFirstSession"
              class="mr-2"
            >
              <v-icon start>mdi-chevron-left</v-icon>
              Vorheriger Chat
            </v-btn>

            <v-btn
              variant="text"
              color="white"
              @click="navigateToOverview"
              class="mr-2"
            >
              <v-icon start>mdi-view-dashboard</v-icon>
              Übersicht
            </v-btn>

            <v-btn
              variant="text"
              color="white"
              @click="navigateToNextSession"
              :disabled="isLastSession"
            >
              Nächster Chat
              <v-icon end>mdi-chevron-right</v-icon>
            </v-btn>
          </v-col>

          <v-col cols="auto" class="d-flex align-center">
            <v-chip
              :color="getStatusColor()"
              :prepend-icon="getStatusIcon()"
              variant="elevated"
              class="mr-2"
            >
              {{ getStatusText() }}
            </v-chip>

            <span class="text-white text-caption">
              {{ ratedMessages }} / {{ totalMessages }} Nachrichten bewertet
              <span v-if="ratedMessages >= 5" class="ml-2 text-grey-darken-3">
                (Chat kann weiter fortgesetzt werden)
              </span>
            </span>
          </v-col>
        </v-row>
      </v-container>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';

interface Props {
  currentSessionId: number;
  allSessions: Array<any>;
  ratedMessages: number;
  totalMessages: number;
}

const props = defineProps<Props>();
const router = useRouter();

const currentSessionIndex = computed(() => {
  return props.allSessions.findIndex(session => session.id === props.currentSessionId);
});

const isFirstSession = computed(() => {
  return currentSessionIndex.value <= 0;
});

const isLastSession = computed(() => {
  return currentSessionIndex.value >= props.allSessions.length - 1;
});

const getStatusColor = () => {
  if (props.ratedMessages === 0) return 'grey';
  if (props.ratedMessages >= 5) return 'green';
  return 'orange';
};

const getStatusIcon = () => {
  if (props.ratedMessages === 0) return 'mdi-play-circle-outline';
  if (props.ratedMessages >= 5) return 'mdi-check-circle';
  return 'mdi-progress-clock';
};

const getStatusText = () => {
  if (props.ratedMessages === 0) return 'Nicht begonnen';
  if (props.ratedMessages >= 5) return 'Abgeschlossen';
  return 'In Bearbeitung';
};

const navigateToPreviousSession = () => {
  if (!isFirstSession.value) {
    const previousSession = props.allSessions[currentSessionIndex.value - 1];
    router.push({ name: 'ComparisonDetail', params: { session_id: previousSession.id } });
  }
};

const navigateToNextSession = () => {
  if (!isLastSession.value) {
    const nextSession = props.allSessions[currentSessionIndex.value + 1];
    router.push({ name: 'ComparisonDetail', params: { session_id: nextSession.id } });
  }
};

const navigateToOverview = () => {
  router.push({ name: 'Comparison' });
};
</script>

<style scoped>
.comparison-footer-wrapper {
  position: fixed;
  bottom: 30px;
  left: 0;
  right: 0;
  z-index: 1000;
}
</style>
