<template>
  <v-container fluid class="fill-height">
    <v-row no-gutters style="height: 100%">
      <!-- Main Content Area - Blocks -->
      <v-col cols="9" class="pr-4">
        <h1 class="text-h4 mb-6">
          {{ promptName }}
          <v-chip
            v-if="isSharedPrompt"
            color="info"
            small
            class="ml-2"
          >
            Geteilt von {{ owner }}
          </v-chip>
        </h1>
        <div class="blocks-container">
          <draggable
            v-model="blocks"
            class="blocks-list"
            item-key="name"
            handle=".drag-handle"
            :disabled="isSharedPrompt"
          >
            <template #item="{ element, index }">
              <v-card class="mb-4">
                <v-card-title class="d-flex align-center">
                  <v-icon
                    class="mr-2"
                    :class="{ 'cursor-move': !isSharedPrompt, 'drag-handle': !isSharedPrompt }"
                  >
                    {{ isSharedPrompt ? 'mdi-text' : 'mdi-drag' }}
                  </v-icon>
                  {{ element.name }}
                  <v-spacer></v-spacer>
                  <v-btn
                    icon
                    @click="removeBlock(index)"
                    v-if="!isSharedPrompt"
                  >
                    <v-icon color="error">mdi-delete</v-icon>
                  </v-btn>
                </v-card-title>
                <v-card-text>
                  <v-textarea
                    v-model="element.content"
                    outlined
                    hide-details
                    rows="4"
                    class="prompt-textarea"
                    :readonly="isSharedPrompt"
                  ></v-textarea>
                </v-card-text>
              </v-card>
            </template>
          </draggable>
        </div>
      </v-col>

      <!-- Sidebar - Tools -->
      <v-col cols="3" class="sidebar">
        <!-- Template Selection Card - nur für nicht geteilte Prompts -->
        <v-card class="mb-4" v-if="!isSharedPrompt">
          <v-card-title>Templates</v-card-title>
          <v-card-text>
            <v-btn
              block
              color="primary"
              @click="showTemplateDialog = true"
              class="mb-4"
            >
              <v-icon left>mdi-file-document-multiple</v-icon>
              Template laden
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- New Block Card - nur für nicht geteilte Prompts -->
        <v-card class="mb-4" v-if="!isSharedPrompt">
          <v-card-title>Neuer Baustein</v-card-title>
          <v-card-text>
            <v-form ref="newBlockForm" v-model="isFormValid">
              <v-text-field
                v-model="newBlockName"
                label="Name"
                :rules="[rules.required]"
                dense
                class="mb-2"
              ></v-text-field>
              <v-btn
                block
                color="primary"
                :disabled="!isFormValid"
                @click="addBlock"
              >
                <v-icon left>mdi-plus</v-icon>
                Hinzufügen
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- Actions Card -->
        <v-card>
          <v-card-title>Aktionen</v-card-title>
          <v-card-text>
            <!-- Speichern-Button nur für nicht geteilte Prompts -->
            <v-btn
              v-if="!isSharedPrompt"
              block
              color="success"
              class="mb-2"
              @click="savePrompt"
            >
              <v-icon left>mdi-content-save</v-icon>
              Speichern
            </v-btn>

            <v-btn
              block
              color="info"
              class="mb-2"
              @click="previewPrompt"
            >
              <v-icon left>mdi-eye</v-icon>
              Vorschau
            </v-btn>

            <v-btn
              block
              color="secondary"
              class="mb-2"
              @click="downloadPrompt"
            >
              <v-icon left>mdi-download</v-icon>
              Als JSON herunterladen
            </v-btn>

            <v-btn
              block
              color="grey"
              @click="goBack"
            >
              <v-icon left>mdi-arrow-left</v-icon>
              Zurück zur Übersicht
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- Share Card - nur für eigene, nicht geteilte Prompts -->
        <v-card class="mt-4" v-if="!isSharedPrompt">
          <v-card-title>Prompt teilen</v-card-title>
          <v-card-text>
            <v-form ref="shareForm" v-model="isShareFormValid">
              <v-text-field
                v-model="shareWithUser"
                label="Benutzername"
                :rules="[rules.required]"
                dense
                class="mb-2"
                placeholder="Mit Benutzer teilen"
              ></v-text-field>
              <v-btn
                block
                color="info"
                :disabled="!isShareFormValid"
                @click="sharePrompt"
              >
                <v-icon left>mdi-share</v-icon>
                Teilen
              </v-btn>
            </v-form>

            <!-- Shared Users List -->
            <template v-if="sharedUsers.length > 0">
              <v-divider class="my-3"></v-divider>
              <div class="text-subtitle-2 mb-2">
                Geteilt mit:
                <v-chip
                  small
                  color="info"
                  class="ml-2"
                >
                  {{ sharedUsers.length }}
                </v-chip>
              </div>
              <v-list dense>
                <v-list-item
                  v-for="user in sharedUsers"
                  :key="user"
                  class="px-0"
                >
                  <v-list-item-icon class="mr-2">
                    <v-icon small color="info">mdi-account</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>{{ user }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </v-list>
            </template>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Preview Dialog -->
    <v-dialog v-model="showPreview" max-width="800">
      <v-card>
        <v-card-title>Vorschau</v-card-title>
        <v-card-text>
          <pre class="preview-content">{{ compiledPrompt }}</pre>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="showPreview = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Template Selection Dialog -->
    <v-dialog v-model="showTemplateDialog" max-width="600">
      <v-card>
        <v-card-title>Template auswählen</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item
              v-for="template in templates"
              :key="template.id"
              @click="loadTemplate(template.id)"
            >
              <v-list-item-title>{{ template.name }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="showTemplateDialog = false">Abbrechen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import draggable from 'vuedraggable';

const templates = [
  {
    id: 'standard',
    name: 'Standard Prompt Template',
    blocks: [
      { name: 'LLM Role Definition', content: 'Defines the role of the LLM in a specific situation.' },
      { name: 'Context', content: 'Provides contextual information and specific requirements to ensure appropriate responses.' },
      { name: 'Task Definition', content: 'Describes what the language model is supposed to do.' },
      { name: 'Input Format', content: 'Explains the structure of the input data.' },
      { name: 'Output Format', content: 'Explains the expected output format.' },
      { name: 'Avoid Formalities', content: 'Specifies wording to be avoided.' },
      { name: 'Data', content: 'The data to be processed should be inserted into this section in the formatting specified above.' },
      { name: 'Role Reminder', content: 'Reminds the model of its role during the task.' },
      { name: 'Task Reminder', content: 'Reminds the model of the specific task to maintain focus and goal orientation.' }
    ]
  },
  {
    id: 'concise',
    name: 'Concise Mode Template',
    blocks: [
      { name: 'Mode Definition', content: 'Claude is operating in Concise Mode. In this mode, Claude aims to reduce its output tokens while maintaining its helpfulness, quality, completeness, and accuracy.' },
      { name: 'Response Guidelines', content: 'Claude provides answers to questions without much unneeded preamble or postamble. It focuses on addressing the specific query or task at hand, avoiding tangential information unless helpful for understanding or completing the request. If it decides to create a list, Claude focuses on key information instead of comprehensive enumeration.' },
      { name: 'Tone and Style', content: 'Claude maintains a helpful tone while avoiding excessive pleasantries or redundant offers of assistance.' },
      { name: 'Evidence and Detail', content: 'Claude provides relevant evidence and supporting details when substantiation is helpful for factuality and understanding of its response. For numerical data, Claude includes specific figures when important to the answer\'s accuracy.' },
      { name: 'Output Quality', content: 'For code, artifacts, written content, or other generated outputs, Claude maintains the exact same level of quality, completeness, and functionality as when NOT in Concise Mode. There should be no impact to these output types.' },
      { name: 'Quality Assurance', content: 'Claude does not compromise on completeness, correctness, appropriateness, or helpfulness for the sake of brevity.' },
      { name: 'Flexibility', content: 'If the human requests a long or detailed response, Claude will set aside Concise Mode constraints and provide a more comprehensive answer. If the human appears frustrated with Claude\'s conciseness, repeatedly requests longer or more detailed responses, or directly asks about changes in Claude\'s response style, Claude informs them that it\'s currently in Concise Mode and explains that Concise Mode can be turned off via Claude\'s UI if desired. Besides these scenarios, Claude does not mention Concise Mode.' }
    ]
  }
];

const route = useRoute();
const router = useRouter();
const promptId = route.params.id;

const promptName = ref('');
const blocks = ref([]);
const newBlockName = ref('');
const isFormValid = ref(false);
const showPreview = ref(false);
const showTemplateDialog = ref(false);

const sharedUsers = ref([]);

const rules = {
  required: (value) => !!value || 'Pflichtfeld',
};

const compiledPrompt = computed(() => {
  return blocks.value
    .map(block => block.content)
    .filter(content => content.trim())
    .join('\n\n');
});

function loadTemplate(templateId) {
  const template = templates.find(t => t.id === templateId);
  if (template) {
    // Ask for confirmation if there are existing blocks
    if (blocks.value.length > 0) {
      if (!confirm('Bestehende Blöcke werden ersetzt. Fortfahren?')) {
        return;
      }
    }
    blocks.value = [...template.blocks];
  }
  showTemplateDialog.value = false;
}

async function savePrompt() {
  try {
    const api_key = localStorage.getItem('api_key');
    // Create content object with blocks and their positions
    const content = {
      blocks: blocks.value.reduce((acc, block, index) => {
        acc[block.name] = {
          content: block.content,
          position: index
        };
        return acc;
      }, {})
    };

    await axios.put(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}`,
      {content},
      {
        headers: {
          Authorization: api_key,
          'Content-Type': 'application/json',
        },
      }
    );
    alert('Prompt wurde erfolgreich gespeichert!');
  } catch (error) {
    console.error('Fehler beim Speichern des Prompts:', error);
    alert('Fehler beim Speichern des Prompts.');
  }
}

// Erweiterte fetchPrompt Funktion
async function fetchPrompt() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}`,
      {
        headers: {Authorization: api_key},
      }
    );

    promptName.value = response.data.name;
    isSharedPrompt.value = response.data.is_shared;
    sharedUsers.value = response.data.shared_with || [];

    if (response.data.content?.blocks) {
      blocks.value = Object.entries(response.data.content.blocks)
        .map(([name, data]) => ({
          name,
          content: data.content,
          position: data.position
        }))
        .sort((a, b) => a.position - b.position)
        .map(({ name, content }) => ({
          name,
          content
        }));
    }
  } catch (error) {
    console.error('Fehler beim Abrufen des Prompts:', error);
    alert('Fehler beim Laden des Prompts.');
  }
}

async function downloadPrompt() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios({
      url: `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}/download`,
      method: 'GET',
      headers: {
        'Authorization': api_key
      },
      responseType: 'blob' // Wichtig für den Download
    });

    // Erstelle einen Blob aus der Response
    const blob = new Blob([response.data], { type: 'application/json' });

    // Erstelle einen temporären Link zum Download
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${promptName.value}.json`; // Verwendet den Prompt-Namen für die Datei

    // Trigger download
    document.body.appendChild(link);
    link.click();

    // Cleanup
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
  } catch (error) {
    console.error('Fehler beim Herunterladen des Prompts:', error);
    alert('Fehler beim Herunterladen des Prompts.');
  }
}

// Neue Refs für das Sharing
const shareWithUser = ref('');
const isShareFormValid = ref(false);
const isSharedPrompt = ref(false);

async function sharePrompt() {
  try {
    const api_key = localStorage.getItem('api_key');
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}/share`,
      {
        shared_with: shareWithUser.value
      },
      {
        headers: {
          'Authorization': api_key,
          'Content-Type': 'application/json',
        },
      }
    );

    // Nach erfolgreichem Teilen die Prompt-Daten neu laden
    await fetchPrompt();

    alert(`Prompt wurde erfolgreich mit ${shareWithUser.value} geteilt!`);
    shareWithUser.value = ''; // Feld zurücksetzen
  } catch (error) {
    console.error('Fehler beim Teilen des Prompts:', error);
    alert(error.response?.data?.error || 'Fehler beim Teilen des Prompts');
  }
}

function goBack() {
  router.push('/promptengineering');
}

function addBlock() {
  blocks.value.push({name: newBlockName.value, content: ''});
  newBlockName.value = '';
}

function removeBlock(index) {
  blocks.value.splice(index, 1);
}

function previewPrompt() {
  showPreview.value = true;
}

onMounted(fetchPrompt);
</script>

<style scoped>
.blocks-container {
  height: calc(100vh - 120px);
  overflow-y: auto;
  padding-right: 16px;
}

.blocks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar {
  height: calc(100vh - 32px);
  overflow-y: auto;
  position: sticky;
  top: 16px;
}

.cursor-move {
  cursor: move;
}

.prompt-textarea {
  font-family: 'Roboto Mono', monospace;
}

.preview-content {
  white-space: pre-wrap;
  font-family: 'Roboto Mono', monospace;
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
}
</style>
