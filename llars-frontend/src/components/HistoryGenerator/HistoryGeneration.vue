<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1>Verlauf Generator Dashboard</h1>
        <p>Wählen Sie einen Verlauf, um ihn zu generieren und anzuzeigen.</p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="4" v-for="emailThread in emailThreads" :key="emailThread.thread_id">
        <v-card class="mb-4 case-card" @click="navigateToCase(emailThread.thread_id)">
          <!-- Rating Status Chip (oben rechts) -->
          <v-chip
            class="category-chip right-aligned-chip rating-status-chip"
            :color="emailThread.rating_status === 'Rated' ? 'green lighten-2' : emailThread.rating_status === 'Partly Rated' ? 'orange lighten-2' : 'grey lighten-2'"
            small
          >
            {{ emailThread.rating_status }}
          </v-chip>

          <div class="card-content">
            <v-card-title>{{ emailThread.subject }}</v-card-title>
            <v-card-text>{{ emailThread.sender }}</v-card-text>

            <!-- Footer-Bereich für Chat ID und Unsaved Changes Chip -->
            <div class="card-footer">
              <v-card-text class="chat-id">{{ 'Chat ID: ' + emailThread.chat_id }}</v-card-text>
              <v-chip
                v-if="checkUnsavedChanges(emailThread.thread_id)"
                color="red lighten-2"
                class="category-chip right-aligned-chip"
                small
              >
                !
              </v-chip>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const emailThreads = ref([]);

onMounted(async () => {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/mailhistory_ratings`, {
      headers: {
        'Authorization': api_key,
      },
    });
    emailThreads.value = response.data;
  } catch (error) {
    console.error('Error fetching email threads:', error);
  }
});

function navigateToCase(threadId) {
  router.push({ name: 'HistoryGenerationDetail', params: { id: threadId } });
}

function checkUnsavedChanges(thread_id) {
  const hasUnsavedChanges = localStorage.getItem(`unsaved_changes_${thread_id}`);
  return !!hasUnsavedChanges;
}
</script>

<style scoped>
.case-card {
  position: relative;
  transition: box-shadow 0.3s ease-in-out, transform 0.1s ease-in-out;
  cursor: pointer;
  height: 200px;
  display: flex;
  flex-direction: column;
}

.case-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.category-chip{
  border-radius: 12px 5px 12px 5px;
  z-index: 1;
}

/* Gleiche rechte Ausrichtung für beide Chips */
.right-aligned-chip {
  position: absolute;
  right: 8px;
}

.rating-status-chip{
  top: 8px;
}


/* Position für Unsaved Changes Chip unten rechts */
.unsaved-changes-chip {
  bottom: 20px;
}

.card-content {
  padding-top: 36px;
  padding-right: 36px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center; /* Vertikale Zentrierung */
  padding-top: 8px;
}

.chat-id {
  /* optional: Styling für die Chat ID */
}
</style>
