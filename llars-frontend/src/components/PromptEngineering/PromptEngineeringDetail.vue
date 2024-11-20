<template>
  <v-container fluid class="fill-height">
    <v-row no-gutters style="height: 100%">
      <!-- Main Content Area - Blocks -->
      <v-col cols="9" class="pr-4">
        <h1 class="text-h4 mb-6">{{ promptName }}</h1>
        <div class="blocks-container">
          <draggable
            v-model="blocks"
            class="blocks-list"
            item-key="name"
            handle=".drag-handle"
          >
            <template #item="{ element, index }">
              <v-card class="mb-4">
                <v-card-title class="d-flex align-center">
                  <v-icon class="drag-handle mr-2 cursor-move">mdi-drag</v-icon>
                  {{ element.name }}
                  <v-spacer></v-spacer>
                  <v-btn icon @click="removeBlock(index)">
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
                  ></v-textarea>
                </v-card-text>
              </v-card>
            </template>
          </draggable>
        </div>
      </v-col>

      <!-- Sidebar - Tools -->
      <v-col cols="3" class="sidebar">
        <v-card class="mb-4">
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

        <v-card>
          <v-card-title>Aktionen</v-card-title>
          <v-card-text>
            <v-btn
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
              @click="previewPrompt"
            >
              <v-icon left>mdi-eye</v-icon>
              Vorschau
            </v-btn>
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
  </v-container>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import axios from 'axios';
import draggable from 'vuedraggable';

const route = useRoute();
const router = useRouter();
const promptId = route.params.id;

const promptName = ref('');
const blocks = ref([]);
const newBlockName = ref('');
const isFormValid = ref(false);
const showPreview = ref(false);

const rules = {
  required: (value) => !!value || 'Pflichtfeld',
};

const compiledPrompt = computed(() => {
  return blocks.value
    .map(block => block.content)
    .filter(content => content.trim())
    .join('\n\n');
});

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
    if (response.data.content && typeof response.data.content === 'object') {
      blocks.value = Object.entries(response.data.content).map(([key, value]) => ({
        name: key,
        content: value
      }));
    }
  } catch (error) {
    console.error('Fehler beim Abrufen des Prompts:', error);
    alert('Fehler beim Laden des Prompts.');
  }
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

async function savePrompt() {
  try {
    const api_key = localStorage.getItem('api_key');
    const content = blocks.value.reduce((acc, block, index) => {
      acc[`${index + 1}_${block.name}`] = block.content;
      return acc;
    }, {});

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
