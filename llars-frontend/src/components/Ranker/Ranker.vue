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
          <v-card-title>{{ emailThread.subject }}</v-card-title>
          <v-card-text>Chat ID: {{ emailThread.chat_id }}</v-card-text>
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
}

.case-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.category-chip {
  position: absolute;
  top: 4px;
  right: 4px;
  border-radius: 12px 5px 12px 5px;
}
</style>
