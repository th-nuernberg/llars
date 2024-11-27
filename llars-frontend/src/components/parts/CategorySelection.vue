<template>
  <div>
    <!-- Fallkategorie Button -->
    <v-btn
      @click="openCategoryDialog"
      class="mb-4"
      :color="selectedCategory ? 'primary' : 'grey'"
    >
      {{ selectedCategory ? selectedCategory.name : 'Wählen Sie eine Fall Kategorie aus' }}
    </v-btn>

    <!-- Kategorie Auswahl Dialog -->
    <v-dialog v-model="categoryDialog" max-width="600px">
      <v-card>
        <v-card-title>Fall Kategorie auswählen</v-card-title>
        <v-card-text>
          <!-- Radiobutton Gruppe für Kategorien -->
          <v-radio-group v-model="selectedCategoryId">
            <v-radio
              v-for="category in consultingCategories"
              :key="category.id"
              :label="`${category.name}`"
              :value="category.id"
            >
              <template v-slot:label>
                <div>
                  <strong>{{ category.name }}</strong>
                  <p class="text-caption grey--text">{{ category.description }}</p>
                </div>
              </template>
            </v-radio>
          </v-radio-group>

          <!-- Anmerkungsfeld -->
          <v-textarea
            v-model="categoryNotes"
            label="Anmerkungen zur Fallkategorie"
            rows="3"
            outlined
            class="mt-4"
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="cancelCategorySelection" color="grey lighten-1">
            Abbrechen
          </v-btn>
          <v-btn
            @click="saveCategorySelection"
            color="primary"
            :disabled="!selectedCategoryId"
          >
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// Referenzen für Kategorieauswahl
const consultingCategories = ref([]);
const categoryDialog = ref(false);
const selectedCategoryId = ref(null);
const selectedCategory = ref(null);
const categoryNotes = ref('');

// Methode zum Öffnen des Dialogs und Laden der Kategorien
async function openCategoryDialog() {
  const api_key = localStorage.getItem('api_key');

  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/consulting_category_types`,
      {
        headers: {
          'Authorization': api_key,
        }
      }
    );

    consultingCategories.value = response.data.consulting_category_types;
    categoryDialog.value = true;
  } catch (error) {
    console.error('Fehler beim Laden der Kategorien:', error);
    alert('Fehler beim Laden der Kategorien');
  }
}

// Methode zum Speichern der Kategorieauswahl
function saveCategorySelection() {
  // Finden der ausgewählten Kategorie
  selectedCategory.value = consultingCategories.value.find(
    category => category.id === selectedCategoryId.value
  );

  // Emit-Event oder direkte Speicherung, je nach Ihrer Architektur
  emit('category-selected', {
    categoryId: selectedCategoryId.value,
    categoryName: selectedCategory.value.name,
    categoryNotes: categoryNotes.value
  });

  // Dialog schließen
  categoryDialog.value = false;
}

// Methode zum Abbrechen der Auswahl
function cancelCategorySelection() {
  categoryDialog.value = false;
  selectedCategoryId.value = null;
}

// Optional: Emit für übergeordnete Komponente
const emit = defineEmits(['category-selected']);
</script>
