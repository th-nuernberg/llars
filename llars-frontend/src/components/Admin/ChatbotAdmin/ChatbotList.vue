<template>
  <div>
    <!-- Loading State -->
    <v-row v-if="loading">
      <v-col v-for="i in 6" :key="i" cols="12" md="6" lg="4">
        <v-skeleton-loader type="card" height="280" />
      </v-col>
    </v-row>

    <!-- Empty State -->
    <LCard v-else-if="chatbots.length === 0" flat class="text-center pa-8">
      <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-robot-outline</v-icon>
      <div class="text-h6 mb-2">Keine Chatbots vorhanden</div>
      <div class="text-medium-emphasis">
        Erstellen Sie Ihren ersten Chatbot, um zu beginnen
      </div>
    </LCard>

    <!-- Chatbot Cards -->
    <v-row v-else>
      <v-col
        v-for="chatbot in chatbots"
        :key="chatbot.id"
        cols="12"
        md="6"
        lg="4"
      >
        <LCard
          :title="chatbot.display_name"
          :subtitle="chatbot.name"
          :icon="chatbot.icon || 'mdi-robot'"
          :color="chatbot.color || '#b0ca97'"
          :status="getStatusLabel(chatbot)"
          :status-variant="getStatusVariant(chatbot)"
          :stats="[
            { icon: 'mdi-folder-multiple', value: chatbot.collections?.length || 0, label: 'Collections' },
            { icon: 'mdi-message-text', value: chatbot.conversation_count || 0, label: 'Gespräche' }
          ]"
        >
          <!-- Description -->
          <div class="description-text">
            {{ chatbot.description || 'Keine Beschreibung vorhanden' }}
          </div>

          <!-- Tags -->
          <template #tags>
            <LTag
              v-if="chatbot.rag_enabled"
              variant="info"
              size="sm"
              prepend-icon="mdi-magnify"
            >
              RAG
            </LTag>
          </template>

          <!-- Actions -->
          <template #actions>
            <LBtn
              size="small"
              variant="text"
              prepend-icon="mdi-play"
              @click="$emit('test', chatbot)"
            >
              Testen
            </LBtn>
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
                <v-list-item
                  v-if="chatbot.build_status && chatbot.build_status !== 'ready'"
                  @click="$emit('resume', chatbot)"
                >
                  <template #prepend>
                    <v-icon>mdi-wizard-hat</v-icon>
                  </template>
                  <v-list-item-title>Konfiguration fortsetzen</v-list-item-title>
                </v-list-item>
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
                <v-list-item
                  v-if="canShare && (isAdmin || chatbot.created_by === currentUsername)"
                  @click="$emit('share', chatbot)"
                >
                  <template #prepend>
                    <v-icon>mdi-account-multiple-plus</v-icon>
                  </template>
                  <v-list-item-title>Zugriff teilen</v-list-item-title>
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
          </template>
        </LCard>
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
  },
  canShare: {
    type: Boolean,
    default: false
  },
  currentUsername: {
    type: String,
    default: ''
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

defineEmits(['edit', 'delete', 'duplicate', 'test', 'manage-collections', 'resume', 'share'])

function getBuildStatusLabel(status) {
  switch (status) {
    case 'draft':
      return 'Entwurf'
    case 'crawling':
      return 'Crawling'
    case 'embedding':
      return 'Embedding'
    case 'configuring':
      return 'Konfiguration'
    case 'paused':
      return 'Pausiert'
    case 'error':
      return 'Fehler'
    default:
      return status || 'Status'
  }
}

function getBuildStatusColor(status) {
  switch (status) {
    case 'draft':
      return 'info'
    case 'crawling':
      return 'info'
    case 'embedding':
      return 'info'
    case 'configuring':
      return 'warning'
    case 'paused':
      return 'warning'
    case 'error':
      return 'error'
    default:
      return 'grey'
  }
}

function getStatusLabel(chatbot) {
  const status = chatbot?.build_status
  if (status && status !== 'ready') return getBuildStatusLabel(status)
  return chatbot?.is_active ? 'Aktiv' : 'Inaktiv'
}

function getStatusColor(chatbot) {
  const status = chatbot?.build_status
  if (status && status !== 'ready') return getBuildStatusColor(status)
  return chatbot?.is_active ? 'success' : 'grey'
}

function getStatusVariant(chatbot) {
  const colorMap = {
    'success': 'success',
    'info': 'info',
    'warning': 'warning',
    'error': 'danger',
    'grey': 'gray'
  }
  return colorMap[getStatusColor(chatbot)] || 'gray'
}
</script>

<style scoped>
.description-text {
  min-height: 48px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
