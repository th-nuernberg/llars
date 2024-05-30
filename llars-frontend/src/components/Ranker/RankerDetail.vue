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
                <transition-group name="fade" tag="div">
                  <draggable
                    v-model="feature.details"
                    group="featureGroup"
                    item-key="feature_id"
                    @start="handleDragStart"
                    @end="handleDragEnd"
                    v-bind="dragOptions"
                    ghost-class="ghost"
                    fallback-class="fallbackStyleClass"
                    :force-fallback="true"
                  >
                    <template #item="{ element }">
                      <div :key="element.feature_id" class="draggable-item no-select">
                        <p><strong>Modell:</strong> {{ element.model_name }}</p>
                        <p>{{ element.value }}</p>
                      </div>
                    </template>
                  </draggable>
                </transition-group>
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
    </v-row>
    <v-spacer></v-spacer> <!-- Dies schiebt die Buttons nach unten -->

    <v-container fluid>
      <v-col cols="12" class="button-class">
        <v-btn @click="saveFeaturesServerSide">Speichern</v-btn>
        <v-btn @click="navigateToPreviousCase">Vorheriger Fall</v-btn>
        <v-btn @click="navigateToNextCase">Nächster Fall</v-btn>
      </v-col>
    </v-container>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import draggable from 'vuedraggable';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const features = ref([]);
const messages = ref([]);
const senderColors = ref({});
const groupedFeatures = ref([]);
const localStorageKey = ref('');

const dragOptions = ref({
  animation: 200,
  group: 'description',
  disabled: false,
  ghostClass: 'ghost',
});

const drag = ref(false);

async function fetchEmailThreads(threadId) {
  try {
    const response = await axios.get(`http://localhost:8081/api/email_threads/${threadId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching email threads:', error);
    return null; // Rückgabe von null bei einem Fehler
  }
}

async function fetchServerRanking(threadId) {
  try {
    const api_key = localStorage.getItem('api_key');
    console.log('API key:', api_key)
    const response = await axios.get(`http://localhost:8081/api/email_threads/${threadId}/current_ranking`, {
      headers: {
        'Authorization': api_key
      }
    });
    console.log('Server ranking:', response.data)
    return response.data;
  } catch (error) {
    console.error('Error fetching server ranking:', error);
    return null; // Rückgabe von null bei einem Fehler
  }
}

onMounted(async () => {
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
      value: f.value,
      feature_id: f.feature_id,
      position: index // include position
    });
  });

  groupedFeatures.value = Array.from(featureMap.values());

  // Set the localStorage key based on thread ID
  localStorageKey.value = `featureOrder_${route.params.id}`;

  // Load the saved order from LocalStorage
  await loadFeatureOrder();

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

  // Create a map with empty arrays for each feature type
  orderedFeatures.forEach(f => {
    featureMap.set(f.type, {
      type: f.type,
      details: new Array(f.details.length)
    });
  });

  // Populate the arrays with saved details in the correct positions
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
  const options = {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'};
  const date = new Date(timestamp);
  const formattedDate = date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
  return formattedDate;
}

const colors = ["#E8F5E9", "#C8E6C9", "#F1F8E9", "#DCEDC8", "#a7ffeb", "#cbf0f8", "#aecbfa", "#d7aefb", "#fdcfe8", "#e6c9a8"];

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
  return colors[index % colors.length];
}

function handleDragStart() {
  document.body.classList.add("dragging");
}

function handleDragEnd() {
  document.body.classList.remove("dragging");
  saveFeatureOrderToLocalStorage();
}

function saveFeatureOrderToLocalStorage() {
  const orderedFeatures = groupedFeatures.value.map(group => ({
    type: group.type,
    details: group.details.map((detail, index) => ({
      model_name: detail.model_name,
      value: detail.value,
      feature_id: detail.feature_id,
      position: index // save the current position
    }))
  }));
  localStorage.setItem(localStorageKey.value, JSON.stringify(orderedFeatures));
}

function navigateToPreviousCase() {
  const currentId = parseInt(route.params.id);
  if (currentId > 1) {
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

function saveFeaturesServerSide() {
  const api_key = localStorage.getItem('api_key'); // API Key aus dem localStorage beziehen
  if (!api_key) {
    alert('API key is missing');
    return;
  }

  // Load the saved feature order from LocalStorage
  const savedFeatureOrder = localStorage.getItem(`featureOrder_${route.params.id}`);
  let orderedFeatures = groupedFeatures.value.map(group => ({
    type: group.type,
    details: group.details.map((detail, index) => ({
      model_name: detail.model_name,
      value: detail.value,
      position: index // include position
    }))
  }));

  if (savedFeatureOrder) {
    orderedFeatures = JSON.parse(savedFeatureOrder);
  }

  axios.post(`http://localhost:8081/api/save_ranking/${route.params.id}`, orderedFeatures, {
    headers: {
      'Authorization': api_key,
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

function navigateToRanker() {
  router.push({ name: 'Ranker' });
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
  cursor: grab; /* Cursor ändert sich zu einer Hand */
}

.draggable-item:active {
  cursor: grabbing !important; /* Cursor ändert sich beim Greifen */
}

.fallbackStyleClass {
  background-color: #528dc6; /* Farbe */
  border-radius: 33px 12px; /* unterschiedliche Radien */
  padding: 15px; /* Innerer Abstand */
  margin-bottom: 8px; /* Abstand unten */
  transform: rotate(1deg); /* Element wird leicht gedreht */
}

.no-select {
  user-select: none; /* Verhindert die Textauswahl */
}

.fill-height {
  height: 20vh; /* Höhe des Viewports */
  flex-direction: column;
  overflow: hidden; /* Verhindert das Scrollen des gesamten Layouts */
}

.row-height {
  height: 100vh; /* oder jede andere Höhe */
}

.list-enter-active, .list-leave-active {
  transition: all 0.5s ease;
}
.list-enter, .list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
.ghost {
  opacity: 0.0;
  background: #c8ebfb;
}

body.dragging * {
  cursor: grabbing !important;
}
</style>
