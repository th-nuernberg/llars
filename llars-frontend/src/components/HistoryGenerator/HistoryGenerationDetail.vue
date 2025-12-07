<!--HistoryGenerationDetail.vue-->
<template>
  <v-container fluid class="main-container">
    <!-- Skeleton Loading -->
    <v-skeleton-loader v-if="isLoading('messages')" type="article, article"></v-skeleton-loader>

    <v-row v-else>
      <v-col cols="12" md="6">

        <div class="email-thread-container">
          <div class="email-thread">
            <div
              v-for="(message, index) in messages"
              :key="message.message_id"
              class="email-message no-select"
              :class="getMessageClass(message.sender)"
            >
              <div class="message-header">
                <span class="message-sender">{{ message.sender }}</span>
                <span class="message-timestamp">{{ formatTimestamp(message.timestamp) }}</span>
              </div>
              <div class="message-body">
                <div v-html="formatContent(message.content)"></div>
                <div class="message-rating no-background">
                  <v-icon @click="rateMessage(index, 'up')" :color="message.rating === 'up' ? 'green' : ''" small>mdi-thumb-up-outline</v-icon>
                  <v-icon @click="rateMessage(index, 'down')" :color="message.rating === 'down' ? 'red' : ''" small>mdi-thumb-down-outline</v-icon>
                </div>
              </div>
            </div>
          </div>
          <div class="fade-overlay top"></div>
          <div class="fade-overlay bottom"></div>
        </div>
      </v-col>

      <v-col cols="12" md="6">
        <div class="rating-section">
          <div class="rating-category" id="rating-category-coherence">
            <h4>1. Kohärenz und Logik</h4>
            <p>Entsprechen die Reaktionen und Interaktionen einem natürlichen Kommunikationsmuster? Stehen die Texte in einem inhaltlichen Zusammenhang zueinander? Gibt es Brüche oder Unstimmigkeiten? Wird auf die Antwort des jeweilig anderen eingegangen und auch neue inhaltliche Aspekte generiert oder wird „stoisch“ immer das gleiche wiederholt? Gibt es Halluzinationen?</p>
        </div>

          <div class="rating-category sub-rating-category" id="rating-category-coherence-client">
            <h4>a) ratsuchende Person</h4>
            <LikertScale v-model="ratings.client_coherence" :disabled="isDisabled.client_coherence" />
          </div>

          <div class="rating-category sub-rating-category" id="rating-category-coherence-counsellor">
            <h4>a) beratende Person</h4>
            <LikertScale v-model="ratings.counsellor_coherence" :disabled="isDisabled.counsellor_coherence"  />
          </div>


          <div class="rating-category" id="rating-category-quality">
            <h4>2. Beratungsqualität</h4>
            <p>Ist die Antwort gut strukturiert und verständlich? Zeigt sich die beratende Person empathisch, wertschätzend und kongruent? Setzt die beratende Person gezielt Beratungstechniken ein, um das Anliegen systematisch zu bearbeiten und Lösungen zu entwickeln?</p>
            <LikertScale v-model="ratings.quality" :disabled="isDisabled.quality" />
          </div>

          <div class="rating-category" id="rating-category-overall">
            <h4>3. Gesamtbewertung</h4>
            <p>Ist der Fall in seiner Gesamtheit authentisch und realistisch? Eignet sich der Fall hinsichtlich Thema und Fachlichkeit als gutes Beispiel für Onlineberatung? </p>
            <BinaryLikertScale v-model="ratings.overall" :disabled="isDisabled.overall"/>
          </div>

          <v-row align="center">
    <v-spacer></v-spacer> <!-- Fügt flexiblen Raum hinzu -->
      <CategorySelection
      :initial-category-id="selectedCategoryId"
      :initial-category-notes="categoryNotes"
      @category-selected="handleCategorySelection"
      class="CategorySelectionButton"
      />
    </v-row>

          <v-textarea
            v-model="feedback"
            label="Ihre Gedanken oder Notizen"
            rows="5"
            outlined
            class="mt-4"
          ></v-textarea>
        </div>
      </v-col>
    </v-row>

    <!-- Bottom bar with added margin -->
    <v-row class="bottom-bar mt-auto">
      <v-col>
        <v-chip
          class="category-chip"
          :color="ratedStatus === 'Done' ? 'green lighten-2' : ratedStatus === 'Progressing' ? 'orange lighten-2' : 'grey lighten-2'"
          small
        >
          {{ratedStatus}}
        </v-chip>
        <v-chip
          v-if="hasUnsavedChanges"
          class="category-chip"
          color="red lighten-2"
          small
        >
          Ungespeicherte Änderungen
        </v-chip>
      </v-col>
      <v-spacer></v-spacer>

      <v-col cols="auto">
        <v-btn class="mr-2" @click="navigateToOverview">
          <v-icon left>mdi-view-list</v-icon>
          Zur Übersicht
        </v-btn>
        <v-btn class="mr-2" @click="saveRatingServerSide">
          <v-icon left>mdi-content-save</v-icon>
          Speichern
        </v-btn>
        <v-btn class="mr-2" @click="handleNavigateToPrevious">
          <v-icon left>mdi-arrow-left</v-icon>
          Vorheriger Fall
        </v-btn>
        <v-btn @click="handleNavigateToNext">
          Nächster Fall
          <v-icon right>mdi-arrow-right</v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>


