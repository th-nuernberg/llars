<template>
  <div class="rater-feature-page">
    <!-- Haupt-Content-Bereich -->
    <div ref="containerRef" class="main-content">
      <!-- Feature-Bereich (links) -->
      <div class="feature-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <h2>Feature Detail</h2>
        </div>
        <div class="panel-content">
          <v-card class="feature-card mb-4">
            <v-card-title class="feature-card-title">{{ feature.model_name }}</v-card-title>
            <v-card-subtitle>{{ translateFeatureType(feature.type) }}</v-card-subtitle>
            <v-card-text class="feature-card-text">{{ feature.content }}</v-card-text>
          </v-card>

          <h3 class="section-title">Bewerten Sie dieses Feature</h3>
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
                  'good-tone': rating === 1 || rating === 2,
                  'bad-tone': rating === 4 || rating === 5,
                  'neutral-tone': rating === 3
                }]"
              >
                <span class="likert-circle">
                  <template v-if="rating === selectedRating">
                    <v-icon class="check-icon" size="small">mdi-check</v-icon>
                  </template>
                </span>
              </div>
            </div>
            <span class="likert-label-text">Schlecht</span>
          </div>

          <v-expansion-panels class="mt-6">
            <v-expansion-panel>
              <v-expansion-panel-title>Feature bearbeiten</v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-form>
                  <v-text-field
                    label="Model Name"
                    v-model="editableFeature.model_name"
                    variant="outlined"
                    density="compact"
                    class="mb-2"
                  ></v-text-field>
                  <v-textarea
                    label="Feature Content"
                    v-model="editableFeature.content"
                    variant="outlined"
                    density="compact"
                    rows="4"
                  ></v-textarea>
                  <v-btn variant="tonal" size="small" @click="saveFeaturesServerSide">
                    <v-icon start size="small">mdi-content-save</v-icon>
                    Speichern
                  </v-btn>
                </v-form>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </div>
      </div>

      <!-- Resize Divider -->
      <div
        class="resize-divider"
        :class="{ 'resizing': isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- E-Mail Verlauf (rechts) -->
      <div class="email-panel" :style="rightPanelStyle()">
        <div class="panel-header">
          <h2>E-Mail Verlauf</h2>
        </div>
        <div class="panel-content">
          <div
            v-for="message in messages"
            :key="message.message_id"
            class="email-message"
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
      </div>
    </div>

    <!-- Action Bar -->
    <div class="action-bar">
      <v-btn variant="tonal" size="small" @click="saveFeaturesServerSide">
        <v-icon start size="small">mdi-content-save</v-icon>
        Speichern
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn variant="tonal" size="small" @click="goBack">
        <v-icon start size="small">mdi-arrow-left</v-icon>
        Zurück zur Übersicht
      </v-btn>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router';
import axios from 'axios';
import { usePanelResize } from '@/composables/usePanelResize';

const route = useRoute();
const router = useRouter();
const feature = ref({});
const editableFeature = ref({});
const messages = ref([]);
const senderColors = ref({});
const selectedRating = ref(null);
const localStorageKey = ref('');

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 50,
  minLeftPercent: 30,
  maxLeftPercent: 70,
  storageKey: 'rater-feature-panel-width'
});

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
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/ratings/${threadId}/${featureId}`);
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
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/get_rating/${threadId}/${featureId}`);
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
    rating_content: selectedRating.value,
    edited_feature: editableFeature.value
  };
  localStorage.setItem(localStorageKey.value, JSON.stringify(ratingData));
}

