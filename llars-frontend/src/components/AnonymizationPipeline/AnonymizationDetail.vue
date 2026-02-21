<template>
  <div class="page-container">
    <!-- Header -->
    <div class="detail-header">
      <div>
        <h1>{{ conversation?.title || 'Conversation' }}</h1>
        <div class="d-flex align-center gap-2 mt-2 flex-wrap">
          <LTag :variant="getStatusVariant(conversation?.status)">
            {{ conversation?.status }}
          </LTag>
          <span class="text-caption text-medium-emphasis">
            {{ conversation?.message_count }} messages · {{ conversation?.entity_count }} entities
          </span>
        </div>
      </div>

      <div class="d-flex gap-2 flex-wrap">
        <LBtn variant="cancel" prepend-icon="mdi-arrow-left" @click="goBack">
          Back
        </LBtn>
        <LBtn
          v-if="hasEditPermission && conversation?.status === 'in_progress'"
          variant="success"
          prepend-icon="mdi-check"
          @click="updateStatus('completed')"
        >
          Mark Completed
        </LBtn>
      </div>
    </div>

    <!-- Main Content -->
    <div ref="containerRef" class="main-content">
      <!-- Left Panel: Message List -->
      <div class="left-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <h3>Messages</h3>
          <v-text-field
            v-model="messageSearch"
            placeholder="Search messages..."
            prepend-inner-icon="mdi-magnify"
            density="compact"
            variant="outlined"
            clearable
            hide-details
            class="mt-2"
          />
        </div>

        <div class="panel-content conversation-view">
          <div class="messages-container">
            <div
              v-for="message in filteredMessages"
              :key="message.id"
              class="message-bubble"
              :class="{
                'user-message': message.author === 'vikl',
                'assistant-message': message.author === 'user',
                'selected': selectedMessage?.id === message.id
              }"
              @click="selectMessage(message)"
            >
              <!-- Message Header -->
              <div class="message-header">
                <v-avatar :color="getAuthorColor(message.author)" size="24" class="mr-2">
                  <span class="text-caption">{{ message.message_number }}</span>
                </v-avatar>
                <span class="message-author">{{ message.author }}</span>

                <!-- Tags -->
                <div class="message-tags ml-auto">
                  <LTag
                    v-if="message.is_manually_edited"
                    variant="warning"
                    size="small"
                    class="mr-1"
                  >
                    Edited v{{ message.current_version }}
                  </LTag>

                  <!-- Entity badges -->
                  <v-chip
                    v-for="entityType in getUniqueEntityTypes(message)"
                    :key="entityType"
                    :color="getEntityColor(entityType)"
                    size="x-small"
                    class="mr-1"
                  >
                    {{ entityType }}
                  </v-chip>
                </div>
              </div>

              <!-- Message Content -->
              <div class="message-content" v-html="highlightEntities(message)"></div>
            </div>

            <div v-if="filteredMessages.length === 0" class="empty-state pa-4 text-center">
              <v-icon size="48" color="grey-lighten-1">mdi-message-off-outline</v-icon>
              <p class="text-medium-emphasis mt-2">No messages found</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Resize Divider -->
      <div
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Right Panel: Message Editor -->
      <div class="right-panel" :style="rightPanelStyle()">
        <div v-if="selectedMessage" class="panel-header">
          <div class="d-flex align-center justify-space-between">
            <h3>Message #{{ selectedMessage.message_number }} - {{ selectedMessage.author }}</h3>
            <LBtn
              v-if="selectedMessage.versions?.length > 0"
              variant="text"
              size="small"
              prepend-icon="mdi-history"
              @click="showVersionHistory = !showVersionHistory"
            >
              History ({{ selectedMessage.current_version }})
            </LBtn>
          </div>
        </div>

        <div v-if="selectedMessage" class="panel-content">
          <!-- Original Content (read-only) -->
          <div class="content-section">
            <h4>Original Content</h4>
            <v-card variant="outlined" class="pa-3">
              <pre class="original-content">{{ selectedMessage.original_content }}</pre>
            </v-card>
          </div>

          <!-- Anonymized Content (editable) -->
          <div class="content-section mt-4">
            <div class="d-flex align-center justify-space-between mb-2">
              <h4>Anonymized Content</h4>
              <LBtn
                v-if="!isEditing && hasEditPermission"
                variant="primary"
                size="small"
                prepend-icon="mdi-pencil"
                @click="startEditing"
              >
                Edit
              </LBtn>
            </div>

            <!-- View Mode -->
            <v-card v-if="!isEditing" variant="outlined" class="pa-3">
              <div class="anonymized-content" v-html="renderContentWithEntities(selectedMessage)"></div>
            </v-card>

            <!-- Edit Mode -->
            <div v-else>
              <v-textarea
                v-model="editedContent"
                variant="outlined"
                rows="8"
                auto-grow
                placeholder="Edit anonymized content..."
              />
              <v-text-field
                v-model="changeDescription"
                variant="outlined"
                label="Change description (optional)"
                placeholder="e.g., Fixed typo in name replacement"
                density="comfortable"
                class="mt-2"
              />
              <div class="d-flex gap-2 mt-2">
                <LBtn variant="cancel" @click="cancelEditing">Cancel</LBtn>
                <LBtn
                  variant="success"
                  prepend-icon="mdi-content-save"
                  :loading="saving"
                  @click="saveEdit"
                >
                  Save Changes
                </LBtn>
              </div>
            </div>
          </div>

          <!-- Entities -->
          <div class="content-section mt-4">
            <h4>Detected Entities ({{ selectedMessage.entities?.length || 0 }})</h4>
            <v-data-table
              :headers="entityHeaders"
              :items="selectedMessage.entities || []"
              density="compact"
              class="mt-2"
            >
              <template #[`item.label`]="{ item }">
                <v-chip :color="getEntityColor(item.label)" size="small">
                  {{ item.label }}
                </v-chip>
              </template>

              <template #[`item.db_hit`]="{ item }">
                <v-icon v-if="item.db_hit" color="success" size="small">
                  mdi-check-circle
                </v-icon>
                <v-icon v-else color="grey" size="small">
                  mdi-minus-circle
                </v-icon>
              </template>
            </v-data-table>
          </div>

          <!-- Version History -->
          <v-expand-transition>
            <div v-if="showVersionHistory" class="content-section mt-4">
              <h4>Version History</h4>
              <v-timeline side="end" density="compact" class="mt-2">
                <v-timeline-item
                  v-for="version in messageVersions"
                  :key="version.id"
                  dot-color="primary"
                  size="small"
                >
                  <template #opposite>
                    <div class="text-caption">v{{ version.version_number }}</div>
                  </template>
                  <v-card variant="outlined">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis mb-2">
                        {{ formatDate(version.changed_at) }} by {{ version.changed_by_username }}
                      </div>
                      <div v-if="version.change_description" class="text-body-2 mb-2">
                        {{ version.change_description }}
                      </div>
                      <pre class="version-content">{{ version.content }}</pre>
                    </v-card-text>
                  </v-card>
                </v-timeline-item>
              </v-timeline>
            </div>
          </v-expand-transition>
        </div>

        <!-- Empty State -->
        <div v-else class="panel-content d-flex align-center justify-center">
          <div class="text-center text-medium-emphasis">
            <v-icon size="64" color="grey-lighten-1">mdi-message-text-outline</v-icon>
            <p class="mt-4">Select a message to view details</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Bar (Navigation) -->
    <div class="action-bar">
      <div class="navigation-actions">
        <LBtn
          variant="text"
          prepend-icon="mdi-chevron-left"
          :disabled="!canGoPrev"
          @click="navigateToPreviousConversation"
        >
          Vorherige
        </LBtn>

        <div v-if="currentIndex >= 0" class="progress-indicator">
          {{ currentIndex + 1 }} / {{ conversationsList.length }}
        </div>

        <LBtn
          variant="text"
          append-icon="mdi-chevron-right"
          :disabled="!canGoNext"
          @click="navigateToNextConversation"
        >
          Nächste
        </LBtn>

        <LTooltip text="Zur nächsten ausstehenden Konversation springen" location="top">
          <LBtn
            variant="text"
            size="small"
            append-icon="mdi-chevron-double-right"
            :disabled="currentIndex < 0"
            @click="navigateToNextWithStatus('pending')"
          >
            Nächste Ausstehend
          </LBtn>
        </LTooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useSnackbar } from '@/composables/useSnackbar'
