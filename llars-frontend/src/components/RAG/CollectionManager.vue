<template>
  <v-container fluid>
    <v-row>
      <!-- Neue Collection Button -->
      <v-col cols="12">
        <LBtn
          variant="primary"
          prepend-icon="mdi-plus"
          size="large"
          @click="$emit('create')"
        >
          Neue Collection erstellen
        </LBtn>
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
          <LCardSkeleton
            :min-height="280"
            :show-status="false"
            :tag-count="0"
            :stat-count="2"
            :action-items="collectionSkeletonActions"
          />
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
          <LCard
            :title="collection.display_name || collection.name"
            :subtitle="collection.name"
            :icon="getIcon(collection.icon)"
            :color="collection.color || '#1976D2'"
          >
            <!-- Description -->
            <p class="description-text">
              {{ collection.description || 'Keine Beschreibung vorhanden' }}
            </p>

            <!-- Stats -->
            <template #stats>
              <div class="collection-stats">
                <div class="stat-item">
                  <div class="stat-value">{{ collection.document_count || 0 }}</div>
                  <div class="stat-label">Dokumente</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ formatSize(collection.total_size_bytes) }}</div>
                  <div class="stat-label">Größe</div>
                </div>
              </div>
            </template>

            <!-- Actions -->
            <template #actions>
              <LBtn
                variant="text"
                prepend-icon="mdi-file-document-multiple"
                size="small"
                @click="$emit('view-documents', collection)"
              >
                Dokumente
              </LBtn>
              <v-spacer />
              <v-btn
                v-if="canShare && (collection.can_share ?? true)"
                icon="mdi-account-multiple-plus"
                size="small"
                variant="text"
                @click="$emit('share', collection)"
              />
              <v-btn
                icon="mdi-pencil"
                size="small"
                variant="text"
                @click="$emit('edit', collection)"
              />
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                @click="$emit('delete', collection)"
              />
            </template>
          </LCard>
        </v-col>

        <!-- Empty State -->
        <v-col v-if="!collections || collections.length === 0" cols="12">
          <LCard outlined class="text-center pa-8">
            <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-folder-open</v-icon>
            <div class="text-h5 mb-2">Keine Collections vorhanden</div>
            <div class="text-medium-emphasis mb-4">
              Erstellen Sie Ihre erste Collection, um Dokumente zu organisieren.
            </div>
            <LBtn
              variant="primary"
              prepend-icon="mdi-plus"
              @click="$emit('create')"
            >
              Erste Collection erstellen
            </LBtn>
          </LCard>
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
  canShare: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['create', 'edit', 'delete', 'share', 'view-documents'])

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

const collectionSkeletonActions = [
  { width: 88, height: 28, shape: 'pill' },
  { width: 28, height: 28, shape: 'circle' },
  { width: 28, height: 28, shape: 'circle' },
  { width: 28, height: 28, shape: 'circle' }
]

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.description-text {
  min-height: 48px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 0;
}

.collection-stats {
  display: flex;
  justify-content: space-around;
  width: 100%;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
</style>
