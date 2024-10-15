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

      <v-col cols="12" md="6">
        <h3>Bewerten Sie den Verlauf</h3>
        <div class="likert-scale-container">
          <span class="likert-label-text">Gut</span>
          <div class="likert-scale">
            <div
              v-for="rating in 5"
              :key="rating"
              @click="rateThread(rating)"
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

        <!-- Textfeld für Gedanken oder Notizen -->
        <v-textarea
          v-model="thoughts"
          label="Ihre Gedanken oder Notizen"
          rows="5"
          outlined
        ></v-textarea>
      </v-col>
    </v-row>

    <!-- Leiste am unteren Rand -->
    <v-row class="bottom-bar mt-auto">
      <v-col>
        <template v-if="ratedStatus === null">
          <v-chip class="category-chip" color="grey lighten-2" small>
            <v-progress-circular indeterminate size="16" width="2" color="grey darken-2" class="mr-2"></v-progress-circular>
            Lädt...
          </v-chip>
        </template>
        <template v-else>
          <v-chip
            class="category-chip"
            :color="ratedStatus ? 'green lighten-2' : 'red lighten-2'"
            small
          >
            {{ ratedStatus ? 'Rated' : 'Not Rated' }}
          </v-chip>
        </template>
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
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

// Setup route, router and data variables
const route = useRoute();
const router = useRouter();
const messages = ref([]);
const selectedRating = ref(null); // Selected rating for the Likert scale
const thoughts = ref(''); // User's thoughts or notes
const ratedStatus = ref(null); // Status whether the thread has been rated

// Fetch email thread details on component mount
onMounted(async () => {
  const threadId = route.params.id;
  const api_key = localStorage.getItem('api_key');

  try {
    // API request to get the email thread details
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/generations/${threadId}`, {
      headers: {
        'Authorization': api_key,
      },
    });
    // Set the messages from the API response
    messages.value = response.data.messages;

    // API request to check if this thread has been rated
    const ratingResponse = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/mail_ratings/${threadId}`, {
      headers: {
        'Authorization': api_key,
      },
    });

    if (ratingResponse.data) {
      ratedStatus.value = true;
      selectedRating.value = ratingResponse.data.rating_score;
      thoughts.value = ratingResponse.data.feedback;
    } else {
      ratedStatus.value = false;
    }
  } catch (error) {
    console.error('Error fetching email thread details or rating status:', error);
  }
});

// Format timestamp for display
function formatTimestamp(timestamp) {
  const options = {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'};
  const date = new Date(timestamp);
  return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
}

// Get class based on sender (to differentiate between user and other messages)
function getMessageClass(sender) {
  return sender === 'Ratsuchende Person' ? 'same-sender' : 'different-sender';
}

// Handle Likert scale rating
function rateThread(rating) {
  selectedRating.value = rating;
}

// Save rating and thoughts to the server
async function saveRatingServerSide() {
  const api_key = localStorage.getItem('api_key');
  const threadId = route.params.id;

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/save_mail_rating/${threadId}`,
      { thoughts: thoughts.value, rating_score: selectedRating.value },
      {
        headers: {
          'Authorization': api_key,
          'Content-Type': 'application/json',
        }
      }
    );
    console.log('Rating saved:', response.data);
    alert('Rating und Gedanken wurden erfolgreich gespeichert!');
    ratedStatus.value = true; // Mark as rated
  } catch (error) {
    console.error('Error saving rating:', error);
    alert('Fehler beim Speichern des Ratings.');
  }
}

// Navigate to the previous case
// Navigate to the previous case
async function navigateToPreviousCase() {
  const currentId = parseInt(route.params.id);
  const caseList = await fetchCaseList(); // Fetch the list of email threads

  if (!caseList || caseList.length === 0) {
    console.log("Keine Fälle verfügbar");
    return;
  }

  // Finde den aktuellen Fall in der Liste
  const currentIndex = caseList.findIndex(c => c.thread_id === currentId);

  if (currentIndex === -1 || currentIndex === 0) {
    console.log("Erster Fall erreicht oder Fall nicht gefunden");
    return;
  }

  // Navigiere zum vorherigen Fall
  const previousCase = caseList[currentIndex - 1];
  router.push({name: 'HistoryGeneratorDetail', params: {id: previousCase.thread_id.toString()}});
}

// Navigate to the next case
async function navigateToNextCase() {
  const currentId = parseInt(route.params.id);
  const caseList = await fetchCaseList(); // Fetch the list of email threads

  if (!caseList || caseList.length === 0) {
    console.log("Keine Fälle verfügbar");
    return;
  }

  // Finde den aktuellen Fall in der Liste
  const currentIndex = caseList.findIndex(c => c.thread_id === currentId);

  if (currentIndex === -1 || currentIndex === caseList.length - 1) {
    console.log("Letzter Fall erreicht oder Fall nicht gefunden");
    return;
  }

  // Navigiere zum nächsten Fall
  const nextCase = caseList[currentIndex + 1];
  router.push({name: 'HistoryGeneratorDetail', params: {id: nextCase.thread_id.toString()}});
}


// Fetch list of cases
async function fetchCaseList() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/mail_ratings`, {
      headers: {
        'Authorization': api_key,
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching case list:', error);
    return [];
  }
}

// Navigate back to the overview
function navigateToOverview() {
  router.push({name: 'HistoryGenerator'});
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

/* Likert Scale Styling */
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
  background-color: #E0F7FA;
  border-color: #00ACC1;
  transform: scale(1.1);
}

/* Bottom Bar Styling */
.bottom-bar {
  position: sticky;
  bottom: 0;
  padding: 1vh;
  border-top: 1px solid #ddd;
  background-color: #d6f6db;
}

.category-chip {
  margin-right: 8px;
  border-radius: 12px 5px 12px 5px;
}

.v-btn {
  margin-right: 10px;
}
</style>
