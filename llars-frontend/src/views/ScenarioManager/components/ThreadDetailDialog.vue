<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="900" scrollable>
    <v-card v-if="thread">
      <!-- Header -->
      <v-card-title class="dialog-header">
        <div class="header-content">
          <LIcon size="24" color="primary" class="mr-3">mdi-email-outline</LIcon>
          <div class="header-text">
            <span class="thread-subject">{{ thread.subject || $t('scenarioManager.data.noSubject') }}</span>
            <span class="thread-meta">
              <span v-if="thread.sender">{{ thread.sender }}</span>
              <span v-if="thread.messages?.length" class="ml-2">
                {{ $t('scenarioManager.threadDetail.messageCount', { count: thread.messages.length }) }}
              </span>
            </span>
          </div>
        </div>
        <v-btn icon variant="text" @click="$emit('update:modelValue', false)">
          <LIcon>mdi-close</LIcon>
        </v-btn>
      </v-card-title>

      <v-card-text class="dialog-content pa-0">
        <div class="content-split">
          <!-- Left: Messages -->
          <div class="messages-panel">
            <div class="panel-header">
              <LIcon size="18" class="mr-2">mdi-message-text-outline</LIcon>
              {{ $t('scenarioManager.threadDetail.messages') }}
            </div>
            <div class="messages-list">
              <div
                v-for="message in thread.messages"
                :key="message.id"
                class="message-item"
                :class="getMessageClass(message)"
              >
                <div class="message-header">
                  <LIcon size="16" class="mr-1">{{ getRoleIcon(message) }}</LIcon>
                  <span class="sender-name">{{ message.sender || message.role || 'Unknown' }}</span>
                  <span v-if="message.timestamp" class="timestamp">
                    {{ formatTime(message.timestamp) }}
                  </span>
                </div>
                <div class="message-content" v-html="formatContent(message.content)"></div>
              </div>
            </div>
          </div>

          <!-- Right: Votes -->
          <div class="votes-panel">
            <div class="panel-header">
              <LIcon size="18" class="mr-2">mdi-vote-outline</LIcon>
              {{ $t('scenarioManager.threadDetail.evaluations') }}
            </div>

            <div v-if="!thread.votes?.length" class="no-votes">
              <LIcon size="40" color="grey">mdi-clipboard-text-off-outline</LIcon>
              <span>{{ $t('scenarioManager.threadDetail.noVotes') }}</span>
            </div>

            <div v-else class="votes-list">
              <!-- Human Votes -->
              <div v-if="humanVotes.length" class="vote-section">
                <div class="section-title">
                  <LIcon size="16" class="mr-1">mdi-account-group-outline</LIcon>
                  {{ $t('scenarioManager.threadDetail.humanVotes') }}
                </div>
                <div v-for="vote in humanVotes" :key="'human-' + vote.user_id" class="vote-card">
                  <div class="vote-header">
                    <LIcon size="16" class="mr-1">mdi-account-outline</LIcon>
                    <span class="voter-name">{{ vote.username }}</span>
                  </div>
                  <div class="vote-content">
                    <!-- Authenticity vote -->
                    <LTag
                      v-if="vote.vote"
                      :variant="getVoteVariant(vote.vote)"
                      size="sm"
                    >
                      {{ vote.vote }}
                    </LTag>
                    <!-- Rating dimensions -->
                    <div v-if="vote.ratings" class="ratings-display">
                      <div v-for="(value, key) in vote.ratings" :key="key" class="rating-item">
                        <span class="rating-label">{{ key }}:</span>
                        <span class="rating-value">{{ value }}</span>
                      </div>
                    </div>
                    <!-- Ranking votes -->
                    <div v-if="vote.rankings && vote.rankings.length > 0" class="rankings-display">
                      <div class="rankings-header">
                        <span class="rankings-summary">
                          {{ vote.ranked_count }}/{{ vote.total_features }} Features bewertet
                        </span>
                      </div>
                      <div class="rankings-list">
                        <div v-for="ranking in vote.rankings" :key="ranking.feature_id" class="ranking-row">
                          <span class="feature-id">#{{ ranking.feature_id }}</span>
                          <LTag :variant="getBucketVariant(ranking.bucket)" size="sm">
                            {{ ranking.bucket }}
                          </LTag>
                        </div>
                      </div>
                    </div>
                    <div v-else-if="vote.ranked_count === 0 && vote.total_features > 0" class="no-rankings">
                      <span class="text-medium-emphasis">Noch keine Bewertungen</span>
                    </div>
                    <span v-if="vote.confidence" class="confidence">
                      {{ $t('scenarioManager.threadDetail.confidence') }}: {{ Math.round(vote.confidence * 100) }}%
                    </span>
                  </div>
                </div>
              </div>

              <!-- LLM Votes -->
              <div v-if="llmVotes.length" class="vote-section">
                <div class="section-title">
                  <LIcon size="16" class="mr-1">mdi-robot-outline</LIcon>
                  {{ $t('scenarioManager.threadDetail.llmVotes') }}
                </div>
                <div v-for="vote in llmVotes" :key="'llm-' + vote.model_id" class="vote-card llm">
                  <div class="vote-header">
                    <LIcon size="16" class="mr-1">mdi-robot-outline</LIcon>
                    <span class="voter-name">{{ formatLlmModelName(vote.model_id) }}</span>
                  </div>
                  <div class="vote-content">
                    <!-- Authenticity vote -->
                    <LTag
                      v-if="vote.vote"
                      :variant="getVoteVariant(vote.vote)"
                      size="sm"
                    >
                      {{ vote.vote }}
                    </LTag>
                    <!-- Labeling label -->
                    <LTag
                      v-if="vote.label"
                      :variant="getLabelVariant(vote.label)"
                      size="sm"
                    >
                      {{ vote.label }}
                    </LTag>
                    <!-- Overall rating (mail_rating) -->
                    <div v-if="vote.overall_rating" class="overall-rating">
                      <span class="rating-label">Bewertung:</span>
                      <span class="rating-value">{{ vote.overall_rating }}/5</span>
                    </div>
                    <div v-if="vote.overall_score" class="overall-rating">
                      <span class="rating-label">Gesamtwertung:</span>
                      <span class="rating-value">{{ vote.overall_score }}</span>
                    </div>
                    <!-- Rating dimensions -->
                    <div v-if="vote.ratings && !vote.rankings" class="ratings-display">
                      <div v-for="(value, key) in vote.ratings" :key="key" class="rating-item">
                        <span class="rating-label">{{ key }}:</span>
                        <span class="rating-value">{{ value }}</span>
                      </div>
                    </div>
                    <!-- Ranking votes -->
                    <div v-if="vote.rankings && vote.rankings.length > 0" class="rankings-display">
                      <div class="rankings-list">
                        <div v-for="(ranking, idx) in vote.rankings" :key="idx" class="ranking-row">
                          <span v-if="ranking.feature_id" class="feature-id">#{{ ranking.feature_id }}</span>
                          <LTag :variant="getBucketVariant(ranking.bucket || ranking)" size="sm">
                            {{ ranking.bucket || ranking }}
                          </LTag>
                        </div>
                      </div>
                    </div>
                    <div v-else-if="vote.rankings === null" class="no-rankings">
                      <span class="text-medium-emphasis">Auswertung ausstehend</span>
                    </div>
                    <span v-if="vote.confidence" class="confidence">
                      {{ $t('scenarioManager.threadDetail.confidence') }}: {{ vote.confidence }}
                    </span>
                    <div v-if="vote.reasoning" class="reasoning">
                      <span class="reasoning-label">{{ $t('scenarioManager.threadDetail.reasoning') }}:</span>
                      <span class="reasoning-text">{{ vote.reasoning }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <LBtn variant="text" @click="$emit('update:modelValue', false)">
          {{ $t('common.close') }}
        </LBtn>
      </v-card-actions>
    </v-card>

    <!-- Loading State -->
    <v-card v-else>
      <v-card-text class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="48" />
        <p class="mt-4">{{ $t('common.loading') }}</p>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { parseUserProviderModelId } from '@/utils/formatters'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  thread: {
    type: Object,
    default: null
  }
})

