<template>
  <v-card flat class="pa-4">
    <div class="text-center">
      <v-icon size="80" color="success">mdi-check-circle</v-icon>
      <h2 class="text-h4 mt-4">Chatbot erstellt!</h2>
      <p class="text-medium-emphasis mt-2">
        Ihr Chatbot "{{ config.displayName }}" wurde erfolgreich erstellt.
      </p>

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
  }
})

defineEmits(['test', 'close'])
</script>

<style scoped>
/* Styles inherited from parent */
</style>
