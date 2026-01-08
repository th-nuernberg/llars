<template>
  <v-dialog
    :model-value="modelValue"
    max-width="700"
    scrollable
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <!-- Header -->
      <v-card-title class="d-flex align-center justify-space-between bg-primary">
        <div class="d-flex align-center">
          <LIcon class="mr-2">mdi-folder-cog</LIcon>
          <div>
            <div>Collections verwalten</div>
            <div class="text-caption font-weight-regular">
              {{ chatbot?.display_name }}
            </div>
          </div>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="closeDialog"
        />
      </v-card-title>

      <!-- Content -->
      <v-card-text class="pa-4" style="min-height: 400px">
        <v-row>
          <!-- Assigned Collections -->
          <v-col cols="12" md="6">
            <div class="section-header mb-3">
              <LIcon class="mr-2" color="success">mdi-check-circle</LIcon>
              <span class="text-subtitle-1 font-weight-medium">
                Zugewiesen ({{ selectedCollections.length }})
              </span>
            </div>

            <v-card
              variant="outlined"
              class="collection-list"
              style="min-height: 300px"
            >
              <v-list v-if="selectedCollections.length > 0" density="compact">
                <draggable
                  v-model="selectedCollections"
                  item-key="id"
                  handle=".drag-handle"
                  @end="onDragEnd"
                >
                  <template #item="{ element, index }">
                    <v-list-item
                      class="collection-item"
                      :class="{ 'dragging': isDragging }"
                    >
                      <!-- Drag Handle -->
                      <template #prepend>
                        <LIcon class="drag-handle" size="20">
                          mdi-drag-vertical
                        </LIcon>
                      </template>

                      <!-- Collection Info -->
                      <v-list-item-title>
                        {{ element.display_name }}
                      </v-list-item-title>
                      <v-list-item-subtitle>
                        <LIcon size="12">mdi-file-document</LIcon>
                        {{ element.document_count || 0 }} Dokumente
                      </v-list-item-subtitle>

                      <!-- Priority Badge -->
                      <template #append>
                        <v-chip
                          size="x-small"
                          color="primary"
                          variant="outlined"
                          class="mr-2"
                        >
                          #{{ index + 1 }}
                        </v-chip>
                        <v-btn
                          icon="mdi-close"
                          variant="text"
                          size="x-small"
                          color="error"
                          @click="removeCollection(element)"
                        />
                      </template>
                    </v-list-item>
                  </template>
                </draggable>
              </v-list>
              <div v-else class="text-center pa-8">
                <LIcon size="48" color="grey-lighten-1" class="mb-2">
                  mdi-folder-off
                </LIcon>
                <div class="text-medium-emphasis">
                  Keine Collections zugewiesen
                </div>
              </div>
            </v-card>

            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="mt-3"
            >
              <div class="text-caption">
                <LIcon size="14" class="mr-1">mdi-information</LIcon>
                Ziehen Sie Collections, um die Priorität zu ändern
              </div>
            </v-alert>
          </v-col>

          <!-- Available Collections -->
          <v-col cols="12" md="6">
            <div class="section-header mb-3">
              <LIcon class="mr-2" color="grey">mdi-folder-multiple</LIcon>
              <span class="text-subtitle-1 font-weight-medium">
                Verfügbar ({{ unassignedCollections.length }})
              </span>
            </div>

            <!-- Search -->
            <v-text-field
              v-model="searchQuery"
              placeholder="Collections durchsuchen..."
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              class="mb-3"
            />

            <v-card
              variant="outlined"
              class="collection-list"
              style="min-height: 300px"
            >
              <v-list v-if="filteredUnassignedCollections.length > 0" density="compact">
                <v-list-item
                  v-for="collection in filteredUnassignedCollections"
                  :key="collection.id"
                  class="collection-item"
                >
                  <!-- Collection Info -->
                  <v-list-item-title>
                    {{ collection.display_name }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <LIcon size="12">mdi-file-document</LIcon>
                    {{ collection.document_count || 0 }} Dokumente
                  </v-list-item-subtitle>

                  <!-- Add Button -->
                  <template #append>
                    <v-btn
                      icon="mdi-plus"
                      variant="text"
                      size="small"
                      color="success"
                      @click="addCollection(collection)"
                    />
                  </template>
                </v-list-item>
              </v-list>
              <div v-else class="text-center pa-8">
                <LIcon size="48" color="grey-lighten-1" class="mb-2">
                  mdi-folder-search
                </LIcon>
                <div class="text-medium-emphasis">
                  {{ searchQuery ? 'Keine Ergebnisse' : 'Alle Collections zugewiesen' }}
                </div>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>

      <!-- Actions -->
      <v-divider />
      <v-card-actions>
        <div class="text-caption text-medium-emphasis ml-2">
          {{ selectedCollections.length }} von {{ availableCollections.length }} Collections ausgewählt
        </div>
        <v-spacer />
        <v-btn variant="text" @click="closeDialog">
          Abbrechen
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          @click="saveAssignments"
        >
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import draggable from 'vuedraggable'

const props = defineProps({
  modelValue: Boolean,
  chatbot: Object,
  availableCollections: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

// State
const selectedCollections = ref([])
const searchQuery = ref('')
const isDragging = ref(false)

// Computed
const unassignedCollections = computed(() => {
  return props.availableCollections.filter(
    collection => !selectedCollections.value.find(sc => sc.id === collection.id)
  )
})

const filteredUnassignedCollections = computed(() => {
  if (!searchQuery.value) return unassignedCollections.value

  const query = searchQuery.value.toLowerCase()
  return unassignedCollections.value.filter(collection =>
    collection.display_name?.toLowerCase().includes(query) ||
    collection.name?.toLowerCase().includes(query)
  )
})

// Methods
function addCollection(collection) {
  selectedCollections.value.push(collection)
}

function removeCollection(collection) {
  const index = selectedCollections.value.findIndex(c => c.id === collection.id)
  if (index > -1) {
    selectedCollections.value.splice(index, 1)
  }
}

function onDragEnd() {
  isDragging.value = false
}

function saveAssignments() {
  const data = {
    collection_ids: selectedCollections.value.map(c => c.id),
    priorities: selectedCollections.value.map((c, index) => ({
      collection_id: c.id,
      priority: index + 1
    }))
  }
  emit('save', data)
}

function closeDialog() {
  emit('update:modelValue', false)
  searchQuery.value = ''
}

// Watch for chatbot changes
watch(() => props.chatbot, (newChatbot) => {
  if (newChatbot && newChatbot.collections) {
    // Sort by priority if available
    selectedCollections.value = [...newChatbot.collections].sort((a, b) => {
      return (a.priority || 0) - (b.priority || 0)
    })
  } else {
    selectedCollections.value = []
  }
}, { immediate: true, deep: true })

// Watch for dialog open
watch(() => props.modelValue, (newVal) => {
  if (newVal && props.chatbot) {
    selectedCollections.value = props.chatbot.collections
      ? [...props.chatbot.collections].sort((a, b) => (a.priority || 0) - (b.priority || 0))
      : []
  }
})
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
}

.collection-list {
  max-height: 350px;
  overflow-y: auto;
}

.collection-item {
  transition: background-color 0.2s;
  color: rgb(var(--v-theme-on-surface));
}

.collection-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.collection-item.dragging {
  opacity: 0.5;
}

.drag-handle {
  cursor: grab;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.drag-handle:active {
  cursor: grabbing;
}

.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}

/* Scrollbar styling */
.collection-list::-webkit-scrollbar {
  width: 6px;
}

.collection-list::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.collection-list::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.collection-list::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.3);
}
</style>
