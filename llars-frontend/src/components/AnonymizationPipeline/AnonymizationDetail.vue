<template>
  <div class="page-container">
    <!-- Header (like EvaluationSession) -->
    <div class="session-header">
      <div class="header-left">
        <LBtn variant="tonal" size="small" @click="goBack">
          <LIcon start>mdi-arrow-left</LIcon>
          Pipeline
        </LBtn>
        <div class="header-info">
          <h1>{{ conversation?.title || 'Conversation' }}</h1>
          <div class="header-meta">
            <LTag :variant="getStatusVariant(conversation?.status)" size="small">
              {{ conversation?.status }}
            </LTag>
            <LTag :variant="getDatasetStateVariant(conversation)" size="small">
              {{ getDatasetStateLabel(conversation) }}
            </LTag>
            <span class="meta-text">
              <LIcon size="14">mdi-message-outline</LIcon>
              {{ conversation?.message_count }}
            </span>
            <span class="meta-text">
              <LIcon size="14">mdi-tag-outline</LIcon>
              {{ conversation?.entity_count }}
            </span>
            <v-chip
              v-for="model in metadataModels.slice(0, 2)"
              :key="`model-${model}`"
              size="x-small"
              variant="tonal"
              color="primary"
            >
              {{ model }}
            </v-chip>
            <v-chip
              v-for="course in metadataCourses.slice(0, 2)"
              :key="`course-${course}`"
              size="x-small"
              variant="tonal"
              color="secondary"
            >
              {{ course }}
            </v-chip>
          </div>
        </div>
      </div>

      <div class="header-right">
        <!-- NER Live Progress -->
        <div v-if="getNerProgress(conversationId)" class="ner-live-progress">
          <span class="ner-live-label">
            NER: {{ getNerProgress(conversationId).message_number }}/{{ getNerProgress(conversationId).total_messages }}
          </span>
          <v-progress-linear
            :model-value="getNerProgress(conversationId).percent"
            color="#88c4c8"
            height="6"
            rounded
            style="min-width: 120px"
          />
          <span class="ner-live-entities">
            {{ getNerProgress(conversationId).entities_found }} entities
          </span>
        </div>

        <!-- Navigation Progress -->
        <div v-if="currentIndex >= 0" class="progress-indicator">
          <span class="progress-text">
            {{ currentIndex + 1 }} / {{ conversationsList.length }}
          </span>
        </div>
        <LBtn
          v-if="hasEditPermission && conversation"
          variant="accent"
          size="small"
          prepend-icon="mdi-shield-search"
          :loading="anonymizingConversation || pipelineIsNerRunning(conversationId)"
          :disabled="anonymizingConversation || pipelineIsNerRunning(conversationId)"
          @click="anonymizeConversation()"
        >
          Anonymize
        </LBtn>
        <LBtn
          v-if="hasEditPermission && conversation?.status === 'in_progress'"
          variant="primary"
          size="small"
          prepend-icon="mdi-check"
          @click="updateStatus('completed')"
        >
          Mark Completed
        </LBtn>
      </div>
    </div>

    <!-- Main Content (like RatingInterface: left=detail, right=messages) -->
    <div ref="containerRef" class="session-content">
      <!-- Left Panel: Selected Message Detail + Quality -->
      <div class="left-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <LIcon size="20" class="mr-2">mdi-clipboard-check-outline</LIcon>
          <h3>Review</h3>
          <v-spacer />
          <LEvaluationStatus
            :status="getEvalStatus()"
            :saving="qualitySaving"
          />
        </div>

        <div class="rating-content">
          <!-- NER Entity Summary (all unique entities with original → replacement) -->
          <div v-if="allEntities.length > 0" class="entity-summary">
            <div class="entity-summary-label">NER Entities ({{ allEntities.length }})</div>
            <div class="entity-summary-list">
              <div
                v-for="(ent, i) in allEntities"
                :key="i"
                class="entity-summary-row"
              >
                <span
                  class="entity-type-badge"
                  :style="{ backgroundColor: getEntityColor(ent.label) + '22', color: getEntityColor(ent.label), borderColor: getEntityColor(ent.label) + '44' }"
                >
                  {{ ent.label }}
                </span>
                <span class="entity-original">{{ ent.original }}</span>
                <LIcon size="13" class="entity-arrow">mdi-arrow-right</LIcon>
                <span class="entity-replacement">{{ ent.replacement }}</span>
                <LIcon v-if="ent.dbHit" size="13" color="success" class="entity-db-hit">mdi-check-circle</LIcon>
              </div>
            </div>
          </div>

          <!-- Quality Rating Section -->
          <div v-if="conversation" class="quality-section">
            <div class="dimension-card">
              <div class="dimension-header">
                <span class="dimension-name">Quality Rating</span>
                <span v-if="conversation.quality_rating" class="dimension-value-badge" :class="getQualityBadgeClass(conversation.quality_rating)">
                  {{ conversation.quality_rating }}/5
                </span>
              </div>
              <LRatingScale
                :model-value="conversation.quality_rating"
                :min="1"
                :max="5"
                :labels="qualityLabels"
                :show-labels="true"
                :disabled="!hasEditPermission || qualitySaving"
                variant="gradient"
                reverse-gradient
                @update:model-value="setQualityRating"
              />
            </div>

            <!-- Exclude from Export -->
            <div class="option-row">
              <LCheckbox
                v-if="hasEditPermission"
                :model-value="Boolean(conversation.exclude_from_export)"
                label="Exclude from export"
                :disabled="qualitySaving"
                @update:model-value="setExcludeFromExport"
              />
            </div>
          </div>

          <!-- Quality Notes / Feedback (resizable) -->
          <div v-if="conversation && hasEditPermission" class="feedback-section">
            <v-textarea
              v-model="qualityNotesDraft"
              label="Quality Notes"
              placeholder="Add notes about quality, issues, or observations..."
              variant="outlined"
              density="compact"
              rows="2"
              auto-grow
              hide-details
              class="resizable-notes"
              @blur="saveQualityNotes"
            />
          </div>

          <!-- Divider -->
          <div class="section-divider" />

          <!-- Selected Message Detail -->
          <template v-if="selectedMessage">
            <div class="message-detail-header">
              <h4>
                <span class="msg-num">#{{ selectedMessage.message_number }}</span>
                {{ selectedMessage.author }}
              </h4>
              <div class="detail-actions">
                <LBtn
                  v-if="!isEditing && hasEditPermission"
                  variant="primary"
                  size="small"
                  prepend-icon="mdi-pencil"
                  @click="startEditing"
                >
                  Edit
                </LBtn>
                <LBtn
                  v-if="selectedMessage.versions?.length > 0"
                  variant="text"
                  size="small"
                  prepend-icon="mdi-history"
                  @click="showVersionHistory = !showVersionHistory"
                >
                  v{{ selectedMessage.current_version }}
                </LBtn>
              </div>
            </div>

            <!-- Original Content -->
            <div class="content-section">
              <h4>Original</h4>
              <div class="content-box original">
                <pre>{{ selectedMessage.original_content }}</pre>
              </div>
            </div>

            <!-- Anonymized Content -->
            <div class="content-section">
              <div class="section-header">
                <h4>Anonymized</h4>
              </div>

              <div v-if="!isEditing" class="content-box anonymized">
                <div v-html="renderContentWithEntities(selectedMessage)"></div>
              </div>

              <div v-else class="edit-area">
                <v-textarea
                  v-model="editedContent"
                  variant="outlined"
                  rows="6"
                  auto-grow
                  placeholder="Edit anonymized content..."
                  hide-details
                />
                <v-text-field
                  v-model="changeDescription"
                  variant="outlined"
                  label="Change description"
                  placeholder="e.g., Fixed typo in name"
                  density="compact"
                  class="mt-2"
                  hide-details
                />
                <div class="edit-actions mt-2">
                  <LBtn variant="cancel" size="small" @click="cancelEditing">Cancel</LBtn>
                  <LBtn
                    variant="primary"
                    size="small"
                    prepend-icon="mdi-content-save"
                    :loading="saving"
                    @click="saveEdit"
                  >
                    Save
                  </LBtn>
                </div>
              </div>
            </div>

            <!-- Entities -->
            <div v-if="selectedMessage.entities?.length > 0" class="content-section">
              <h4>Entities ({{ selectedMessage.entities.length }})</h4>
              <div class="entities-grid">
                <div
                  v-for="entity in selectedMessage.entities"
                  :key="`${entity.label}-${entity.start_pos}`"
                  class="entity-row"
                >
                  <span
                    class="entity-type-badge"
                    :style="{ backgroundColor: getEntityColor(entity.label) + '22', color: getEntityColor(entity.label), borderColor: getEntityColor(entity.label) + '44' }"
                  >
                    {{ entity.label }}
                  </span>
                  <span class="entity-original">{{ entity.original_text }}</span>
                  <LIcon size="14" color="grey">mdi-arrow-right</LIcon>
                  <span class="entity-replacement">{{ entity.replacement_text }}</span>
                  <LIcon v-if="entity.db_hit" size="14" color="success">mdi-check-circle</LIcon>
                </div>
              </div>
            </div>

            <!-- Version History -->
            <v-expand-transition>
              <div v-if="showVersionHistory && messageVersions.length > 0" class="content-section">
                <h4>History</h4>
                <div class="version-list">
                  <div v-for="version in messageVersions" :key="version.id" class="version-item">
                    <div class="version-header">
                      <LTag variant="gray" size="small">v{{ version.version_number }}</LTag>
                      <span class="version-meta">
                        {{ formatDate(version.changed_at) }} by {{ version.changed_by_username }}
                      </span>
                    </div>
                    <div v-if="version.change_description" class="version-desc">
                      {{ version.change_description }}
                    </div>
                    <pre class="version-content">{{ version.content }}</pre>
                  </div>
                </div>
              </div>
            </v-expand-transition>
          </template>

          <!-- Metadata (collapsible, at bottom) -->
          <div v-if="metadataEntries.length > 0" class="metadata-section">
            <button class="metadata-toggle" @click="showMetadata = !showMetadata">
              <LIcon size="16">mdi-information-outline</LIcon>
              <span>Metadata ({{ metadataEntries.length }})</span>
              <LIcon size="14">{{ showMetadata ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</LIcon>
            </button>
            <v-expand-transition>
              <div v-if="showMetadata" class="metadata-grid">
                <div v-for="entry in metadataEntries" :key="entry.key" class="metadata-row">
                  <span class="metadata-key">{{ entry.key }}</span>
                  <span class="metadata-value">{{ entry.value }}</span>
                </div>
              </div>
            </v-expand-transition>
          </div>

          <!-- Empty State (no message selected) -->
          <div v-else class="empty-detail">
            <LIcon size="48" color="grey-lighten-1">mdi-message-text-outline</LIcon>
            <p>Select a message to view details</p>
          </div>
        </div>
      </div>

      <!-- Resize Handle -->
      <div
        class="resize-handle"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="handle-line" />
      </div>

      <!-- Right Panel: Conversation Messages -->
      <div class="right-panel" :style="rightPanelStyle()">
        <div class="panel-header">
          <LIcon size="20" class="mr-2">mdi-message-text-outline</LIcon>
          <h3>Messages</h3>
          <v-spacer />
          <div class="message-view-toggle">
            <button
              class="toggle-btn"
              :class="{ active: messageDisplayMode === 'original' }"
              @click="messageDisplayMode = 'original'"
            >
              Original
            </button>
            <button
              class="toggle-btn"
              :class="{ active: messageDisplayMode === 'anonymized', disabled: !isAnonymized }"
              :disabled="!isAnonymized"
              @click="isAnonymized && (messageDisplayMode = 'anonymized')"
            >
              Anonymized
            </button>
          </div>
          <span class="message-count">{{ filteredMessages.length }}</span>
        </div>

        <!-- Message Search -->
        <div class="message-search">
          <v-text-field
            v-model="messageSearch"
            placeholder="Search messages..."
            prepend-inner-icon="mdi-magnify"
            density="compact"
            variant="outlined"
            clearable
            hide-details
          />
        </div>

        <!-- Messages List -->
        <div class="panel-content conversation-view">
          <div class="messages-container">
            <div
              v-for="message in filteredMessages"
              :key="message.id"
              class="message-wrapper"
              :class="getMessageAlignment(message)"
            >
              <div
                class="message-bubble"
                :class="{
                  'bubble-client': isClientMessage(message),
                  'bubble-counselor': !isClientMessage(message),
                  'selected': selectedMessage?.id === message.id
                }"
                @click="selectMessage(message)"
              >
                <div class="message-header">
                  <div class="msg-author-badge" :class="isClientMessage(message) ? 'primary' : 'secondary'">
                    {{ message.message_number }}
                  </div>
                  <span class="message-author">{{ message.author }}</span>

                  <div class="message-tags">
                    <LTag
                      v-if="message.is_manually_edited"
                      variant="warning"
                      size="small"
                    >
                      v{{ message.current_version }}
                    </LTag>
                    <span
                      v-for="entityType in getUniqueEntityTypes(message)"
                      :key="entityType"
                      class="entity-badge"
                      :style="{ backgroundColor: getEntityColor(entityType) + '33', color: getEntityColor(entityType) }"
                    >
                      {{ entityType }}
                    </span>
                  </div>
                </div>

                <div
                  class="message-content"
                  v-html="messageDisplayMode === 'original' ? escapeHtml(message.original_content) : highlightEntities(message)"
                ></div>
              </div>
            </div>

            <div v-if="filteredMessages.length === 0" class="empty-state">
              <LIcon size="48" color="grey-lighten-1">mdi-message-off-outline</LIcon>
              <p>No messages found</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation Footer (like EvaluationSession) -->
    <div class="session-footer">
      <LBtn
        variant="tonal"
        size="small"
        :disabled="!canGoPrev"
        @click="navigateToPreviousConversation"
      >
        <LIcon start>mdi-chevron-left</LIcon>
        Previous
      </LBtn>

      <div class="footer-center">
        <LBtn
          variant="text"
          size="small"
          append-icon="mdi-chevron-double-right"
          :disabled="currentIndex < 0"
          @click="navigateToNextWithStatus('pending')"
        >
          Next Pending
        </LBtn>
        <span v-if="currentIndex >= 0" class="nav-position">
          {{ currentIndex + 1 }} / {{ conversationsList.length }}
        </span>
      </div>

      <LBtn
        variant="primary"
        size="small"
        :disabled="!canGoNext"
        @click="navigateToNextConversation"
      >
        Next
        <LIcon end>mdi-chevron-right</LIcon>
      </LBtn>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useSnackbar } from '@/composables/useSnackbar'