import { usePermissions } from '@/composables/usePermissions'
import { usePanelResize } from '@/composables/usePanelResize'

const route = useRoute()
const router = useRouter()
const { showSuccess, showError } = useSnackbar()
const { hasPermission } = usePermissions()

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 35,
  minLeftPercent: 25,
  maxLeftPercent: 50,
  storageKey: 'anonymization-detail-panel-width'
})

// State
const conversation = ref(null)
const selectedMessage = ref(null)
const messageVersions = ref([])
const messageSearch = ref('')
const isEditing = ref(false)
const editedContent = ref('')
const changeDescription = ref('')
const saving = ref(false)
const showVersionHistory = ref(false)
const loading = ref(false)

// Navigation state
const conversationsList = ref([])

const hasEditPermission = computed(() =>
  hasPermission('feature:anonymization-pipeline:edit')
)

const filteredMessages = computed(() => {
  if (!conversation.value?.messages) return []
  if (!messageSearch.value) return conversation.value.messages

  const search = messageSearch.value.toLowerCase()
  return conversation.value.messages.filter(
    msg =>
      msg.anonymized_content.toLowerCase().includes(search) ||
      msg.author.toLowerCase().includes(search)
  )
})

// Navigation computed properties
const currentIndex = computed(() => {
  const id = parseInt(route.params.id)
  return conversationsList.value.findIndex(c => c.id === id)
})

