<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h5 font-weight-bold mb-2">
          <v-icon start>mdi-compare-horizontal</v-icon>
          Gegenüberstellung Dashboard
        </h1>
        <p>Wählen Sie eine Persona, um den Chat mit dieser zu betreten.</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col
        v-for="session in sessions"
        :key="session.id"
        cols="12"
        sm="4"
      >
        <v-card
          class="case-card"
          :class="getCardClass(session.color)"
          @click="goToDetail(session.id)"
          elevation="2"
        >
          <v-card-item class="text-truncate">
            <div class="text-subtitle-1">{{ session.persona_name }} (Szenario {{ session.scenario_id }})</div>
            <div class="text-caption grey--text">
              Status: {{ getStatusText(session.status) }} ({{ session.rated_messages }} bewertete Nachrichten)
            </div>
          </v-card-item>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue';
import {useRouter} from 'vue-router';
import {listSessionsForUser} from '@/services/comparisonApi';

const router = useRouter();
const sessions = ref<Array<any>>([]);

onMounted(async () => {
  await fetchSessions();
});

async function fetchSessions() {
  try {
    sessions.value = await listSessionsForUser();
  } catch (e) {
    console.error('Error fetching sessions', e);
  }
}

function goToDetail(id: string | number) {
  router.push({name: 'ComparisonDetail', params: {session_id: id}});
}

function getCardClass(color: string) {
  return {
    'card-grey': color === 'grey',
    'card-yellow': color === 'yellow',
    'card-green': color === 'green'
  };
}

function getStatusText(status: string) {
  switch(status) {
    case 'not_started': return 'Nicht begonnen';
    case 'progressing': return 'In Bearbeitung';
    case 'completed': return 'Abgeschlossen';
    default: return status;
  }
}
</script>

<style scoped>
.case-card {
  transition: box-shadow 0.3s, transform 0.1s;
  cursor: pointer;
}

.case-card:hover {
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.card-grey {
  border-left: 4px solid #9e9e9e;
}

.card-yellow {
  border-left: 4px solid #ffc107;
  background-color: #fffde7;
}

.card-green {
  border-left: 4px solid #4caf50;
  background-color: #e8f5e8;
}

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