import { usePermissions } from '@/composables/usePermissions'
import { usePanelResize } from '@/composables/usePanelResize'
import { useAnonymizationPipeline } from '@/composables/useAnonymizationPipeline'

const route = useRoute()
const router = useRouter()
const { showSuccess, showError } = useSnackbar()
const { hasPermission, fetchPermissions } = usePermissions()

// Socket.IO session for live NER updates
const conversationId = computed(() => Number(route.params.id))
const {
  nerProgress: pipelineNerProgress,
  isNerRunning: pipelineIsNerRunning,
  getNerProgress,
  runNer: pipelineRunNer,
} = useAnonymizationPipeline({ autoJoinOverview: false, watchConversationId: conversationId.value })

// Panel Resize (left=review 45%, right=messages 55%)
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 45,
  minLeftPercent: 30,
  maxLeftPercent: 60,
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
const anonymizingConversation = ref(false)
const showVersionHistory = ref(false)
const loading = ref(false)
const qualitySaving = ref(false)
const qualityNotesDraft = ref('')
const showMetadata = ref(false)
const messageDisplayMode = ref('original')

// Navigation state
const conversationsList = ref([])

const hasEditPermission = computed(() =>
  hasPermission('feature:anonymization-pipeline:edit')
)

const isAnonymized = computed(() =>
  (conversation.value?.entity_count ?? 0) > 0
)

