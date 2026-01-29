<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="900"
    scrollable
  >
    <v-card>
      <v-card-title class="d-flex align-center pa-4 bg-grey-lighten-4">
        <LIcon class="mr-2" color="primary">mdi-folder-open</LIcon>
        <div class="d-flex flex-column">
          <span class="text-h6">{{ category?.display_name || $t('kaimo.hintDialog.categoryFallback') }}</span>
          <span class="text-caption text-grey">
            {{ $t('kaimo.hintDialog.progress', { assigned: assignedHintCount, total: relevantHints.length }) }}
          </span>
        </div>
        <v-spacer />
        <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" @click="closeDialog" />
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
            {{ $t('kaimo.hintDialog.noCategory') }}
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
                      :label="$t('kaimo.hintDialog.subcategoryLabel')"
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
                        {{ $t('kaimo.ratings.risk') }}
                      </v-btn>

                      <v-btn
                        :variant="localAssignments[hint.id]?.rating === 'resource' ? 'flat' : 'outlined'"
                        :color="localAssignments[hint.id]?.rating === 'resource' ? 'success' : 'grey'"
                        size="small"
                        prepend-icon="mdi-check-circle"
                        @click="setRating(hint.id, 'resource')"
                      >
                        {{ $t('kaimo.ratings.resource') }}
                      </v-btn>

                      <v-btn
                        :variant="localAssignments[hint.id]?.rating === 'unclear' ? 'flat' : 'outlined'"
                        :color="localAssignments[hint.id]?.rating === 'unclear' ? 'grey-darken-1' : 'grey'"
                        size="small"
                        prepend-icon="mdi-help-circle"
                        @click="setRating(hint.id, 'unclear')"
                      >
                        {{ $t('kaimo.ratings.unclear') }}
                      </v-btn>
                    </div>
                  </v-col>
                </v-row>
              </div>

              <v-divider class="my-3" />

              <div class="hint-status">
                <!-- Auto-save status indicator -->
                <div v-if="isHintSaving(hint.id)" class="status-indicator saving">
                  <v-progress-circular size="16" width="2" indeterminate color="primary" />
                  <span>{{ $t('kaimo.hintDialog.saving') }}</span>
                </div>
                <div v-else-if="isHintAssigned(hint.id) && isHintFullyAssigned(hint.id)" class="status-indicator saved">
                  <LIcon size="16" color="success">mdi-check-circle</LIcon>
                  <span>{{ $t('kaimo.hintDialog.saved') }}</span>
                </div>
                <div v-else-if="isHintAssigned(hint.id)" class="status-indicator partial">
                  <LIcon size="16" color="warning">mdi-circle-half-full</LIcon>
                  <span>{{ $t('kaimo.hintDialog.partialSaved') }}</span>
                </div>
                <div v-else-if="canSaveHint(hint.id)" class="status-indicator ready">
                  <LIcon size="16" color="primary">mdi-content-save</LIcon>
                  <span>{{ $t('kaimo.hintDialog.readyToSave') }}</span>
                </div>
                <div v-else class="status-indicator pending">
                  <LIcon size="16" color="grey">mdi-circle-outline</LIcon>
                  <span>{{ $t('kaimo.hintDialog.selectAny') }}</span>
                </div>

                <v-spacer />

                <v-btn
                  v-if="isHintAssigned(hint.id)"
                  color="grey"
                  variant="text"
                  size="small"
                  @click="resetHint(hint.id)"
                >
                  {{ $t('kaimo.hintDialog.reset') }}
                </v-btn>
              </div>
            </div>

            <div v-if="relevantHints.length === 0" class="no-hints">
              <LIcon size="48" color="grey-lighten-1">mdi-lightbulb-outline</LIcon>
              <p class="text-grey">{{ $t('kaimo.hintDialog.empty') }}</p>
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
          {{ $t('common.close') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

// Debounce utility
const debounce = (fn, delay) => {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

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

// Track which hints are currently saving (for visual feedback)
const savingHints = ref(new Set())

// Get all hints
const allHints = computed(() => props.caseData?.hints || [])

// Get relevant hints for this category
// Priority:
// 1. Hints with expected_category_id matching this category
// 2. Unassigned hints without expected_category_id
// 3. Hints already assigned to this category
const relevantHints = computed(() => {
  if (!props.category?.id) return []

  return allHints.value.filter(hint => {
    const assignment = props.hintAssignments.get(hint.id)

    // Already assigned to this category
    if (assignment && assignment.category_id === props.category.id) {
      return true
    }

    // Has expected_category_id matching this category
    if (hint.expected_category_id === props.category.id) {
      return true
    }

    // Unassigned hint without expected category (can be assigned to any category)
    if (!assignment && !hint.expected_category_id) {
      return true
    }

    return false
  })
})

// Count of assigned hints for this category
const assignedHintCount = computed(() => {
  return relevantHints.value.filter(hint => props.hintAssignments.has(hint.id)).length
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

// Check if hint can be saved (has at least one field filled)
const canSaveHint = (hintId) => {
  const assignment = localAssignments.value[hintId]
  // Allow saving if either subcategory OR rating is set
  return assignment && (assignment.subcategory_id || assignment.rating)
}

// Check if hint is fully assigned (both fields filled)
const isHintFullyAssigned = (hintId) => {
  const assignment = localAssignments.value[hintId]
  return assignment && assignment.subcategory_id && assignment.rating
}

// Auto-save logic - debounced to prevent excessive API calls
const performAutoSave = (hintId) => {
  const assignment = localAssignments.value[hintId]
  console.log('[KAIMO Auto-Save] performAutoSave called for hint', hintId, {
    assignment,
    canSave: canSaveHint(hintId)
  })

  if (!assignment || !canSaveHint(hintId)) {
    console.log('[KAIMO Auto-Save] Skipping save - conditions not met')
    return
  }

  // Mark as saving
  savingHints.value.add(hintId)
  savingHints.value = new Set(savingHints.value) // Trigger reactivity

  console.log('[KAIMO Auto-Save] Emitting save event:', {
    hintId,
    category_id: props.category.id,
    subcategory_id: assignment.subcategory_id,
    rating: assignment.rating
  })

  emit('save', hintId, {
    category_id: props.category.id,
    subcategory_id: assignment.subcategory_id,
    rating: assignment.rating
  })

  // Remove saving indicator after a short delay (parent handles actual save)
  setTimeout(() => {
    savingHints.value.delete(hintId)
    savingHints.value = new Set(savingHints.value)
  }, 500)
}

// Create debounced auto-save per hint
const debouncedAutoSaveMap = {}
const triggerAutoSave = (hintId) => {
  console.log('[KAIMO Auto-Save] triggerAutoSave called for hint', hintId)
  if (!debouncedAutoSaveMap[hintId]) {
    console.log('[KAIMO Auto-Save] Creating new debounced function for hint', hintId)
    debouncedAutoSaveMap[hintId] = debounce(() => performAutoSave(hintId), 300)
  }
  debouncedAutoSaveMap[hintId]()
}

// Set subcategory for hint
const setSubcategory = (hintId, subcategoryId) => {
  console.log('[KAIMO] setSubcategory called:', { hintId, subcategoryId })

  if (!localAssignments.value[hintId]) {
    localAssignments.value[hintId] = {
      category_id: props.category.id,
      subcategory_id: null,
      rating: null
    }
  }
  localAssignments.value[hintId].subcategory_id = subcategoryId

  const canSave = canSaveHint(hintId)
  console.log('[KAIMO] After setSubcategory - canSaveHint:', canSave, 'localAssignments:', localAssignments.value[hintId])

  // Auto-save if both fields are filled
  if (canSave) {
    triggerAutoSave(hintId)
  }
}

// Set rating for hint
const setRating = (hintId, rating) => {
  console.log('[KAIMO] setRating called:', { hintId, rating })

  if (!localAssignments.value[hintId]) {
    localAssignments.value[hintId] = {
      category_id: props.category.id,
      subcategory_id: null,
      rating: null
    }
  }
  localAssignments.value[hintId].rating = rating

  const canSave = canSaveHint(hintId)
  console.log('[KAIMO] After setRating - canSaveHint:', canSave, 'localAssignments:', localAssignments.value[hintId])

  // Auto-save if both fields are filled
  if (canSave) {
    triggerAutoSave(hintId)
  }
}

// Check if hint is currently saving
const isHintSaving = (hintId) => {
  return savingHints.value.has(hintId)
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

// Track if dialog has been initialized to prevent resetting on hintAssignments updates
let dialogInitialized = false

// Initialize local assignments when dialog opens or category changes
watch([() => props.modelValue, () => props.category, () => props.hintAssignments], ([newModelValue, newCategory, newHintAssignments], [oldModelValue, oldCategory]) => {
  // Only reinitialize when dialog opens or category changes, NOT when hintAssignments updates
  const isInitialRun = oldModelValue === undefined
  const dialogJustOpened = newModelValue && !oldModelValue
  const categoryChanged = newCategory?.id !== oldCategory?.id

  console.log('[KAIMO Watch] Triggered:', {
    isInitialRun,
    dialogJustOpened,
    categoryChanged,
    dialogInitialized,
    modelValue: newModelValue,
    categoryId: newCategory?.id
  })

  // Reset initialized flag when dialog closes
  if (!newModelValue) {
    dialogInitialized = false
    return
  }

  // Skip reinitialization if dialog is already open and only hintAssignments changed
  // This prevents overwriting user's in-progress edits after a save
  if (dialogInitialized && !categoryChanged) {
    console.log('[KAIMO Watch] Skipping - dialog already initialized and category unchanged')
    return
  }

  if (newModelValue && newCategory) {
    // Initialize local state from props
    const newAssignments = {}

    relevantHints.value.forEach(hint => {
      const existing = newHintAssignments?.get(hint.id)
      if (existing && existing.category_id === newCategory.id) {
        newAssignments[hint.id] = { ...existing }
      } else {
        newAssignments[hint.id] = {
          category_id: newCategory.id,
          subcategory_id: null,
          rating: null
        }
      }
    })

    console.log('[KAIMO Watch] Initializing localAssignments:', newAssignments)
    localAssignments.value = newAssignments
    dialogInitialized = true
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

.hint-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.status-indicator.saving {
  color: rgb(var(--v-theme-primary));
}

.status-indicator.saved {
  color: rgb(var(--v-theme-success));
}

.status-indicator.partial {
  color: rgb(var(--v-theme-warning));
}

.status-indicator.ready {
  color: rgb(var(--v-theme-primary));
  animation: pulse 1.5s ease-in-out infinite;
}

.status-indicator.pending {
  color: rgb(var(--v-theme-on-surface-variant));
  opacity: 0.7;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
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
