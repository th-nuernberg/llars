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

    <!-- Benutzerfortschritt -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Benutzerfortschritt</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item v-for="user in userStats" :key="user.username">
                <v-list-item-content>
                  <v-list-item-title class="text-h6">{{ user.username }}</v-list-item-title>
                  <v-list-item-subtitle>
                    Bearbeitete Threads: {{ user.ranked_threads_count }} von {{ calculateTotalThreads(user) }}
                  </v-list-item-subtitle>
                  <v-progress-linear
                    :model-value="calculateProgress(user)"
                    height="25"
                    rounded
                    color=#b0ca97
                  >
                    <template v-slot:default="{ value }">
                      <strong>{{ Math.round(value) }}%</strong>
                    </template>
                  </v-progress-linear>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Detaillierte Benutzerstatistiken -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Detaillierte Benutzerstatistiken</v-card-title>
          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="userStats"
              item-key="username"
              class="elevation-1"
              :loading="loading"
            >
              <template v-slot:item.progress="{ item }">
                <v-progress-circular
                  :rotate="-90"
                  :size="50"
                  :width="7"
                  :model-value="calculateProgress(item)"
                  color=#b0ca97
                >
                  {{ item.ranked_threads_count }}
                </v-progress-circular>
              </template>
              <template v-slot:item.ranked_threads="{ item }">
                <v-btn
                  v-if="item.ranked_threads.length > 0"
                  small
                  color="primary"
                  @click="showThreadDetails(item)"
                >
                  Details anzeigen
                </v-btn>
                <span v-else>Keine Threads</span>
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
                <v-list-item-subtitle>
                  Gerankte Features: {{ thread.ranked_features_count }} / {{ thread.total_features_in_thread }}
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
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const headers = [
  { text: 'Benutzername', value: 'username' },
  { text: 'Fortschritt', value: 'progress', sortable: false },
  { text: 'Erledigte Rankings', value: 'ranked_threads_count' },
  { text: 'Gesamte zu rankende Features', value: 'total_rankable_features' },
  { text: 'Gerankte Threads', value: 'ranked_threads', sortable: false },
];

const userStats = ref([]);
const loading = ref(true);
const dialogVisible = ref(false);
const selectedUser = ref({});

const showThreadDetails = (user) => {
  selectedUser.value = user;
  dialogVisible.value = true;
};

const calculateTotalThreads = (user) => {
  return user.total_rankable_features > 0 ? Math.ceil(user.total_rankable_features / 10) : 0;
};

const calculateProgress = (user) => {
  const totalThreads = calculateTotalThreads(user);
  console.log('Total Threads:', totalThreads); // Debug: Gesamtanzahl der Threads
  console.log('Ranked Threads:', user.ranked_threads_count); // Debug: Anzahl der bewerteten Threads
  const progress = totalThreads > 0 ? (user.ranked_threads_count / totalThreads) * 100 : 0;
  console.log('Progress:', progress); // Debug: Berechneter Fortschritt
  return progress;
};



onMounted(async () => {
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
});

console.log('Admin Dashboard loaded');
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

.content-card {
  background-color: #f1efd5;
}

.secondary-text {
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

@media (max-width: 768px) {
  .title-card .v-card__title {
    font-size: 2rem;
  }
}
</style>
