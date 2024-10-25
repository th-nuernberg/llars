<template>
  <v-container class="admin-dashboard" fluid>
    <v-card class="mb-4 title-card">
      <v-card-title class="text-h5">Admin Dashboard</v-card-title>
      <v-card-subtitle>Übersicht der Benutzeraktivitäten</v-card-subtitle>
    </v-card>

    <!-- Legende und globale Auswahl -->
    <v-card class="mb-2 legend-card">
      <v-card-text class="py-2">
        <v-row align="center" no-gutters class="legend-row">
          <v-col cols="auto" class="mr-3 checkbox-col">
            <v-checkbox
              v-model="selectAll"
              @change="toggleAllUsers"
              hide-details
              dense
              class="mt-0 pt-0"
            />
          </v-col>
          <v-col cols="2" sm="1" class="username-col">
            <strong>Benutzer</strong>
          </v-col>
          <v-col cols="3" sm="2" class="threads-col">
            <strong>Threads</strong>
          </v-col>
          <v-col class="progress-col">
            <strong>Fortschritt</strong>
          </v-col>
          <v-col cols="auto" class="actions-col">
            <strong>Aktionen</strong>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Benutzerkarten -->
    <v-card v-for="user in userStats" :key="user.username" class="mb-2 user-card">
      <v-card-text class="py-2">
        <v-row align="center" no-gutters class="user-row">
          <v-col cols="auto" class="mr-3 checkbox-col">
            <v-checkbox
              v-model="selectedUsers"
              :value="user.username"
              hide-details
              dense
              class="mt-0 pt-0"
            />
          </v-col>
          <v-col cols="2" sm="1" class="username-col">
            <span class="username">{{ user.username }}</span>
          </v-col>
          <v-col cols="3" sm="2" class="threads-col">
            <span class="thread-info">
              {{ user.ranked_threads_count }} / {{ user.total_threads }}
              ({{ calculateUnrankedThreads(user) }})
            </span>
          </v-col>
          <v-col class="progress-col">
            <v-progress-linear
              :model-value="calculateProgress(user)"
              height="20"
              rounded
              color="#b0ca97"
              background-color="#f1efd5"
              class="progress-bar"
            >
              <template v-slot:default="{ value }">
                <strong>{{ Math.round(value) }}%</strong>
              </template>
            </v-progress-linear>
          </v-col>
          <v-col cols="auto" class="actions-col" style="padding-left: 16px;">
            <v-btn
              v-if="user.ranked_threads_count > 0 || user.unranked_threads.length > 0"
              x-small
              color="primary"
              @click="showThreadDetails(user)"
            >
              Details
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Globale Fortschrittsanzeige -->
    <v-card v-if="selectedUsers.length > 0" class="mt-4 global-progress-card">
      <v-card-text class="py-2">
        <v-row no-gutters align="center">
          <v-col cols="auto" class="mr-3">
            <span class="text-subtitle-2">Gesamtfortschritt:</span>
          </v-col>
          <v-col>
            <v-progress-linear
              :model-value="calculateGlobalProgress()"
              height="24"
              rounded
              color="#b0ca97"
              background-color="#f1efd5"
            >
              <template v-slot:default="{ value }">
                <strong>{{ Math.round(value) }}%</strong>
              </template>
            </v-progress-linear>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Thread Details Dialog -->
    <v-dialog v-model="dialogVisible" max-width="700px">
      <v-card>
        <v-card-title>Thread Details für {{ selectedUser.username }}</v-card-title>
        <v-card-text>
          <!-- Anzeige der bearbeiteten Threads -->
          <v-subheader>Bearbeitete Threads</v-subheader>
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

          <!-- Anzeige der nicht bearbeiteten Threads -->
          <v-subheader>Nicht bearbeitete Threads</v-subheader>
          <v-list dense>
            <v-list-item v-for="thread in selectedUser.unranked_threads" :key="thread.thread_id">
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import axios from 'axios';

