<template>
  <v-container fluid class="fill-height">
    <v-row no-gutters style="height: 100%">
      <!-- Main Content Area - Blocks -->
      <v-col cols="9" class="pr-4">
        <div class="prompt-title-container">
          <div class="d-flex align-center">
            <div class="collaborators-list" v-if="otherCollaborators.length > 0">
              <v-chip
                v-for="collaborator in otherCollaborators"
                :key="collaborator.username"
                small
                class="mr-2"
                :style="{ backgroundColor: getCursorColor(collaborator.user_id), color: 'white' }"
              >
                {{ collaborator.username }}
              </v-chip>
            </div>
            <template v-if="isEditing">
              <v-text-field
                v-model="editedName"
                :rules="[rules.required]"
                hide-details
                class="prompt-edit-field text-h4"
                @keyup.enter="saveName"
              ></v-text-field>
              <div class="edit-actions">
                <v-btn
                  text
                  x-small
                  color="success"
                  class="edit-btn mr-1"
                  @click="saveName"
                >
                  <v-icon small>mdi-check</v-icon>
                </v-btn>
                <v-btn
                  text
                  x-small
                  color="error"
                  class="edit-btn"
                  @click="cancelEdit"
                >
                  <v-icon small>mdi-close</v-icon>
                </v-btn>
              </div>
            </template>
            <template v-else>
              <div class="prompt-title-wrapper">
                <h1 class="text-h4 prompt-title">{{ promptName }}</h1>
                <v-btn
                  text
                  x-small
                  class="edit-title-btn ml-2"
                  @click="startEdit"
                  v-if="hasEditPermission"
                >
                  <v-icon small>mdi-pencil</v-icon>
                </v-btn>
              </div>
            </template>
            <v-chip
              v-if="isSharedPrompt"
              color="info"
              small
              class="ml-2"
            >
              Geteilt von {{ owner }}
            </v-chip>
          </div>
        </div>

        <div class="blocks-container">
          <draggable
            v-model="blocks"
            class="blocks-list"
            item-key="name"
            handle=".drag-handle"
            :disabled="!hasEditPermission"
          >
            <template #item="{ element, index }">
              <v-card class="mb-4">
                <v-card-title class="d-flex align-center">
                  <v-icon
                    class="mr-2"
                    :class="{ 'cursor-move': hasEditPermission, 'drag-handle': hasEditPermission }"
                  >
                    {{ hasEditPermission ? 'mdi-drag' : 'mdi-text' }}
                  </v-icon>
                  {{ element.name }}
                  <v-spacer></v-spacer>
                  <v-btn
                    icon
                    @click="removeBlock(index)"
                    v-if="hasEditPermission"
                  >
                    <v-icon color="error">mdi-delete</v-icon>
                  </v-btn>
                </v-card-title>
                <v-card-text>
                  <div class="textarea-container">
                    <v-textarea
                      v-model="element.content"
                      outlined
                      hide-details
                      rows="4"
                      class="prompt-textarea"
                      :readonly="!hasEditPermission"
                      :data-block-id="element.name"
                      @input="value => handleTextChange(element.name, value)"
                      @click="updateCursorPosition($event.target, element.name)"
                      @keyup="updateCursorPosition($event.target, element.name)"
                      @select="updateCursorPosition($event.target, element.name)"
                    ></v-textarea>
                    <!-- Remote Cursors für diesen Block -->
                    <div
                      v-for="cursor in getCursorsForBlock(element.name)"
                      :key="cursor.user_id"
                      class="remote-cursor"
                      :style="calculateCursorPosition(cursor)"
                    >
                      <div class="cursor-label" :style="{ backgroundColor: getCursorColor(cursor.user_id) }">
                        {{ getUsernameFromId(cursor.user_id) }}
                      </div>
                      <div class="cursor-line" :style="{ backgroundColor: getCursorColor(cursor.user_id) }"></div>
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </template>
          </draggable>
        </div>
      </v-col>

      <!-- Sidebar - Tools -->
      <v-col cols="3" class="sidebar">
        <!-- Template Selection Card -->
        <v-card class="mb-4" v-if="hasEditPermission">
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


        <!-- New Block Card -->
        <v-card class="mb-4" v-if="hasEditPermission">
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
            <v-btn
              v-if="hasEditPermission"
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

            <!-- New Upload Button -->
            <v-btn
              v-if="hasEditPermission"
              block
              color="primary"
              class="mb-2"
              @click="$refs.fileInput.click()"
            >
              <v-icon left>mdi-upload</v-icon>
              JSON hochladen
            </v-btn>
            <input
              ref="fileInput"
              type="file"
              accept=".json"
              style="display: none"
              @change="handleFileUpload"
            >
            <v-dialog v-model="showUploadDialog">
            <v-card>
              <v-card-title>JSON importieren</v-card-title>
              <v-card-text>
                Wie möchten Sie die Blöcke aus der JSON-Datei importieren?
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="error" @click="cancelUpload">Abbrechen</v-btn>
                <v-btn color="warning" @click="mergeBlocks">Zu bestehenden hinzufügen</v-btn>
                <v-btn color="primary" @click="replaceBlocks">Bestehende ersetzen</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
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
        <!-- Share Card -->
