<template>
  <div class="rater-feature-page">
    <!-- Skeleton Loading -->
    <div v-if="isLoading('data')" class="skeleton-container">
      <v-skeleton-loader type="card, paragraph, paragraph" height="520" />
    </div>

    <!-- Haupt-Content-Bereich -->
    <div v-else ref="containerRef" class="main-content">
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
                  <div class="text-caption text-medium-emphasis mt-2">
                    Änderungen werden automatisch gespeichert.
                  </div>
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
      <v-chip
        v-if="saving && savingKey === currentKey"
        color="grey"
        size="x-small"
      >
        <v-progress-circular indeterminate size="10" width="2" class="mr-1"></v-progress-circular>
        Speichert...
      </v-chip>
      <v-chip v-else-if="currentSaveError" color="error" size="x-small">
        Speichern fehlgeschlagen
      </v-chip>
      <v-chip v-else-if="currentLastSavedAt" color="success" size="x-small">
        Gespeichert
      </v-chip>
      <v-chip v-else color="grey" size="x-small">
        Auto-Speichern aktiv
      </v-chip>

      <v-spacer></v-spacer>

      <LBtn
        v-if="currentSaveError"
        variant="primary"
        prepend-icon="mdi-reload"
        class="mr-2"
        :loading="saving && savingKey === currentKey"
        @click="retrySave"
      >
        Erneut speichern
      </LBtn>
      <LBtn variant="secondary" prepend-icon="mdi-arrow-left" @click="goBack">
        Zurück zur Übersicht
      </LBtn>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { usePanelResize } from '@/composables/usePanelResize';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { useActiveDuration, useScrollDepth } from '@/composables/useAnalyticsMetrics';
import { matomoTrackEvent } from '@/plugins/llars-metrics';

const route = useRoute();
const router = useRouter();
const feature = ref({});
const editableFeature = ref({});
const messages = ref([]);
const senderColors = ref({});
const selectedRating = ref(null);
const localStorageKey = ref('');

// Skeleton Loading
const { isLoading, withLoading } = useSkeletonLoading(['data']);

// Auto-save state
const saving = ref(false);
const savingKey = ref(null);
const saveErrors = ref({});
const lastSavedAt = ref({});
const initialLoadDone = ref(false);

const currentKey = computed(() => `${route.params.id}_${route.params.feature}`);
const currentSaveError = computed(() => saveErrors.value[currentKey.value] || '');
const currentLastSavedAt = computed(() => lastSavedAt.value[currentKey.value] || 0);

const saveQueue = [];
let isProcessingSaveQueue = false;

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

// ==================== ANALYTICS ====================

// Entity dimension for this thread/feature combination
const evalEntity = computed(() => `thread:${route.params.id}|feature:${route.params.feature}`);

// Track session active time for rating
useActiveDuration({
  category: 'eval',
  action: 'session_active_ms',
  name: () => evalEntity.value,
  dimensions: () => ({ entity: evalEntity.value, view: 'rating' })
});

// Track decision time (time from page load to rating)
const pageLoadTime = ref(0);
onMounted(() => {
  pageLoadTime.value = Date.now();
});

// Track rating decision with time-to-decision
function trackRatingDecision(rating, isChange = false) {
  const timeToDecision = Date.now() - pageLoadTime.value;
  matomoTrackEvent('eval', isChange ? 'decision_change' : 'decision', evalEntity.value, timeToDecision, {
    entity: evalEntity.value,
    view: 'rating'
  });
}

// Track rating changes (when user changes their rating)
const previousRating = ref(null);

watch(
  () => [route.params.id, route.params.feature],
  async ([threadId, featureId]) => {
    await loadAll(threadId, featureId);
  },
  { immediate: true }
);

async function loadAll(threadId = route.params.id, featureId = route.params.feature) {
  initialLoadDone.value = false;

  feature.value = {};
  editableFeature.value = {};
  messages.value = [];
  senderColors.value = {};
  selectedRating.value = null;

  const key = `${threadId}_${featureId}`;
  saveErrors.value[key] = '';

  await withLoading('data', async () => {
    const ok = await loadFeatureDetail(threadId, featureId);
    if (!ok) return;
    await loadFromLocalStorageOrServer(threadId, featureId);
  });

  // Prevent watchers from triggering a save due to initial hydration.
  setTimeout(() => {
    initialLoadDone.value = true;
  }, 0);
}