defineEmits(['update:modelValue'])

const humanVotes = computed(() => {
  return (props.thread?.votes || []).filter(v => v.type === 'human')
})

const llmVotes = computed(() => {
  return (props.thread?.votes || []).filter(v => v.type === 'llm')
})

function formatLlmModelName(modelId) {
  const parsed = parseUserProviderModelId(modelId)
  if (parsed?.displayName) {
    return parsed.displayName
  }
  return modelId || 'LLM'
}

function getMessageClass(message) {
  const role = message.role?.toLowerCase() || message.sender?.toLowerCase() || ''
  if (role.includes('client') || role.includes('klient') || role.includes('user')) {
    return 'message-client'
  }
  if (role.includes('berater') || role.includes('assistant') || role.includes('counselor')) {
    return 'message-counselor'
  }
  return ''
}

function getRoleIcon(message) {
  const role = message.role?.toLowerCase() || message.sender?.toLowerCase() || ''
  if (role.includes('client') || role.includes('klient') || role.includes('user')) {
    return 'mdi-account-outline'
  }
  if (role.includes('berater') || role.includes('assistant') || role.includes('counselor')) {
    return 'mdi-account-tie-outline'
  }
  return 'mdi-account-outline'
}

function getVoteVariant(vote) {
  const v = vote?.toLowerCase() || ''
  if (v.includes('real') || v.includes('echt') || v.includes('authentic')) {
    return 'success'
  }
  if (v.includes('fake') || v.includes('ai') || v.includes('ki')) {
    return 'danger'
  }
  return 'default'
}

