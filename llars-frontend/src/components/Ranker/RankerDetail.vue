<template>
  <v-container fluid class="pa-0">
    <v-row>
      <!-- Feature-Bereich -->
      <v-col :cols="emailPaneExpanded ? 12 : 11" :md="emailPaneExpanded ? 6 : 11">
        <h2 class="mb-2">Features</h2>
        <div class="features-container">
          <v-expansion-panels>
            <v-expansion-panel v-for="feature in groupedFeatures" :key="feature.type">
              <v-expansion-panel-title>
                <div>{{ translateFeatureType(feature.type) }}</div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div style="display: flex; justify-content: space-around;">
                  <!-- Gut Bucket -->
                  <div class="bucket good-bucket">
                    <h3>Gut</h3>
                    <draggable
                      v-model="feature.goodList"
                      class="list-group bucket-content"
                      group="featureGroup"
                      item-key="id"
                       @end="saveToLocalStorage(route.params.id)"
                    >
                      <template #item="{ element }">
                        <div class="list-group-item item">
                          <div v-if="element.minimized" class="clamped-text" v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <div v-else v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <div class="toggle-btn-container">
                            <v-btn
                              v-if="isLongContent(element.content)"
                              class="small-toggle-btn"
                              small
                              @click="toggleMinimize(element)"
                            >
                              {{ element.minimized ? 'Mehr anzeigen' : 'Weniger anzeigen' }}
                            </v-btn>
                          </div>
                        </div>
                      </template>
                    </draggable>
                  </div>

                  <!-- Mittel Bucket -->
                  <div class="bucket average-bucket">
                    <h3>Mittel</h3>
                    <draggable
                      v-model="feature.averageList"
                      class="list-group bucket-content"
                      group="featureGroup"
                      item-key="id"
                       @end="saveToLocalStorage(route.params.id)"
                    >
                      <template #item="{ element }">
                        <div class="list-group-item item">
                          <div v-if="element.minimized" class="clamped-text" v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <div v-else v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <div class="toggle-btn-container">
                            <v-btn
                              v-if="isLongContent(element.content)"
                              class="small-toggle-btn"
                              small
                              @click="toggleMinimize(element)"
                            >
                              {{ element.minimized ? 'Mehr anzeigen' : 'Weniger anzeigen' }}
                            </v-btn>
                          </div>
                        </div>
                      </template>
                    </draggable>
                  </div>

                  <!-- Schlecht Bucket -->
                  <div class="bucket bad-bucket">
                    <h3>Schlecht</h3>
                    <draggable
                      v-model="feature.badList"
                      class="list-group bucket-content"
                      group="featureGroup"
                      item-key="id"
                       @end="saveToLocalStorage(route.params.id)"
                    >
                      <template #item="{ element }">
                        <div class="list-group-item item">
                          <div v-if="element.minimized" class="clamped-text" v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <div v-else v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <div class="toggle-btn-container">
                            <v-btn
                              v-if="isLongContent(element.content)"
                              class="small-toggle-btn"
                              small
                              @click="toggleMinimize(element)"
                            >
                              {{ element.minimized ? 'Mehr anzeigen' : 'Weniger anzeigen' }}
                            </v-btn>
                          </div>
                        </div>
                      </template>
                    </draggable>
                  </div>
                </div>

  <!-- Neutraler Bucket -->
  <div class="neutral-bucket-container">
    <h3>Neutral</h3>
    <draggable
      v-model="feature.neutralList"
      class="neutral-list-group"
      group="featureGroup"
      item-key="id"
       @end="saveToLocalStorage(route.params.id)"
    >
      <template #item="{ element }">
        <div class="neutral-item">
          <div v-if="element.minimized" class="clamped-text" v-html="formatFeatureContent(feature.type, element.content)"></div>
          <div v-else v-html="formatFeatureContent(feature.type, element.content)"></div>
          <div class="toggle-btn-container">
            <v-btn
              v-if="isLongContent(element.content)"
              class="small-toggle-btn"
              small
              @click="toggleMinimize(element)"
            >
              {{ element.minimized ? 'Mehr anzeigen' : 'Weniger anzeigen' }}
            </v-btn>
          </div>
        </div>
      </template>
    </draggable>
  </div>