async function loadFeatureDetail(threadId = route.params.id, featureId = route.params.feature) {
  const featureDetail = await fetchFeatureDetail(threadId, featureId);
  if (!featureDetail) return false;
  feature.value = featureDetail.feature;
  messages.value = featureDetail.messages;

  localStorageKey.value = `featureRating_${threadId}_${feature.value.feature_id}`;

  let lastSender = '';
  let currentColor = 'same-sender';
  messages.value.forEach(message => {
    if (message.sender !== lastSender) {
      currentColor = currentColor === 'same-sender' ? 'different-sender' : 'same-sender';
      lastSender = message.sender;
    }
    senderColors.value[message.sender] = currentColor;
  });

  return true;
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

async function loadFromLocalStorageOrServer(threadId = route.params.id, featureId = route.params.feature) {
  const savedRatingData = localStorage.getItem(localStorageKey.value);
  if (savedRatingData) {
    const parsedRatingData = JSON.parse(savedRatingData);
    selectedRating.value = parsedRatingData.rating_content;
    editableFeature.value = parsedRatingData.edited_feature;
  } else {
    const serverRatingData = await fetchRatingFromServer(threadId, featureId);
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
  // Analytics: Track the rating decision
  const isChange = previousRating.value !== null && previousRating.value !== rating;
  trackRatingDecision(rating, isChange);
  previousRating.value = rating;

  selectedRating.value = rating;
  saveRatingToLocalStorage();
  requestAutoSave();
}

function saveRatingToLocalStorage() {
  const ratingData = {
    rating_content: selectedRating.value,
    edited_feature: editableFeature.value
  };
  localStorage.setItem(localStorageKey.value, JSON.stringify(ratingData));
}

function debounce(fn, delay) {
  let timeout = null;
  return (...args) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
}

function requestAutoSave() {
  const threadId = Number(route.params.id);
  const featureId = Number(route.params.feature);
  if (!Number.isFinite(threadId) || threadId <= 0) return;
  if (!Number.isFinite(featureId) || featureId <= 0) return;
  if (selectedRating.value === null || selectedRating.value === undefined) return;

  const content = editableFeature.value?.content ?? feature.value?.content ?? '';
  if (content === null || content === undefined) return;

  const payload = {
    rating_content: selectedRating.value,
    edited_feature: content
  };

  enqueueAutoSave(currentKey.value, threadId, featureId, payload);
}

const debouncedRequestAutoSave = debounce(requestAutoSave, 500);

function enqueueAutoSave(key, threadId, featureId, payload) {
  const existingIndex = saveQueue.findIndex(t => t.key === key);
  const task = { key, threadId, featureId, payload };

  if (existingIndex !== -1) {
    saveQueue[existingIndex] = task;
  } else {
    saveQueue.push(task);
  }

  void processSaveQueue();
}

async function saveRatingToServer(threadId, featureId, payload) {
  return axios.post(
    `${import.meta.env.VITE_API_BASE_URL}/api/save_rating/${threadId}/${featureId}`,
    payload,
    {
      headers: {
        'Content-Type': 'application/json'
      }
    }
  );
}

async function processSaveQueue() {
  if (isProcessingSaveQueue) return;
  isProcessingSaveQueue = true;

  try {
    while (saveQueue.length > 0) {
      const task = saveQueue.shift();
      saving.value = true;
      savingKey.value = task.key;
      saveErrors.value[task.key] = '';

      try {
        await saveRatingToServer(task.threadId, task.featureId, task.payload);
        lastSavedAt.value[task.key] = Date.now();
      } catch (error) {
        const msg =
          error?.response?.data?.error ||
          error?.response?.data?.message ||
          error?.message ||
          'Fehler beim Speichern.';
        saveErrors.value[task.key] = msg;

        // Re-queue the latest snapshot for this feature and stop processing.
        saveQueue.unshift(task);
        break;
      } finally {
        saving.value = false;
        savingKey.value = null;
      }
    }
  } finally {
    saving.value = false;
    savingKey.value = null;
    isProcessingSaveQueue = false;
  }
}

function retrySave() {
  requestAutoSave();
}

function goBack() {
  router.push({ name: 'RaterDetail', params: { id: route.params.id } });
}

// Watch the editableFeature for changes and save to local storage immediately
watch(editableFeature, () => {
  saveRatingToLocalStorage();
  if (!initialLoadDone.value) return;
  debouncedRequestAutoSave();
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

.skeleton-container {
  padding: 16px;
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
