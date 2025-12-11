<template>
  <div class="rater-page">
    <!-- Skeleton Loading -->
    <div v-if="isLoading('data')" class="skeleton-container">
      <v-skeleton-loader type="article, article"></v-skeleton-loader>
    </div>

    <!-- Haupt-Content-Bereich -->
    <div v-else ref="containerRef" class="main-content">
      <!-- Feature-Bereich (links) -->
      <div class="features-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <h2>Features</h2>
        </div>
        <div class="panel-content">
          <v-expansion-panels>
            <v-expansion-panel v-for="featureGroup in groupedFeatures" :key="featureGroup.type">
              <v-expansion-panel-title>
                <div>{{ translateFeatureType(featureGroup.type) }}</div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div v-for="feature in featureGroup.details" :key="feature.feature_id" class="feature-item">
                  <v-card class="feature-card" @click="navigateToFeatureDetail(featureGroup.type, feature.feature_id)">
                    <v-card-title class="feature-card-title">{{ feature.model_name }}</v-card-title>
                    <v-card-text class="feature-card-text">{{ feature.content }}</v-card-text>
                  </v-card>
                </div>
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

    <!-- Action Bar mit Buttons -->
    <div class="action-bar">
      <LBtn variant="primary" prepend-icon="mdi-content-save" @click="saveFeaturesServerSide">
        Speichern
      </LBtn>
      <v-spacer></v-spacer>
      <LBtn variant="secondary" prepend-icon="mdi-arrow-left" class="mr-2" @click="navigateToPreviousCase">
        Vorheriger
      </LBtn>
      <LBtn variant="secondary" append-icon="mdi-arrow-right" @click="navigateToNextCase">
        Nächster
      </LBtn>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { usePanelResize } from '@/composables/usePanelResize';

const route = useRoute();
const router = useRouter();
const features = ref([]);
const messages = ref([]);
const senderColors = ref({});
const groupedFeatures = ref([]);
const localStorageKey = ref('');

// Skeleton Loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['data']);

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 50,
  minLeftPercent: 25,
  maxLeftPercent: 75,
  storageKey: 'rater-panel-width'
});

onMounted(async () => {
  await withLoading('data', async () => {
    const threadData = await fetchEmailThreads(route.params.id);
    if (!threadData) return;

    features.value = threadData.features;
    messages.value = threadData.messages;

    const featureMap = new Map();
    features.value.forEach((f, index) => {
      if (!featureMap.has(f.type)) {
        featureMap.set(f.type, {
          type: f.type,
          details: []
        });
      }
      featureMap.get(f.type).details.push({
        model_name: f.model_name,
        content: f.content,
        feature_id: f.feature_id,
        position: index
      });
    });

    groupedFeatures.value = Array.from(featureMap.values());
    localStorageKey.value = `featureOrder_${route.params.id}`;
    await loadFeatureOrder();

    // Sender-Farben zuweisen
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
});

async function fetchEmailThreads(threadId) {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/ratings/${threadId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching email threads:', error);
    return null;
  }
}

async function fetchServerRanking(threadId) {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/${threadId}/current_ranking`);
    return response.data;
  } catch (error) {
    console.error('Error fetching server ranking:', error);
    return null;
  }
}

async function loadFeatureOrder() {
  const savedOrder = localStorage.getItem(localStorageKey.value);
  if (savedOrder) {
    const orderedFeatures = JSON.parse(savedOrder);
    applyFeatureOrder(orderedFeatures);
  } else {
    const serverRanking = await fetchServerRanking(route.params.id);
    if (serverRanking && !serverRanking.warning) {
      applyFeatureOrder(serverRanking);
    }
  }
}

function applyFeatureOrder(orderedFeatures) {
  const featureMap = new Map();
  orderedFeatures.forEach(f => {
    featureMap.set(f.type, {
      type: f.type,
      details: new Array(f.details.length)
    });
  });

  orderedFeatures.forEach(f => {
    f.details.forEach(detail => {
      featureMap.get(f.type).details[detail.position] = detail;
    });
  });

  groupedFeatures.value = Array.from(featureMap.values());
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

function saveFeatureOrderToLocalStorage() {
  const orderedFeatures = groupedFeatures.value.map(group => ({
    type: group.type,
    details: group.details.map((detail, index) => ({
      model_name: detail.model_name,
      content: detail.content,
      feature_id: detail.feature_id,
      position: index
    }))
  }));
  localStorage.setItem(localStorageKey.value, JSON.stringify(orderedFeatures));
}

function navigateToPreviousCase() {
  const currentId = parseInt(route.params.id);
  if (currentId > 1) {
    const previousId = currentId - 1;
    router.push({ name: 'RaterDetail', params: { id: previousId } });
  }
}

async function navigateToNextCase() {
  const currentId = parseInt(route.params.id);
  const totalCases = await fetchTotalCases();
  const nextId = currentId + 1;

  if (nextId <= totalCases) {
    router.push({ name: 'RaterDetail', params: { id: nextId } });
  } else {
    console.log("Letzter Fall erreicht, kann nicht zum nächsten navigieren");
  }
}

async function fetchTotalCases() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/ratings`);
    return response.data.length;
  } catch (error) {
    console.error('Error fetching total number of cases:', error);
    return 0;
  }
}

function saveFeaturesServerSide() {
  const savedFeatureOrder = localStorage.getItem(`featureOrder_${route.params.id}`);
  let orderedFeatures = groupedFeatures.value.map(group => ({
    type: group.type,
    details: group.details.map((detail, index) => ({
      model_name: detail.model_name,
      content: detail.content,
      position: index
    }))
  }));

  if (savedFeatureOrder) {
    orderedFeatures = JSON.parse(savedFeatureOrder);
  }

  axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/save_ranking/${route.params.id}`, orderedFeatures, {
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => {
      console.log('Ranking saved successfully:', response.data);
      alert('Ranking wurde erfolgreich gespeichert!');
    })
    .catch(error => {
      console.error('Error saving ranking:', error);
      alert('Fehler beim Speichern des Rankings.');
    });
}

async function navigateToFeatureDetail(featureType, featureId) {
  const threadId = route.params.id;
  const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/feature_type_mapping/${featureType}`);
  const featureTypeId = response.data.type_id;

  const response1 = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/ratings/${threadId}`);
  const featureId1 = response1.data.feature_id;

  router.push({ name: 'RaterDetailFeature', params: { id: threadId, feature: featureId } });
}
</script>

<style scoped>
/* ============================================
   HAUPT-LAYOUT: Feste Viewport-Höhe, kein Scroll
   64px AppBar + 30px Footer = 94px
   ============================================ */
.rater-page {
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
.features-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 200px;
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
  min-width: 200px;
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
   FEATURE CARDS
   ============================================ */
.feature-item {
  margin-bottom: 12px;
}

.feature-card {
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}

.feature-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
}

.feature-card-title {
  font-size: 0.95rem;
  font-weight: 600;
  padding-bottom: 4px;
}

.feature-card-text {
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.85;
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
   ACTION BAR (kompakt, über dem App-Footer)
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