</v-expansion-panel-text>

            </v-expansion-panel>
          </v-expansion-panels>
        </div>
      </v-col>

      <!-- E-Mail Verlauf -->
      <v-col v-if="emailPaneExpanded" cols="6" class="d-flex flex-column email-pane">
        <h2 class="mb-2">
          E-Mail Verlauf
          <v-btn icon small @click="toggleEmailPane" class="custom-collapse-btn">
            <v-icon>mdi-chevron-right</v-icon>
          </v-btn>
        </h2>
        <div class="email-thread-container flex-grow-1">
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

      <v-col v-else class="email-pane-toggle">
        <div class="email-pane-collapsed">
          <v-btn class="expand-btn" @click="toggleEmailPane">
            <v-icon>mdi-chevron-left</v-icon>
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Button-Leiste -->
    <v-row class="button-class mt-auto">
      <v-col>
        <template v-if="ranked === null">
          <v-chip class="category-chip" color="grey lighten-2" small>
            <v-progress-circular indeterminate size="16" width="2" color="grey darken-2" class="mr-2"></v-progress-circular>
            Lädt...
          </v-chip>
        </template>
        <template v-else>
          <v-chip
            class="category-chip"
            :color="ranked ? 'green lighten-2' : 'red lighten-2'"
            small
          >
            {{ ranked ? 'Ranked' : 'Not Ranked' }}
          </v-chip>
        </template>
      </v-col>

      <v-spacer></v-spacer>

      <v-col cols="auto">
        <v-btn class="mr-2" @click="saveFeaturesServerSide">
          <v-icon left>mdi-content-save</v-icon>
          Speichern
        </v-btn>
        <v-btn class="mr-2" @click="navigateToPreviousCase">
          <v-icon left>mdi-arrow-left</v-icon>
          Vorheriger Fall
        </v-btn>
        <v-btn @click="navigateToNextCase">
          Nächster Fall
          <v-icon right>mdi-arrow-right</v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>


<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import draggable from 'vuedraggable';
import {
  useRankerFeatures,
  useRankerApi,
  useRankerHelpers
} from './RankerDetail/composables';

const route = useRoute();
const router = useRouter();

// Initialize composables
const {
  features,
  groupedFeatures,
  localStorageKey,
  ranked,
  saveToLocalStorage,
  loadFromLocalStorage,
  groupFeaturesByType,
  applyServerRanking,
  applyFeatureOrder,
  saveFeatureOrderToLocalStorage,
  prepareForServerSave
} = useRankerFeatures();

const {
  fetchEmailThreads,
  fetchServerRanking,
  fetchRankingThreads,
  saveRankingToServer
} = useRankerApi();

const {
  emailPaneExpanded,
  senderColors,
  dragOptions,
  toggleEmailPane,
  toggleMinimize,
  isLongContent,
  getTooltipText,
  translateFeatureType,
  formatTimestamp,
  formatFeatureContent,
  getMessageClass,
  updateSenderColors,
  handleDragStart,
  handleDragEnd
} = useRankerHelpers();

const messages = ref([]);

// Load case data for a specific case ID
const loadCaseData = async (caseId) => {
  let dataLoadedFromLocalStorage = false;

  // Check localStorage first
  if (loadFromLocalStorage(caseId)) {
    dataLoadedFromLocalStorage = true;
  }

  // If no localStorage data, fetch from server
  if (!dataLoadedFromLocalStorage) {
    const threadData = await fetchEmailThreads(caseId);
    if (!threadData) return;

    const serverRanking = await fetchServerRanking(caseId);

    ranked.value = threadData.ranked;
    features.value = threadData.features;

    // Group features by type
    const featureMap = groupFeaturesByType(features.value);

    // Apply server ranking if available
    if (serverRanking) {
      applyServerRanking(featureMap, serverRanking);
    }

    groupedFeatures.value = Array.from(featureMap.values());
    console.log('Grouped features:', groupedFeatures.value);
    localStorageKey.value = `featureOrder_${caseId}`;

    // Save to localStorage
    saveToLocalStorage(caseId);
  }

  // Always load messages from server
  const threadData = await fetchEmailThreads(caseId);
  if (threadData) {
    messages.value = threadData.messages;
    ranked.value = threadData.ranked;
  }

  // Update sender colors
  updateSenderColors(messages.value);
};

onMounted(() => {
  const caseId = route.params.id;
  if (caseId) {
    loadCaseData(caseId);
  }
});

// Watch for route changes
watch(() => route.params.id, (newId) => {
  loadCaseData(newId);
}, { immediate: true });

// Load feature order from localStorage or server
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

// Navigation methods
async function navigateToPreviousCase() {
  const currentId = parseInt(route.params.id);
  const rankingThreads = await fetchRankingThreads();

  if (!rankingThreads || rankingThreads.length === 0) {
    console.log("Keine Ranking-Threads verfügbar");
    return;
  }

  const currentIndex = rankingThreads.findIndex(thread => thread.thread_id === currentId);

  if (currentIndex === -1 || currentIndex === 0) {
    console.log("Erster Ranking-Thread erreicht oder Thread nicht gefunden");
    return;
  }

  const previousThread = rankingThreads[currentIndex - 1];
  router.push({ name: 'RankerDetail', params: { id: previousThread.thread_id.toString() } });
}

async function navigateToNextCase() {
  const currentId = parseInt(route.params.id);
  const rankingThreads = await fetchRankingThreads();

  if (!rankingThreads || rankingThreads.length === 0) {
    console.log("Keine Ranking-Threads verfügbar");
    return;
  }

  const currentIndex = rankingThreads.findIndex(thread => thread.thread_id === currentId);

  if (currentIndex === -1 || currentIndex === rankingThreads.length - 1) {
    console.log("Letzter Ranking-Thread erreicht oder Thread nicht gefunden");
    return;
  }

  const nextThread = rankingThreads[currentIndex + 1];
  router.push({ name: 'RankerDetail', params: { id: nextThread.thread_id.toString() } });
}

