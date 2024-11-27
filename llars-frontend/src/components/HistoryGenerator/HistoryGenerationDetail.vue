<template>
  <v-container fluid class="main-container">
    <v-row>
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
        <div class="rating-section">
          <div class="rating-category" id="rating-category-coherence">
            <h4>1. Kohärenz und Logik ratsuchenden Person</h4>
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
      :initial-category-id="consulting_category_id"
      :initial-category-notes="consulting_category_notes"
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
          :color="ratedStatus === 'Rated' ? 'green lighten-2' : ratedStatus === 'Partly Rated' ? 'orange lighten-2' : 'grey lighten-2'"
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
import { ref, onMounted, watch, watchEffect } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import LikertScale from '../parts/LikertScale.vue';
import BinaryLikertScale from "@/components/parts/BinaryLikertScale.vue";
import CategorySelection from '../parts/CategorySelection.vue';

// Setup route, router and data variables
const route = useRoute();
const threadId = route.params.id;
const router = useRouter();
const messages = ref([]);
const ratings = ref({
  counsellor_coherence: null,
  client_coherence: null,
  quality: null,
  overall: null
});
const feedback = ref('');

const selectedCategoryId = ref(null);
const categoryNotes = ref(null);

// for comparison tee see if there are unsaved changes
const initial_rating = ref(null)
const initial_feedback = ref(null)
const initial_messages = ref([]);
const initialSelectedCategoryId = ref(null);
const initial_categoryNotes = ref(null)

const ratedStatus = ref(null);
const hasUnsavedChanges = ref(false)

const isDisabled = ref({
  counsellor_coherence: false,
  client_coherence: false,
  quality: false,
  overall: false
})

// Fetch email thread details on component mount
onMounted(async () => {
  await initializeWebsiteComponent()
});