const userStats = ref([]);
const dialogVisible = ref(false);
const selectedUser = ref({});
const selectedUsers = ref([]);
const selectAll = ref(false);
let pollingInterval = null;

// Öffnet den Dialog und zeigt die Details des ausgewählten Benutzers an
const showThreadDetails = (user) => {
  selectedUser.value = user;
  dialogVisible.value = true;
};

// Berechnung der unbearbeiteten Threads
const calculateUnrankedThreads = (user) => {
  return user.total_threads - user.ranked_threads_count;
};

// Berechnung des Fortschritts für jeden Benutzer
const calculateProgress = (user) => {
  const totalThreads = user.total_threads;
  const progress = totalThreads > 0 ? (user.ranked_threads_count / totalThreads) * 100 : 0;
  return progress;
};

// Berechnung des globalen Fortschritts für ausgewählte Benutzer
const calculateGlobalProgress = () => {
  if (selectedUsers.value.length === 0) return 0;

  let totalProgress = 0;
  let count = 0;

  selectedUsers.value.forEach((username) => {
    const user = userStats.value.find((u) => u.username === username);
    if (user) {
      totalProgress += calculateProgress(user);
      count++;
    }
  });

  return count > 0 ? totalProgress / count : 0;
};

// Abrufen der Benutzerstatistiken von der API
const fetchUserStats = async () => {
  const apiKey = localStorage.getItem('api_key');

  if (!apiKey) {
    console.error('Kein API-Key im localStorage gefunden');
    return;
  }

  try {
    const response = await axios.get('/api/admin/user_ranking_stats', {
      headers: {
        Authorization: apiKey,
      },
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

// Umschalten der Auswahl aller Benutzer
const toggleAllUsers = () => {
  if (selectAll.value) {
    selectedUsers.value = userStats.value.map((user) => user.username);
  } else {
    selectedUsers.value = [];
  }
};

// Beobachten von Änderungen an der Auswahl und Aktualisieren der Checkbox "Alle auswählen"
watch(selectedUsers, (newValue) => {
  selectAll.value = newValue.length === userStats.value.length;
});

// Beim Laden der Komponente die Statistiken abrufen und Polling starten
onMounted(() => {
  fetchUserStats();
  pollingInterval = setInterval(fetchUserStats, 10000);
});

// Beim Verlassen der Komponente das Polling stoppen
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

.title-card, .legend-card {
  background-color: #b0ca97;
}

.title-card .v-card__title {
  color: #ffffff;
  padding: 12px 16px 4px;
}

.title-card .v-card__subtitle,
.legend-card .v-card__text {
  color: #556B2F;
  padding: 0 16px 12px;
}

.user-card {
  border: 1px solid #b0ca97;
  border-radius: 4px;
  transition: box-shadow 0.3s ease-in-out;
}

.user-card:hover {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.legend-row,
.user-row {
  display: flex;
  align-items: center;
}

.checkbox-col {
  flex: 0 0 40px;
}

.username-col {
  flex: 0 0 100px;
}

.threads-col {
  flex: 0 0 150px;
}

.progress-col {
  flex: 1;
  padding-right: 16px;
}

.actions-col {
  flex: 0 0 80px;
  text-align: right;
  padding-left: 16px;
}

.username, .thread-info {
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.thread-info {
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
  border-radius: 4px;
}

.v-progress-linear >>> .v-progress-linear__content {
  color: #2F4F4F;
  font-weight: bold;
}

.global-progress-card {
  background-color: #f1efd5;
}

@media (max-width: 600px) {
  .user-row {
    flex-wrap: wrap;
  }

  .username-col,
  .threads-col,
  .progress-col,
  .actions-col {
    padding-top: 4px;
    padding-bottom: 4px;
  }

  .progress-col {
    flex-basis: 100%;
    padding-right: 0;
  }

  .actions-col {
    flex-basis: 100%;
    text-align: left;
    margin-top: 8px;
  }
}
</style>
