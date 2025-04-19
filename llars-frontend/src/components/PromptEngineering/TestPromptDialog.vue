<template>
  <div v-if="modelValue" class="dialog-overlay">
    <div class="dialog-box test-prompt-dialog">
      <h3>Prompt testen</h3>
      <!-- Beispiele auswählen -->
      <div class="examples-section mb-4">
        <h4>Beispiele:</h4>
        <ul class="examples-list">
          <li v-for="(ex, idx) in examples" :key="idx" :class="{ selected: idx === selectedExampleIndex }">
            <button class="example-select-button" @click="selectedExampleIndex = idx">
              {{ ex.name }}<span v-if="ex.error" class="example-error"> !</span>
            </button>
            <button class="example-toggle-button" @click="expandedExamples[idx] = !expandedExamples[idx]"
                    :title="expandedExamples[idx] ? 'Weniger anzeigen' : 'Mehr anzeigen'">
              <span v-if="expandedExamples[idx]">▲</span>
              <span v-else>▼</span>
            </button>
            <div v-if="expandedExamples[idx]" class="example-content">
              <pre class="sent-prompt">{{ ex.formatted }}</pre>
            </div>
          </li>
        </ul>
      </div>
      <v-switch v-model="testJsonMode" label="JSON Mode" class="mb-4" :color="testJsonMode ? 'success' : 'error'" />
      <div v-if="testJsonMode" class="mb-4">
        <p><strong>JSON Schema:</strong></p>
        <textarea v-model="jsonSchemaInput" rows="6" style="width:100%; font-family: monospace;" placeholder="{}"></textarea>
      </div>
      <p><strong>Gesendetes Prompt:</strong></p>
      <pre class="sent-prompt" v-html="promptHighlighted"></pre>
      <button class="toggle-button" @click="promptCollapsed = !promptCollapsed">
        {{ promptCollapsed ? 'Mehr anzeigen' : 'Weniger anzeigen' }}
      </button>
      <p><strong>Antwort:</strong></p>
      <div class="response-stream" ref="responseContainer">
        <pre>{{ testPromptResponse }}</pre>
        <div v-if="!testResponseComplete" class="stream-indicator">▪▪▪</div>
      </div>
      <div class="dialog-buttons">
        <button class="regen-button" @click="regenerate">Erneut generieren</button>
        <button class="cancel-button" @click="closeDialog">Schließen</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue';
// Hilfsfunktion: formatiert JSON-Daten zur E-Mail-Historie oder markiert Fehler
function formatHistory(data) {
  const requiredTop = ['type','chat_id','institut_id','subject','sender','total_messages','messages'];
  for (const key of requiredTop) {
    if (!(key in data)) return { text: '', error: true };
  }
  if (!Array.isArray(data.messages)) return { text: '', error: true };
  const lines = [];
  for (const msg of data.messages) {
    const requiredMsg = ['message_id','sender','content','timestamp','generated_by'];
    for (const mk of requiredMsg) {
      if (!(mk in msg)) return { text: '', error: true };
    }
    const ts = msg.timestamp;
    const parts = ts.split(' ');
    if (parts.length !== 2) return { text: '', error: true };
    const [date, time] = parts;
    lines.push(`${msg.sender} schrieb am ${date} um ${time}: ${msg.content}`);
  }
  // Füge Leerzeile zwischen einzelnen Nachrichten ein, um die Lesbarkeit zu erhöhen
  return { text: lines.join('\n\n'), error: false };
}
// Beispiele aus JSON-Dateien laden und validieren
const exampleModules = import.meta.glob('./examples/*.json', { eager: true });
const examples = Object.entries(exampleModules).map(([path, module]) => {
  const data = module.default || module;
  const name = data.subject || data.id || path.split('/').pop().replace('.json', '');
  const { text: formatted, error } = formatHistory(data);
  return { name, data, formatted, error };
});
// State für ausgeklappte Beispiele
const expandedExamples = ref(examples.map(() => false));
// Ausgewähltes Beispiel (Index)
const selectedExampleIndex = ref(0);
// Computed für formatierten Text und Fehlerindikator des gewählten Beispiels
const selectedExampleFormatted = computed(() => {
  const ex = examples[selectedExampleIndex.value];
  return ex ? ex.formatted : '';
});
const selectedExampleError = computed(() => {
  const ex = examples[selectedExampleIndex.value];
  return ex ? ex.error : false;
});
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
const jsonSchemaInput = ref('{}');
const promptCollapsed = ref(true);
// Prompt mit formatiertem Beispiel ersetzen
const replacedPrompt = computed(() => {
  const placeholder = '{{complete_email_history}}';
  const exampleText = selectedExampleFormatted.value;
  return props.prompt.split(placeholder).join(exampleText);
});
// QoL: Komprimierte Anzeige des ersetzten Prompts (erste und letzte 50 Zeichen)
const collapsedPrompt = computed(() => {
  const text = replacedPrompt.value;
  if (text.length <= 100) return text;
  const firstPart = text.slice(0, 50);
  const lastPart = text.slice(-50);
  return `${firstPart}...${lastPart}`;
});