// Quality rating labels (matching LRatingScale pattern)
const qualityLabels = {
  min: 'Low',
  max: 'High',
  1: 'Poor',
  2: 'Below avg',
  3: 'Average',
  4: 'Good',
  5: 'Excellent'
}

const metadata = computed(() => conversation.value?.metadata || null)

// Collect all unique entities across all messages (deduplicated by label+original+replacement)
const allEntities = computed(() => {
  if (!conversation.value?.messages) return []
  const seen = new Set()
  const entities = []
  for (const msg of conversation.value.messages) {
    if (!msg.entities) continue
    for (const entity of msg.entities) {
      const key = `${entity.label}|${entity.original_text}|${entity.replacement_text}`
      if (seen.has(key)) continue
      seen.add(key)
      entities.push({
        label: entity.label,
        original: entity.original_text,
        replacement: entity.replacement_text,
        dbHit: entity.db_hit
      })
    }
  }
  // Sort by label then by original text
  return entities.sort((a, b) => a.label.localeCompare(b.label) || a.original.localeCompare(b.original))
})

const metadataSummary = computed(() => conversation.value?.metadata_summary || {})

const metadataModels = computed(() => {
  const summaryModels = metadataSummary.value?.models
  if (Array.isArray(summaryModels) && summaryModels.length > 0) return summaryModels
  const derivedModels = metadata.value?.derived?.models
  return Array.isArray(derivedModels) ? derivedModels : []
})

