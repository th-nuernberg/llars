<template>
  <div class="ranker-page">
    <!-- Haupt-Content-Bereich -->
    <div ref="containerRef" class="main-content">
      <!-- Feature-Bereich (links) -->
      <div class="features-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <h2>Features</h2>
        </div>
        <div class="panel-content">
          <v-expansion-panels>
            <v-expansion-panel v-for="feature in groupedFeatures" :key="feature.type">
              <v-expansion-panel-title>
                <div>{{ translateFeatureType(feature.type) }}</div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <!-- Buckets Container -->
                <div class="buckets-row">
                  <!-- Gut Bucket -->
                  <div class="bucket good-bucket">
                    <h4>Gut</h4>
                    <draggable
                      v-model="feature.goodList"
                      class="bucket-content"
                      group="featureGroup"
                      item-key="id"
                      @end="saveToLocalStorage(route.params.id)"
                    >
                      <template #item="{ element }">
                        <div class="bucket-item">
                          <div :class="{ 'clamped-text': element.minimized }" v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <v-btn
                            v-if="isLongContent(element.content)"
                            size="x-small"
                            variant="text"
                            class="toggle-btn"
                            @click.stop="toggleMinimize(element)"
                          >
                            {{ element.minimized ? 'Mehr' : 'Weniger' }}
                          </v-btn>
                        </div>
                      </template>
                    </draggable>
                  </div>

                  <!-- Mittel Bucket -->
                  <div class="bucket average-bucket">
                    <h4>Mittel</h4>
                    <draggable
                      v-model="feature.averageList"
                      class="bucket-content"
                      group="featureGroup"
                      item-key="id"
                      @end="saveToLocalStorage(route.params.id)"
                    >
                      <template #item="{ element }">
                        <div class="bucket-item">
                          <div :class="{ 'clamped-text': element.minimized }" v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <v-btn
                            v-if="isLongContent(element.content)"
                            size="x-small"
                            variant="text"
                            class="toggle-btn"
                            @click.stop="toggleMinimize(element)"
                          >
                            {{ element.minimized ? 'Mehr' : 'Weniger' }}
                          </v-btn>
                        </div>
                      </template>
                    </draggable>
                  </div>

                  <!-- Schlecht Bucket -->
                  <div class="bucket bad-bucket">
                    <h4>Schlecht</h4>
                    <draggable
                      v-model="feature.badList"
                      class="bucket-content"
                      group="featureGroup"
                      item-key="id"
                      @end="saveToLocalStorage(route.params.id)"
                    >
                      <template #item="{ element }">
                        <div class="bucket-item">
                          <div :class="{ 'clamped-text': element.minimized }" v-html="formatFeatureContent(feature.type, element.content)"></div>
                          <v-btn
                            v-if="isLongContent(element.content)"
                            size="x-small"
                            variant="text"
                            class="toggle-btn"
                            @click.stop="toggleMinimize(element)"
                          >
                            {{ element.minimized ? 'Mehr' : 'Weniger' }}
                          </v-btn>
                        </div>
                      </template>
                    </draggable>
                  </div>
                </div>

                <!-- Neutraler Bucket -->
                <div class="neutral-bucket">
                  <h4>Neutral</h4>
                  <draggable
                    v-model="feature.neutralList"
                    class="neutral-content"
                    group="featureGroup"
                    item-key="id"
                    @end="saveToLocalStorage(route.params.id)"
                  >
                    <template #item="{ element }">
                      <div class="bucket-item">
                        <div :class="{ 'clamped-text': element.minimized }" v-html="formatFeatureContent(feature.type, element.content)"></div>
                        <v-btn
                          v-if="isLongContent(element.content)"
                          size="x-small"
                          variant="text"
                          class="toggle-btn"
                          @click.stop="toggleMinimize(element)"
                        >
                          {{ element.minimized ? 'Mehr' : 'Weniger' }}
                        </v-btn>
                      </div>
                    </template>
                  </draggable>
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
      <v-chip
        v-if="ranked !== null"
        :color="ranked ? 'success' : 'error'"
        size="x-small"
      >
        {{ ranked ? 'Bewertet' : 'Nicht bewertet' }}
      </v-chip>
      <v-chip v-else color="grey" size="x-small">
        <v-progress-circular indeterminate size="10" width="2" class="mr-1"></v-progress-circular>
        Lädt...
      </v-chip>
      <v-spacer></v-spacer>
      <v-btn variant="tonal" size="small" class="mr-2" @click="saveFeaturesServerSide">
        <v-icon start size="small">mdi-content-save</v-icon>
        Speichern
      </v-btn>
      <v-btn variant="tonal" size="small" class="mr-2" @click="navigateToPreviousCase">
        <v-icon start size="small">mdi-arrow-left</v-icon>
        Vorheriger
      </v-btn>
      <v-btn variant="tonal" size="small" @click="navigateToNextCase">
        Nächster
        <v-icon end size="small">mdi-arrow-right</v-icon>
      </v-btn>
    </div>
  </div>
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
import { usePanelResize } from '@/composables/usePanelResize';

