<!--
  ChatbotEditor - Collections Tab

  RAG collection selection and document upload interface.
-->
<template>
  <div v-if="collections.length === 0" class="text-center pa-8">
    <v-icon size="48" color="grey-lighten-1" class="mb-2">
      mdi-folder-off
    </v-icon>
    <div class="text-medium-emphasis">
      Keine Collections verfügbar
    </div>
  </div>
  <template v-else>
    <v-list>
      <v-list-item
        v-for="collection in collections"
        :key="collection.id"
      >
        <template #prepend>
          <v-checkbox-btn
            :model-value="isCollectionSelected(collection.id)"
            @update:model-value="$emit('toggle-collection', collection.id)"
          />
        </template>
        <v-list-item-title>{{ collection.display_name }}</v-list-item-title>
        <v-list-item-subtitle>
          {{ collection.document_count || 0 }} Dokumente
        </v-list-item-subtitle>
      </v-list-item>
    </v-list>

    <v-divider class="my-4" />

    <div class="d-flex align-center mb-2">
      <v-icon class="mr-2" color="primary">mdi-upload</v-icon>
      <span class="text-subtitle-1 font-weight-medium">Dokumente hinzufügen</span>
    </div>
    <v-alert type="info" variant="tonal" density="compact" class="mb-3">
      Laden Sie PDFs, Markdown oder TXT direkt in eine zugewiesene Collection hoch.
    </v-alert>

    <v-row v-if="selectedCollections.length > 0">
      <v-col
        v-for="collection in selectedCollections"
        :key="collection.id"
        cols="12"
        md="6"
      >
        <v-card variant="outlined">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-folder</v-icon>
            <span class="text-truncate">{{ collection.display_name || collection.name }}</span>
            <v-spacer />
            <LBtn
              size="small"
              variant="primary"
              prepend-icon="mdi-upload"
              @click="$emit('open-upload', collection.id)"
            >
              Upload
            </LBtn>
          </v-card-title>
          <v-card-text class="text-caption text-medium-emphasis">
            {{ collection.document_count || 0 }} Dokumente
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <div v-else class="text-center pa-6 text-medium-emphasis">
      <v-icon size="48" class="mb-2">mdi-folder-plus</v-icon>
      <div>Bitte zuerst mindestens eine Collection auswählen.</div>
    </div>
  </template>
</template>

<script setup>
/**
 * @component CollectionsTab
 * @description Collection selection and document upload interface.
 */

defineProps({
  /** Available collections */
  collections: {
    type: Array,
    default: () => []
  },
  /** Currently selected collections (filtered) */
  selectedCollections: {
    type: Array,
    default: () => []
  },
  /** Function to check if collection is selected */
  isCollectionSelected: {
    type: Function,
    required: true
  }
});

defineEmits(['toggle-collection', 'open-upload']);
</script>

<style scoped>
.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}
</style>
