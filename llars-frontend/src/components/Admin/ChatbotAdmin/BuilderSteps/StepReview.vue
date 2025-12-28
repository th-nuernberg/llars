<template>
  <v-card flat class="pa-4">
    <div class="text-center">
      <v-icon size="80" color="success">mdi-check-circle</v-icon>
      <h2 class="text-h4 mt-4">Chatbot erstellt!</h2>
      <p class="text-medium-emphasis mt-2">
        Ihr Chatbot "{{ config.displayName }}" wurde erfolgreich erstellt.
      </p>

      <!-- Embedding-in-Progress Hinweis -->
      <v-alert
        v-if="embeddingInProgress"
        type="info"
        variant="tonal"
        class="mt-4 mx-auto text-left"
        max-width="500"
      >
        <template #prepend>
          <v-progress-circular
            :model-value="embeddingProgress"
            :indeterminate="embeddingProgress === 0"
            size="24"
            width="3"
            color="info"
          />
        </template>
        <div class="d-flex align-center justify-space-between">
          <div>
            <strong>Embedding läuft im Hintergrund</strong>
            <div class="text-caption">
              Der Chatbot ist bereits nutzbar. Die Wissensbasis wird weiter aufgebaut.
            </div>
          </div>
          <span class="text-body-2 font-weight-medium ml-2">{{ embeddingProgress }}%</span>
        </div>
      </v-alert>

      <v-card class="mt-6 mx-auto" max-width="400" variant="outlined">
        <v-card-text>
          <div class="d-flex align-center mb-4">
            <v-avatar :color="config.color" size="48" class="mr-4">
              <v-icon color="white">{{ config.icon || 'mdi-robot' }}</v-icon>
            </v-avatar>
            <div class="text-left">
              <div class="text-h6">{{ config.displayName }}</div>
              <div class="text-caption text-medium-emphasis">{{ config.name }}</div>
            </div>
          </div>
          <v-divider class="mb-4" />
          <div class="text-body-2 text-left">
            <div class="mb-2">
              <strong>Quelle:</strong> {{ url }}
            </div>
            <div v-if="collectionInfo">
              <strong>Wissensbasis:</strong>
              {{ collectionInfo.document_count }} Dokumente,
              {{ collectionInfo.total_chunks }} Chunks
              <span v-if="embeddingInProgress" class="text-info">(wird erweitert...)</span>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <div class="mt-6">
        <v-btn
          color="primary"
          size="large"
          prepend-icon="mdi-chat"
          class="mr-4"
          @click="$emit('test')"
        >
          Chatbot testen
        </v-btn>
        <v-btn
          variant="outlined"
          size="large"
          prepend-icon="mdi-close"
          @click="$emit('close')"
        >
          Schliessen
        </v-btn>
      </div>
    </div>
  </v-card>
</template>

<script setup>
defineProps({
  config: {
    type: Object,
    required: true
  },
  url: {
    type: String,
    required: true
  },
  collectionInfo: {
    type: Object,
    default: null
  },
  embeddingInProgress: {
    type: Boolean,
    default: false
  },
  embeddingProgress: {
    type: Number,
    default: 0
  }
})

defineEmits(['test', 'close'])
</script>

<style scoped>
/* Styles inherited from parent */
</style>