<!-- Share Card -->
<v-card class="mt-4" v-if="owner === currentUser">
  <v-card-title>Prompt teilen</v-card-title>
  <v-card-text>
    <v-form ref="shareForm" v-model="isShareFormValid">
      <v-text-field
        v-model="shareWithUser"
        label="Benutzername"
        dense
        class="mb-2"
        placeholder="Mit Benutzer teilen"
      />
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
      <v-list density="compact">
        <v-list-item
          v-for="user in sharedUsers"
          :key="user"
          :value="user"
        >
          <template v-slot:prepend>
            <v-icon size="small" color="info">mdi-account</v-icon>
          </template>
          {{ user }}
          <template v-slot:append>
            <v-btn
              icon="mdi-delete"
              size="small"
              color="error"
              variant="text"
              @click="unsharePrompt(user)"
            >
              <v-icon size="small">mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-list-item>
      </v-list>
    </template>
  </v-card-text>
</v-card>

<!-- Read-only Shared Users List for shared users -->
<v-card class="mt-4" v-else-if="sharedUsers.length > 0">
  <v-card-title>Geteilt mit</v-card-title>
  <v-card-text>
    <v-list density="compact">
      <v-list-item
        v-for="user in sharedUsers"
        :key="user"
        :value="user"
      >
        <template v-slot:prepend>
          <v-icon size="small" color="info">mdi-account</v-icon>
        </template>
        {{ user }}
      </v-list-item>
    </v-list>
  </v-card-text>
</v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useCollaborativeEditing } from './collaborative';
import axios from 'axios';
import draggable from 'vuedraggable';
const blocks = ref([]);




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
const { collaborators, cursors, updateCursorPosition, handleTextChange } =
  useCollaborativeEditing(promptId, blocks);
// Füge diese computed property zu den anderen computed properties hinzu
const currentUser = computed(() => localStorage.getItem('username'));


const promptName = ref('');

const newBlockName = ref('');
const isFormValid = ref(false);
const showPreview = ref(false);
const showTemplateDialog = ref(false);

const sharedUsers = ref([]);
const owner = ref('');

const shareWithUser = ref('');
const isShareFormValid = ref(false);
const isSharedPrompt = ref(false);

const isEditing = ref(false);
const editedName = ref('');

const rules = {
  required: (value) => !!value || 'Pflichtfeld',
};

const compiledPrompt = computed(() => {
  return blocks.value
    .map(block => block.content)
    .filter(content => content.trim())
    .join('\n\n');
});

