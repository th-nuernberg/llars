<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1>Prompt Engineering: {{ promptName }}</h1>
        <p>Fügen Sie Bausteine hinzu, bearbeiten Sie bestehende und speichern Sie das fertige Prompt.</p>
      </v-col>
    </v-row>

    <!-- Liste der Bausteine -->
    <v-row>
      <v-col cols="12" sm="6" v-for="(block, index) in blocks" :key="index">
        <v-card class="mb-4">
          <v-card-title>
            {{ block.name }}
            <v-spacer></v-spacer>
            <v-btn icon @click="removeBlock(index)">
              <v-icon color="red">mdi-delete</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-textarea
              v-model="block.content"
              outlined
              label="Inhalt des Bausteins"
            ></v-textarea>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Neues Baustein hinzufügen -->
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>Neuen Baustein hinzufügen</v-card-title>
          <v-card-text>
            <v-form ref="newBlockForm" v-model="isFormValid">
              <v-text-field
                v-model="newBlockName"
                label="Baustein Name"
                :rules="[rules.required]"
                required
              ></v-text-field>
              <v-btn
                :disabled="!isFormValid"
                color="primary"
                @click="addBlock"
              >
                Hinzufügen
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Speichern -->
    <v-row>
      <v-col cols="12">
        <v-btn color="success" @click="savePrompt">
          <v-icon left>mdi-content-save</v-icon>
          Speichern
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

// Route und Router
const route = useRoute();
const router = useRouter();
const promptId = route.params.id;

// Prompt Name und Bausteine
const promptName = ref('');
const blocks = ref([]);

// Formularstatus
const newBlockName = ref('');
const isFormValid = ref(false);
const rules = {
  required: (value) => !!value || 'Pflichtfeld',
};

// API Call zum Abrufen des Prompts
// API Call zum Abrufen des Prompts
async function fetchPrompt() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}`, {
      headers: {
        Authorization: api_key,
      },
    });

    // Prompt-Daten verarbeiten
    promptName.value = response.data.name;

    // Konvertiere den Content direkt in Blocks
    if (response.data.content && typeof response.data.content === 'object') {
      blocks.value = Object.entries(response.data.content).map(([key, value]) => ({
        name: key,
        content: value
      }));
    } else {
      blocks.value = [];
    }
  } catch (error) {
    console.error('Fehler beim Abrufen des Prompts:', error);
    alert('Fehler beim Laden des Prompts.');
  }
}


// Neuen Baustein hinzufügen
function addBlock() {
  blocks.value.push({ name: newBlockName.value, content: '' });
  newBlockName.value = '';
}

// Baustein entfernen
function removeBlock(index) {
  blocks.value.splice(index, 1);
}

// Bausteine als JSON speichern
async function savePrompt() {
  try {
    const api_key = localStorage.getItem('api_key');
    const content = blocks.value.reduce((acc, block) => {
      acc[block.name] = block.content;
      return acc;
    }, {});

    const response = await axios.put(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}`,
      { content },
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


// Prompt laden, wenn die Komponente gemountet wird
onMounted(fetchPrompt);
</script>

<style scoped>
.case-card {
  cursor: pointer;
  transition: box-shadow 0.3s ease-in-out, transform 0.1s ease-in-out;
}

.case-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}
</style>
