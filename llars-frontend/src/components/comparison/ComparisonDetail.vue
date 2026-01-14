<template>
  <LEvaluationLayout
    :title="session?.persona_name || $t('comparison.detail.loadingTitle')"
    :subtitle="$t('comparison.detail.scenarioLabel', { id: session?.scenario_id || '-' })"
    :back-label="$t('comparison.detail.backLabel')"
    :status="evaluationStatus"
    :can-go-prev="canGoPrev"
    :can-go-next="canGoNext"
    :current-index="currentIndex"
    :total-items="allSessions.length"
    @back="goToOverview"
    @prev="navigateToPreviousSession"
    @next="navigateToNextSession"
  >
    <!-- Header Right Slot -->
    <template #header-right>
      <LIconBtn
        icon="mdi-information"
        size="small"
        variant="text"
        @click="infoDialog = true"
      />
    </template>

    <!-- Info Dialog -->
    <v-dialog v-model="infoDialog" max-width="600">
      <v-card>
        <v-card-title class="text-h5 bg-primary text-white pa-4">
          <LIcon start class="mr-2">mdi-information</LIcon>
          {{ $t('comparison.detail.infoDialog.title') }}
        </v-card-title>
        <v-card-text class="pa-6">
          <div class="text-body-1 mb-4">
            <LIcon color="primary" class="mr-2">mdi-robot</LIcon>
            <strong>{{ $t('comparison.detail.infoDialog.modeTitle') }}</strong>
          </div>
          <p class="mb-4">
            {{ $t('comparison.detail.infoDialog.modeBody') }}
          </p>

          <div class="text-body-1 mb-4">
            <LIcon color="primary" class="mr-2">mdi-account-details</LIcon>
            <strong>{{ $t('comparison.detail.infoDialog.personaTitle') }}</strong>
          </div>
          <p class="mb-4">
            {{ $t('comparison.detail.infoDialog.personaBody') }}
          </p>

          <div class="text-body-1 mb-4">
            <LIcon color="primary" class="mr-2">mdi-star</LIcon>
            <strong>{{ $t('comparison.detail.infoDialog.ratingTitle') }}</strong>
          </div>
          <p class="mb-4">
            {{ $t('comparison.detail.infoDialog.ratingBody') }}
          </p>

          <div class="text-body-1 mb-4">
            <LIcon color="primary" class="mr-2">mdi-infinity</LIcon>
            <strong>{{ $t('comparison.detail.infoDialog.limitsTitle') }}</strong>
          </div>
          <p class="mb-0">
            {{ $t('comparison.detail.infoDialog.limitsBody') }}
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <LBtn variant="primary" @click="infoDialog = false">
            {{ $t('comparison.detail.infoDialog.confirm') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Persona Sidebar -->
      <div class="sidebar-panel">
        <PersonaSidebar
          :persona="session?.persona_json"
          :loading="loadingSession"
          :generating-suggestion="generatingSuggestion"
          :input-disabled="!canSendMessage"
          @suggestion="onSuggestion"
        />
      </div>

      <!-- Chat Area -->
      <div class="chat-panel">
        <template v-if="loadingSession">
          <div class="loading-container">
            <v-skeleton-loader type="paragraph" />
          </div>
        </template>
        <template v-else>
          <ComparisonChat
            ref="chatComponent"
            :session-id="session?.id"
            :persona="session?.persona_json"
            @message-update="onMessageUpdate"
            @suggestion-state-change="onSuggestionStateChange"
          />
        </template>
      </div>
    </div>

    <!-- Action Bar Right Slot: Additional rating info -->
    <template #action-bar-right>
      <span class="rating-info">
        <LIcon size="16" class="mr-1">mdi-message-check</LIcon>
        {{ $t('comparison.detail.ratedMessages', { rated: getRatedMessagesCount(), total: messagesToRate }) }}
      </span>
    </template>
  </LEvaluationLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PersonaSidebar from '@/components/comparison/PersonaSidebar.vue'
import { getSession, listSessionsForUser } from '@/services/comparisonApi'
import ComparisonChat from '@/components/comparison/ComparisonChat.vue'

const route = useRoute()
const router = useRouter()

// Constants
const messagesToRate = 30

const sessionId = ref<string | null>(null)
const session = ref<any>(null)
const allSessions = ref<Array<any>>([])
const loadingSession = ref<boolean>(false)
const infoDialog = ref(false)
const chatComponent = ref<any>(null)
const generatingSuggestion = ref(false)

// Evaluation status for LEvaluationStatus component
const evaluationStatus = computed(() => {
  const rated = getRatedMessagesCount()
  if (rated === 0) return 'pending'
  if (rated >= messagesToRate) return 'done'
  return 'in_progress'
})

// Navigation computed properties
const currentIndex = computed(() => {
  if (!session.value) return -1
  return allSessions.value.findIndex(s => s.id === session.value.id)
})

const canGoPrev = computed(() => currentIndex.value > 0)
const canGoNext = computed(() => currentIndex.value >= 0 && currentIndex.value < allSessions.value.length - 1)

async function init() {
  sessionId.value = route.params.session_id as string
  try {
    allSessions.value = await listSessionsForUser()
  } catch (error) {
    console.error('Fehler beim Laden aller Sessions', error)
  }

  // Bestehende Session laden
  loadingSession.value = true
  try {
    session.value = await getSession(parseInt(sessionId.value))
  } catch (error) {
    console.error('Fehler beim Laden der Session', error)
  } finally {
    loadingSession.value = false
  }
}

function onMessageUpdate() {
  // Reload session data when messages are updated
  if (session.value) {
    getSession(session.value.id).then(updatedSession => {
      session.value = updatedSession
    }).catch(error => {
      console.error('Fehler beim Aktualisieren der Session', error)
    })
  }
}

function onSuggestion() {
  if (chatComponent.value && chatComponent.value.generateSuggestion) {
    chatComponent.value.generateSuggestion()
  }
}

function onSuggestionStateChange(generating: boolean) {
  generatingSuggestion.value = generating
}

const canSendMessage = computed(() => {
  if (!session.value?.messages) return true

  const messages = session.value.messages
  const lastMessage = messages[messages.length - 1]

  return !lastMessage ||
    lastMessage.type === 'user' ||
    (lastMessage.type === 'bot_pair' && lastMessage.selected)
})

function getRatedMessagesCount(): number {
  if (!session.value?.messages) return 0
  return session.value.messages.filter((msg: any) => msg.type === 'bot_pair' && msg.selected).length
}

function getTotalMessagesCount(): number {
  if (!session.value?.messages) return 0
  return session.value.messages.filter((msg: any) => msg.type === 'bot_pair').length
}

function goToOverview() {
  router.push({ name: 'Comparison' })
}

function navigateToPreviousSession() {
  if (!canGoPrev.value) return
  const prev = allSessions.value[currentIndex.value - 1]
  router.push({ name: 'ComparisonDetail', params: { session_id: prev.id } })
}

function navigateToNextSession() {
  if (!canGoNext.value) return
  const next = allSessions.value[currentIndex.value + 1]
  router.push({ name: 'ComparisonDetail', params: { session_id: next.id } })
}

onMounted(init)
</script>

<style scoped>
/* ============================================
   MAIN CONTENT
   ============================================ */
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar-panel {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  overflow-y: auto;
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-container {
  padding: 16px;
}

/* Rating Info in Action Bar */
.rating-info {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}
</style>