const metadataCourses = computed(() => {
  const summaryCourses = metadataSummary.value?.courses
  if (Array.isArray(summaryCourses) && summaryCourses.length > 0) return summaryCourses
  const derivedCourses = metadata.value?.derived?.courses
  return Array.isArray(derivedCourses) ? derivedCourses : []
})

const metadataEntries = computed(() => {
  const source = metadata.value?.raw || metadata.value
  if (!source || typeof source !== 'object') return []
  const entries = []
  collectMetadataEntries(source, '', entries, 0)
  return entries
})

const filteredMessages = computed(() => {
  if (!conversation.value?.messages) return []
  if (!messageSearch.value) return conversation.value.messages
  const search = messageSearch.value.toLowerCase()
  return conversation.value.messages.filter(
    msg =>
      (msg.anonymized_content || '').toLowerCase().includes(search) ||
      (msg.original_content || '').toLowerCase().includes(search) ||
      msg.author.toLowerCase().includes(search)
  )
})

const currentIndex = computed(() => {
  const id = parseInt(route.params.id)
  return conversationsList.value.findIndex(c => c.id === id)
})

const canGoPrev = computed(() => currentIndex.value > 0)

const canGoNext = computed(() =>
  currentIndex.value >= 0 &&
  currentIndex.value < conversationsList.value.length - 1
)

const MIN_EXPORT_QUALITY = 3

function getQualityBadgeClass(rating) {
  if (rating >= 4) return 'quality-high'
  if (rating >= 3) return 'quality-mid'
  return 'quality-low'
}