const testPromptResponse = ref('');
const testResponseComplete = ref(false);
// Ref auf das Container-Element, in dem der LLM-Output scrollt
const responseContainer = ref(null);
/** HTML-Escaping */
function escapeHtml(str) {
  return str.replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
/** Regex-Escaping */
function escapeRegex(str) {
  return str.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
}
/**
 * Hebt im Prompt den eingesetzten Beispieltext hervor
 */
const promptHighlighted = computed(() => {
  const text = promptCollapsed.value ? collapsedPrompt.value : replacedPrompt.value;
  const exampleText = selectedExampleFormatted.value;
  // Escape alles
  const escaped = escapeHtml(text);
  if (!exampleText) {
    return escaped.replace(/\n/g, '<br/>');
  }
  const escapedExample = escapeHtml(exampleText);
  const pattern = new RegExp(escapeRegex(escapedExample), 'g');
  const highlighted = escaped.replace(pattern, `<span class=\"example-highlight\">${escapedExample}</span>`);
  return highlighted.replace(/\n/g, '<br/>');
});
// Flag, ob automatisch nach unten gescrollt werden soll
const follow = ref(true);
// Scroll-Handler, pausiert Follow, wenn der User manuell scrollt
watch(responseContainer, (el) => {
  if (el) {
    el.addEventListener('scroll', () => {
      const threshold = 10;
      // Wenn innerhalb threshold zum unteren Ende, Follow=true, sonst false
      if (el.scrollHeight - el.scrollTop - el.clientHeight <= threshold) {
        follow.value = true;
      } else {
        follow.value = false;
      }
    });
  }
});
/**
 * Sendet das Prompt an den Server, ersetzt {{complete_email_history}} mit dem ausgewählten Beispiel
 */
function sendTestPrompt() {
  const placeholder = '{{complete_email_history}}';
  const exampleText = selectedExampleFormatted.value;
  // Basis-Prompt mit Platzhalter ersetzt
  let promptString = props.prompt.split(placeholder).join(exampleText);

  // Debug logging: JSON mode and prompt to send
  console.log('[TestPromptDialog] Sending test prompt. JSON Mode:', testJsonMode.value);
  console.log('[TestPromptDialog] Prompt to send:', promptString);
  let schemaObj = {};
  if (testJsonMode.value) {
    try {
      schemaObj = JSON.parse(jsonSchemaInput.value);
    } catch (e) {
      console.error('[TestPromptDialog] Invalid JSON Schema:', e);
    }
  }
  chatSocket.emit('test_prompt_stream', {
    prompt: promptString,
    jsonMode: testJsonMode.value,
    schema: schemaObj
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
// Wenn JSON Mode umgeschaltet wird: Prompt neu senden
watch(testJsonMode, (newVal) => {
  console.log('[TestPromptDialog] JSON Mode toggled:', newVal);
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
    // Automatisch scrollen, wenn Follow nicht pausiert
    if (follow.value && responseContainer.value) {
      responseContainer.value.scrollTop = responseContainer.value.scrollHeight;
    }
  });
  if (data.complete) {
    testResponseComplete.value = true;
  }
});
function regenerate() {
  testPromptResponse.value = '';
  testResponseComplete.value = false;
  sendTestPrompt();
}

function closeDialog() {
  emit('update:modelValue', false);
}
</script>

<style scoped>
.example-error {
  color: #e74c3c;
  font-weight: bold;
  margin-left: 4px;
}
.sent-prompt {
  white-space: pre-wrap;       /* Umbrüche bei Zeilenende und Whitespaces erlauben */
  word-break: normal;         /* Keine Zwangsumbrüche innerhalb von Wörtern */
  overflow-wrap: break-word;  /* Lange Wörter bei Bedarf umbrechen */
  hyphens: auto;              /* Silbentrennung, falls verfügbar */
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

.dialog-buttons .regen-button {
  background-color: #3498db;
  color: #fff;
  transition: background-color 0.2s;
}
.dialog-buttons .regen-button:hover {
  background-color: #217dbb;
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
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.examples-list li {
  display: inline-flex;
  align-items: center;
  background: #f1f3f5;
  border-radius: 24px;
  padding: 4px;
}
.examples-list li.selected .example-select-button {
  background-color: #3498db;
  color: #fff;
}
.example-select-button {
  background: none;
  border: none;
  padding: 8px 12px;
  border-radius: 16px;
  cursor: pointer;
  color: #333;
  transition: background-color 0.2s;
}
.example-select-button:hover {
  background-color: #e2e6ea;
}
.example-toggle-button {
  background: none;
  border: none;
  padding: 8px;
  border-radius: 50%;
  cursor: pointer;
  color: #333;
  transition: background-color 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 4px;
}
.example-toggle-button:hover {
  background-color: #e2e6ea;
}
.example-content {
  background: #eaf6ea;
  padding: 8px;
  border: 1px solid #81b68b;
  border-radius: 4px;
  margin-top: 4px;
  max-height: 200px;
  overflow: auto;
}
/* Highlight für eingesetzte Beispieldaten */
:deep(.example-highlight) {
  background-color: #81b68b;
}
</style>
