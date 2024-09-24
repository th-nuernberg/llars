<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="headline">Admin Dashboard</v-card-title>
          <v-card-subtitle>Übersicht der Benutzeraktivitäten</v-card-subtitle>
        </v-card>
      </v-col>
    </v-row>

    <!-- Benutzerfortschritt und Tabelle -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Benutzerfortschritt und E-Mail-Thread-Statistiken</v-card-title>
          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="userStats"
              item-key="username"
              class="elevation-1"
              :loading="loading"
            >
              <!-- Fortschrittsanzeige über die gesamte Breite -->
              <template v-slot:item.progress="{ item }">
                <div class="progress-row">
                  <strong>{{ Math.round(calculateProgress(item)) }}%</strong>
                  <v-progress-linear
                    :model-value="calculateProgress(item)"
                    height="25"
                    rounded
                    color="#b0ca97"
                    class="progress-bar"
                  />
                </div>
              </template>

              <!-- Bearbeitete und Unbearbeitete Threads -->
              <template v-slot:item.ranked_threads="{ item }">
                {{ item.ranked_threads_count }} / {{ calculateTotalThreads(item) }} ({{ calculateUnrankedThreads(item) }} unbearbeitet)
              </template>

              <!-- Details anzeigen Button -->
              <template v-slot:item.details="{ item }">
                <v-btn
                  v-if="item.ranked_threads_count > 0"
                  small
                  color="primary"
                  @click="showThreadDetails(item)"
                >
                  Details anzeigen
                </v-btn>
                <span v-else>Keine bearbeiteten Threads</span>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Thread Details Dialog -->
    <v-dialog v-model="dialogVisible" max-width="700px">
      <v-card>
        <v-card-title>Thread Details für {{ selectedUser.username }}</v-card-title>
        <v-card-text>
          <v-list dense>
            <v-list-item v-for="thread in selectedUser.ranked_threads" :key="thread.thread_id">
              <v-list-item-content>
                <v-list-item-title class="text-subtitle-1">{{ thread.subject }}</v-list-item-title>
                <v-list-item-subtitle>
                  Thread ID: {{ thread.thread_id }} | Chat ID: {{ thread.chat_id }} | Institut ID: {{ thread.institut_id }}
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="dialogVisible = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';

// Tabellenspalten-Konfiguration
const headers = [
  { text: 'Benutzername', value: 'username' },
  { text: 'Fortschritt', value: 'progress', sortable: false },
  { text: 'Bearbeitete Threads / Gesamt', value: 'ranked_threads', sortable: false },
  { text: 'Details', value: 'details', sortable: false },
];

const userStats = ref([]);
const loading = ref(true);
const dialogVisible = ref(false);
const selectedUser = ref({});
let pollingInterval = null;

// Zeige die Details der bearbeiteten Threads an
const showThreadDetails = (user) => {
  selectedUser.value = user;
  dialogVisible.value = true;
};

// Berechne die gesamte Anzahl der zu bearbeitenden Threads
const calculateTotalThreads = (user) => {
  return user.total_rankable_features > 0 ? Math.ceil(user.total_rankable_features / 10) : 0;
};

// Berechne die Anzahl der unbearbeiteten Threads
const calculateUnrankedThreads = (user) => {
  return calculateTotalThreads(user) - user.ranked_threads_count;
};

// Berechne den Fortschritt basierend auf der Anzahl der bearbeiteten Threads
const calculateProgress = (user) => {
  const totalThreads = calculateTotalThreads(user);
  const progress = totalThreads > 0 ? (user.ranked_threads_count / totalThreads) * 100 : 0;
  return progress;
};

// Hole Benutzerstatistiken von der API
const fetchUserStats = async () => {
  const apiKey = localStorage.getItem('api_key');

  if (!apiKey) {
    console.error('Kein API-Key im localStorage gefunden');
    return;
  }

  try {
    const response = await axios.get('/api/api/admin/user_ranking_stats', {
      headers: {
        'Authorization': apiKey
      }
    });

    if (Array.isArray(response.data)) {
      userStats.value = response.data;
    } else {
      console.error('Unerwartetes Format der API-Antwort:', response.data);
    }
  } catch (error) {
    console.error('Fehler beim Laden der Benutzerstatistiken:', error);
  } finally {
    loading.value = false;
  }
};

// Starte das Polling
onMounted(() => {
  fetchUserStats();

  // Polling alle 10 Sekunden
  pollingInterval = setInterval(() => {
    fetchUserStats();
  }, 10000); // 10 Sekunden Intervall
});

// Stoppe das Polling bei der Zerstörung der Komponente
onUnmounted(() => {
  clearInterval(pollingInterval);
});
</script>

<style scoped>
.admin-dashboard {
  background-color: #ffffff;
  color: #2F4F4F;
  font-family: Arial, sans-serif;
}

.title-card {
  background-color: #b0ca97;
}

.title-card .v-card__title {
  color: #ffffff;
  font-size: 2.5rem;
}

.title-card .v-card__subtitle {
  color: #556B2F;
}

.v-btn {
  background-color: #b0ca97 !important;
  color: #2F4F4F !important;
}

.v-btn:hover {
  background-color: #556B2F !important;
  color: #ffffff !important;
}

.v-progress-linear {
  background-color: #f1efd5 !important;
  width: 100%; /* Volle Breite */
}

.v-progress-linear__determinate {
  background-color: #b0ca97 !important;
}

.v-data-table {
  background-color: #ffffff;
}

.v-data-table th {
  background-color: #b0ca97 !important;
  color: #2F4F4F !important;
}

.progress-row {
  display: flex;
  flex-direction: column;
  width: 100%; /* Volle Breite */
}
</style>