function isClientMessage(message) {
  // "vikl" = Klient, "user" = Berater/Counselor
  const author = (message.author || '').toLowerCase()
  return author !== 'user'
}

function getMessageAlignment(message) {
  return isClientMessage(message) ? 'align-left' : 'align-right'
}

function escapeHtml(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>')
}

function getEvalStatus() {
  if (!conversation.value) return 'pending'
  if (conversation.value.status === 'completed') return 'done'
  if (conversation.value.status === 'in_progress') return 'in_progress'
  return 'pending'
}

function formatMetadataValue(value) {
  const text = String(value ?? '').replace(/\s+/g, ' ').trim()
  if (!text) return ''
  return text.length > 140 ? `${text.slice(0, 137)}...` : text
}

function collectMetadataEntries(value, path, entries, depth) {
  if (entries.length >= 80 || depth > 4 || value === null || value === undefined) return

  if (Array.isArray(value)) {
    if (value.length === 0) return
    const isPrimitiveArray = value.every(item =>
      item === null || ['string', 'number', 'boolean'].includes(typeof item)
    )
    if (isPrimitiveArray) {
      const formatted = formatMetadataValue(value.join(', '))
      if (formatted) entries.push({ key: path || 'value', value: formatted })
      return
    }
    value.slice(0, 5).forEach((item, index) => {
      collectMetadataEntries(item, `${path}[${index}]`, entries, depth + 1)
    })
    if (value.length > 5) entries.push({ key: `${path}[]`, value: `+${value.length - 5} more entries` })
    return
  }

  if (typeof value === 'object') {
    Object.entries(value).forEach(([key, item]) => {
      collectMetadataEntries(item, path ? `${path}.${key}` : key, entries, depth + 1)
    })
    return
  }

  const formatted = formatMetadataValue(value)
  if (formatted) entries.push({ key: path || 'value', value: formatted })
}

// Methods
async function loadConversationsList() {
  try {
    const params = new URLSearchParams({ limit: '-1' })
    if (route.query.status) params.append('status', route.query.status)
    if (route.query.model) params.append('model', route.query.model)
    if (route.query.course) params.append('course', route.query.course)
    if (route.query.search) params.append('search', route.query.search)

    const response = await axios.get('/api/anonymization/conversations', { params })
    conversationsList.value = response.data.conversations
  } catch (error) {
    console.error('Failed to load conversations list:', error)
  }
}

