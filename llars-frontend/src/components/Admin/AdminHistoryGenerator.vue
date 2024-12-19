<template>
  <v-container class="email-progress-dashboard" fluid>
    <v-card class="mb-4 title-card">
      <v-card-title class="text-h5">Admin Dashboard</v-card-title>
      <v-card-subtitle>Übersicht der E-Mail-Bewertungen</v-card-subtitle>
    </v-card>

    <!-- Legende -->
    <v-card class="mb-2 legend-card">
      <v-card-text class="py-2">
        <v-row align="center" no-gutters class="legend-row">
          <v-col cols="2" sm="1" class="username-col">
            <strong>Benutzer</strong>
          </v-col>
          <v-col cols="3" sm="2" class="threads-col">
            <strong>Done</strong>
          </v-col>
          <v-col cols="3" sm="2" class="threads-col">
            <strong>In Progress</strong>
          </v-col>
          <v-col cols="3" sm="2" class="threads-col">
            <strong>Not Started</strong>
          </v-col>
          <v-col class="progress-col">
            <strong>Gesamtfortschritt</strong>
          </v-col>
          <v-col cols="auto" class="actions-col">
            <strong>Aktionen</strong>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card v-for="user in userStats" :key="user.username" class="mb-2 user-card">
  <v-card-text class="py-2">
    <v-row align="center" no-gutters class="user-row">
      <!-- Benutzername -->
      <v-col cols="2" sm="1" class="username-col">
        <span class="username">{{ user.username }}</span>
      </v-col>

      <!-- Bewertete Threads -->
      <v-col cols="3" sm="2" class="threads-col">
        <span class="thread-info">{{ user.done_threads }}</span>
      </v-col>

      <!-- Teilweise bewertete Threads -->
      <v-col cols="3" sm="2" class="threads-col">
        <span class="thread-info">{{ user.progressing_threads }}</span>
      </v-col>

      <!-- Nicht bewertete Threads -->
      <v-col cols="3" sm="2" class="threads-col">
        <span class="thread-info">{{ user.not_started_threads }}</span>
      </v-col>

      <!-- Fortschrittsbalken -->
      <v-col class="progress-col">
        <div class="progress-bar-wrapper">
          <!-- Bewertete Threads (grün) -->
          <div
            :style="{ width: `${user.donePercentage}%` }"
            class="progress-bar progress-bar-done"
          >
            <span
              v-if="user.donePercentage > 5"
              class="progress-label progress-label-done"
            >
              {{ Math.round(user.donePercentage) }}%
            </span>
          </div>

          <!-- Teilweise bewertete Threads (gelb) -->
          <div
            :style="{ width: `${user.progressingPercentage}%`, left: `${user.donePercentage}%` }"
            class="progress-bar progress-bar-progressing"
          >
            <span
              v-if="user.progressingPercentage > 5"
              class="progress-label progress-label-progressing"
            >
              {{ Math.round(user.progressingPercentage) }}%
            </span>
          </div>

          <!-- Nicht bewertete Threads (rot) -->
          <div
            :style="{ width: `${user.notStartedPercentage}%`, left: `${user.donePercentage + user.progressingPercentage}%` }"
            class="progress-bar progress-bar-not-started"
          >
            <span
              v-if="user.notStartedPercentage > 5"
              class="progress-label progress-label-not-started"
            >
              {{ Math.round(user.notStartedPercentage) }}%
            </span>
          </div>
        </div>
      </v-col>

      <!-- Details Button -->
      <v-col cols="auto" class="actions-col" style="padding-left: 16px;">
        <v-btn x-small color="primary" @click="showThreadDetails(user)">
          Details
        </v-btn>
      </v-col>
    </v-row>
  </v-card-text>
