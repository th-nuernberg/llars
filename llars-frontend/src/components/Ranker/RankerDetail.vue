<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6">
        <h2>Features</h2>
        <div class="email-thread">
        <v-expansion-panels>
          <v-expansion-panel v-for="feature in groupedFeatures" :key="feature.type">
            <v-expansion-panel-title>
              <div>{{ translateFeatureType(feature.type) }}</div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <draggable v-model="feature.details" group="featureGroup" item-key="model_name" @change="log">
                <template #item="{element, index}">
                  <div :key="element.model_name" class="draggable-item">
                    <p><strong>Modell:</strong> {{ element.model_name }}</p>
                    <p>{{ element.value }}</p>
                  </div>
                </template>
              </draggable>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
        <v-spacer></v-spacer>

        </div>
      </v-col>

      <v-col cols="12" md="6">
        <h2>E-Mail Verlauf</h2>
        <div class="email-thread-container">
          <div class="email-thread">
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
          <div class="fade-overlay top"></div>
          <div class="fade-overlay bottom"></div>
        </div>
      </v-col>
    </v-row>
    <v-spacer></v-spacer> <!-- Dies schiebt die Buttons nach unten -->

    <v-container fluid>
      <v-col cols="12" class="button-class">
        <v-btn @click="saveFeatures">Speichern</v-btn>
        <v-btn @click="navigateToPreviousCase">Vorheriger Fall</v-btn>
        <v-btn @click="navigateToNextCase">Nächster Fall</v-btn>
      </v-col>
    </v-container>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import {useRoute, useRouter} from 'vue-router';
import draggable from 'vuedraggable';


const route = useRoute();
const router = useRouter();
const features = ref([]);
const messages = ref([]);
const senderColors = ref({}); // Verwende ein reaktives Objekt statt einer Map
const groupedFeatures = ref([]);

async function fetchFeatureRanking(threadId) {
  try {
    const response = await axios.get(`http://localhost:8081/api/email_threads/${threadId}/ranking`);
    return response.data.rankings;
  } catch (error) {
    console.error('Error fetching feature ranking:', error);
    return [];
  }
}

async function fetchEmailThreads(threadId) {
  try {
    const response = await axios.get(`http://localhost:8081/api/email_threads/${threadId}`);
    //console.log(response);
    return response.data;
  } catch (error) {
    //console.error('Error fetching email threads:', error);
    return null; // Rückgabe von null bei einem Fehler
  }
}

// Definiere Props, einschließlich 'id', falls benötigt


onMounted(async () => {
  const threadData = await fetchEmailThreads(route.params.id);
  const rankingData = await fetchFeatureRanking(route.params.id);
  console.log(rankingData);
  //if (!threadData) return;

  if (threadData) {
    features.value = threadData.features;
    messages.value = threadData.messages;
    let lastSender = '';
    let currentColor = 'same-sender';
  const featureMap = new Map();
rankingData.forEach(ranking => {
  const featureDetail = {
    feature_id: ranking.feature_id,
    model_name: ranking.model_name,
    value: ranking.value,
    ranking: ranking.ranking,
  };

  if (!featureMap.has(ranking.feature_type)) {
    featureMap.set(ranking.feature_type, {
      type: ranking.feature_type,
      details: []
    });
  }
  featureMap.get(ranking.feature_type).details.push(featureDetail);
});

// Sortieren der Features innerhalb jeder Gruppe basierend auf dem Ranking
featureMap.forEach((value, key) => {
  value.details.sort((a, b) => a.ranking - b.ranking);
});

groupedFeatures.value = Array.from(featureMap.values());


    messages.value.forEach(message => {
      if (message.sender !== lastSender) {
        currentColor = currentColor === 'same-sender' ? 'different-sender' : 'same-sender';
        lastSender = message.sender;
      }
      senderColors.value[message.sender] = currentColor;
    });
  }
});

function getMessageClass(sender) {
  // Hole die Farbe des Senders aus dem reaktiven Objekt
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
  const formattedDate = date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
  return formattedDate;
}

