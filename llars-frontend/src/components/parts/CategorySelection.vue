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
        <v-card-title class="popup-header">Fall Kategorie auswählen</v-card-title>
        <v-card-text>
          <!-- Radiobutton Gruppe für Kategorien -->
          <v-radio-group v-model="currentSelectedCategoryId">
            <v-radio
              v-for="category in consultingCategories"
              :key="category.id"
              :value="category.id"
              class="radio-option"
              @click="toggleCategorySelection(category)"
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
            v-model="currentCategoryNotes"
            label="Anmerkungen zur Fallkategorie"
            rows="3"
            outlined
            class="mt-4"
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="cancelCategorySelection" color="grey lighten-2">
            Abbrechen
          </v-btn>
          <v-btn
            @click="saveCategorySelection"
            color="primary"
            background-color="green lighen2"
          >
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  initialCategoryId: {
    type: Number,
    default: null
  },
  initialCategoryNotes: {
    type: String,
    default: ''
  }
});

const consultingCategories = ref([]);
const categoryDialog = ref(false);
const currentSelectedCategoryId = ref(null);
const selectedCategory = ref(null);
const currentCategoryNotes = ref(null);

// Watcher für Props
watch([() => props.initialCategoryId, () => props.initialCategoryNotes],
  async ([newCategoryId, newCategoryNotes]) => {
    // Stelle sicher, dass Kategorien geladen sind
    if (consultingCategories.value.length === 0) {
      await loadCategories();
    }

    // Behandle Kategorien UND Notes separat
    if (newCategoryId) {
      const initialCategory = consultingCategories.value.find(
        category => category.id === newCategoryId
      );

      if (initialCategory) {
        selectedCategory.value = {
          ...initialCategory,
          notes: newCategoryNotes || ''
        };
        currentSelectedCategoryId.value = initialCategory.id;
      }
    }

    // Notes immer setzen, unabhängig von Kategorie
    currentCategoryNotes.value = newCategoryNotes || '';
  },
  { immediate: true }
);


async function loadCategories() {
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
  } catch (error) {
    console.error('Fehler beim Laden der Kategorien:', error);
    alert('Fehler beim Laden der Kategorien');
  }
}

async function openCategoryDialog() {
  // Lade Kategorien, falls noch nicht geladen
  if (consultingCategories.value.length === 0) {
    await loadCategories();
  }

  categoryDialog.value = true;
}

function toggleCategorySelection(category) {
  if (currentSelectedCategoryId.value === category.id) {
    currentSelectedCategoryId.value = null;
  }
}

function saveCategorySelection() {
  // Behandle Notes separat von Category
  const trimmedNotes = currentCategoryNotes.value ? currentCategoryNotes.value.trim() : null;

  if (currentSelectedCategoryId.value) {
    // Finden der ausgewählten Kategorie
    selectedCategory.value = consultingCategories.value.find(
      category => category.id === currentSelectedCategoryId.value
    );

    // Notizen zur Kategorie hinzufügen
    selectedCategory.value.notes = trimmedNotes;
  } else {
    // Wenn keine Kategorie ausgewählt, trotzdem Notes speichern
    selectedCategory.value = null;
  }

  // Emit-Event mit allen Informationen
  emit('category-selected', {
    categoryId: selectedCategory.value ? selectedCategory.value.id : null,
    categoryName: selectedCategory.value ? selectedCategory.value.name : null,
    categoryNotes: trimmedNotes // Sendet null für leere/nur Whitespace Strings
  });

  // Dialog schließen
  categoryDialog.value = false;
}

function cancelCategorySelection() {
  categoryDialog.value = false;
  // Zurücksetzen auf den vorherigen Zustand
  currentSelectedCategoryId.value = selectedCategory.value ? selectedCategory.value.id : null;
  currentCategoryNotes.value = selectedCategory.value ? selectedCategory.value.notes : null;
}

// Optional: Emit für übergeordnete Komponente
const emit = defineEmits(['category-selected']);
</script>

<style>
.radio-option {
  margin-bottom: 12px; /* Abstand nach unten */
}

.popup-header {
  color: #2F4F4F;
  margin-bottom: 12px;
  font-size: 1.1em;
}
</style>
