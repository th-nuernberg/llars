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
    <div
      :key="element.feature_id"
      class="draggable-item no-select"
      :style="{ backgroundColor: getColorForText(element.content) }"
    >
                        <div>
                          <v-btn
                            v-if="isLongContent(element.content)"
                            class="small-toggle-btn"
                            small
                            @click="toggleMinimize(element)">
                            {{ element.minimized ? 'Mehr anzeigen' : 'Weniger anzeigen' }}
                          </v-btn>
                        </div>
                        <!-- Zeige den formatierten Text im minimierten Zustand, aber begrenze ihn auf 3 Zeilen -->
                        <div v-if="element.minimized" class="clamped-text" v-html="formatFeatureContent(feature.type, element.content)"></div>
                        <div v-else v-html="formatFeatureContent(feature.type, element.content)"></div>
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
      position: index,
      minimized: false, // Zustand für minimiert/expandiert
      version: `Version ${featureMap.get(f.type).details.length + 1}` // Feste Version setzen
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

function getColorForText(text) {
  const hash = hashCode(text);

  // Base color: #F0F4C3 (240, 244, 195 in RGB)
  const baseHue = 65; // Approximate hue of #F0F4C3
  const baseSaturation = 68; // Approximate saturation of #F0F4C3
  const baseLightness = 86; // Approximate lightness of #F0F4C3

  // Generate variations
  const hueVariation = (hash & 0xFF) % 21 - 10;  // -10 to +10
  const saturationVariation = ((hash >> 8) & 0xFF) % 31 - 15;  // -15 to +15
  const lightnessVariation = ((hash >> 16) & 0xFF) % 21 - 10;  // -10 to +10

  // Apply variations
  const hue = (baseHue + hueVariation + 360) % 360; // Ensure hue is 0-359
  const saturation = Math.max(40, Math.min(100, baseSaturation + saturationVariation));
  const lightness = Math.max(70, Math.min(95, baseLightness + lightnessVariation));

  // Convert to HSL color string
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash;
}
function isLongContent(content) {
  // Temporäres Element erstellen, um die Höhe zu berechnen
  const div = document.createElement('div');
  div.style.position = 'absolute';
  div.style.visibility = 'hidden';
  div.style.width = '300px'; // Passe dies an die tatsächliche Breite deines Elements an
  div.style.webkitBoxOrient = 'vertical';
  div.style.display = '-webkit-box';
  div.style.webkitLineClamp = '3';
  div.style.overflow = 'hidden';
  div.innerHTML = formatFeatureContent('type', content);
  document.body.appendChild(div);

  // Berechne, ob der Inhalt länger als 3 Zeilen ist
  const isLong = div.scrollHeight > div.clientHeight;
  document.body.removeChild(div);
  return isLong;
}

async function fetchEmailThreads(threadId) {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/rankings/${threadId}`, {
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

function toggleMinimize(element) {
  element.minimized = !element.minimized;
}

async function fetchServerRanking(threadId) {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/${threadId}/current_ranking`, {
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
  const options = {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'};
  const date = new Date(timestamp);
  return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
}

function formatFeatureContent(type, content) {
  console.log('Formatting feature content:', type, content);
  switch (type) {
    case 'generated_subject':
      try {
        const subjectObj = JSON.parse(content);
        return subjectObj.Betreff || content; // Return the extracted subject or the original content if parsing fails
      } catch (error) {
        console.error('Error parsing generated_subject JSON:', error);
        return content; // Return the original content if parsing fails
      }

    case 'situation_summary':
      try {
        const summaryObj = JSON.parse(content);
        let formattedContent = '<div class="situation-summary">';
        for (const [key, values] of Object.entries(summaryObj)) {
          const capitalizedKey = key.charAt(0).toUpperCase() + key.slice(1);
          formattedContent += `<p><strong>${capitalizedKey}:</strong></p>`;
          formattedContent += '<ul>';
          values.forEach(item => {
            formattedContent += `<li>${item}</li>`;
          });
          formattedContent += '</ul>';
        }
        formattedContent += '</div>';

        // Add CSS for indentation
        formattedContent += `
          <style>
            .situation-summary ul {
              padding-left: 20px;
              margin-top: 5px;
              margin-bottom: 15px;
            }
            .situation-summary p {
              margin-bottom: 5px;
            }
          </style>
        `;

        return formattedContent;
      } catch (error) {
        console.error('Error parsing situation_summary JSON:', error);
        return content;
      }

    default:
      return content; // No formatting applied by default
  }
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
    router.push({name: 'RankerDetail', params: {id: previousId}});
  }
}

async function navigateToNextCase() {
  const currentId = parseInt(route.params.id);
  const totalCases = await fetchTotalCases();
  const nextId = currentId + 1;

  if (nextId <= totalCases) {
    router.push({name: 'RankerDetail', params: {id: nextId}});
  } else {
    console.log("Letzter Fall erreicht, kann nicht zum nächsten navigieren");
  }
}

async function fetchTotalCases() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/rankings`, {
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
  /* background-color: #F0F4C3; */ /* Remove this line */
  border-radius: 33px 12px;
  padding: 15px;
  margin-bottom: 8px;
  cursor: grab;
  overflow: hidden;
  text-overflow: ellipsis;
  word-wrap: break-word;
  position: relative;
}

.draggable-item.expanded {
  white-space: normal;
  overflow: visible;
}

.draggable-item:active {
  cursor: grabbing !important;
}

.small-toggle-btn {
  font-size: 7px; /* Noch kleinere Schriftgröße */
  padding: 0; /* Kein Padding */
  min-width: unset;
  width: 80px; /* Feste Breite */
  height: 20px; /* Feste Höhe */
  line-height: 20px; /* Zentrierter Text */
  text-align: center; /* Zentriere den Text */
  position: absolute;
  top: 5px;
  right: 5px;
  overflow: hidden; /* Verhindert, dass der Text aus dem Button läuft */
  text-overflow: ellipsis; /* Schneidet den Text ab, wenn er zu lang ist */
  white-space: nowrap; /* Verhindert Zeilenumbruch */
}

.clamped-text {
  display: -webkit-box;
  -webkit-line-clamp: 3; /* Zeigt bis zu 3 Zeilen an */
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

.ghost {
  opacity: 0.1;
  background: #c8ebfb;
}
</style>
