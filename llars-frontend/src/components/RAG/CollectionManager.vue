<template>
  <v-container fluid>
    <v-row>
      <!-- Neue Collection Button -->
      <v-col cols="12">
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="$emit('create')"
          size="large"
        >
          Neue Collection erstellen
        </v-btn>
      </v-col>

      <!-- Loading Skeletons -->
      <template v-if="loading">
        <v-col
          v-for="i in 6"
          :key="`skeleton-${i}`"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <v-skeleton-loader type="card" height="280"></v-skeleton-loader>
        </v-col>
      </template>

      <!-- Collection Cards -->
      <template v-else>
        <v-col
          v-for="collection in collections"
          :key="collection.id"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <v-card
            class="collection-card"
            elevation="2"
            :style="{ borderTop: `4px solid ${collection.color || '#1976D2'}` }"
          >
            <v-card-item>
              <template v-slot:prepend>
                <v-avatar :color="collection.color || '#1976D2'" size="48">
                  <v-icon size="28" color="white">{{ getIcon(collection.icon) }}</v-icon>
                </v-avatar>
              </template>

              <v-card-title>{{ collection.display_name || collection.name }}</v-card-title>
              <v-card-subtitle class="text-medium-emphasis">{{ collection.name }}</v-card-subtitle>
            </v-card-item>

            <v-card-text>
              <p class="text-body-2 text-medium-emphasis mb-3">
                {{ collection.description || 'Keine Beschreibung vorhanden' }}
              </p>

              <v-divider class="mb-3"></v-divider>

              <div class="d-flex justify-space-between">
                <div class="text-center">
                  <div class="text-h6">{{ collection.document_count || 0 }}</div>
                  <div class="text-caption text-medium-emphasis">Dokumente</div>
                </div>
                <div class="text-center">
                  <div class="text-h6">{{ formatSize(collection.total_size_bytes) }}</div>
                  <div class="text-caption text-medium-emphasis">Größe</div>
                </div>
              </div>
            </v-card-text>

            <v-card-actions>
              <v-btn
                variant="text"
                color="primary"
                prepend-icon="mdi-file-document-multiple"
                @click="$emit('view-documents', collection)"
              >
                Dokumente
              </v-btn>

              <v-spacer></v-spacer>

              <v-btn
                icon="mdi-pencil"
                size="small"
                variant="text"
                @click="$emit('edit', collection)"
              ></v-btn>

              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                @click="$emit('delete', collection)"
              ></v-btn>
            </v-card-actions>
          </v-card>
        </v-col>

        <!-- Empty State -->
        <v-col v-if="!collections || collections.length === 0" cols="12">
          <v-card class="text-center pa-8" variant="outlined">
            <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-folder-open</v-icon>
            <v-card-title class="text-h5 mb-2">Keine Collections vorhanden</v-card-title>
            <v-card-text class="text-medium-emphasis">
              Erstellen Sie Ihre erste Collection, um Dokumente zu organisieren.
            </v-card-text>
            <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              @click="$emit('create')"
              class="mt-4"
            >
              Erste Collection erstellen
            </v-btn>
          </v-card>
        </v-col>
      </template>
    </v-row>
  </v-container>
</template>

<script setup>
const props = defineProps({
  collections: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['create', 'edit', 'delete', 'view-documents'])

const getIcon = (iconName) => {
  const iconMap = {
    'book': 'mdi-book',
    'folder': 'mdi-folder',
    'faq': 'mdi-comment-question',
    'database': 'mdi-database',
    'text': 'mdi-text-box',
    'email': 'mdi-email',
    'archive': 'mdi-archive'
  }
  return iconMap[iconName] || 'mdi-folder'
}

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.collection-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
}

.collection-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1) !important;
}

.v-card-text {
  flex-grow: 1;
}
</style>
