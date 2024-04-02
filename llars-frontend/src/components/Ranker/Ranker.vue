<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1>Ranker Dashboard</h1>
        <p>Klicken Sie auf einen Fall, um ein Ranking durchzuführen.</p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="4" v-for="emailThread in emailThreads" :key="emailThread.thread_id">
        <v-card class="mb-4 case-card" @click="navigateToCase(emailThread.thread_id)">
          <v-chip
            class="category-chip"
            color="grey lighten-2"
            small
          >
            Default Kategorie
          </v-chip>
          <div class="card-content">
            <v-card-title>{{ emailThread.subject }}</v-card-title>
            <v-card-text class="chat-id">{{ 'Chat ID: ' + emailThread.chat_id }}</v-card-text>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>


<script setup>
import {ref, onMounted} from 'vue';
import {useRouter} from 'vue-router';
import axios from 'axios';

const router = useRouter();
const emailThreads = ref([]);

onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:8081/api/email_threads');
    emailThreads.value = response.data;
  } catch (error) {
    console.error('Error fetching email threads:', error);
  }
});

function navigateToCase(threadId) {
  router.push({ name: 'RankerDetail', params: { id: threadId } });
}
</script>

<style scoped>
.case-card {
  position: relative;
  transition: box-shadow 0.3s ease-in-out, transform 0.1s ease-in-out;
  cursor: pointer;
  height: 200px; /* Setzen Sie eine feste Höhe oder min-height für eine Mindesthöhe */
  display: flex;
  flex-direction: column; /* Organisieren Sie den Inhalt der Karte in einer Spalte */
}

.case-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.category-chip {
  position: absolute;
  top: 8px; /* Vergrößern Sie den oberen Abstand, um Überlappungen zu vermeiden */
  right: 8px; /* Fügen Sie etwas horizontalen Abstand hinzu */
  border-radius: 12px 5px 12px 5px;
  z-index: 1; /* Stellen Sie sicher, dass der Chip über dem Titel liegt */
}

.card-content {
  padding-top: 36px; /* Fügen Sie zusätzlichen Platz oben hinzu, damit der Titel nicht überdeckt wird */
  padding-right: 36px; /* Fügen Sie auch rechts Platz hinzu, um Überlappungen mit dem Chip zu vermeiden */

  flex-grow: 1; /* Lassen Sie den Inhalt den verfügbaren Platz ausfüllen */
  display: flex;
  flex-direction: column;
  justify-content: space-between; /* Verteilen Sie den Inhalt gleichmäßig in der Karte */
}

.v-card-title {
  font-size: 1rem; /* Passen Sie die Schriftgröße nach Bedarf an */
  white-space: normal; /* Erlauben Sie den Umbruch */
  overflow: hidden; /* Verstecken Sie überlaufenden Text */
  text-overflow: ellipsis; /* Zeigen Sie "..." am Ende des überlaufenden Textes an */
  display: -webkit-box;
  -webkit-line-clamp: 2; /* Begrenzen Sie auf 2 Zeilen */
  -webkit-box-orient: vertical;
}
.v-card-text {
  margin-top: auto; /* Schiebt den Text nach unten, weg vom Titel */
}
.chat-id {
  align-self: auto; /* Positioniert die Chat-ID am Ende der Karte */
}
</style>
