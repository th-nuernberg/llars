<!-- Ranker/Ranker.vue -->
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
            :color="emailThread.ranked ? 'green lighten-2' : 'grey lighten-2'"
            small
          >
            {{ emailThread.ranked ? 'Ranked' : 'Not Ranked' }}
          </v-chip>
          <div class="card-content">
            <v-card-title>{{ emailThread.subject }}</v-card-title>
            <v-card-text>{{emailThread.sender }}</v-card-text> <!-- Sender anzeigen -->
            <v-card-text class="chat-id">{{ 'Chat ID: ' + emailThread.chat_id }}</v-card-text>
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
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/rankings`, {
      headers: {
        'Authorization': api_key,
      },
    });
    console.log('Email threads:', response.data);
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
  height: 200px;
  display: flex;
  flex-direction: column;
}

.case-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.category-chip {
  position: absolute;
  top: 8px;
  right: 8px;
  border-radius: 12px 5px 12px 5px;
  z-index: 1;
}

.card-content {
  padding-top: 36px;
  padding-right: 36px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.v-card-title {
  font-size: 1rem;
  white-space: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.v-card-text {
  margin-top: auto;
}

.chat-id {
  align-self: auto;
}
</style>
