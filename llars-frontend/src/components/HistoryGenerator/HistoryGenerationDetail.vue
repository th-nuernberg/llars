<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6">
        <h2>E-Mail Verlauf</h2>
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
  <p>{{ message.content }}</p>
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
        <h3>Bewerten Sie den Verlauf</h3>

        <!-- Plausibilität -->
        <h4>1. Plausibilität</h4>
        <p>Ist der Gesprächsverlauf plausibel? ?</p>
        <LikertScale v-model="ratings.plausibility" />

        <!-- Kohärenz und Logik -->
        <h4>2. Kohärenz und Logik</h4>
        <p>Ist der Gesprächsverlauf inhaltlich sinnvoll? Gibt es Brüche in der Logik oder Unstimmigkeiten? Gibt es Halluzinationen?</p>
        <LikertScale v-model="ratings.coherence" />

        <!-- Beratungsqualität -->
        <h4>3. Beratungsqualität</h4>
        <p>Ist die Antwort gut strukturiert und verständlich? Zeigt sich die beratende Person empathisch, wertschätzend und kongruent? Setzt die beratende Person gezielt Beratungstechniken ein, um das Anliegen systematisch zu bearbeiten und Lösungen zu entwickeln?</p>
        <LikertScale v-model="ratings.quality" />

        <!-- Gesamtbewertung -->
        <h4>4. Gesamtbewertung</h4>
        <p>Ist der Fall in seiner Gesamtheit realistisch? Stimmen die Interaktionen und die behandelten Themen mit dem typischen Verlauf eines echten Beratungsprozesses überein?</p>
        <LikertScale v-model="ratings.overall" />

        <!-- Textfeld für Feedback -->
        <v-textarea
          v-model="feedback"
          label="Ihre Gedanken oder Notizen"
          rows="5"
          outlined
        ></v-textarea>
      </v-col>
    </v-row>

    <!-- Leiste am unteren Rand -->
    <v-row class="bottom-bar mt-auto">
      <v-col>
        <v-chip
          class="category-chip"
          :color="ratedStatus === 'Rated' ? 'green lighten-2' : ratedStatus === 'Partly Rated' ? 'orange lighten-2' : 'grey lighten-2'"
          small
        >
          {{ratedStatus}}
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
import LikertScale from '../parts/LikertScale.vue';

// Setup route, router and data variables
const route = useRoute();
const router = useRouter();
const messages = ref([]);
const ratings = ref({
  plausibility: null,
  coherence: null,
  quality: null,
  overall: null
});
const feedback = ref('');
const ratedStatus = ref(null);

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
    // Set the messages from the API response and initialize ratings
    messages.value = response.data.messages.map(message => ({
      ...message,
      rating: null // Initialize rating for each message
    }));

    // Check if the user has already rated the thread
    const mailRatingResponse = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/mail_ratings/${threadId}`, {
      headers: {
        'Authorization': api_key,
      }
    });

    if (mailRatingResponse.data) {
      // If the mail rating exists, set the data accordingly
      ratings.value = {
        plausibility: mailRatingResponse.data.rating.plausibility_rating,
        coherence: mailRatingResponse.data.rating.coherence_rating,
        quality: mailRatingResponse.data.rating.quality_rating,
        overall: mailRatingResponse.data.rating.overall_rating
      };
      feedback.value = mailRatingResponse.data.rating.feedback;
      ratedStatus.value = calculateRatedStatus();

      // Set individual message ratings if available
      if (mailRatingResponse.data.message_ratings) {
        mailRatingResponse.data.message_ratings.forEach((rating, index) => {
          if (messages.value[index]) {
            messages.value[index].rating = rating;
          }
        });
      }
    } else {
      ratedStatus.value = 'Not Rated';
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


function calculateRatedStatus() {
  const ratingValues = Object.values(ratings.value);
  const filledRatings = ratingValues.filter(value => value !== null).length;

  if (filledRatings === 4) {
    return 'Rated';
  } else if (filledRatings > 0) {
    return 'Partly Rated';
  } else {
    return 'Not Rated';
  }
}

// Get class based on sender (to differentiate between user and other messages)
function getMessageClass(sender) {
  return sender === 'Ratsuchende Person' ? 'same-sender' : 'different-sender';
}

// Rate individual messages
function rateMessage(index, rating) {
  messages.value[index].rating = messages.value[index].rating === rating ? null : rating;
}

// Save rating and thoughts to the server
async function saveRatingServerSide() {
  const api_key = localStorage.getItem('api_key');
  const threadId = route.params.id;
  console.log(ratings.value)
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/save_mail_rating/${threadId}`,
      {
        plausibility_rating: ratings.value.plausibility_rating,
        coherence_rating: ratings.value.coherence,
        quality_rating: ratings.value.quality,
        overall_rating: ratings.value.overall,
        feedback: feedback.value,
        message_ratings: messages.value.map(message => message.rating)
      },
      {
        headers: {
          'Authorization': api_key,
          'Content-Type': 'application/json',
        }
      }
    );
    console.log('Rating saved:', response.data);
    alert('Rating und Feedback wurden erfolgreich gespeichert!');
    ratedStatus.value = calculateRatedStatus(); // Mark as rated / partly rated
  } catch (error) {
    console.error('Error saving rating:', error);
    alert('Fehler beim Speichern des Ratings und Feedbacks.');
  }
}

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
  router.push({name: 'HistoryGenerationDetail', params: {id: previousCase.thread_id}});
}

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
  router.push({name: 'HistoryGenerationDetail', params: {id: nextCase.thread_id}});
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

/* Updated hover styles */
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

</style>