const route = useRoute();
const router = useRouter();

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 60,
  minLeftPercent: 30,
  maxLeftPercent: 80,
  storageKey: 'ranker-panel-width'
});

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
  senderColors,
  toggleMinimize,
  isLongContent,
  translateFeatureType,
  formatTimestamp,
  formatFeatureContent,
  getMessageClass,
  updateSenderColors
} = useRankerHelpers();

const messages = ref([]);

const loadCaseData = async (caseId) => {
  let dataLoadedFromLocalStorage = false;

  if (loadFromLocalStorage(caseId)) {
    dataLoadedFromLocalStorage = true;
  }

  if (!dataLoadedFromLocalStorage) {
    const threadData = await fetchEmailThreads(caseId);
    if (!threadData) return;

    const serverRanking = await fetchServerRanking(caseId);

    ranked.value = threadData.ranked;
    features.value = threadData.features;

    const featureMap = groupFeaturesByType(features.value);

    if (serverRanking) {
      applyServerRanking(featureMap, serverRanking);
    }

    groupedFeatures.value = Array.from(featureMap.values());
    localStorageKey.value = `featureOrder_${caseId}`;
    saveToLocalStorage(caseId);
  }

  const threadData = await fetchEmailThreads(caseId);
  if (threadData) {
    messages.value = threadData.messages;
    ranked.value = threadData.ranked;
  }

  updateSenderColors(messages.value);
};

onMounted(() => {
  const caseId = route.params.id;
  if (caseId) {
    loadCaseData(caseId);
  }
});

watch(() => route.params.id, (newId) => {
  loadCaseData(newId);
}, { immediate: true });

async function navigateToPreviousCase() {
  const currentId = parseInt(route.params.id);
  const rankingThreads = await fetchRankingThreads();

  if (!rankingThreads || rankingThreads.length === 0) return;

  const currentIndex = rankingThreads.findIndex(thread => thread.thread_id === currentId);
  if (currentIndex === -1 || currentIndex === 0) return;

  const previousThread = rankingThreads[currentIndex - 1];
  router.push({ name: 'RankerDetail', params: { id: previousThread.thread_id.toString() } });
}

async function navigateToNextCase() {
  const currentId = parseInt(route.params.id);
  const rankingThreads = await fetchRankingThreads();

  if (!rankingThreads || rankingThreads.length === 0) return;

  const currentIndex = rankingThreads.findIndex(thread => thread.thread_id === currentId);
  if (currentIndex === -1 || currentIndex === rankingThreads.length - 1) return;

  const nextThread = rankingThreads[currentIndex + 1];
  router.push({ name: 'RankerDetail', params: { id: nextThread.thread_id.toString() } });
}

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
</script>

<style scoped>
/* ============================================
   HAUPT-LAYOUT: Feste Viewport-Höhe, kein Scroll
   64px AppBar + 30px Footer = 94px
   ============================================ */
.ranker-page {
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
   BUCKETS (Gut / Mittel / Schlecht)
   ============================================ */
.buckets-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.bucket {
  flex: 1;
  min-height: 200px;
  padding: 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.bucket h4 {
  margin: 0 0 8px 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.bucket-content {
  flex: 1;
  min-height: 100px;
}

.good-bucket {
  background-color: rgba(var(--v-theme-success), 0.08);
  border: 1px solid rgba(var(--v-theme-success), 0.3);
}

.average-bucket {
  background-color: rgba(var(--v-theme-warning), 0.08);
  border: 1px solid rgba(var(--v-theme-warning), 0.3);
}

.bad-bucket {
  background-color: rgba(var(--v-theme-error), 0.08);
  border: 1px solid rgba(var(--v-theme-error), 0.3);
}

/* Neutral Bucket */
.neutral-bucket {
  background-color: rgba(var(--v-theme-surface-variant), 0.5);
  border: 1px solid rgb(var(--v-theme-surface-variant));
  padding: 12px;
  border-radius: 8px;
  margin-top: 8px;
}

.neutral-bucket h4 {
  margin: 0 0 8px 0;
  font-size: 0.875rem;
  font-weight: 600;
}

.neutral-content {
  min-height: 60px;
}

/* Bucket Items */
.bucket-item {
  background-color: rgb(var(--v-theme-surface));
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
  cursor: grab;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  position: relative;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
}

.bucket-item:active {
  cursor: grabbing;
}

.clamped-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.toggle-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 0.625rem;
}

/* ============================================
   E-MAIL NACHRICHTEN
   ============================================ */
.email-message {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
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

/* ============================================
   DRAG & DROP
   ============================================ */
.sortable-ghost {
  opacity: 0.4;
}

.sortable-chosen {
  background-color: rgba(var(--v-theme-primary), 0.15);
}
</style>
