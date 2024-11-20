<template>
  <v-container fluid>
    <v-row>
      <!-- Linke Seite: Kacheln für bestehende Prompts -->
      <v-col cols="12" md="8">
        <h1>Prompt Engineering</h1>
        <p>Wählen Sie ein Prompt aus, um es zu bearbeiten oder zu teilen.</p>

        <v-row>
          <v-col cols="12" sm="6" v-for="prompt in prompts" :key="prompt.id">
            <v-card class="mb-4 case-card" @click="navigateToPromptDetail(prompt.id)">
              <v-card-title>{{ prompt.name }}</v-card-title>
              <v-card-text>
                <p><strong>Erstellt von:</strong> {{ prompt.owner }}</p>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>

      <!-- Rechte Seite: Menü zum Anlegen eines neuen Prompts -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>Neues Prompt anlegen</v-card-title>
          <v-card-text>
            <v-form ref="newPromptForm" v-model="isFormValid">
              <v-text-field
                v-model="newPrompt.name"
                label="Prompt Name"
                :rules="[rules.required]"
                required
              ></v-text-field>

              <v-text-field
                v-model="sharedWith"
                label="Mit Benutzer teilen (Optional)"
                hint="Benutzername eingeben"
              ></v-text-field>

              <v-btn
                :disabled="!isFormValid"
                color="primary"
                @click="savePrompt"
              >
                Prompt anlegen
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

// Router
const router = useRouter();

// Prompts State
const prompts = ref([]);

// Form State
const newPrompt = ref({ name: '' });
const sharedWith = ref('');
const isFormValid = ref(false);
const rules = {
  required: (value) => !!value || 'Pflichtfeld',
};

// API Call zum Abrufen aller Prompts
async function fetchPrompts() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/prompts`, {
      headers: {
        'Authorization': api_key,
      },
    });
    prompts.value = response.data.prompts || [];
  } catch (error) {
    console.error('Fehler beim Abrufen der Prompts:', error);
  }
}

// API Call zum Speichern eines neuen Prompts
async function savePrompt() {
  try {
    const api_key = localStorage.getItem('api_key');

    // Neues Prompt speichern
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts`,
      {
        name: newPrompt.value.name,
        content: '{}', // Standard leeres JSON
      },
      {
        headers: {
          'Authorization': api_key,
          'Content-Type': 'application/json',
        },
      }
    );

    // Prompt zur Liste hinzufügen
    prompts.value.push(response.data.prompt);

    // Falls "Mit Benutzer teilen" ausgefüllt wurde
    if (sharedWith.value) {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${response.data.prompt.id}/share`,
        {
          shared_with: sharedWith.value,
        },
        {
          headers: {
            'Authorization': api_key,
            'Content-Type': 'application/json',
          },
        }
      );
      alert(`Prompt wurde erfolgreich mit ${sharedWith.value} geteilt.`);
    }

    // Felder zurücksetzen
    newPrompt.value.name = '';
    sharedWith.value = '';
  } catch (error) {
    console.error('Fehler beim Speichern des Prompts:', error);
  }
}

// Navigation zu Prompt-Detail
function navigateToPromptDetail(promptId) {
  router.push(`/promptengineering/${promptId}`);
}

// Prompts laden, wenn die Komponente gemountet wird
onMounted(fetchPrompts);
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
