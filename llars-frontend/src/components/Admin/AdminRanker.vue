<template>
  <v-container class="admin-dashboard">
    <v-card class="mb-6 title-card">
      <v-card-title class="headline">Admin Dashboard</v-card-title>
      <v-card-subtitle>Übersicht der Benutzeraktivitäten</v-card-subtitle>
    </v-card>

    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card v-for="user in userStats" :key="user.username" class="mb-4 user-card">
          <v-card-text>
            <div class="user-info d-flex flex-wrap justify-space-between align-center mb-2">
              <span class="username"><strong>{{ user.username }}</strong></span>
              <span class="thread-info">
                Bearbeitete Threads: {{ user.ranked_threads_count }} / {{ calculateTotalThreads(user) }}
                ({{ calculateUnrankedThreads(user) }} unbearbeitet)
              </span>
              <v-btn
                v-if="user.ranked_threads_count > 0"
                small
                color="primary"
                @click="showThreadDetails(user)"
              >
                Details anzeigen
              </v-btn>
              <span v-else class="no-threads">Keine bearbeiteten Threads</span>
            </div>
            <v-progress-linear
              :model-value="calculateProgress(user)"
              height="25"
              rounded
              color="#b0ca97"
              background-color="#f1efd5"
              class="progress-bar"
            >
              <template v-slot:default="{ value }">
                <strong>{{ Math.round(value) }}%</strong>
              </template>
            </v-progress-linear>
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

const userStats = ref([]);
const dialogVisible = ref(false);
const selectedUser = ref({});
let pollingInterval = null;

const showThreadDetails = (user) => {
  selectedUser.value = user;
  dialogVisible.value = true;
};

const calculateTotalThreads = (user) => {
  return user.total_rankable_features > 0 ? Math.ceil(user.total_rankable_features / 10) : 0;
};

const calculateUnrankedThreads = (user) => {
  return calculateTotalThreads(user) - user.ranked_threads_count;
};

const calculateProgress = (user) => {
  const totalThreads = calculateTotalThreads(user);
  const progress = totalThreads > 0 ? (user.ranked_threads_count / totalThreads) * 100 : 0;
  return progress;
};

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
  }
};

onMounted(() => {
  fetchUserStats();
  pollingInterval = setInterval(fetchUserStats, 10000);
});

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

.user-card {
  border: 1px solid #b0ca97;
  border-radius: 8px;
  transition: box-shadow 0.3s ease-in-out;
}

.user-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.user-info {
  font-size: 0.9rem;
}

.username {
  font-size: 1.1rem;
  margin-right: 1rem;
}

.thread-info {
  color: #556B2F;
  margin-right: 1rem;
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
  border-radius: 4px;
}

.v-progress-linear >>> .v-progress-linear__content {
  color: #2F4F4F;
  font-weight: bold;
}

.no-threads {
  color: #999;
  font-style: italic;
}

@media (max-width: 600px) {
  .user-info {
    flex-direction: column;
    align-items: flex-start;
  }

  .username, .thread-info, .v-btn {
    margin-bottom: 0.5rem;
  }
}
</style>