const colors = ["#E8F5E9", "#C8E6C9", "#F1F8E9", "#DCEDC8 ", "#a7ffeb", "#cbf0f8", "#aecbfa", "#d7aefb", "#fdcfe8", "#e6c9a8"];
function getItemStyle(index) {
  const backgroundColor = getColor(index);
  return {
    padding: '10px',
    borderRadius: '10px',
    margin: '5px 0',
    backgroundColor: `rgba(${parseInt(backgroundColor.slice(1, 3), 16)}, ${parseInt(backgroundColor.slice(3, 5), 16)}, ${parseInt(backgroundColor.slice(5, 7), 16)}, 0.8)`,
    color: '#000'
  };
}

function getColor(index) {
  return colors[index % colors.length]; // Loop through the colors array
}

async function saveFeatures() {
  try {
    const response = await axios.post('http://localhost:8081/api/save_ranking', {
      features: groupedFeatures.value
    });
    console.log('Speichern erfolgreich:', response.data);
    // Füge hier weitere Logik nach dem Speichern hinzu, z.B. eine Benachrichtigung anzeigen
  } catch (error) {
    console.error('Fehler beim Speichern der Features:', error);
    // Behandle den Fehler, z.B. durch Anzeigen einer Fehlermeldung
  }
}

function log(event) {
  console.log('Element moved', event);
  // Hier kannst du zusätzliche Logik implementieren,
  // z.B. das aktualisierte Array an den Server senden
}

function navigateToPreviousCase() {
  console.log('Navigating to case:', route.params.id)
  const currentId = parseInt(route.params.id);
  if (currentId > 1) {
    console.log(currentId)
    console.log(typeof currentId)
    const previousId = currentId - 1;
    router.push({ name: 'RankerDetail', params: { id: previousId } });
  }
}

async function navigateToNextCase() {
  const currentId = parseInt(route.params.id);
  const totalCases = await fetchTotalCases(); // Angenommen, fetchTotalCases() ist eine Methode, die die Gesamtzahl der Fälle zurückgibt
  const nextId = currentId + 1;

  if (nextId <= totalCases) {
    router.push({ name: 'RankerDetail', params: { id: nextId } });
  } else {
    console.log("Letzter Fall erreicht, kann nicht zum nächsten navigieren");
    // Hier könnten Sie zusätzliche Logik hinzufügen, z.B. eine Benachrichtigung anzeigen
  }
}

async function fetchTotalCases() {
  try {
    const response = await axios.get('http://localhost:8081/api/email_threads');
    return response.data.length; // Die Gesamtzahl der Fälle entspricht der Länge des zurückgegebenen Arrays
  } catch (error) {
    console.error('Error fetching total number of cases:', error);
    return 0; // Falls ein Fehler auftritt, gehen wir von 0 Fällen aus
  }
}



function navigateToRanker() {
  router.push({ name: 'Ranker' });
}

function reloadPage() {
  location.reload();
}

</script>

<style scoped>
.button-class {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border: 1px solid #8AC007;
  margin-top: 5px;
  position: sticky;

}

.email-thread-container {
  max-height: 500px;
  overflow-y: auto;
  min-height: 80vh; /* Stellt sicher, dass der Container den gesamten Viewport einnimmt */
  display: flex; /* Ermöglicht die Verwendung von Flexbox-Layout */
  flex-direction: column; /* Orientiert die Kinder (Zeilen) vertikal */
  position: relative; /* Wichtig für die Positionierung der Pseudo-Elemente */
}

.fade-overlay {
  position: absolute;
  left: 0;
  right: 0;
  height: 5px; /* Höhe des Überblendeffekts */
  pointer-events: none; /* Verhindert, dass die Überlagerung Mausereignisse blockiert */
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
  background-color: #B2EBF2; /* Farbe für Nachrichten vom selben Sender */
}

.different-sender {
  background-color: #C8E6C9; /* Farbe für Nachrichten von verschiedenen Sendern */
}

.another-sender {
  background-color: #F0F4C3; /* Eine weitere Farbe für die Unterscheidung */
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

.draggable-item {
  background-color: #F0F4C3; /* Farbe */
  border-radius: 33px 12px; /* unterschiedliche Radien */
  padding: 15px; /* Innerer Abstand */
  margin-bottom: 8px; /* Abstand unten */
}

.fill-height {
  height: 20vh; /* Höhe des Viewports */
  //display: flex;
  flex-direction: column;
  overflow: hidden; /* Verhindert das Scrollen des gesamten Layouts */
}


.row-height {
  height: 100vh; /* oder jede andere Höhe */
}

</style>
