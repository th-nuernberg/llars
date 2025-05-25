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
        :key="session.session_id"
        cols="12"
        sm="4"
      >
        <v-card
          class="case-card"
          @click="goToDetail(session.id)"
          elevation="2"
        >
          <v-card-item class="text-truncate">
            <div class="text-subtitle-1">{{ 'Session #' + session.id }}</div>
            <div class="text-caption grey--text">
              Mit einem Klick auf diese Session wird eine zufällige Persona ausgewählt mit der ein
              Chat geführt wird. Bitte bewerten Sie hier die Antworten der Persona.
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
  router.push({name: 'ComparisonDetail', params: {id}});
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

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
