<template>
  <v-container fluid class="pa-0">
    <v-row no-gutters>
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
    <v-row class="button-class">
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
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const features = ref([]);
const messages = ref([]);
const senderColors = ref({});
const groupedFeatures = ref([]);
const localStorageKey = ref('');
const ranked = ref(null);

const emailPaneExpanded = ref(true);

const toggleEmailPane = () => {
  emailPaneExpanded.value = !emailPaneExpanded.value;
};

const dragOptions = ref({
  animation: 200,
  group: 'description',
  disabled: false,
  ghostClass: 'ghost',
});

// Der Key für LocalStorage
const STORAGE_KEY = 'rankerDetail_data';

// Speichern in LocalStorage mit threadId
function saveToLocalStorage(threadId) {
  const key = `${STORAGE_KEY}_${threadId}`;
  const data = groupedFeatures.value.map(group => ({
    type: group.type,
    goodList: group.goodList,
    averageList: group.averageList,
    badList: group.badList,
    neutralList: group.neutralList,
  }));
  localStorage.setItem(key, JSON.stringify(data));
}

// Daten aus LocalStorage laden mit threadId
function loadFromLocalStorage(threadId) {
  const key = `${STORAGE_KEY}_${threadId}`;
  const savedData = localStorage.getItem(key);

  if (savedData) {
    const parsedData = JSON.parse(savedData);
    groupedFeatures.value = parsedData.map(group => ({
      type: group.type,
      goodList: group.goodList || [],
      averageList: group.averageList || [],
      badList: group.badList || [],
      neutralList: group.neutralList || []
    }));
    return true;  // Daten wurden aus LocalStorage geladen
  }
  return false;  // Keine Daten im LocalStorage gefunden
}

// Funktion zum Laden der Daten für einen spezifischen Fall
// Funktion zum Laden der Daten für einen spezifischen Fall
const loadCaseData = async (caseId) => {

  loadFromLocalStorage(caseId);
  // Wenn keine Daten im LocalStorage sind oder sie unvollständig sind, rufe die Daten vom Server ab
  if (loadFromLocalStorage) {
    const threadData = await fetchEmailThreads(caseId);
    if (!threadData) return;
    console.log('Thread data:', threadData);
    // Setze den Status, ob dieser Thread geranked wurde
    ranked.value = threadData.ranked;

    features.value = threadData.features;

    // Erstelle ein Feature-Map, um die Features nach Typ zu gruppieren
    const featureMap = new Map();
    features.value.forEach((f, index) => {
      // console.log('Feature type:', f.type);
      if (!featureMap.has(f.type)) {
        featureMap.set(f.type, {
          type: f.type,
          goodList: [],
          averageList: [],
          badList: [],
          neutralList: []
        });
      }

      // Platziere das Feature initial in der Neutral-Liste
      featureMap.get(f.type).neutralList.push({
        model_name: f.model_name,
        content: f.content,
        feature_id: f.feature_id,
        position: index,
        minimized: true,
      });
    });

    groupedFeatures.value = Array.from(featureMap.values());
    localStorageKey.value = `featureOrder_${caseId}`;
    console.log(fetchServerRanking(caseId));
    // Speichern der vom Server abgerufenen Daten im LocalStorage
    //saveToLocalStorage(caseId);
  }

  // Stelle sicher, dass die Nachrichten immer aktuell sind, indem sie vom Server geladen werden
  const threadData = await fetchEmailThreads(caseId);
  console.log('Thread data:', threadData);
  if (threadData) {
    messages.value = threadData.messages;

    // Setze den Status des Rankings basierend auf den aktuellen Daten vom Server
    ranked.value = threadData.ranked;
  }

  // Aktualisiere die Farben der Nachrichten im E-Mail-Verlauf
  let lastSender = '';
  let currentColor = 'same-sender';
  messages.value.forEach(message => {
    if (message.sender !== lastSender) {
      currentColor = currentColor === 'same-sender' ? 'different-sender' : 'same-sender';
      lastSender = message.sender;
    }
    senderColors.value[message.sender] = currentColor;
  });
};

onMounted(() => {
  const caseId = route.params.id;
  if (caseId) {
    loadCaseData(caseId);  // Lade zuerst aus LocalStorage, dann (falls nötig) vom Server
  }
});



