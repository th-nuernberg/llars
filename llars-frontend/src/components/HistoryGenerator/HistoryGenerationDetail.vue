<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6">
        <h2>E-Mail Verlauf</h2>
        <div class="email-thread-container">
          <div class="email-thread">
            <div
              v-for="message in messages"
              :key="message.message_id"
              class="email-message no-select"
              :class="getMessageClass(message.sender)"
            >
              <div class="message-header">
                <span class="message-sender">{{ message.sender }}</span>
                <span class="message-timestamp">{{ formatTimestamp(message.timestamp) }}</span>
              </div>
              <div class="message-body">
                <p>{{ message.content }}</p>
              </div>
            </div>
          </div>
          <div class="fade-overlay top"></div>
          <div class="fade-overlay bottom"></div>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const messages = ref([]);

onMounted(async () => {
  const threadId = route.params.id;
  const api_key = localStorage.getItem('api_key');

  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/generations/${threadId}`, {
      headers: {
        'Authorization': api_key,
      },
    });
    messages.value = response.data.messages;
  } catch (error) {
    console.error('Error fetching email thread details:', error);
  }
});

function formatTimestamp(timestamp) {
  const options = {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'};
  const date = new Date(timestamp);
  return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
}

function getMessageClass(sender) {
  return sender === 'user' ? 'same-sender' : 'different-sender';
}
</script>

<style scoped>
.email-thread-container {
  max-height: 500px;
  overflow-y: auto;
  min-height: 75vh;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: white;
}

.email-thread {
  max-height: 100%;
  overflow-y: auto;
}

.email-message {
  padding: 16px;
  margin-bottom: 10px;
  border-radius: 10px;
}

.same-sender {
  background-color: #f1efd5;
}

.different-sender {
  background-color: #b0ca97;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.message-sender {
  font-weight: bold;
  color: #2F4F4F;
}

.message-timestamp {
  color: #556B2F;
  font-size: 0.8rem;
}

.message-body p {
  margin: 0;
  color: #2F4F4F;
}

.fade-overlay {
  position: absolute;
  left: 0;
  right: 0;
  height: 5px;
  pointer-events: none;
}

.fade-overlay.top {
  top: 0;
  background: linear-gradient(to bottom, white, transparent);
}

.fade-overlay.bottom {
  bottom: 0;
  background: linear-gradient(to top, white, transparent);
}
</style>