<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import LikertScale from '../parts/LikertScale.vue';
import BinaryLikertScale from "@/components/parts/BinaryLikertScale.vue";
import CategorySelection from '../parts/CategorySelection.vue';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import {
  useHistoryHelpers,
  useHistoryNavigation,
  useHistoryRatings
} from './HistoryGenerationDetail/composables';

// Setup route and thread ID
const route = useRoute();
const threadId = computed(() => route.params.id);

// Skeleton Loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['messages']);

// Initialize composables
const { formatContent, formatTimestamp, getMessageClass } = useHistoryHelpers();
const { navigateToPreviousCase, navigateToNextCase, navigateToOverview } = useHistoryNavigation();
const {
  messages,
  ratings,
  feedback,
  selectedCategoryId,
  categoryNotes,
  ratedStatus,
  hasUnsavedChanges,
  isDisabled,
  initializeData,
  rateMessage,
  handleCategorySelection,
  saveRatingServerSide,
  setupWatchers
} = useHistoryRatings(threadId);

// Navigation wrappers using current thread ID
async function handleNavigateToPrevious() {
  await navigateToPreviousCase(parseInt(route.params.id));
}

async function handleNavigateToNext() {
  await navigateToNextCase(parseInt(route.params.id));
}

// Initialize on mount
onMounted(async () => {
  await withLoading('messages', async () => {
    await initializeData();
    setupWatchers();
  });
});
</script>

<style scoped>
/* Main container setup */
.main-container {
  min-height: calc(100vh - 150px); /* Adjust for app footer */
  display: flex;
  flex-direction: column;
  padding-bottom: 80px; /* Space for bottom bar */
}

/* Email thread container adjustments */
.email-thread-container {
  height: calc(100vh - 25vh); /* Adjust to match rating section */
  overflow-y: auto;
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

.message-body {
  margin: 0;
  word-wrap: break-word; /* Lange Wörter umbrechen */
  overflow-wrap: break-word; /* Sicherstellen, dass es auf allen Browsern funktioniert */
  white-space: pre-wrap; /* Erlaubt Zeilenumbrüche und behandelt Leerzeichen */
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
  gap: 5vh;
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
  background-color: #66BB6A;
}

.selected-rating.purple-tone .likert-circle {
  background-color: #AB47BC;
}

.selected-rating.gray-tone .likert-circle {
  background-color: #BDBDBD;
}

.likert-option:hover .likert-circle {
  transform: scale(1.1);
}

.green-tone:hover .likert-circle {
  background-color: #68c66b;
  border-color: #54a356;
}

.purple-tone:hover .likert-circle {
  background-color: #bb55c1;
  border-color: #8e4a9a;
}

.gray-tone:hover .likert-circle {
  background-color: #d3d3d3;
  border-color: #515151;
}

/* Rating section styling */
.rating-section {
  height: calc(100vh - 25vh); /* Adjust to match rating section */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: white;
  margin-top: 2px;
}

.rating-category {
  background-color: #f5f5f5;
  padding: 20px;
  margin-bottom: 24px;
  border-radius: 8px;
  transition: background-color 0.3s ease;
}

.rating-category:hover {
  background-color: #eeeeee;
}

.rating-category h4 {
  color: #2F4F4F;
  margin-bottom: 12px;
  font-size: 1.1em;
}

.rating-category p {
  color: #4a4a4a;
  margin-bottom: 16px;
  line-height: 1.5;
  font-size: 0.95em;
}


/* Bottom Bar Styling */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  margin-bottom: 20px;
  border-top: 1px solid #ddd;
  background-color: #d6f6db;
  z-index: 100;
}

.category-chip {
  margin-right: 8px;
  border-radius: 12px 5px 12px 5px;
}
.message-rating.no-background {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

.message-rating .v-icon {
  cursor: pointer;
  font-size: 1.2em;
  color: #757575; /* Dezentere Standardfarbe */
  transition: color 0.3s, transform 0.3s; /* Weicher Übergang für Hover-Effekte */
  margin-right: 8px; /* Abstand zwischen den Icons */
}

.message-rating .mdi-thumb-down-outline {
  margin-right: 0; /* Letztes Icon hat keinen rechten Abstand */
}

.message-rating .v-icon:hover {
  transform: scale(1.15); /* Vergrößern bei Hover */
}

.message-rating .mdi-thumb-up-outline:hover {
  color: rgba(102, 187, 106, 0.58); /* Leichtes Grün bei Hover */
}

.message-rating .mdi-thumb-down-outline:hover {
  color: rgba(229, 115, 115, 0.61); /* Leichtes Rot bei Hover */
}

.disabled {
    opacity: 0.5;
    background-color: rgba(0, 0, 0, 0.1);
    cursor: not-allowed;
  }

.sub-rating-category{
  margin-left: 10%;
}
.CategorySelectionButton{
  margin-right: 2.5%;
}

</style>
