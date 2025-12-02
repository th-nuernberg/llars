<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="900"
    scrollable
  >
    <v-card>
      <v-card-title class="d-flex align-center pa-4 bg-grey-lighten-4">
        <v-icon class="mr-2" color="primary">mdi-folder-open</v-icon>
        <span class="text-h6">{{ category?.display_name || 'Kategorie' }}</span>
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" @click="closeDialog" />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-0">
        <v-container fluid>
          <v-alert
            v-if="!category?.id"
            type="warning"
            variant="tonal"
            class="ma-4"
          >
            Keine Kategorie ausgewählt
          </v-alert>

          <template v-else>
            <!-- Hints List -->
            <div
              v-for="hint in relevantHints"
              :key="hint.id"
              class="hint-item"
            >
              <div class="hint-content">
                <div class="hint-text">{{ hint.content }}</div>

                <v-row class="mt-3" dense>
                  <v-col cols="12" md="5">
                    <v-select
                      :model-value="localAssignments[hint.id]?.subcategory_id"
                      @update:model-value="setSubcategory(hint.id, $event)"
                      :items="subcategoryOptions"
                      item-title="display_name"
                      item-value="id"
                      label="Unterkategorie"
                      density="compact"
                      variant="outlined"
                      hide-details
                    />
                  </v-col>

                  <v-col cols="12" md="7">
                    <div class="rating-buttons">
                      <v-btn
                        :variant="localAssignments[hint.id]?.rating === 'risk' ? 'flat' : 'outlined'"
                        :color="localAssignments[hint.id]?.rating === 'risk' ? 'error' : 'grey'"
                        size="small"
                        prepend-icon="mdi-alert-circle"
                        @click="setRating(hint.id, 'risk')"
                      >
                        Risiko
                      </v-btn>

                      <v-btn
                        :variant="localAssignments[hint.id]?.rating === 'resource' ? 'flat' : 'outlined'"
                        :color="localAssignments[hint.id]?.rating === 'resource' ? 'success' : 'grey'"
                        size="small"
                        prepend-icon="mdi-check-circle"
                        @click="setRating(hint.id, 'resource')"
                      >
                        Ressource
                      </v-btn>

                      <v-btn
                        :variant="localAssignments[hint.id]?.rating === 'unclear' ? 'flat' : 'outlined'"
                        :color="localAssignments[hint.id]?.rating === 'unclear' ? 'grey-darken-1' : 'grey'"
                        size="small"
                        prepend-icon="mdi-help-circle"
                        @click="setRating(hint.id, 'unclear')"
                      >
                        Unklar
                      </v-btn>
                    </div>
                  </v-col>
                </v-row>
              </div>

              <v-divider class="my-3" />

              <div class="hint-actions">
                <v-btn
                  color="primary"
                  variant="flat"
                  size="small"
                  :disabled="!canSaveHint(hint.id)"
                  @click="saveHint(hint.id)"
                >
                  Speichern
                </v-btn>

                <v-btn
                  v-if="isHintAssigned(hint.id)"
                  color="grey"
                  variant="text"
                  size="small"
                  @click="resetHint(hint.id)"
                >
                  Zurücksetzen
                </v-btn>
              </div>
            </div>

            <div v-if="relevantHints.length === 0" class="no-hints">
              <v-icon size="48" color="grey-lighten-1">mdi-lightbulb-outline</v-icon>
              <p class="text-grey">Keine Hinweise für diese Kategorie</p>
            </div>
          </template>
        </v-container>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn
          variant="text"
          @click="closeDialog"
        >
          Schließen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  category: {
    type: Object,
    default: null
  },
  caseData: {
    type: Object,
    default: null
  },
  assessment: {
    type: Object,
    default: null
  },
  hintAssignments: {
    type: Map,
    default: () => new Map()
  },
  categories: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

// Local state for assignments (working copy)
const localAssignments = ref({})

// Get all hints
const allHints = computed(() => props.caseData?.hints || [])

// Get relevant hints for this category
const relevantHints = computed(() => {
  if (!props.category?.id) return []

  // Show hints that are either:
  // 1. Not assigned yet
  // 2. Already assigned to this category
  return allHints.value.filter(hint => {
    const assignment = props.hintAssignments.get(hint.id)
    return !assignment || assignment.category_id === props.category.id
  })
})

// Get subcategories for selected category
const subcategoryOptions = computed(() => {
  if (!props.category?.id) return []

  // Find category in categories prop (preferred) or caseData
  const category = props.categories?.find(c => c.id === props.category.id)
    || props.caseData?.categories?.find(c => c.id === props.category.id)
  return category?.subcategories || []
})

// Check if hint is already assigned
const isHintAssigned = (hintId) => {
  return props.hintAssignments.has(hintId)
}

// Check if hint can be saved (has all required fields)
const canSaveHint = (hintId) => {
  const assignment = localAssignments.value[hintId]
  return assignment && assignment.subcategory_id && assignment.rating
}

// Set subcategory for hint
const setSubcategory = (hintId, subcategoryId) => {
  if (!localAssignments.value[hintId]) {
    localAssignments.value[hintId] = {
      category_id: props.category.id,
      subcategory_id: null,
      rating: null
    }
  }
  localAssignments.value[hintId].subcategory_id = subcategoryId
}

// Set rating for hint
const setRating = (hintId, rating) => {
  if (!localAssignments.value[hintId]) {
    localAssignments.value[hintId] = {
      category_id: props.category.id,
      subcategory_id: null,
      rating: null
    }
  }
  localAssignments.value[hintId].rating = rating
}

// Save individual hint
const saveHint = (hintId) => {
  const assignment = localAssignments.value[hintId]
  if (!assignment || !canSaveHint(hintId)) return

  emit('save', hintId, {
    category_id: props.category.id,
    subcategory_id: assignment.subcategory_id,
    rating: assignment.rating
  })
}

// Reset hint assignment
const resetHint = (hintId) => {
  localAssignments.value[hintId] = {
    category_id: props.category.id,
    subcategory_id: null,
    rating: null
  }
}

// Close dialog
const closeDialog = () => {
  emit('update:modelValue', false)
}

// Initialize local assignments when dialog opens or category changes
watch([() => props.modelValue, () => props.category, () => props.hintAssignments], () => {
  if (props.modelValue && props.category) {
    // Initialize local state from props
    const newAssignments = {}

    relevantHints.value.forEach(hint => {
      const existing = props.hintAssignments.get(hint.id)
      if (existing && existing.category_id === props.category.id) {
        newAssignments[hint.id] = { ...existing }
      } else {
        newAssignments[hint.id] = {
          category_id: props.category.id,
          subcategory_id: null,
          rating: null
        }
      }
    })

    localAssignments.value = newAssignments
  }
}, { immediate: true })
</script>

<style scoped>
.hint-item {
  padding: 20px;
  background-color: rgb(var(--v-theme-surface));
  border-radius: 8px;
  margin-bottom: 16px;
}

.hint-content {
  color: rgb(var(--v-theme-on-surface));
}

.hint-text {
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.rating-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hint-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.no-hints {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
}
</style>
