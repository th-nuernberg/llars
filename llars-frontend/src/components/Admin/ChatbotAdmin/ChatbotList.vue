<template>
  <div>
    <!-- Loading State -->
    <v-row v-if="loading">
      <v-col v-for="i in 6" :key="i" cols="12" md="6" lg="4">
        <v-skeleton-loader type="card" height="280" />
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-card v-else-if="chatbots.length === 0" class="text-center pa-8">
      <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-robot-outline</v-icon>
      <div class="text-h6 mb-2">Keine Chatbots vorhanden</div>
      <div class="text-medium-emphasis">
        Erstellen Sie Ihren ersten Chatbot, um zu beginnen
      </div>
    </v-card>

    <!-- Chatbot Cards -->
    <v-row v-else>
      <v-col
        v-for="chatbot in chatbots"
        :key="chatbot.id"
        cols="12"
        md="6"
        lg="4"
      >
        <v-card
          class="chatbot-card"
          :style="{ borderTop: `4px solid ${chatbot.color || '#b0ca97'}` }"
          elevation="2"
        >
          <!-- Header -->
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-avatar
                :color="chatbot.color || 'primary'"
                size="40"
                class="mr-3"
              >
                <v-icon color="white">{{ chatbot.icon || 'mdi-robot' }}</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6">{{ chatbot.display_name }}</div>
                <div class="text-caption text-medium-emphasis">
                  {{ chatbot.name }}
                </div>
              </div>
            </div>
            <v-chip
              :color="chatbot.is_active ? 'success' : 'grey'"
              size="small"
              variant="flat"
            >
              {{ chatbot.is_active ? 'Aktiv' : 'Inaktiv' }}
            </v-chip>
          </v-card-title>

          <!-- Description -->
          <v-card-text>
            <div class="text-medium-emphasis mb-3" style="min-height: 48px">
              {{ chatbot.description || 'Keine Beschreibung vorhanden' }}
            </div>

            <!-- Stats -->
            <v-divider class="mb-3" />
            <v-row dense class="text-caption">
              <v-col cols="6">
                <div class="d-flex align-center">
                  <v-icon size="16" class="mr-1">mdi-folder-multiple</v-icon>
                  <span class="text-medium-emphasis">
                    {{ chatbot.collections?.length || 0 }} Collections
                  </span>
                </div>
              </v-col>
              <v-col cols="6">
                <div class="d-flex align-center">
                  <v-icon size="16" class="mr-1">mdi-message-text</v-icon>
                  <span class="text-medium-emphasis">
                    {{ chatbot.conversation_count || 0 }} Gespräche
                  </span>
                </div>
              </v-col>
            </v-row>

            <!-- RAG Badge -->
            <v-chip
              v-if="chatbot.rag_enabled"
              size="x-small"
              color="info"
              variant="outlined"
              class="mt-2"
            >
              <v-icon start size="12">mdi-magnify</v-icon>
              RAG aktiviert
            </v-chip>
          </v-card-text>

          <!-- Actions -->
          <v-card-actions class="px-4 pb-4">
            <v-btn
              size="small"
              variant="text"
              color="primary"
              prepend-icon="mdi-play"
              @click="$emit('test', chatbot)"
            >
              Testen
            </v-btn>
            <v-spacer />
            <v-menu>
              <template #activator="{ props }">
                <v-btn
                  icon="mdi-dots-vertical"
                  variant="text"
                  size="small"
                  v-bind="props"
                />
              </template>
              <v-list>
                <v-list-item @click="$emit('edit', chatbot)">
                  <template #prepend>
                    <v-icon>mdi-pencil</v-icon>
                  </template>
                  <v-list-item-title>Bearbeiten</v-list-item-title>
                </v-list-item>
                <v-list-item @click="$emit('manage-collections', chatbot)">
                  <template #prepend>
                    <v-icon>mdi-folder-cog</v-icon>
                  </template>
                  <v-list-item-title>Collections verwalten</v-list-item-title>
                </v-list-item>
                <v-list-item @click="$emit('duplicate', chatbot)">
                  <template #prepend>
                    <v-icon>mdi-content-copy</v-icon>
                  </template>
                  <v-list-item-title>Duplizieren</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item @click="$emit('delete', chatbot)">
                  <template #prepend>
                    <v-icon color="error">mdi-delete</v-icon>
                  </template>
                  <v-list-item-title class="text-error">
                    Löschen
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
defineProps({
  chatbots: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['edit', 'delete', 'duplicate', 'test', 'manage-collections'])
</script>

<style scoped>
.chatbot-card {
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100%;
  display: flex;
  flex-direction: column;
  color: rgb(var(--v-theme-on-surface));
}

.chatbot-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.v-card-text {
  color: rgb(var(--v-theme-on-surface));
}

.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}
</style>