function getCursorPosition(cursor) {
  // Finde den Block anhand der cursor.block_id
  const blockIndex = blocks.value.findIndex(b => b.name === cursor.block_id);
  if (blockIndex === -1) {
    return {}; // Keine Position, wenn Block nicht gefunden
  }

  // Hier könntest du logischerweise die genaue Position im Text berechnen.
  // Für ein funktionierendes Minimum kann man erstmal einen statischen Wert zurückgeben.
  return {
    position: 'relative',
    top: `${blockIndex * 30}px`,
    left: '10px'
  };
}


// Neue Refs für das Hochladen
const fileInput = ref(null);
const showUploadDialog = ref(false);
const uploadedBlocks = ref(null);

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
    owner.value = response.data.owner || '';

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
    console.log({
  currentUser: localStorage.getItem('username'),
  owner: owner.value,
  isShared: isSharedPrompt.value,
  sharedUsers: sharedUsers.value,
  hasPermission: hasEditPermission.value
});
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
      responseType: 'blob'
    });

    const blob = new Blob([response.data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${promptName.value}.json`;

    document.body.appendChild(link);
    link.click();

    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
  } catch (error) {
    console.error('Fehler beim Herunterladen des Prompts:', error);
    alert('Fehler beim Herunterladen des Prompts.');
  }
}

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

    await fetchPrompt();

    alert(`Prompt wurde erfolgreich mit ${shareWithUser.value} geteilt!`);
    shareWithUser.value = '';
  } catch (error) {
    console.error('Fehler beim Teilen des Prompts:', error);
    alert(error.response?.data?.error || 'Fehler beim Teilen des Prompts');
  }
}

function startEdit() {
  editedName.value = promptName.value;
  isEditing.value = true;
}

function cancelEdit() {
  editedName.value = '';
  isEditing.value = false;
}

async function saveName() {
  if (!editedName.value.trim()) {
    return;
  }

  try {
    const api_key = localStorage.getItem('api_key');
    await axios.put(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}/rename`,
      { name: editedName.value },
      {
        headers: {
          Authorization: api_key,
          'Content-Type': 'application/json',
        },
      }
    );

    promptName.value = editedName.value;
    isEditing.value = false;
  } catch (error) {
    console.error('Fehler beim Umbenennen des Prompts:', error);
    alert(error.response?.data?.error || 'Fehler beim Umbenennen des Prompts');
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

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = JSON.parse(e.target.result);

        // Prüfen, ob die Struktur content.blocks existiert
        if (content?.content?.blocks) {
          uploadedBlocks.value = Object.entries(content.content.blocks)
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
        } else {
          // Falls nicht vorhanden, alle Top-Level-Keys als Blöcke interpretieren
          const keys = Object.keys(content);
          uploadedBlocks.value = keys.map((key, index) => ({
            name: key,
            content: content[key],
            position: index
          }));
        }

        showUploadDialog.value = true;
      } catch (error) {
        alert('Fehler beim Parsen der JSON-Datei: ' + error.message);
      }
    };
    reader.readAsText(file);
  } catch (error) {
    console.error('Fehler beim Lesen der Datei:', error);
    alert('Fehler beim Lesen der Datei.');
  }
  event.target.value = '';
}

