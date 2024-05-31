<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6">
        <h2>Feature Detail</h2>
        <v-card class="mb-4">
          <v-card-title>{{ feature.model_name }}</v-card-title>
          <v-card-subtitle>{{ translateFeatureType(feature.type) }}</v-card-subtitle>
          <v-card-text>{{ feature.value }}</v-card-text>
        </v-card>
        <h3>Bewerten Sie dieses Feature</h3>
        <div class="likert-scale">
          <v-btn
            v-for="rating in 5"
            :key="rating"
            @click="rateFeature(rating)"
            :class="{'selected-rating': rating === selectedRating}"
          >
            {{ rating }}
          </v-btn>
        </div>
      </v-col>
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
const feature = ref({});
const messages = ref([]);
const senderColors = ref({});
const selectedRating = ref(null);

onMounted(async () => {
  const featureDetail = await fetchFeatureDetail(route.params.id, route.params.feature);
  if (!featureDetail) return;

  feature.value = featureDetail.feature;
  messages.value = featureDetail.messages;

  let lastSender = '';
  let currentColor = 'same-sender';
  messages.value.forEach(message => {
    if (message.sender !== lastSender) {
      currentColor = currentColor === 'same-sender' ? 'different-sender' : 'same-sender';
      lastSender = message.sender;
    }
    senderColors.value[message.sender] = currentColor;
  });
});

async function fetchFeatureDetail(threadId, featureId) {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`http://localhost:8081/api/email_threads/ratings/${threadId}/${featureId}`, {
      headers: {
        'Authorization': api_key
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching feature detail:', error);
    return null;
  }
}

function getMessageClass(sender) {
  return senderColors.value[sender];
}

function translateFeatureType(type) {
  const translations = {
    abstract_summary: 'Abstrakte Fallzusammenfassung',
    generated_category: 'Generierte Kategorie',
    generated_subject: 'Generierter Betreff',
    order_clarification: 'Ordnungsklärung',
  };
  return translations[type] || type;
}

function formatTimestamp(timestamp) {
  const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
  const date = new Date(timestamp);
  return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
}

function rateFeature(rating) {
  selectedRating.value = rating;
  console.log(`Feature rated with: ${rating}`);
  // Hier können Sie den Code hinzufügen, um das Rating auf dem Server zu speichern
}
</script>

<style scoped>
.email-thread-container {
  max-height: 500px;
  overflow-y: auto;
  min-height: 80vh;
  display: flex;
  flex-direction: column;
  position: relative;
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
  background-color: #B2EBF2;
}

.different-sender {
  background-color: #C8E6C9;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.message-sender {
  font-weight: bold;
}

.message-timestamp {
  color: #666;
  font-size: 0.8rem;
}

.message-body p {
  margin: 0;
}

.no-select {
  user-select: none;
}

.likert-scale {
  display: flex;
  justify-content: space-around;
  margin-top: 10px;
}

.likert-scale v-btn {
  min-width: 40px;
}

.selected-rating {
  background-color: #1976d2 !important;
  color: white !important;
}
</style>
