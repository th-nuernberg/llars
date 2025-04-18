<template>
  <div v-if="modelValue" class="dialog-overlay">
    <div class="dialog-box test-prompt-dialog">
      <h3>Prompt testen</h3>
      <!-- Beispiele auswählen -->
      <div class="examples-section mb-4">
        <h4>Beispiele:</h4>
        <ul class="examples-list">
          <li v-for="(ex, idx) in examples" :key="idx" :class="{ selected: idx === selectedExampleIndex }">
            <button class="example-select-button" @click="selectedExampleIndex = idx">{{ ex.name }}</button>
            <button class="example-toggle-button" @click="expandedExamples[idx] = !expandedExamples[idx]">
              {{ expandedExamples[idx] ? 'Weniger anzeigen' : 'Mehr anzeigen' }}
            </button>
            <div v-if="expandedExamples[idx]" class="example-content"><pre>{{ JSON.stringify(ex.data, null, 2) }}</pre></div>
          </li>
        </ul>
      </div>
      <v-switch v-model="testJsonMode" label="JSON Mode" class="mb-4" :color="testJsonMode ? 'success' : 'error'" />
      <p><strong>Gesendetes Prompt:</strong></p>
      <pre class="sent-prompt">{{ promptCollapsed ? collapsedPrompt : replacedPrompt }}</pre>
      <button class="toggle-button" @click="promptCollapsed = !promptCollapsed">
        {{ promptCollapsed ? 'Mehr anzeigen' : 'Weniger anzeigen' }}
      </button>
      <p><strong>Antwort:</strong></p>
      <div class="response-stream" ref="responseContainer">
        <pre>{{ testPromptResponse }}</pre>
        <div v-if="!testResponseComplete" class="stream-indicator">▪▪▪</div>
      </div>
      <div class="dialog-buttons">
        <button class="cancel-button" @click="closeDialog">Schließen</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue';
// Beispiele aus JSON-Dateien laden
const exampleModules = import.meta.glob('./examples/*.json', { eager: true });
const examples = Object.entries(exampleModules).map(([path, module]) => {
  const data = module.default || module;
  const name = data.subject || data.id || path.split('/').pop().replace('.json', '');
  return { name, data };
});
// State für ausgeklappte Beispiele
const expandedExamples = ref(examples.map(() => false));
// Ausgewähltes Beispiel
const selectedExampleIndex = ref(0);
// Computed für gerade ausgewähltes Beispiel
const selectedExampleData = computed(() => examples[selectedExampleIndex.value].data);
import { io } from 'socket.io-client';

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  prompt: {
    type: String,
    required: true
  }
});
const emit = defineEmits(['update:modelValue']);

const username = localStorage.getItem('username') || 'Unbekannter Benutzer';
const chatSocket = io(import.meta.env.VITE_API_BASE_URL, {
  path: '/socket.io/',
  transports: ['websocket'],
  query: { username },
  headers: { 'Content-Type': 'application/json; charset=utf-8' }
});

const testJsonMode = ref(true);
const promptCollapsed = ref(true);
// Prompt mit Beispiel ersetzen
const replacedPrompt = computed(() => {
  const placeholder = '{{complete_email_history}}';
  const exampleJson = JSON.stringify(selectedExampleData.value);
  return props.prompt.split(placeholder).join(exampleJson);
});
// QoL: Komprimierte Anzeige des ersetzten Prompts
const collapsedPrompt = computed(() => {
  const lines = replacedPrompt.value.split('\n');
  if (lines.length <= 3) return replacedPrompt.value;
  return lines.slice(0, 3).join('\n') + '\n...';
});

const testPromptResponse = ref('');
const testResponseComplete = ref(false);
const responseContainer = ref(null);
/**
 * Sendet das Prompt an den Server, ersetzt {{complete_email_history}} mit dem ausgewählten Beispiel
 */
function sendTestPrompt() {
  const placeholder = '{{complete_email_history}}';
  const exampleJson = JSON.stringify(selectedExampleData.value);
  const promptString = props.prompt.split(placeholder).join(exampleJson);
  chatSocket.emit('test_prompt_stream', {
    prompt: promptString,
    jsonMode: testJsonMode.value
  });
}

// Wenn Dialog geöffnet wird: Ausgabe zurücksetzen und Prompt mit Beispiel senden
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    testPromptResponse.value = '';
    testResponseComplete.value = false;
    testJsonMode.value = true;
    promptCollapsed.value = true;
    // Prompt mit ausgewähltem Beispiel senden
    sendTestPrompt();
  }
});
// Wenn ein anderes Beispiel ausgewählt wird: Ausgabe zurücksetzen und neues Prompt senden
watch(selectedExampleIndex, (newIdx) => {
  if (props.modelValue) {
    testPromptResponse.value = '';
    testResponseComplete.value = false;
    promptCollapsed.value = true;
    sendTestPrompt();
  }
});

chatSocket.on('test_prompt_response', (data) => {
  testPromptResponse.value += data.content;
  nextTick(() => {
    if (responseContainer.value) {
      responseContainer.value.scrollTop = responseContainer.value.scrollHeight;
    }
  });
  if (data.complete) {
    testResponseComplete.value = true;
  }
});

function closeDialog() {
  emit('update:modelValue', false);
}
</script>

<style scoped>
.sent-prompt {
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-all;
  max-width: 100%;
}
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog-box.test-prompt-dialog {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 80%;
  max-height: 80%;
  overflow: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.dialog-box h3 {
  margin: 0 0 16px 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
}
.dialog-box p {
  margin: 0 0 20px 0;
  color: #4b5563;
  font-size: 0.95rem;
  line-height: 1.5;
}
.response-stream {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  margin-bottom: 12px;
}
.stream-indicator {
  margin-top: 8px;
  font-weight: bold;
}
.toggle-button {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  margin-bottom: 12px;
  padding: 0;
}
.toggle-button:hover {
  text-decoration: underline;
}
.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.dialog-buttons button {
  padding: 8px 14px;
  border: none;
  border-radius: 16px 4px 16px 4px;
  cursor: pointer;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dialog-buttons .cancel-button {
  background-color: #9e9e9e;
  color: #fff;
  transition: background-color 0.2s;
}
.dialog-buttons .cancel-button:hover {
  background-color: #7e7e7e;
}
/* Styles für Beispiele-Auswahl */
.examples-section {
  border-bottom: 1px solid #ddd;
  padding-bottom: 12px;
  margin-bottom: 16px;
}
.examples-list {
  list-style: none;
  padding: 0;
}
.examples-list li {
  margin-bottom: 8px;
}
.examples-list li.selected .example-select-button {
  font-weight: bold;
}
.example-select-button {
  background: #eef;
  border: 1px solid #ccd;
  padding: 4px 8px;
  margin-right: 8px;
  cursor: pointer;
  border-radius: 4px;
}
.example-select-button:hover {
  background: #dde;
}
.example-toggle-button {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  margin-left: 4px;
}
.example-content {
  background: #f9f9f9;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  margin-top: 4px;
  max-height: 200px;
  overflow: auto;
}
</style>