function saveFeaturesServerSide() {
  const ratingData = {
    rating_content: selectedRating.value,
    edited_feature: editableFeature.value.content
  };

  axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/save_rating/${route.params.id}/${feature.value.feature_id}`, ratingData, {
    headers: {
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

function goBack() {
  router.push({ name: 'RaterDetail', params: { id: route.params.id } });
}

onBeforeRouteUpdate(async (to, from, next) => {
  await loadFeatureDetail(to.params.id, to.params.feature);
  loadFromLocalStorageOrServer();
  next();
});

// Watch the editableFeature for changes and save to local storage immediately
watch(editableFeature, () => {
  saveRatingToLocalStorage();
}, { deep: true });
</script>

<style scoped>
/* ============================================
   HAUPT-LAYOUT: Feste Viewport-Höhe, kein Scroll
   64px AppBar + 30px Footer = 94px
   ============================================ */
.rater-feature-page {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 0;
}

/* ============================================
   FEATURE-PANEL (links)
   ============================================ */
.feature-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 300px;
}

/* ============================================
   RESIZE DIVIDER
   ============================================ */
.resize-divider {
  width: 6px;
  background-color: rgb(var(--v-theme-surface-variant));
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 0.15s ease;
}

.resize-divider:hover,
.resize-divider.resizing {
  background-color: rgb(var(--v-theme-primary));
}

.resize-handle {
  width: 4px;
  height: 40px;
  background-color: rgba(var(--v-theme-on-surface), 0.3);
  border-radius: 2px;
  transition: background-color 0.15s ease;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background-color: rgba(255, 255, 255, 0.8);
}

/* ============================================
   E-MAIL-PANEL (rechts)
   ============================================ */
.email-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-surface));
  min-width: 250px;
}

/* ============================================
   PANEL-HEADER & CONTENT
   ============================================ */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  flex-shrink: 0;
  border-bottom: 1px solid rgb(var(--v-theme-surface-variant));
}

.panel-header h2 {
  margin: 0;
  font-size: 1.1rem;
  color: rgb(var(--v-theme-on-surface));
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* ============================================
   FEATURE CARD
   ============================================ */
.feature-card {
  margin-bottom: 16px;
}

.feature-card-title {
  font-size: 1rem;
  font-weight: 600;
}

.feature-card-text {
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: rgb(var(--v-theme-on-surface));
}

/* ============================================
   LIKERT SCALE
   ============================================ */
.likert-scale-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 0;
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  margin-bottom: 16px;
}

.likert-label-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.8;
}

.likert-scale {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin: 0 20px;
  gap: 24px;
}

.likert-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.likert-circle {
  border: 2.5px solid rgb(var(--v-theme-surface-variant));
  border-radius: 50%;
  transition: background-color 0.2s, border-color 0.2s, transform 0.2s;
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

/* Good tone (green/success) */
.good-tone .likert-circle {
  border-color: rgb(var(--v-theme-success));
}

.good-tone:hover .likert-circle {
  background-color: rgba(var(--v-theme-success), 0.15);
  transform: scale(1.1);
}

.selected-rating.good-tone .likert-circle {
  background-color: rgb(var(--v-theme-success));
}

/* Bad tone (error/red) */
.bad-tone .likert-circle {
  border-color: rgb(var(--v-theme-error));
}

.bad-tone:hover .likert-circle {
  background-color: rgba(var(--v-theme-error), 0.15);
  transform: scale(1.1);
}

.selected-rating.bad-tone .likert-circle {
  background-color: rgb(var(--v-theme-error));
}

/* Neutral tone (gray) */
.neutral-tone .likert-circle {
  border-color: rgb(var(--v-theme-surface-variant));
}

.neutral-tone:hover .likert-circle {
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  transform: scale(1.1);
}

.selected-rating.neutral-tone .likert-circle {
  background-color: rgb(var(--v-theme-surface-variant));
}

.check-icon {
  color: white;
}

/* ============================================
   E-MAIL NACHRICHTEN
   ============================================ */
.email-message {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  user-select: none;
}

.same-sender {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.different-sender {
  background-color: rgba(var(--v-theme-secondary), 0.12);
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.message-sender {
  font-weight: 600;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
}

.message-timestamp {
  font-size: 0.75rem;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.6;
}

.message-body p {
  margin: 0;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.5;
}

/* ============================================
   ACTION BAR
   ============================================ */
.action-bar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-top: 1px solid rgb(var(--v-theme-surface-variant));
  background-color: rgb(var(--v-theme-surface));
  flex-shrink: 0;
}
</style>