</v-card>

    <!-- Thread Details Dialog -->
    <v-dialog v-model="dialogVisible" max-width="700px">
      <v-card>
        <v-card-title>Thread Details für {{ selectedUser.username }}</v-card-title>
        <v-card-text>
          <!-- Anzeige der bewerteten Threads -->
          <v-subheader>Bewertete Threads</v-subheader>
          <v-list dense>
            <v-list-item v-for="thread in selectedUser.done_threads_list" :key="thread.thread_id">
              <v-list-item-content>
                <v-list-item-title class="text-subtitle-1">{{ thread.subject }}</v-list-item-title>
                <v-list-item-subtitle>Thread ID: {{ thread.thread_id }}</v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>

          <!-- Anzeige der teils bewerteten Threads -->
          <v-subheader>Teilweise bewertete Threads</v-subheader>
          <v-list dense>
            <v-list-item v-for="thread in selectedUser.progressing_threads_list" :key="thread.thread_id">
              <v-list-item-content>
                <v-list-item-title class="text-subtitle-1">{{ thread.subject }}</v-list-item-title>
                <v-list-item-subtitle>Thread ID: {{ thread.thread_id }}</v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>

          <!-- Anzeige der nicht bewerteten Threads -->
          <v-subheader>Nicht bewertete Threads</v-subheader>
          <v-list dense>
            <v-list-item v-for="thread in selectedUser.not_started_threads_list" :key="thread.thread_id">
              <v-list-item-content>
                <v-list-item-title class="text-subtitle-1">{{ thread.subject }}</v-list-item-title>
                <v-list-item-subtitle>Thread ID: {{ thread.thread_id }}</v-list-item-subtitle>
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
import { ref, computed, watch, onMounted } from 'vue';
import axios from 'axios';

const userStats = ref([]);
const dialogVisible = ref(false);
const selectedUser = ref({});

// Öffnet den Dialog und zeigt die Details des ausgewählten Benutzers an
const showThreadDetails = (user) => {
  selectedUser.value = user;
  dialogVisible.value = true;
};

// Berechnung des Fortschritts für jeden Benutzer
const calculateProgressSections = (total_threads, done_threads, progressing_threads) => {
  const donePercentage = (done_threads / total_threads) * 100 || 0;
  const inProgresPercentage = (progressing_threads / total_threads) * 100 || 0;
  const notStartedPercentage = 100 - donePercentage - inProgresPercentage;

  return {
    donePercentage: donePercentage,
    progressingPercentage: inProgresPercentage,
    notStartedPercentage,
  };
};

// Abrufen der Benutzerstatistiken von der API
const fetchUserStats = async () => {
  const apiKey = localStorage.getItem('api_key');

  if (!apiKey) {
    console.error('Kein API-Key im localStorage gefunden');
    return;
  }

  try {
    const response = await axios.get('/api/admin/user_HistoryGeneration_stats', {
      headers: {
        Authorization: apiKey,
      },
    });

    if (Array.isArray(response.data)) {
      userStats.value = response.data.map(user => {
        // Berechnung der Prozentwerte für den Fortschritt
        const progressSections = calculateProgressSections(
          user.total_threads,
          user.done_threads,
          user.progressing_threads
        );

        // Rückgabe des erweiterten Objekts
        return {
          ...user,
          ...progressSections,
        };
      });
    } else {
      console.error('Unerwartetes Format der API-Antwort:', response.data);
    }
  } catch (error) {
    console.error('Fehler beim Laden der Benutzerstatistiken:', error);
  }
};

// Beim Laden der Komponente die Statistiken abrufen
onMounted(() => {
  fetchUserStats();
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

/* Fortschrittsbalken Wrapper */
.progress-bar-wrapper {
  position: relative;
  height: 20px;
  background-color: #f1efd5; /* Hintergrundfarbe der Progressbar */
  border-radius: 10px;
  overflow: hidden;
}

/* Allgemeine Balken */
.progress-bar {
  height: 100%;
  position: absolute;
}

/* Farben der Balken */
.progress-bar-done {
  background-color: #e9f5ea; /* Grün für bewertete Threads */
}

.progress-bar-progressing {
  background-color: #f7ebd9; /* Gelb für teilweise bewertete Threads */
}

.progress-bar-not-started {
  background-color: #f3f3f3; /* Rot für nicht bewertete Threads */
}

/* Prozentzahlen (Labels) */
.progress-label {
  font-size: 12px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  white-space: nowrap;
}

/* Farben der Prozentzahlen */
.progress-label-done{
  color: #4aae4d;
}

.progress-label-progressing {
  color: #ff9c12;
}

.progress-label-not-started {
  color: #a1a1a1;
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
