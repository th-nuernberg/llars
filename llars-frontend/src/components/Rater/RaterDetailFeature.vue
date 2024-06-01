<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6">
        <h2>Feature Detail</h2>
        <v-card class="mb-4">
          <v-card-title>{{ feature.model_name }}</v-card-title>
          <v-card-subtitle>{{ translateFeatureType(feature.type) }}</v-card-subtitle>
          <v-card-text>{{ feature.content }}</v-card-text>
        </v-card>
        <h3>Bewerten Sie dieses Feature</h3>
        <div class="likert-scale-container">
          <span class="likert-label-text">Gut</span>
          <div class="likert-scale">
            <div
              v-for="rating in 5"
              :key="rating"
              @click="rateFeature(rating)"
              :class="['likert-option', {
                'selected-rating': rating === selectedRating,
                'size-1': rating === 1 || rating === 5,
                'size-2': rating === 2 || rating === 4,
                'size-3': rating === 3,
                'green-tone': rating === 1 || rating === 2,
                'purple-tone': rating === 4 || rating === 5,
                'gray-tone': rating === 3
              }]"
            >
              <span class="likert-circle">
                <template v-if="rating === selectedRating">
                  <v-icon class="white-icon">mdi-check</v-icon>
                </template>
              </span>
            </div>
          </div>
          <span class="likert-label-text">Schlecht</span>
        </div>
        <div class="expandable-padding"></div>
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>
              Feature bearbeiten
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-form>
                <v-text-field
                  label="Model Name"
                  v-model="editableFeature.model_name"
                ></v-text-field>
                <v-textarea
                  label="Feature Content"
                  v-model="editableFeature.content"
                ></v-textarea>
                <v-btn @click="saveFeaturesServerSide">Speichern</v-btn>
              </v-form>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
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
import { ref, onMounted, watch } from 'vue';
import { useRoute, onBeforeRouteUpdate } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const feature = ref({});
const editableFeature = ref({});
const messages = ref([]);
const senderColors = ref({});
const selectedRating = ref(null);
const localStorageKey = ref('');

onMounted(async () => {
  await loadFeatureDetail();
  loadFromLocalStorageOrServer();
});

async function loadFeatureDetail(threadId = route.params.id, featureId = route.params.feature) {
  const featureDetail = await fetchFeatureDetail(threadId, featureId);
  if (!featureDetail) return;
  feature.value = featureDetail.feature;
  messages.value = featureDetail.messages;

  localStorageKey.value = `featureRating_${route.params.id}_${feature.value.feature_id}`;

  let lastSender = '';
  let currentColor = 'same-sender';
  messages.value.forEach(message => {
    if (message.sender !== lastSender) {
      currentColor = currentColor === 'same-sender' ? 'different-sender' : 'same-sender';
      lastSender = message.sender;
    }
    senderColors.value[message.sender] = currentColor;
  });
}

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

async function loadFromLocalStorageOrServer() {
  const savedRatingData = localStorage.getItem(localStorageKey.value);
  if (savedRatingData) {
    const parsedRatingData = JSON.parse(savedRatingData);
    selectedRating.value = parsedRatingData.rating_content;
    editableFeature.value = parsedRatingData.edited_feature;
  } else {
    const serverRatingData = await fetchRatingFromServer(route.params.id, feature.value.feature_id);
    if (serverRatingData) {
      selectedRating.value = serverRatingData.rating_content;
      editableFeature.value = { ...feature.value, content: serverRatingData.edited_feature };
    } else {
      selectedRating.value = null;
      editableFeature.value = { ...feature.value };
    }
  }
}

async function fetchRatingFromServer(threadId, featureId) {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`http://localhost:8081/api/get_rating/${threadId}/${featureId}`, {
      headers: {
        'Authorization': api_key
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching rating from server:', error);
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
  const options = {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'};
  const date = new Date(timestamp);
  return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
}

async function rateFeature(rating) {
  selectedRating.value = rating;
  saveRatingToLocalStorage();
}

function saveRatingToLocalStorage() {
  const ratingData = {
    rating_content: selectedRating.value,
    edited_feature: editableFeature.value
  };
  localStorage.setItem(localStorageKey.value, JSON.stringify(ratingData));
}

function saveFeaturesServerSide() {
  const api_key = localStorage.getItem('api_key');
  if (!api_key) {
    alert('API key is missing');
    return;
  }
  const ratingData = {
    rating_content: selectedRating.value,
    edited_feature: editableFeature.value.content
  };

  axios.post(`http://localhost:8081/api/save_rating/${route.params.id}/${feature.value.feature_id}`, ratingData, {
    headers: {
      'Authorization': api_key,
      'Content-Type': 'application/json'
    }
  })
    .then(response => {
      alert('Rating wurde erfolgreich gespeichert!');
    })
    .catch(error => {
      console.error('Error saving rating:', error);
      alert('Fehler beim Speichern des Ratings.');
    });
}

onBeforeRouteUpdate(async (to, from, next) => {
  await loadFeatureDetail(to.params.id, to.params.feature);
  loadFromLocalStorageOrServer();
  next();
});

// Watch the editableFeature for changes and save to local storage immediately
watch(editableFeature, () => {
  saveRatingToLocalStorage();
}, {deep: true});
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

.likert-scale-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 10px;
}

.likert-scale {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin: 0 20px;
  gap: 5vh; /* Add padding between the options */
}

.likert-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.likert-circle {
  border: 2.5px solid #C8E6C9;
  border-radius: 50%;
  margin-bottom: 4px;
  transition: background-color 0.3s, border-color 0.3s, transform 0.3s;
  display: flex;
  justify-content: center;
  align-items: center;
}

.size-1 .likert-circle {
  width: 44px;
  height: 44px;
}

.size-2 .likert-circle {
  width: 36px;
  height: 36px;
}

.size-3 .likert-circle {
  width: 28px;
  height: 28px;
}

.green-tone .likert-circle {
  border-color: #66BB6A;
}

.purple-tone .likert-circle {
  border-color: #AB47BC;
}

.gray-tone .likert-circle {
  border-color: #BDBDBD;
}

.selected-rating.green-tone .likert-circle {
  background-color: #66BB6A; /* Füllt den Kreis mit grün */
}

.selected-rating.purple-tone .likert-circle {
  background-color: #AB47BC; /* Füllt den Kreis mit lila */
}

.selected-rating.gray-tone .likert-circle {
  background-color: #BDBDBD; /* Füllt den Kreis mit grau */
}

.likert-option:hover .likert-circle {
  background-color: #E0F7FA;
  border-color: #00ACC1;
  transform: scale(1.1);
}

.green-tone:hover .likert-circle {
  background-color: #E8F5E9;
  border-color: #66BB6A;
}

.purple-tone:hover .likert-circle {
  background-color: #F3E5F5;
  border-color: #AB47BC;
}

.gray-tone:hover .likert-circle {
  background-color: #F5F5F5;
  border-color: #BDBDBD;
}

/* Neue Regeln für ausgewählte Punkte */
.selected-rating .likert-circle:hover {
  transform: scale(1.1);
}

.selected-rating.green-tone .likert-circle:hover {
  background-color: #66BB6A; /* Bleibt grün */
  border-color: #66BB6A;
}

.selected-rating.purple-tone .likert-circle:hover {
  background-color: #AB47BC; /* Bleibt lila */
  border-color: #AB47BC;
}

.selected-rating.gray-tone .likert-circle:hover {
  background-color: #BDBDBD; /* Bleibt grau */
  border-color: #BDBDBD;
}


.expandable-padding {
  padding-top: 20px;
}

.white-icon {
  color: white;
}
</style>