function getBucketVariant(bucket) {
  const b = bucket?.toLowerCase() || ''
  if (b.includes('gut') || b.includes('good') || b.includes('sehr gut') || b.includes('very good')) {
    return 'success'
  }
  if (b.includes('schlecht') || b.includes('poor') || b.includes('bad')) {
    return 'danger'
  }
  if (b.includes('mittel') || b.includes('medium') || b.includes('average')) {
    return 'warning'
  }
  return 'info'
}

function getLabelVariant(label) {
  const l = label?.toLowerCase() || ''
  if (l.includes('positiv') || l.includes('positive') || l.includes('good')) {
    return 'success'
  }
  if (l.includes('negativ') || l.includes('negative') || l.includes('bad')) {
    return 'danger'
  }
  if (l.includes('neutral')) {
    return 'warning'
  }
  return 'info'
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleString()
  } catch {
    return timestamp
  }
}

function formatContent(content) {
  if (!content) return ''
  // Simple HTML escaping and line break handling
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.dialog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.header-content {
  display: flex;
  align-items: flex-start;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.thread-subject {
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.3;
}

.thread-meta {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 4px;
}

.dialog-content {
  height: 500px;
}

.content-split {
  display: flex;
  height: 100%;
}

.messages-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.votes-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 0.9rem;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.message-item {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
}

.message-item.message-client {
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.message-item.message-counselor {
  background-color: rgba(var(--v-theme-secondary), 0.08);
  border-left: 3px solid rgb(var(--v-theme-secondary));
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.8rem;
}

.sender-name {
  font-weight: 600;
}

.timestamp {
  margin-left: auto;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.message-content {
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.votes-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.no-votes {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-align: center;
}

.vote-section {
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 8px;
  text-transform: uppercase;
}

.vote-card {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.04);
}

.vote-card.llm {
  background-color: rgba(136, 196, 200, 0.1);
}

.vote-header {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.voter-name {
  font-weight: 500;
}

.vote-content {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.confidence {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.ratings-display {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rating-item {
  font-size: 0.8rem;
}

.rating-label {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.rating-value {
  font-weight: 600;
}

.overall-rating {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-radius: 4px;
  font-size: 0.85rem;
}

.overall-rating .rating-label {
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.overall-rating .rating-value {
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}

.reasoning {
  width: 100%;
  margin-top: 8px;
  font-size: 0.8rem;
  padding: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 4px;
}

.reasoning-label {
  font-weight: 500;
  display: block;
  margin-bottom: 4px;
}

.reasoning-text {
  color: rgba(var(--v-theme-on-surface), 0.8);
  display: block;
}

.rankings-display {
  width: 100%;
  margin-top: 4px;
}

.rankings-header {
  margin-bottom: 8px;
}

.rankings-summary {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.rankings-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 4px;
}

.feature-id {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  min-width: 40px;
}

.no-rankings {
  font-size: 0.8rem;
  padding: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 4px;
  text-align: center;
}
</style>