function getTooltipText(type) {
  const tooltips = {
    abstract_summary: 'Diese Zusammenfassung gibt einen Überblick über den Fall.',
    generated_category: 'Dies ist die generierte Kategorie des Falls.',
    generated_subject: 'Das Feature "Generierter Betreff" beschreibt einen prägnanten und individuellen Betreff, der aus der ersten Nachricht der ratsuchenden Person generiert wurde.\n\nDer Betreff soll den Hauptinhalt der Anfrage klar und verständlich in maximal 6 Wörtern zusammenfassen, ohne unnötige Formalitäten oder zusätzliche Phrasen.\n\nDie Qualität des "Generierter Betreff" wird danach bewertet, wie gut es den Kerninhalt der Erstnachricht präzise und direkt wiedergibt. Ein guter Betreff ermöglicht es dem Beratungsteam, schnell einen Überblick über das Anliegen zu erhalten und effektiv darauf zu reagieren.',
    order_clarification: 'Hier werden Unklarheiten in der Anfrage geklärt.',
    situation_summary: 'Das Feature "Situationsbeschreibung" fasst die aktuelle Situation der ratsuchenden Person in den Bereichen sozial, beruflich und persönlich zusammen.\n\nDiese Zusammenfassungen basieren auf der bisherigen Kommunikation. Zusätzlich können relevante Aspekte in weiteren Feldern wie "zusätzlicher_aspekt" beschrieben werden.\n\nJeder Bereich wird durch Stichpunkte dargestellt, die aus maximal zwei Sätzen bestehen und die wichtigsten Informationen prägnant zusammenfassen.\n\nDie Qualität der "Situationsbeschreibung" wird danach bewertet, wie genau und umfassend sie die soziale, berufliche und persönliche Lage der ratsuchenden Person wiedergibt, ohne unnötige Formalitäten oder Ausschweifungen.',
  };

  return tooltips[type] || 'Allgemeine Informationen zum Feature.';
}

// Beobachte Änderungen in den Routenparametern
watch(() => route.params.id, (newId) => {
  loadCaseData(newId);
}, { immediate: true });

function getColorForText(text) {
  const hash = hashCode(text);

  // Basisfarbe
  const baseHue = 65;
  const baseSaturation = 68;
  const baseLightness = 86;

  // Variationen generieren
  const hueVariation = (hash & 0xFF) % 21 - 10;
  const saturationVariation = ((hash >> 8) & 0xFF) % 31 - 15;
  const lightnessVariation = ((hash >> 16) & 0xFF) % 21 - 10;

  // Variationen anwenden
  const hue = (baseHue + hueVariation + 360) % 360;
  const saturation = Math.max(40, Math.min(100, baseSaturation + saturationVariation));
  const lightness = Math.max(70, Math.min(95, baseLightness + lightnessVariation));

  // In HSL-Farbstring umwandeln
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return hash;
}