const canGoPrev = computed(() => currentIndex.value > 0)

const canGoNext = computed(() =>
  currentIndex.value >= 0 &&
  currentIndex.value < conversationsList.value.length - 1
)

const entityHeaders = [
  { title: 'Type', key: 'label', sortable: true },
  { title: 'Original', key: 'original_text', sortable: false },
  { title: 'Replacement', key: 'replacement_text', sortable: false },
  { title: 'Position', key: 'start_pos', sortable: false },
  { title: 'DB Hit', key: 'db_hit', sortable: true, align: 'center' }
]

// Methods
async function loadConversationsList() {
  try {
    // Read filter parameters from route query
    const params = new URLSearchParams({
      limit: '-1'  // Get all for navigation
    })

    if (route.query.status) {
      params.append('status', route.query.status)
    }
    if (route.query.search) {
      params.append('search', route.query.search)
    }

    const response = await axios.get('/api/anonymization/conversations', { params })
    conversationsList.value = response.data.conversations
  } catch (error) {
    console.error('Failed to load conversations list:', error)
    showError('Fehler beim Laden der Konversationsliste')
  }
}

async function loadConversation() {
  loading.value = true
  try {
    const response = await axios.get(
      `/api/anonymization/conversations/${route.params.id}`
    )
    conversation.value = response.data.conversation

    // Auto-start review if conversation is pending
    if (conversation.value.status === 'pending' && hasEditPermission.value) {
      await updateStatus('in_progress', false)  // Don't show message for auto-start
    }
  } catch (error) {
    showError('Failed to load conversation')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function selectMessage(message) {
  selectedMessage.value = message
  showVersionHistory.value = false
  isEditing.value = false

  // Load version history if message has been edited
  if (message.is_manually_edited) {
    try {
      const response = await axios.get(`/api/anonymization/messages/${message.id}/versions`)
      messageVersions.value = response.data.versions
    } catch (error) {
      console.error('Failed to load version history:', error)
    }
  } else {
    messageVersions.value = []
  }
}

function startEditing() {
  editedContent.value = selectedMessage.value.anonymized_content
  changeDescription.value = ''
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
  editedContent.value = ''
  changeDescription.value = ''
}

async function saveEdit() {
  if (!editedContent.value.trim()) {
    showError('Content cannot be empty')
    return
  }

  saving.value = true
  try {
    const response = await axios.patch(
      `/api/anonymization/messages/${selectedMessage.value.id}`,
      {
        anonymized_content: editedContent.value,
        change_description: changeDescription.value
      }
    )

    // Update local data
    const updatedMessage = response.data.message
    const msgIndex = conversation.value.messages.findIndex(
      m => m.id === updatedMessage.id
    )
    if (msgIndex !== -1) {
      conversation.value.messages[msgIndex] = updatedMessage
      selectedMessage.value = updatedMessage
    }

    messageVersions.value.push(response.data.version)

    showSuccess('Message updated successfully')
    isEditing.value = false
  } catch (error) {
    showError(error.response?.data?.error || 'Failed to save changes')
  } finally {
    saving.value = false
  }
}

async function updateStatus(newStatus, showMessage = true) {
  try {
    await axios.patch(`/api/anonymization/conversations/${conversation.value.id}/status`, {
      status: newStatus
    })
    conversation.value.status = newStatus

    if (showMessage) {
      showSuccess(`Conversation marked as ${newStatus}`)
    }

    // Auto-advance to next conversation when marking as completed
    if (newStatus === 'completed' && canGoNext.value) {
      setTimeout(() => {
        navigateToNextConversation()
      }, 500)  // Small delay so user sees success message
    } else if (newStatus === 'completed' && !canGoNext.value) {
      showSuccess('Alle Konversationen abgeschlossen!')
    }
  } catch (error) {
    showError('Failed to update status')
  }
}

function getStatusVariant(status) {
  const variants = {
    pending: 'gray',
    in_progress: 'info',
    completed: 'success',
    error: 'danger'
  }
  return variants[status] || 'gray'
}

function getEntityColor(entityType) {
  const colors = {
    PER: '#E8A087',   // Soft Coral
    LOC: '#A8C5E2',   // Soft Blue
    ORG: '#D1BC8A',   // Golden Beige
    DATE: '#98D4BB',  // Soft Mint
    AGE: '#E8C87A',   // Soft Gold
    PHONE: '#B0CA97', // Sage Green
    MAIL: '#88C4C8',  // Soft Teal
    AHV: '#C5A3D9',   // Soft Purple
    PLZ: '#F0B8C3',   // Soft Pink
    MISC: '#9E9E9E'   // Gray
  }
  return colors[entityType] || colors.MISC
}

function getUniqueEntityTypes(message) {
  if (!message.entities) return []
  return [...new Set(message.entities.map(e => e.label))]
}

function getAuthorColor(author) {
  // vikl (client) = primary, user (counselor) = secondary
  return author === 'vikl' ? 'primary' : 'secondary'
}

function highlightEntities(message) {
  let content = message.anonymized_content || ''

  if (!message.entities || message.entities.length === 0) {
    return content
  }

  // Sort entities by start_pos in reverse to replace from end to start
  const sortedEntities = [...message.entities].sort((a, b) => b.start_pos - a.start_pos)

  for (const entity of sortedEntities) {
    const before = content.substring(0, entity.start_pos)
    const text = content.substring(entity.start_pos, entity.end_pos)
    const after = content.substring(entity.end_pos)

    const color = getEntityColor(entity.label)
    content = `${before}<span class="entity-highlight" style="background-color: ${color}33; border-bottom: 2px solid ${color}; padding: 2px 4px; border-radius: 3px;" title="${entity.label}: ${entity.original_text} → ${entity.replacement_text}">${text}</span>${after}`
  }

  return content
}

function renderContentWithEntities(message) {
  let content = message.anonymized_content
  const entities = [...(message.entities || [])].sort((a, b) => b.start_pos - a.start_pos)

  entities.forEach(entity => {
    const highlighted = `<span class="entity-highlight" style="background-color: ${getEntityColor(
      entity.label
    )}33; padding: 2px 4px; border-radius: 4px; font-weight: 500;">${entity.replacement_text}</span>`
    content =
      content.substring(0, entity.start_pos) +
      highlighted +
      content.substring(entity.end_pos)
  })

  return content.replace(/\n/g, '<br>')
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function goBack() {
  router.push('/anonymization')
}

// Navigation functions
function navigateToPreviousConversation() {
  if (!canGoPrev.value) return
  const prev = conversationsList.value[currentIndex.value - 1]
  router.push({
    path: `/anonymization/${prev.id}`,
    query: route.query  // Preserve filter state
  })
}

function navigateToNextConversation() {
  if (!canGoNext.value) return
  const next = conversationsList.value[currentIndex.value + 1]
  router.push({
    path: `/anonymization/${next.id}`,
    query: route.query  // Preserve filter state
  })
}

// Navigate to next conversation with specific status
function navigateToNextWithStatus(targetStatus = 'pending') {
  if (currentIndex.value < 0) return

  // Find next conversation matching status
  const remaining = conversationsList.value.slice(currentIndex.value + 1)
  const next = remaining.find(c => c.status === targetStatus)

  if (next) {
    router.push({
      path: `/anonymization/${next.id}`,
      query: route.query
    })
  } else {
    showError(`Keine weiteren ${targetStatus} Konversationen`)
  }
}

// Keyboard navigation
function handleKeyboardNavigation(event) {
  // Don't interfere with text input
  if (
    event.target.tagName === 'INPUT' ||
    event.target.tagName === 'TEXTAREA' ||
    event.target.isContentEditable
  ) {
    return
  }

  if (event.key === 'ArrowLeft' && canGoPrev.value) {
    navigateToPreviousConversation()
  } else if (event.key === 'ArrowRight' && canGoNext.value) {
    navigateToNextConversation()
  }
}

// Lifecycle
onMounted(() => {
  loadConversationsList()
  loadConversation()
  window.addEventListener('keydown', handleKeyboardNavigation)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyboardNavigation)
})
</script>

<style scoped>
.page-container {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  flex-shrink: 0;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.detail-header h1 {
  font-size: 1.5rem;
  font-weight: 500;
}

.gap-2 {
  gap: 8px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  flex-shrink: 0;
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.panel-header h3 {
  font-size: 1.1rem;
  font-weight: 500;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.resize-divider {
  width: 8px;
  background: rgba(0, 0, 0, 0.05);
  cursor: col-resize;
  position: relative;
  flex-shrink: 0;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: var(--llars-primary);
}

.resize-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 3px;
  height: 48px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.content-section h4 {
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 8px;
}

.original-content,
.version-content {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}

.anonymized-content {
  font-size: 0.95rem;
  line-height: 1.6;
}

.entity-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

:deep(.v-list-item--active) {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

/* Conversation View Styles */
.conversation-view {
  background: #f5f5f5;
}

.messages-container {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-bubble {
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.2s ease;
}

.message-bubble:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.message-bubble.selected {
  border: 2px solid var(--llars-primary);
  background: rgba(176, 202, 151, 0.05);
}

.user-message {
  align-self: flex-end;
  margin-left: auto;
  max-width: 75%;
  border-right: 4px solid var(--llars-primary);
  border-left: none;
  background: rgba(176, 202, 151, 0.08);
}

.assistant-message {
  align-self: flex-start;
  margin-right: auto;
  max-width: 75%;
  border-left: 4px solid var(--llars-secondary);
  background: rgba(209, 188, 138, 0.08);
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
}

.message-author {
  text-transform: capitalize;
}

.message-tags {
  display: flex;
  align-items: center;
  gap: 4px;
}

.message-content {
  font-size: 0.95rem;
  line-height: 1.5;
  color: rgba(0, 0, 0, 0.87);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.entity-highlight {
  display: inline;
  transition: all 0.2s ease;
  cursor: help;
}

.entity-highlight:hover {
  opacity: 0.8;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

/* Action Bar */
.action-bar {
  flex-shrink: 0;
  padding: 12px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navigation-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.progress-indicator {
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  padding: 4px 12px;
  background: rgba(var(--v-theme-primary), 0.1);
  border-radius: 12px;
}
</style>