async function unsharePrompt(username) {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}/unshare`,
      { unshare_with: username },
      {
        headers: {
          Authorization: api_key,
          'Content-Type': 'application/json',
        },
      }
    );

    // Erfolgsmeldung anzeigen
    alert(`Prompt wurde erfolgreich für ${username} entfernt.`);

    // Aktualisiere die Liste der geteilten Benutzer
    const index = sharedUsers.value.indexOf(username);
    if (index > -1) {
      sharedUsers.value.splice(index, 1);
    }
  } catch (error) {
    console.error('Fehler beim Entfernen der Freigabe:', error);
    alert(error.response?.data?.error || 'Fehler beim Entfernen der Freigabe.');
  }
}


function mergeBlocks() {
  if (!uploadedBlocks.value) return;
  blocks.value = [...blocks.value, ...uploadedBlocks.value];
  uploadedBlocks.value = null;
  showUploadDialog.value = false;
}

function replaceBlocks() {
  if (!uploadedBlocks.value) return;
  blocks.value = [...uploadedBlocks.value];
  uploadedBlocks.value = null;
  showUploadDialog.value = false;
}

function cancelUpload() {
  uploadedBlocks.value = null;
  showUploadDialog.value = false;
}

onMounted(fetchPrompt);

const otherCollaborators = computed(() => {
  const currentUser = localStorage.getItem('username');
  return collaborators.value.filter(collaborator =>
    collaborator.username !== currentUser
  );
});

const hasEditPermission = computed(() => {
  const currentUser = localStorage.getItem('username');
  if (!isSharedPrompt.value) {
    // Wenn es kein geteilter Prompt ist, darf nur der Besitzer editieren
    return owner.value === currentUser;
  }
  // Bei einem geteilten Prompt dürfen Besitzer und geteilte User editieren
  return owner.value === currentUser || sharedUsers.value.includes(currentUser);
});

// Moved cursorColors to the component scope to be accessible for both chips and cursors
const cursorColors = ref({});

// Updated getRandomColor to ensure consistent colors
const getRandomColor = () => {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
};

// Updated getCursorColor to use ref
const getCursorColor = (user_id) => {
  if (!cursorColors.value[user_id]) {
    cursorColors.value[user_id] = getRandomColor();
  }
  return cursorColors.value[user_id];
};

const getUsernameFromId = (user_id) => {
  const collab = collaborators.value.find(c => c.user_id === user_id);
  return collab ? collab.username : 'Unbekannt';
};

function calculateCursorPosition(cursor) {
  try {
    // Find the textarea element for this block
    const textareaEl = document.querySelector(`[data-block-id="${cursor.block_id}"]`);
    if (!textareaEl) {
      console.warn('Textarea element not found for block:', cursor.block_id);
      return { left: '0px', top: '0px' };
    }

    // Get the actual textarea within the Vuetify component
    const textarea = textareaEl.querySelector('textarea');
    if (!textarea) {
      console.warn('Textarea not found within component');
      return { left: '0px', top: '0px' };
    }

    // Get Vuetify's inner container padding
    const inputWrapper = textarea.closest('.v-input__slot');
    const wrapperStyles = inputWrapper ? window.getComputedStyle(inputWrapper) : null;
    const wrapperPaddingLeft = wrapperStyles ? parseFloat(wrapperStyles.paddingLeft) || 0 : 0;

    // Get the text content up to the cursor position
    const text = textarea.value || '';
    const cursorPosition = Math.min(cursor.position, text.length);
    const textUpToCursor = text.substring(0, cursorPosition);
    const lines = textUpToCursor.split('\n');
    const currentLine = lines.length - 1;
    const currentLineStart = textUpToCursor.lastIndexOf('\n') + 1;
    const currentLineText = text.substring(currentLineStart, cursorPosition);

    // Create a hidden measurement div with the same styling as the textarea
    const measureElement = document.createElement('div');
    const textareaStyles = window.getComputedStyle(textarea);

    // Copy all relevant text styles
    measureElement.style.cssText = `
      position: absolute;
      visibility: hidden;
      white-space: pre;
      overflow: hidden;
      font-family: ${textareaStyles.fontFamily};
      font-size: ${textareaStyles.fontSize};
      letter-spacing: ${textareaStyles.letterSpacing};
      line-height: ${textareaStyles.lineHeight};
      text-transform: ${textareaStyles.textTransform};
      border-style: ${textareaStyles.borderStyle};
      border-width: ${textareaStyles.borderWidth};
      padding-left: ${textareaStyles.paddingLeft};
      padding-top: ${textareaStyles.paddingTop};
      width: auto;
    `;

    // Measure the text width up to the cursor
    measureElement.textContent = currentLineText;
    document.body.appendChild(measureElement);
    const textWidth = measureElement.getBoundingClientRect().width;
    document.body.removeChild(measureElement);

    // Calculate the width of three characters for adjustment
    const threeCharWidth = measureElement.textContent = 'AAA';
    measureElement.textContent = 'AAA';
    document.body.appendChild(measureElement);
    const adjustmentWidth = measureElement.getBoundingClientRect().width / 3; // Average per character
    document.body.removeChild(measureElement);

    // Calculate positions
    const lineHeight = parseFloat(textareaStyles.lineHeight);
    const scrollTop = textarea.scrollTop;
    const paddingTop = parseFloat(textareaStyles.paddingTop) || 0;
    const paddingLeft = parseFloat(textareaStyles.paddingLeft) || 0;
    const borderTop = parseFloat(textareaStyles.borderTopWidth) || 0;

    // Calculate final position, adjusting for three characters
    const top = (currentLine * lineHeight) - scrollTop + paddingTop + borderTop;
    const left = textWidth - (1 * adjustmentWidth) + paddingLeft + wrapperPaddingLeft;

    return {
      position: 'absolute',
      left: `${left}px`,
      top: `${top}px`
    };
  } catch (error) {
    console.error('Error calculating cursor position:', error);
    return { left: '0px', top: '0px' };
  }
}


// Update the template section where cursors are rendered:
const getCursorsForBlock = (blockId) => {
  if (!cursors.value) return [];
  return Object.values(cursors.value).filter(cursor => cursor.block_id === blockId);
};
</script>

<style scoped>
.blocks-container {
  height: calc(100vh - 15vh);
  overflow-y: auto;
  padding-right: 16px;
}

.blocks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar {
  height: calc(100vh - 15vh);
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

.prompt-title-container {
  position: relative;
  padding: 8px 0;
  margin-bottom: 24px;
}

.prompt-title-wrapper {
  display: flex;
  align-items: center;
  position: relative;
}

.prompt-title {
  margin: 0;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
  line-height: 1.2;
}

.edit-title-btn {
  opacity: 0.2;
  transition: opacity 0.2s ease;
  min-width: 24px !important;
  width: 24px;
  height: 24px !important;
  padding: 0 !important;
}

.prompt-title-wrapper:hover .edit-title-btn {
  opacity: 0.7;
}

.edit-title-btn:hover {
  opacity: 1 !important;
}

.prompt-edit-field {
  max-width: 500px;
  font-size: 2rem !important;
  font-weight: 500;
}

.prompt-edit-field :deep(.v-input__slot) {
  min-height: unset !important;
  padding: 0 8px !important;
  background-color: transparent !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  border-radius: 4px;
}

.prompt-edit-field :deep(.v-text-field__slot input) {
  padding: 4px 0;
  font-size: 2rem;
  font-weight: 500;
  line-height: 1.2;
}

.edit-actions {
  display: flex;
  align-items: center;
  margin-left: 8px;
}

.edit-btn {
  min-width: 24px !important;
  width: 24px;
  height: 24px !important;
  padding: 0 !important;
}

.edit-btn:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.textarea-container {
  position: relative;
}

.remote-cursor {
  position: absolute;
  pointer-events: none;
  z-index: 1000;
}

.cursor-line {
  width: 2px;
  height: 20px;
  position: absolute;
}

.cursor-label {
  position: absolute;
  top: -20px;
  left: 0;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 12px;
  color: white;
  white-space: nowrap;
  transform: translateX(-50%);
  opacity: 1;
  animation: fadeOut 5s forwards;
}

@keyframes fadeOut {
  0% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

.prompt-textarea {
  position: relative;
  font-family: 'Roboto Mono', monospace;
  width: 100%;
  box-sizing: border-box;
}
</style>
