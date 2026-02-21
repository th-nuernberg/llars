<template>
  <div :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- Loading State -->
    <v-row v-if="loading">
      <v-col v-for="i in 6" :key="i" cols="12" :sm="isMobile ? 12 : 6" :md="6" :lg="4">
        <LCardSkeleton
          :min-height="isMobile ? 200 : 280"
          :avatar-size="isMobile ? 32 : 40"
          :title-width="isMobile ? 120 : 160"
          :subtitle-width="isMobile ? 80 : 110"
          :status-width="isMobile ? 52 : 70"
          :description-min-height="isMobile ? 36 : 48"
          :stat-width="isMobile ? 70 : 90"
          :tag-width="isMobile ? 46 : 60"
          :primary-action-width="isMobile ? 64 : 72"
        />
      </v-col>
    </v-row>

    <!-- Empty State -->
    <LCard v-else-if="chatbots.length === 0" flat :class="isMobile ? 'text-center pa-4' : 'text-center pa-8'">
      <LIcon :size="isMobile ? 48 : 64" color="grey-lighten-1" class="mb-4">mdi-robot-outline</LIcon>
      <div :class="isMobile ? 'text-subtitle-1 mb-2' : 'text-h6 mb-2'">Keine Chatbots vorhanden</div>
      <div class="text-medium-emphasis" :class="isMobile ? 'text-body-2' : ''">
        Erstellen Sie Ihren ersten Chatbot, um zu beginnen
      </div>
    </LCard>

    <!-- Chatbot Cards -->
    <v-row v-else :dense="isMobile">
      <v-col
        v-for="chatbot in chatbots"
        :key="chatbot.id"
        cols="12"
        :sm="isMobile ? 12 : 6"
        :md="6"
        :lg="4"
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
              v-if="getChatbotTypeTag(chatbot)"
              :variant="getChatbotTypeTag(chatbot).variant"
              size="sm"
              :prepend-icon="getChatbotTypeTag(chatbot).icon"
            >
              {{ getChatbotTypeTag(chatbot).label }}
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
                    <LIcon>wand</LIcon>
                  </template>
                  <v-list-item-title>Konfiguration fortsetzen</v-list-item-title>
                </v-list-item>
                <v-list-item @click="$emit('edit', chatbot)">
                  <template #prepend>
                    <LIcon>mdi-pencil</LIcon>
                  </template>
                  <v-list-item-title>Bearbeiten</v-list-item-title>
                </v-list-item>
                <v-list-item @click="$emit('manage-collections', chatbot)">
                  <template #prepend>
                    <LIcon>mdi-folder-cog</LIcon>
                  </template>
                  <v-list-item-title>Collections verwalten</v-list-item-title>
                </v-list-item>
                <v-list-item @click="$emit('duplicate', chatbot)">
                  <template #prepend>
                    <LIcon>mdi-content-copy</LIcon>
                  </template>
                  <v-list-item-title>Duplizieren</v-list-item-title>
                </v-list-item>
                <v-list-item
                  v-if="canShare && (isAdmin || chatbot.created_by === currentUsername)"
                  @click="$emit('share', chatbot)"
                >
                  <template #prepend>
                    <LIcon>mdi-account-multiple-plus</LIcon>
                  </template>
                  <v-list-item-title>Zugriff teilen</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item @click="$emit('delete', chatbot)">
                  <template #prepend>
                    <LIcon color="error">mdi-delete</LIcon>
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
import { useMobile } from '@/composables/useMobile'

const { isMobile, isTablet } = useMobile()

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

function getChatbotTypeTag(bot) {
  const agentMode = bot?.prompt_settings?.agent_mode
  if (agentMode && agentMode !== 'standard') {
    const agentTags = {
      act: { label: 'ACT', variant: 'success', icon: 'mdi-play' },
      react: { label: 'ReAct', variant: 'accent', icon: 'mdi-thought-bubble' },
      reflact: { label: 'ReflAct', variant: 'secondary', icon: 'mdi-target' }
    }
    return agentTags[agentMode] || { label: agentMode.toUpperCase(), variant: 'gray', icon: 'mdi-robot' }
  }

  if (bot?.rag_enabled) {
    return { label: 'RAG', variant: 'info', icon: 'mdi-magnify' }
  }

  return null
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

/* Mobile styles */
.is-mobile .description-text {
  min-height: 36px;
  font-size: 0.8rem;
}

.is-mobile :deep(.l-card) {
  padding: 12px;
}

.is-mobile :deep(.l-card-title) {
  font-size: 1rem;
}

.is-mobile :deep(.l-card-subtitle) {
  font-size: 0.75rem;
}

/* Touch-friendly tap targets */
.is-mobile :deep(.v-btn) {
  min-height: 40px;
}

.is-mobile :deep(.v-list-item) {
  min-height: 44px;
}
</style>