// Save features to server
async function saveFeaturesServerSide() {
  const threadId = route.params.id;
  const orderedFeatures = prepareForServerSave();

  const result = await saveRankingToServer(threadId, orderedFeatures);
  if (result.success) {
    alert('Ranking wurde erfolgreich gespeichert!');
    ranked.value = true;
  } else {
    alert('Fehler beim Speichern des Rankings.');
  }
}

// Handle drag end with localStorage save
function onDragEnd() {
  handleDragEnd();
  saveFeatureOrderToLocalStorage();
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.button-class {
  position: sticky;
  bottom: 0;
  padding: 1vh;
  border-top: 1px solid rgb(var(--v-theme-surface-variant));
  margin-top: 1vh;
  background-color: rgb(var(--v-theme-surface));
}

.category-chip {
  margin-right: 8px;
  border-radius: 12px 5px 12px 5px;
}

.email-thread-container {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: rgb(var(--v-theme-surface));
}

.features-container,
.email-thread-container {
  overflow-y: auto;
  max-height: 75vh;
  min-height: 74vh;
}

.fade-overlay {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  pointer-events: none;
}

.fade-overlay.top {
  top: 0;
  background: linear-gradient(to bottom, rgb(var(--v-theme-surface)), transparent);
}

.fade-overlay.bottom {
  bottom: 0;
  background: linear-gradient(to top, rgb(var(--v-theme-surface)), transparent);
}

.email-thread {
  overflow-y: auto;
}

.email-message {
  padding: 16px;
  margin-bottom: 10px;
  border-radius: 10px;
  box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);
}

.same-sender {
  background-color: #f1efd5; /* Heller Grünton für Benutzer */
}

.different-sender {
  background-color: #b0ca97; /* Dunklerer Grünton für Berater */
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.message-sender {
  font-weight: bold;
  color: rgb(var(--v-theme-on-surface));
}

.message-timestamp {
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
  font-size: 0.8rem;
}

.message-body p {
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
}

.draggable-item {
  border-radius: 33px 12px;
  padding: 15px;
  margin-bottom: 8px;
  cursor: grab;
  overflow: hidden;
  text-overflow: ellipsis;
  word-wrap: break-word;
  position: relative;
  box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);
}

.draggable-item.expanded {
  white-space: normal;
  overflow: visible;
}

.draggable-item:active {
  cursor: grabbing !important;
}

.small-toggle-btn {
  font-size: 7px;
  padding: 0;
  min-width: unset;
  width: 80px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  position: absolute;
  top: 5px;
  right: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clamped-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fallbackStyleClass {
  background-color: #528dc6;
  border-radius: 33px 12px;
  padding: 15px;
  margin-bottom: 8px;
  transform: rotate(1deg);
}

.no-select {
  user-select: none;
}

body.dragging * {
  cursor: grabbing !important;
}

.button-spacing {
  margin-right: 8px;
}

/* Optional: Entfernen Sie den rechten Abstand vom letzten Button */
.button-spacing:last-child {
  margin-right: 0;
}

.ghost {
  opacity: 0.1;
  background: #c8ebfb;
}

.v-tooltip__content {
  white-space: pre-line;
}

.buckets-container {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 30px;
  padding: 20px 10px 0;
}

.bucket {
  flex: 1;
  border: 1px solid rgb(var(--v-theme-surface-variant));
  padding: 10px;
  border-radius: 8px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* Abgemilderte Farbgebung für die Buckets */
.good-bucket {
  background-color: #e8f5e9; /* Leicht grünlich */
  border: 1px solid #a5d6a7;
}

.average-bucket {
  background-color: #fffde7; /* Leicht gelblich */
  border: 1px solid #fff59d;
}

.bad-bucket {
  background-color: #ffebee; /* Leicht rötlich */
  border: 1px solid #ef9a9a;
}

.bucket-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.item {
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 5px;
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: grab;
  position: relative;
}

/* Neutraler Bucket */
.neutral-bucket-container {
  background-color: rgb(var(--v-theme-surface-variant));
  min-height: 150px;
  border: 1px solid rgb(var(--v-theme-surface-variant));
  padding: 10px;
  border-radius: 8px;
  margin-top: 30px;
}

.neutral-list-group {
  display: flex;
  flex-direction: column; /* Vertikale Ausrichtung */
  gap: 10px;
}

.neutral-item {
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 5px;
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: grab;
  position: relative;
  width: 100%;
  text-align: left;
}

.toggle-btn-container {
  text-align: right;
  margin-top: 10px;
}

.email-pane {
  transition: width 0.3s ease;
}

.email-pane-toggle {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  background-color: rgb(var(--v-theme-surface-variant));
  width: 40px;
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
}

.email-pane-collapsed {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.email-pane-toggle {
  transition: width 0.3s ease;
}

.custom-collapse-btn {
  position: relative;
  right: -15px;
  background-color: #ccc;
  border-radius: 50%;
  width: 35px;
  height: 35px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.expand-btn {
  width: 35px;
  height: 100%;
  background-color: #ccc;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 0;
}
</style>
