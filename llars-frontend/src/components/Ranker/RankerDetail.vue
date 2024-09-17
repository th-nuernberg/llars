<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6">
        <h2>Features</h2>
        <div class="features-container">
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
                      <p>{{ element.content }}</p>
                    </div>
                  </template>
                </draggable>
              </transition-group>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
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
    <v-spacer></v-spacer>
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
      content: f.content,
      feature_id: f.feature_id,
      position: index
    });
  });

  groupedFeatures.value = Array.from(featureMap.values());
  localStorageKey.value = `featureOrder_${route.params.id}`;
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

async function fetchEmailThreads(threadId) {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`http://localhost:8081/api/email_threads/rankings/${threadId}`, {
      headers: {
        'Authorization': api_key
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching email threads:', error);
    return null;
  }
}

async function fetchServerRanking(threadId) {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`http://localhost:8081/api/email_threads/${threadId}/current_ranking`, {
      headers: {
        'Authorization': api_key
      }
    });
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
    situation_summary: 'Situationsbeschreibung'
  };
  return translations[type] || type;
}

function formatTimestamp(timestamp) {
  const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
  const date = new Date(timestamp);
  return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
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
    router.push({ name: 'RankerDetail', params: { id: previousId } });
  }
}

async function navigateToNextCase() {
  const currentId = parseInt(route.params.id);
  const totalCases = await fetchTotalCases();
  const nextId = currentId + 1;

  if (nextId <= totalCases) {
    router.push({ name: 'RankerDetail', params: { id: nextId } });
  } else {
    console.log("Letzter Fall erreicht, kann nicht zum nächsten navigieren");
  }
}

async function fetchTotalCases() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get('http://localhost:8081/api/email_threads/rankings', {
    headers: {
      'Authorization': api_key,
    }
  });
    return response.data.length;
  } catch (error) {
    console.error('Error fetching total number of cases:', error);
    return 0;
  }
}

function saveFeaturesServerSide() {
  const api_key = localStorage.getItem('api_key');
  if (!api_key) {
    alert('API key is missing');
    return;
  }

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
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

.features-container {
  max-height: 500px;
  overflow-y: auto;
  min-height: 70vh;
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
  background-color: #B2EBF2;
}

.different-sender {
  background-color: #C8E6C9;
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
  background-color: #F0F4C3;
  border-radius: 33px 12px;
  padding: 15px;
  margin-bottom: 8px;
  cursor: grab;
}

.draggable-item:active {
  cursor: grabbing !important;
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

.ghost {
  opacity: 0.1;
  background: #c8ebfb;
}
</style>