function isLongContent(content) {
  // Eine Annahme über die durchschnittliche Anzahl von Zeichen pro Zeile
  const maxCharsPerLine = 80; // Beispielwert, abhängig von der CSS-Breite und Schriftart

  // Prüfe, ob der Inhalt die Schwelle für lange Inhalte überschreitet
  return content.length > (maxCharsPerLine * 3); // Mehr als 3 Zeilen
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
    console.log('Server ranking:', response.data);
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

  // Überprüfe, ob die Struktur korrekt ist
  orderedFeatures.forEach(f => {
    if (!featureMap.has(f.type)) {
      featureMap.set(f.type, {
        type: f.type,
        goodList: [],
        averageList: [],
        badList: [],
        neutralList: []
      });
    }

    f.details.forEach(detail => {
      const featureGroup = featureMap.get(f.type);

      // Verteile die Features basierend auf dem Bucket
      if (detail.bucket === 'Gut') {
        featureGroup.goodList.push(detail);
      } else if (detail.bucket === 'Mittel') {
        featureGroup.averageList.push(detail);
      } else if (detail.bucket === 'Schlecht') {
        featureGroup.badList.push(detail);
      } else {
        featureGroup.neutralList.push(detail);
      }
    });
  });

  // Ordne die Features der groupedFeatures zu
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
  // console.log('Formatting feature content:', type, content);
  switch (type) {
    case 'generated_subject':
      try {
        const subjectObj = JSON.parse(content);
        return subjectObj.Betreff || content;
      } catch (error) {
        console.error('Error parsing generated_subject JSON:', error);
        return content;
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
      return content;
  }
}

function handleDragStart() {
  document.body.classList.add("dragging");
}

function handleDragEnd() {
  document.body.classList.remove("dragging");
  //saveFeatureOrderToLocalStorage();
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

async function navigateToPreviousCase() {
  const currentId = parseInt(route.params.id);
  const rankingThreads = await fetchRankingThreads();

  if (!rankingThreads || rankingThreads.length === 0) {
    console.log("Keine Ranking-Threads verfügbar");
    return;
  }

  // Finde den aktuellen Thread in der Liste
  const currentIndex = rankingThreads.findIndex(thread => thread.thread_id === currentId);

  if (currentIndex === -1 || currentIndex === 0) {
    console.log("Erster Ranking-Thread erreicht oder Thread nicht gefunden");
    return;
  }

  // Navigiere zum vorherigen Ranking-Thread
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

  // Finde den aktuellen Thread in der Liste
  const currentIndex = rankingThreads.findIndex(thread => thread.thread_id === currentId);

  if (currentIndex === -1 || currentIndex === rankingThreads.length - 1) {
    console.log("Letzter Ranking-Thread erreicht oder Thread nicht gefunden");
    return;
  }

  // Navigiere zum nächsten Ranking-Thread
  const nextThread = rankingThreads[currentIndex + 1];
  router.push({ name: 'RankerDetail', params: { id: nextThread.thread_id.toString() } });
}

async function fetchRankingThreads() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/ranking_list`, {
      headers: {
        'Authorization': api_key,
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching ranking threads:', error);
    return [];
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

  const threadId = route.params.id;

  // Erstelle ein Objekt, das die Buckets enthält
  let orderedFeatures = groupedFeatures.value.map(group => {
    return {
      type: group.type,
      details: [
        ...group.goodList.map((detail, index) => ({
          model_name: detail.model_name,
          content: detail.content,
          position: index,
          bucket: 'Gut' // Bucket-Information für "Gut"
        })),
        ...group.averageList.map((detail, index) => ({
          model_name: detail.model_name,
          content: detail.content,
          position: index,
          bucket: 'Mittel' // Bucket-Information für "Mittel"
        })),
        ...group.badList.map((detail, index) => ({
          model_name: detail.model_name,
          content: detail.content,
          position: index,
          bucket: 'Schlecht' // Bucket-Information für "Schlecht"
        }))
      ]
    };
  });

  // Senden der Daten an den Server
  axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/save_ranking/${threadId}`, orderedFeatures, {
    headers: {
      'Authorization': api_key,
      'Content-Type': 'application/json'
    }
  })
    .then(response => {
      console.log('Ranking saved successfully:', response.data);
      alert('Ranking wurde erfolgreich gespeichert!');
      ranked.value = true;
    })
    .catch(error => {
      console.error('Error saving ranking:', error);
      alert('Fehler beim Speichern des Rankings.');
    });
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
  border-top: 1px solid #ddd;
  margin-top: 1vh;
}

.button-class {
  background-color: #d6f6db;
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
  background-color: white; /* Beige Hintergrund */
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
  background: linear-gradient(to bottom, white, transparent); /* Heller Verlauf */
}

.fade-overlay.bottom {
  bottom: 0;
  background: linear-gradient(to top, white, transparent); /* Heller Verlauf */
}

.email-thread {
  overflow-y: auto;
}

.email-message {
  padding: 16px;
  margin-bottom: 10px;
  border-radius: 10px;
  box-shadow: 0px 1px 2px rgba(0,0,0,0.1);
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
  color: #2F4F4F; /* Dunkles Grau-Grün für den Text */
}

.message-timestamp {
  color: #556B2F; /* Graugrüner Farbton für den Zeitstempel */
  font-size: 0.8rem;
}

.message-body p {
  margin: 0;
  color: #2F4F4F; /* Einheitliche Textfarbe */
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
  box-shadow: 0px 1px 2px rgba(0,0,0,0.1);
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
  border: 1px solid #ddd;
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
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: grab;
  position: relative;
}

/* Neutraler Bucket */
.neutral-bucket-container {
  background-color: #f5f5f5;
  min-height: 150px;
  border: 1px solid #bdbdbd;
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
  background-color: white;
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
  background-color: #f5f5f5;
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
