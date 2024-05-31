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
                  label="Feature Value"
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
  loadFromLocalStorage();
});

async function loadFeatureDetail(threadId = route.params.id, featureId = route.params.feature) {
  const featureDetail = await fetchFeatureDetail(threadId, featureId);
  if (!featureDetail) return;
  console.log('Feature detail:', featureDetail);
  console.log(typeof featureDetail.feature.content);
  console.log(typeof featureDetail.feature);
  feature.value = featureDetail.feature;
  //editableFeature.value = { ...feature.value }; // Ensure editableFeature includes feature_id
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

async function rateFeature(rating) {
  selectedRating.value = rating;
  saveRatingToLocalStorage();
}

function saveRatingToLocalStorage() {
  const ratingData = {
    rating_value: selectedRating.value,
    edited_feature: editableFeature.value
  };
  localStorage.setItem(localStorageKey.value, JSON.stringify(ratingData));
}

function loadFromLocalStorage() {
  const savedRatingData = localStorage.getItem(localStorageKey.value);
  if (savedRatingData) {
    console.log('Loading rating data from local storage:', savedRatingData)
    const parsedRatingData = JSON.parse(savedRatingData);
    selectedRating.value = parsedRatingData.rating_value;
    editableFeature.value = parsedRatingData.edited_feature;
  }
}

function saveFeaturesServerSide() {
  const api_key = localStorage.getItem('api_key');
  if (!api_key) {
    alert('API key is missing');
    return;
  }

  const ratingData = {
    rating_value: selectedRating.value,
    edited_feature: editableFeature.value
  };

  axios.post(`http://localhost:8081/api/save_rating/${route.params.id}/${feature.value.feature_id}`, ratingData, {
    headers: {
      'Authorization': api_key,
      'Content-Type': 'application/json'
    }
  })
    .then(response => {
      console.log('Rating saved successfully:', response.data);
      alert('Rating wurde erfolgreich gespeichert!');
    })
    .catch(error => {
      console.error('Error saving rating:', error);
      alert('Fehler beim Speichern des Ratings.');
    });
}

onBeforeRouteUpdate(async (to, from, next) => {
  await loadFeatureDetail(to.params.id, to.params.feature);
  loadFromLocalStorage();
  next();
});

// Watch the editableFeature for changes and save to local storage immediately
watch(editableFeature, () => {
  saveRatingToLocalStorage();
}, { deep: true });

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

.expandable-padding {
  padding-top: 20px;
}
</style>