async function loadConversation() {
  loading.value = true
  try {
    const response = await axios.get(`/api/anonymization/conversations/${route.params.id}`)
    conversation.value = response.data.conversation
    qualityNotesDraft.value = conversation.value?.quality_notes || ''

    if ((conversation.value.entity_count ?? 0) > 0) {
      messageDisplayMode.value = 'anonymized'
    }

    if (conversation.value.status === 'pending' && hasEditPermission.value) {
      await updateStatus('in_progress', false)
    }
  } catch (error) {
    showError('Failed to load conversation')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function getDatasetState(item) {
  if (!item) return 'unrated'
  if (item.exclude_from_export) return 'excluded'
  if (item.status !== 'completed') return 'in_review'
  if (!item.quality_rating) return 'unrated'
  if (Number(item.quality_rating) >= MIN_EXPORT_QUALITY) return 'ready'
  return 'low_quality'
}

function getDatasetStateLabel(item) {
  const labels = { ready: 'Ready', low_quality: 'Low Quality', excluded: 'Excluded', in_review: 'In Review', unrated: 'Unrated' }
  return labels[getDatasetState(item)] || 'Unrated'
}

function getDatasetStateVariant(item) {
  const variants = { ready: 'success', low_quality: 'warning', excluded: 'danger', in_review: 'info', unrated: 'gray' }
  return variants[getDatasetState(item)] || 'gray'
}

async function updateConversationQuality(payload, successMessage = 'Quality updated') {
  if (!conversation.value?.id || !hasEditPermission.value) return
  qualitySaving.value = true
  try {
    const response = await axios.patch(
      `/api/anonymization/conversations/${conversation.value.id}/quality`,
      payload
    )
    conversation.value = { ...conversation.value, ...response.data.conversation }
    qualityNotesDraft.value = conversation.value?.quality_notes || ''
    showSuccess(successMessage)
  } catch (error) {
    showError(error.response?.data?.error || 'Failed to update quality')
  } finally {
    qualitySaving.value = false
  }
}

async function setQualityRating(value) {
  const rating = value ? Number(value) : null
  // Toggle off if clicking same value
  const currentRating = conversation.value?.quality_rating || null
  const newRating = currentRating === rating ? null : rating
  if (currentRating === newRating) return
  await updateConversationQuality({ quality_rating: newRating }, 'Quality rating updated')
}

async function setExcludeFromExport(value) {
  const excludeFromExport = Boolean(value)
  if (Boolean(conversation.value?.exclude_from_export) === excludeFromExport) return
  await updateConversationQuality(
    { exclude_from_export: excludeFromExport },
    excludeFromExport ? 'Conversation excluded from export' : 'Conversation included in export'
  )
}

async function saveQualityNotes() {
  const notes = qualityNotesDraft.value.trim()
  const currentNotes = (conversation.value?.quality_notes || '').trim()
  if (notes === currentNotes) return
  await updateConversationQuality({ quality_notes: notes }, 'Quality notes saved')
}

async function selectMessage(message) {
  selectedMessage.value = message
  showVersionHistory.value = false
  isEditing.value = false

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

    const updatedMessage = response.data.message
    const msgIndex = conversation.value.messages.findIndex(m => m.id === updatedMessage.id)
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

    if (showMessage) showSuccess(`Conversation marked as ${newStatus}`)

    if (newStatus === 'completed' && canGoNext.value) {
      setTimeout(() => navigateToNextConversation(), 500)
    } else if (newStatus === 'completed' && !canGoNext.value) {
      showSuccess('All conversations completed!')
    }
  } catch (error) {
    showError('Failed to update status')
  }
}

async function anonymizeConversation(force = false) {
  if (!conversation.value?.id || !hasEditPermission.value || anonymizingConversation.value) return

  if (!force) {
    const confirmed = confirm('Run anonymization (NER) for this conversation? This will regenerate anonymized text and entities.')
    if (!confirmed) return
  }

  anonymizingConversation.value = true
  try {
    const result = await pipelineRunNer(conversation.value.id, { force })
    if (result?.started) {
      // NER is now running async - progress will be shown via socket events
      // Update local status immediately
      conversation.value.status = 'in_progress'
    }
  } catch (error) {
    const apiError = error?.response?.data?.error || error?.error || ''
    if (!force && typeof apiError === 'string' && apiError.toLowerCase().includes('manually edited')) {
      const overwriteConfirmed = confirm('This conversation contains manually edited messages. Force anonymization and overwrite those edits?')
      if (overwriteConfirmed) {
        anonymizingConversation.value = false
        await anonymizeConversation(true)
        return
      }
    }
    showError(apiError || 'Failed to anonymize conversation')
  } finally {
    anonymizingConversation.value = false
  }
}

function getStatusVariant(status) {
  const variants = { pending: 'gray', in_progress: 'info', completed: 'success', error: 'danger' }
  return variants[status] || 'gray'
}

function getEntityColor(entityType) {
  const colors = {
    PER: '#E8A087', LOC: '#A8C5E2', ORG: '#D1BC8A', DATE: '#98D4BB',
    AGE: '#E8C87A', PHONE: '#B0CA97', MAIL: '#88C4C8', AHV: '#C5A3D9',
    PLZ: '#F0B8C3', MISC: '#9E9E9E'
  }
  return colors[entityType] || colors.MISC
}

function getUniqueEntityTypes(message) {
  if (!message.entities) return []
  return [...new Set(message.entities.map(e => e.label))]
}

function highlightEntities(message) {
  const content = message.anonymized_content || ''
  if (!message.entities || message.entities.length === 0) return escapeHtml(content)

  const sortedEntities = [...message.entities].sort((a, b) => a.start_pos - b.start_pos)
  const parts = []
  let lastEnd = 0
  for (const entity of sortedEntities) {
    parts.push(escapeHtml(content.substring(lastEnd, entity.start_pos)))
    const text = escapeHtml(content.substring(entity.start_pos, entity.end_pos))
    const color = getEntityColor(entity.label)
    const safeLabel = escapeHtml(entity.label)
    const safeOriginal = escapeHtml(entity.original_text)
    const safeReplacement = escapeHtml(entity.replacement_text)
    parts.push(`<span class="entity-highlight" style="background-color: ${color}33; border-bottom: 2px solid ${color}; padding: 2px 4px; border-radius: 3px;" title="${safeLabel}: ${safeOriginal} → ${safeReplacement}">${text}</span>`)
    lastEnd = entity.end_pos
  }
  parts.push(escapeHtml(content.substring(lastEnd)))
  return parts.join('')
}

function renderContentWithEntities(message) {
  const content = message.anonymized_content || ''
  const entities = [...(message.entities || [])].sort((a, b) => a.start_pos - b.start_pos)
  const parts = []
  let lastEnd = 0
  entities.forEach(entity => {
    parts.push(escapeHtml(content.substring(lastEnd, entity.start_pos)))
    const safeReplacement = escapeHtml(entity.replacement_text)
    parts.push(`<span class="entity-highlight" style="background-color: ${getEntityColor(entity.label)}33; padding: 2px 4px; border-radius: 4px; font-weight: 500;">${safeReplacement}</span>`)
    lastEnd = entity.end_pos
  })
  parts.push(escapeHtml(content.substring(lastEnd)))
  return parts.join('')
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('de-DE', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

function goBack() {
  router.push({ path: '/anonymization', query: route.query })
}

// Navigation
function navigateToPreviousConversation() {
  if (!canGoPrev.value) return
  const prev = conversationsList.value[currentIndex.value - 1]
  router.push({ path: `/anonymization/${prev.id}`, query: route.query })
}

function navigateToNextConversation() {
  if (!canGoNext.value) return
  const next = conversationsList.value[currentIndex.value + 1]
  router.push({ path: `/anonymization/${next.id}`, query: route.query })
}

function navigateToNextWithStatus(targetStatus = 'pending') {
  if (currentIndex.value < 0) return
  const remaining = conversationsList.value.slice(currentIndex.value + 1)
  const next = remaining.find(c => c.status === targetStatus)
  if (next) {
    router.push({ path: `/anonymization/${next.id}`, query: route.query })
  } else {
    showError(`No more ${targetStatus} conversations`)
  }
}

// Keyboard navigation
function handleKeyboardNavigation(event) {
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.isContentEditable) return
  if (event.key === 'ArrowLeft' && canGoPrev.value) navigateToPreviousConversation()
  else if (event.key === 'ArrowRight' && canGoNext.value) navigateToNextConversation()
}

// Lifecycle
// Reload conversation when NER completes (socket event clears nerProgress entry)
watch(
  () => pipelineNerProgress.value[conversationId.value],
  (newVal, oldVal) => {
    // NER was running (oldVal existed) and now finished (newVal undefined)
    if (oldVal && !newVal) {
      loadConversation()
    }
  }
)

onMounted(async () => {
  try { await fetchPermissions() } catch (error) { console.error('Failed to fetch permissions:', error) }
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
  background: rgb(var(--v-theme-background));
}

/* Header - matches EvaluationSession */
.session-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
  flex: 1;
}

.header-info {
  min-width: 0;
}

.header-info h1 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.meta-text {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.ner-live-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: rgba(136, 196, 200, 0.1);
  border-radius: 16px 4px 16px 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.ner-live-label {
  color: rgba(var(--v-theme-on-surface), 0.7);
  white-space: nowrap;
}

.ner-live-entities {
  color: var(--llars-accent, #88c4c8);
  white-space: nowrap;
}

.progress-indicator {
  padding: 4px 12px;
  background: rgba(var(--v-theme-primary), 0.1);
  border-radius: 16px 4px 16px 4px;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Session Content - matches RatingInterface layout */
.session-content {
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

.left-panel {
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.message-count {
  font-size: 0.72rem;
  padding: 2px 8px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Resize Handle - matches RatingInterface */
.resize-handle {
  width: 6px;
  cursor: col-resize;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  flex-shrink: 0;
}

.resize-handle:hover,
.resize-handle.resizing {
  background: rgba(var(--v-theme-primary), 0.15);
}

.handle-line {
  width: 3px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}

/* Rating Content (left panel scrollable area) */
.rating-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* NER Entity Summary */
.entity-summary {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px 3px 8px 3px;
  padding: 10px 14px;
}

.entity-summary-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(var(--v-theme-on-surface), 0.45);
  margin-bottom: 8px;
}

.entity-summary-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.entity-summary-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 4px;
  font-size: 0.78rem;
}

.entity-summary-row .entity-type-badge {
  font-size: 0.62rem;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
  border: 1px solid;
  min-width: 32px;
  text-align: center;
  flex-shrink: 0;
}

.entity-summary-row .entity-original {
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-decoration: line-through;
  font-size: 0.76rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entity-arrow {
  flex-shrink: 0;
  opacity: 0.35;
}

.entity-summary-row .entity-replacement {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.76rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entity-db-hit {
  flex-shrink: 0;
}

/* Quality Section - uses LRatingScale */
.quality-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dimension-card {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  padding: 14px 16px;
}

.dimension-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.dimension-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.dimension-value-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
}

.dimension-value-badge.quality-high {
  background: rgba(152, 212, 187, 0.2);
  color: #5ba882;
}

.dimension-value-badge.quality-mid {
  background: rgba(209, 188, 138, 0.2);
  color: #b5993e;
}

.dimension-value-badge.quality-low {
  background: rgba(232, 160, 135, 0.2);
  color: #c4735a;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Feedback Section - matches RatingInterface */
.feedback-section {
  padding-top: 8px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.resizable-notes :deep(textarea) {
  resize: vertical;
  min-height: 48px;
}

/* Metadata Section */
.metadata-section {
  padding-top: 8px;
}

.metadata-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 0;
}

.metadata-toggle:hover {
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.metadata-grid {
  display: grid;
  gap: 4px;
  padding: 12px 0 0;
  max-height: 200px;
  overflow-y: auto;
}

.metadata-row {
  display: grid;
  grid-template-columns: minmax(140px, 200px) minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  font-size: 0.78rem;
}

.metadata-key {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  word-break: break-word;
}

.metadata-value {
  color: rgba(var(--v-theme-on-surface), 0.85);
  word-break: break-word;
}

.section-divider {
  height: 1px;
  background: rgba(var(--v-theme-on-surface), 0.08);
}

/* Message Detail Header */
.message-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.message-detail-header h4 {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
}

.msg-num {
  color: rgba(var(--v-theme-on-surface), 0.45);
  font-weight: 500;
}

.detail-actions {
  display: flex;
  gap: 4px;
}

/* Content Sections */
.content-section {
  margin-bottom: 4px;
}

.content-section h4 {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.content-box {
  padding: 12px;
  border-radius: 8px 3px 8px 3px;
  font-size: 0.88rem;
  line-height: 1.6;
}

.content-box.original {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.content-box.original pre {
  font-family: 'IBM Plex Mono', 'Courier New', monospace;
  font-size: 0.82rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.content-box.anonymized {
  background: rgba(var(--v-theme-primary), 0.04);
  border: 1px solid rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-on-surface));
}

.edit-area {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px 3px 8px 3px;
  padding: 12px;
}

.edit-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* Entities */
.entities-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.entity-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px 2px 6px 2px;
  font-size: 0.8rem;
}

.entity-type-badge {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid;
  min-width: 40px;
  text-align: center;
}

.entity-original {
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-decoration: line-through;
  font-size: 0.78rem;
}

.entity-replacement {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.78rem;
}

/* Version History */
.version-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.version-item {
  padding: 10px 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px 3px 8px 3px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.version-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.version-meta {
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.version-desc {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 6px;
}

.version-content {
  font-family: 'IBM Plex Mono', 'Courier New', monospace;
  font-size: 0.78rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.75);
}

/* Empty Detail State */
.empty-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Right Panel: Messages */
.message-search {
  flex-shrink: 0;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.conversation-view {
  background: rgba(var(--v-theme-surface-variant), 0.25);
}

/* Message View Toggle */
.message-view-toggle {
  display: inline-flex;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 6px 2px 6px 2px;
  overflow: hidden;
  margin-right: 8px;
}

.toggle-btn {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 3px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: rgba(var(--v-theme-on-surface), 0.45);
  transition: all 0.15s;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.toggle-btn:first-child {
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.15);
}

.toggle-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.06);
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.toggle-btn.active {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.toggle-btn.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.toggle-btn.disabled:hover {
  background: transparent;
}

.messages-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Message wrapper for left/right alignment */
.message-wrapper {
  display: flex;
}

.message-wrapper.align-left {
  justify-content: flex-start;
  padding-right: 40px;
}

.message-wrapper.align-right {
  justify-content: flex-end;
  padding-left: 40px;
}

.message-bubble {
  background: rgb(var(--v-theme-surface));
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  max-width: 100%;
}

.message-bubble:hover {
  box-shadow: 0 2px 8px rgba(var(--v-theme-on-surface), 0.1);
}

.message-bubble.selected {
  border-color: var(--llars-primary, #b0ca97);
}

.bubble-client {
  border-radius: 12px 4px 12px 4px;
  border-left: 3px solid var(--llars-primary, #b0ca97);
  background: rgba(176, 202, 151, 0.05);
}

.bubble-client.selected {
  background: rgba(176, 202, 151, 0.1);
}

.bubble-counselor {
  border-radius: 4px 12px 4px 12px;
  border-right: 3px solid var(--llars-secondary, #D1BC8A);
  background: rgba(209, 188, 138, 0.05);
}

.bubble-counselor.selected {
  background: rgba(209, 188, 138, 0.1);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 0.8rem;
}

.msg-author-badge {
  width: 22px;
  height: 22px;
  border-radius: 6px 2px 6px 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.msg-author-badge.primary {
  background: var(--llars-primary, #b0ca97);
}

.msg-author-badge.secondary {
  background: var(--llars-secondary, #D1BC8A);
}

.message-author {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: capitalize;
  font-size: 0.78rem;
}

.message-tags {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.entity-badge {
  font-size: 0.6rem;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 4px;
}

.message-content {
  font-size: 0.88rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.85);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  gap: 8px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Navigation Footer - matches EvaluationSession */
.session-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 24px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
}

.footer-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-position {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  min-width: 60px;
  text-align: center;
}

/* Scrollbar styling */
.rating-content::-webkit-scrollbar,
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.rating-content::-webkit-scrollbar-track,
.panel-content::-webkit-scrollbar-track {
  background: transparent;
}

.rating-content::-webkit-scrollbar-thumb,
.panel-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

/* Responsive */
@media (max-width: 960px) {
  .session-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
    padding: 12px 16px;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }

  .session-content {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    width: 100% !important;
  }

  .left-panel {
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  }

  .resize-handle {
    display: none;
  }
}
</style>