async function initializeWebsiteComponent()
{
  //const threadId = route.params.id;
  const api_key = localStorage.getItem('api_key');
  try {
    // API request to get the email thread details /  messages of mail history
    const thread_messages = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/generations/${threadId}`, {
      headers: {
        'Authorization': api_key,
      },
    });

    //api request to get rating of each message
    const message_ratings = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/message_ratings/${threadId}`, {
      headers: {
        'Authorization': api_key,
      },
    });

    // putting the messages and the ratings together
    messages.value = thread_messages.data.messages.map(message => {
      const ratingObj = message_ratings.data.find(rating => rating.message_id === message.message_id);
      return {
        ...message,
        rating: ratingObj ? ratingObj.rating : null // Setze Bewertung auf null, wenn keine vorhanden ist
      };
    });
    console.log("Combined Messages with Ratings:", messages.value);


    // get the rating of mail history
    const mailhistoryRatingResponse = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/mailhistory_ratings/${threadId}`, {
      headers: {
        'Authorization': api_key,
      }
    });

    // Check if the user has already rated the thread
    if (mailhistoryRatingResponse.data) {
      // If the mail rating exists, set the data accordingly
      let temp_rating ={ // for avoiding bugs cause of 0 value
        counsellor_coherence: mailhistoryRatingResponse.data.rating.counsellor_coherence_rating,
        client_coherence: mailhistoryRatingResponse.data.rating.client_coherence_rating,
        quality: mailhistoryRatingResponse.data.rating.quality_rating,
        overall: mailhistoryRatingResponse.data.rating.overall_rating
      }

      // If Values are saved as 0 in the db, use null for the frontend. 0 stands for a disabled scal

      Object.keys(temp_rating).forEach(key => {
        if (temp_rating[key] === 0) {
          temp_rating[key] = null;
        }
      });

      ratings.value = {
        counsellor_coherence: temp_rating.counsellor_coherence,
        client_coherence: temp_rating.client_coherence,
        quality: temp_rating.quality,
        overall: temp_rating.overall
      };
      selectedCategoryId.value = mailhistoryRatingResponse.data.consulting_category.consulting_category_type_id
      categoryNotes.value = mailhistoryRatingResponse.data.consulting_category.consulting_category_note


      feedback.value = mailhistoryRatingResponse.data.rating.feedback;
      ratedStatus.value = mailhistoryRatingResponse.data.rating.rating_status;

    // set rating status to none if no rating is found
    } else {
      ratedStatus.value = 'Not Rated';
    }
    console.log(` Ist rated? ${ratedStatus.value}`)

    // set the db retrieved values as initial values, in order for comparison if changes occurred
    initial_rating.value = JSON.parse(JSON.stringify(ratings.value));
    initial_feedback.value = JSON.parse(JSON.stringify(feedback.value));
    initial_messages.value = JSON.parse(JSON.stringify(messages.value));
    initialSelectedCategoryId.value = JSON.parse(JSON.stringify(selectedCategoryId))
    initial_categoryNotes.value = JSON.parse(JSON.stringify(categoryNotes))

    // load ratings from local storage
    loadMailHistoryRatingsFromLocalStorage();
    loadMessageRatingsFromLocalStorage();

    hasUnsavedChanges.value = check_for_changes()
  } catch (error) {
    console.error('Error fetching email thread details or rating status:', error);
  }
}

function handleCategorySelection(selectedCategory) {
  selectedCategoryId.value = selectedCategory.categoryId;
  categoryNotes.value = selectedCategory.categoryNotes;
  console.log("Test Kategory", categoryNotes.value)
}

// Format timestamp for display
function formatTimestamp(timestamp) {
  const options = {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'};
  const date = new Date(timestamp);
  return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
}


// Load changes of mail history ratings from local storage
function loadMailHistoryRatingsFromLocalStorage() {
  const savedData = JSON.parse(localStorage.getItem(`local_rating_changes_${threadId}`));
  if (savedData) {
    ratings.value = savedData.ratings;
    feedback.value = savedData.feedback;
    selectedCategoryId.value= savedData.category_id
    categoryNotes.value = savedData.category_notes
    console.log("Ratings wurden aus dem Local Storage geladen")
    hasUnsavedChanges.value = check_for_changes();
  }
}

// Load changes of message ratings from local storage
function loadMessageRatingsFromLocalStorage() {
  // retrieve data from local storage
  const savedMessageRatings = JSON.parse(localStorage.getItem(`local_messageRating_changes_${threadId}`));

  // check if data got retrieved
  if (savedMessageRatings) {
    savedMessageRatings.forEach(savedRating => {
      // if yes set the individual rating of each message
      const message = messages.value.find(msg => msg.message_id === savedRating.message_id);
      if (message) {
        message.rating = savedRating.rating;
      }
    });
    console.log("Nachrichtenbewertungen aus Local Storage geladen:", messages.value);
  }
}

// save local changes of mail history rating into local storage
function saveMailhistoryRatingsToLocalStorage() {
  if (feedback.value === ""){feedback.value = null}
  const dataToSave = {
    ratings: ratings.value,
    feedback: feedback.value,
    category_id: selectedCategoryId.value,
    category_notes: categoryNotes.value
  };
  localStorage.setItem(`local_rating_changes_${threadId}`, JSON.stringify(dataToSave));
  console.log("Änderungen wurden im LocalStorage gespeichert")
}


// save local changes of message rating into local storage
function saveMessageRatingsToLocalStorage() {
  const messageRatingsToSave = messages.value.map(message => ({
    message_id: message.message_id,
    rating: message.rating
  }));

  // save ratings and message id into local storage
  localStorage.setItem(`local_messageRating_changes_${threadId}`, JSON.stringify(messageRatingsToSave));
  console.log("Nachrichtenbewertungen im Local Storage gespeichert:", messageRatingsToSave);
}

// Observes for mail history ratings and feedback
watch(
  [ratings, selectedCategoryId, categoryNotes],
  () => {
    console.log("Bewertung wurde geändert, speichere in Local Storage...");

    saveMailhistoryRatingsToLocalStorage();
    hasUnsavedChanges.value = check_for_changes();
    updateLikertActivationStatus()
  },
  { deep: true }
);

watch(
  [feedback],
  () => {
    console.log("Feedback wurde geändert, speichere in Local Storage...");


    saveMailhistoryRatingsToLocalStorage();
    hasUnsavedChanges.value = check_for_changes();
  },
  { deep: true }
);


function updateLikertActivationStatus() {
  // Hilfsfunktion zum Hinzufügen und Entfernen der "disabled"-Klassen
  function toggleClassForDiv(elementId, shouldDisable) {
    const div = document.getElementById(elementId);
    if (shouldDisable) {
      div.classList.add('disabled');
    } else {
      div.classList.remove('disabled');
    }
  }

  const shouldDisableCounsellorCoherence = ratings.value.client_coherence > 2
  toggleClassForDiv('rating-category-coherence-counsellor', shouldDisableCounsellorCoherence);

  const shouldDisableClientCoherence = ratings.value.counsellor_coherence > 2
  toggleClassForDiv('rating-category-coherence-client', shouldDisableClientCoherence);

  const shouldDisableQuality = ratings.value.counsellor_coherence > 2 || ratings.value.client_coherence > 2;
  toggleClassForDiv('rating-category-quality', shouldDisableQuality || shouldDisableClientCoherence || shouldDisableCounsellorCoherence);

  // Wenn der Wert von quality >= 2, deaktivieren wir "rating-category-overall"
  const shouldDisableOverall = ratings.value.quality > 2;
  toggleClassForDiv('rating-category-overall', shouldDisableQuality || shouldDisableOverall || shouldDisableClientCoherence || shouldDisableCounsellorCoherence);

  isDisabled.value.counsellor_coherence = checkIfDisabled('rating-category-coherence-counsellor')
  isDisabled.value.client_coherence = checkIfDisabled('rating-category-coherence-client')
  isDisabled.value.quality = checkIfDisabled('rating-category-quality')
  isDisabled.value.overall = checkIfDisabled('rating-category-overall')
}



function checkIfDisabled(elementID) {
  const element = document.getElementById(elementID);

  return element.classList.contains('disabled')

}

function check_for_changes() {
  // did changes occur in mail history rating or feedback?
  if(initial_rating.value.counsellor_coherence !== ratings.value.counsellor_coherence||
    initial_rating.value.client_coherence !== ratings.value.client_coherence ||
    initial_rating.value.quality !== ratings.value.quality  ||
    initial_rating.value.overall !== ratings.value.overall ||
    initial_feedback.value !== feedback.value ||
    initialSelectedCategoryId !== selectedCategoryId ||
    initial_categoryNotes !== categoryNotes)
  {
    localStorage.setItem(`hasUnsaved_ratingChanges_${threadId}`, JSON.stringify(true));
    return true;
  }

  // occurred changes in the ratings of the message rating?
  for(let i = 0; i < initial_messages.value.length; i++)
  {
    if(initial_messages.value[i].rating !== messages.value[i].rating)
    {
      localStorage.setItem(`hasUnsaved_ratingChanges_${threadId}`, JSON.stringify(true))
      return true;
    }
  }
  localStorage.removeItem(`hasUnsaved_ratingChanges_${threadId}`)
  return false
}


// Get class based on sender (to differentiate between user and other messages)
function getMessageClass(sender) {
  return sender === 'Ratsuchende Person' ? 'same-sender' : 'different-sender';
}

// Rate individual messages
function rateMessage(index, rating) {
  messages.value[index].rating = messages.value[index].rating === rating ? null : rating;
  saveMessageRatingsToLocalStorage()
  hasUnsavedChanges.value = check_for_changes()
}

// Save ratings of history and messages to the server
async function saveRatingServerSide() {
  const api_key = localStorage.getItem('api_key');
  const threadId = route.params.id;
  const rating_and_category = {
    counsellor_coherence_rating: ratings.value.counsellor_coherence,
    client_coherence_rating: ratings.value.client_coherence,
    quality_rating: ratings.value.quality,
    overall_rating: ratings.value.overall,
    feedback: feedback.value,
    consulting_category_id: selectedCategoryId.value,
    consulting_category_notes: categoryNotes.value,
    consider_category_for_status: true
  }
  if(checkIfDisabled("rating-category-coherence-client") && rating_and_category.client_coherence_rating === null)
    rating_and_category.client_coherence_rating = 0;
    rating_and_category.consider_category_for_status = false;
  if(checkIfDisabled("rating-category-coherence-counsellor") && rating_and_category.counsellor_coherence_rating === null)
    rating_and_category.counsellor_coherence_rating = 0;
    rating_and_category.consider_category_for_status = false;
  if(checkIfDisabled("rating-category-quality") && rating_and_category.quality_rating === null)
    rating_and_category.quality_rating = 0;
    rating_and_category.consider_category_for_status = false;
  if(checkIfDisabled("rating-category-overall") && rating_and_category.overall_rating === null)
    rating_and_category.overall_rating = 0;
    rating_and_category.consider_category_for_status = false;

  try {
    // saving mail history ratings
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/save_mailhistory_rating/${threadId}`,
      rating_and_category,
      {
        headers: {
          'Authorization': api_key,
          'Content-Type': 'application/json',
        }
      }
    );
    console.log('Mail Rating saved:', response.data);

    // save message ratings
    const messageRatings = messages.value.map(message => ({
      message_id: message.message_id,
      rating: message.rating // Wenn kein Rating vorhanden ist, wird null übermittelt
    }));
    // API request to save message ratings
    const messageRatingResponse = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/save_message_ratings/${threadId}`,
      { message_ratings: messageRatings },
      {
        headers: {
          'Authorization': api_key,
          'Content-Type': 'application/json',
        }
      }
    );
    console.log('Message Ratings saved:', messageRatingResponse.data);

    alert('Rating und Feedback wurden erfolgreich gespeichert!');
    localStorage.removeItem(`local_rating_changes_${threadId}`); // remove the local changes from local storage
    localStorage.removeItem(`local_messageRating_changes_${threadId}`);
    await initializeWebsiteComponent() //reload website

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
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/mailhistory_ratings`, {
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
