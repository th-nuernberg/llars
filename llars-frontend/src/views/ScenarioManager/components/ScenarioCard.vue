<template>
  <div
    class="scenario-card"
    :class="{
      'is-owner': scenario.is_owner,
      'is-rejected': isRejected
    }"
    @click="handleClick"
  >
    <!-- Rejected Overlay -->
    <div v-if="isRejected" class="rejected-overlay">
      <div class="rejected-content">
        <LIcon size="24" color="grey">mdi-email-remove-outline</LIcon>
        <span class="rejected-text">{{ $t('scenarioManager.invitation.rejected') }}</span>
        <LBtn variant="primary" size="small" @click.stop="handleAccept" :loading="responding">
          <LIcon start size="16">mdi-email-check-outline</LIcon>
          {{ $t('scenarioManager.invitation.acceptAgain') }}
        </LBtn>
      </div>
    </div>

    <!-- Header -->
    <div class="card-header">
      <div class="type-icon" :style="{ backgroundColor: typeColor + '20' }">
        <LIcon :color="typeColor">{{ typeIcon }}</LIcon>
      </div>
      <div class="card-menu">
        <v-menu>
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon
              size="small"
              variant="text"
              @click.stop
            >
              <LIcon size="18">mdi-dots-vertical</LIcon>
            </v-btn>
          </template>
          <v-list density="compact">
            <v-list-item @click.stop="$emit('click')">
              <template #prepend>
                <LIcon size="18" class="mr-2">mdi-open-in-new</LIcon>
              </template>
              <v-list-item-title>{{ $t('scenarioManager.actions.open') }}</v-list-item-title>
            </v-list-item>
            <v-list-item v-if="scenario.is_owner" @click.stop="$emit('edit')">
              <template #prepend>
                <LIcon size="18" class="mr-2">mdi-pencil-outline</LIcon>
              </template>
              <v-list-item-title>{{ $t('scenarioManager.actions.edit') }}</v-list-item-title>
            </v-list-item>
            <!-- Reject invitation option for invited users -->
            <v-list-item v-if="!scenario.is_owner && !isRejected" @click.stop="handleReject" class="text-warning">
              <template #prepend>
                <LIcon size="18" class="mr-2" color="warning">mdi-email-remove-outline</LIcon>
              </template>
              <v-list-item-title>{{ $t('scenarioManager.invitation.reject') }}</v-list-item-title>
            </v-list-item>
            <v-list-item v-if="scenario.is_owner" @click.stop="$emit('delete')" class="text-error">
              <template #prepend>
                <LIcon size="18" class="mr-2" color="error">mdi-delete-outline</LIcon>
              </template>
              <v-list-item-title>{{ $t('scenarioManager.actions.delete') }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </div>

    <!-- Title & Description -->
    <div class="card-body">
      <h3 class="scenario-name">{{ scenario.scenario_name }}</h3>
      <p class="scenario-description" v-if="scenario.description">
        {{ scenario.description }}
      </p>
      <div class="scenario-type">
        <LTag :variant="typeVariant" size="sm">{{ typeName }}</LTag>
      </div>
    </div>

    <!-- Status & Progress -->
    <div class="card-status">
      <div class="status-badge" :class="statusClass">
        <LIcon size="14">{{ statusIcon }}</LIcon>
        <span>{{ statusLabel }}</span>
      </div>
      <div class="progress-bar" v-if="showProgress">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <div class="progress-text" v-if="showProgress">
        {{ progressPercent }}% {{ $t('scenarioManager.progress.complete') }}
      </div>
    </div>

    <!-- Footer Stats -->
    <div class="card-footer">
      <div class="stat">
        <LIcon size="16" color="grey">mdi-email-outline</LIcon>
        <span>{{ scenario.thread_count || 0 }}</span>
      </div>
      <div class="stat">
        <LIcon size="16" color="grey">mdi-account-multiple-outline</LIcon>
        <span>{{ scenario.user_count || 0 }}</span>
      </div>
      <div class="stat" v-if="scenario.llm_evaluator_count">
        <LIcon size="16" color="grey">mdi-robot-outline</LIcon>
        <span>{{ scenario.llm_evaluator_count }}</span>
      </div>
      <v-spacer />
      <!-- Invitation badge -->
      <div v-if="!scenario.is_owner && scenario.invitation" class="invitation-badge" :class="invitationBadgeClass">
        <LIcon size="12">{{ invitationBadgeIcon }}</LIcon>
        <span>{{ $t(`scenarioManager.invitation.${scenario.invitation.status}`) }}</span>
      </div>
      <div class="owner-info" v-if="!scenario.is_owner">
        <LIcon size="14" color="grey">mdi-account-outline</LIcon>
        <span>{{ scenario.owner_name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useScenarioManager } from '../composables/useScenarioManager'

const props = defineProps({
  scenario: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click', 'edit', 'delete', 'invitation-changed'])

const { t } = useI18n()
const { respondToInvitation } = useScenarioManager()

const responding = ref(false)

// Invitation status
const isRejected = computed(() => {
  return !props.scenario.is_owner && props.scenario.invitation?.status === 'rejected'
})

const invitationBadgeClass = computed(() => {
  const status = props.scenario.invitation?.status
  return {
    'badge-accepted': status === 'accepted',
    'badge-rejected': status === 'rejected',
    'badge-pending': status === 'pending'
  }
})

const invitationBadgeIcon = computed(() => {
  const status = props.scenario.invitation?.status
  if (status === 'accepted') return 'mdi-check'
  if (status === 'rejected') return 'mdi-close'
  return 'mdi-clock-outline'
})

function handleClick() {
  if (isRejected.value) return // Don't allow clicking rejected cards
  emit('click')
}

async function handleAccept() {
  responding.value = true
  try {
    await respondToInvitation(props.scenario.id, 'accept')
    emit('invitation-changed', { id: props.scenario.id, status: 'accepted' })
  } finally {
    responding.value = false
  }
}

async function handleReject() {
  responding.value = true
  try {
    await respondToInvitation(props.scenario.id, 'reject')
    emit('invitation-changed', { id: props.scenario.id, status: 'rejected' })
  } finally {
    responding.value = false
  }
}

// Type mapping
const typeConfig = {
  1: { icon: 'mdi-podium', color: '#b0ca97', name: 'ranking', variant: 'success' },
  2: { icon: 'mdi-star-outline', color: '#D1BC8A', name: 'rating', variant: 'warning' },
  3: { icon: 'mdi-email-outline', color: '#88c4c8', name: 'mailRating', variant: 'info' },
  4: { icon: 'mdi-compare-horizontal', color: '#c4a0d4', name: 'comparison', variant: 'primary' },
  5: { icon: 'mdi-shield-search', color: '#e8a087', name: 'authenticity', variant: 'danger' }
}

const typeIcon = computed(() => {
  return typeConfig[props.scenario.function_type_id]?.icon || 'mdi-clipboard-outline'
})

const typeColor = computed(() => {
  return typeConfig[props.scenario.function_type_id]?.color || '#888'
})

const typeName = computed(() => {
  const key = typeConfig[props.scenario.function_type_id]?.name || 'unknown'
  return t(`scenarioManager.types.${key}`)
})

const typeVariant = computed(() => {
  return typeConfig[props.scenario.function_type_id]?.variant || 'gray'
})

// Status mapping
const statusConfig = {
  draft: { icon: 'mdi-file-document-edit-outline', class: 'status-draft' },
  data_collection: { icon: 'mdi-database-import-outline', class: 'status-active' },
  evaluating: { icon: 'mdi-play-circle-outline', class: 'status-active' },
  analyzing: { icon: 'mdi-chart-line', class: 'status-active' },
  completed: { icon: 'mdi-check-circle-outline', class: 'status-completed' },
  archived: { icon: 'mdi-archive-outline', class: 'status-archived' }
}

const statusIcon = computed(() => {
  return statusConfig[props.scenario.status]?.icon || 'mdi-help-circle-outline'
})

const statusClass = computed(() => {
  return statusConfig[props.scenario.status]?.class || ''
})

const statusLabel = computed(() => {
  return t(`scenarioManager.status.${props.scenario.status || 'draft'}`)
})

// Progress
const showProgress = computed(() => {
  return ['data_collection', 'evaluating', 'analyzing'].includes(props.scenario.status)
})

const progressPercent = computed(() => {
  if (!props.scenario.stats) return 0
  const { completed, total } = props.scenario.stats
  if (!total) return 0
  return Math.round((completed / total) * 100)
})
</script>

<style scoped>
.scenario-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.scenario-card.is-owner {
  border-left: 3px solid rgb(var(--v-theme-primary));
}

/* Header */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.type-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px 3px 8px 3px;
}

/* Body */
.card-body {
  flex: 1;
  margin-bottom: 12px;
}

.scenario-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0 0 6px;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.scenario-description {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0 0 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.scenario-type {
  margin-top: 8px;
}

/* Status */
.card-status {
  margin-bottom: 12px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-draft {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.status-active {
  background-color: rgba(33, 150, 243, 0.12);
  color: #1976d2;
}

.status-completed {
  background-color: rgba(76, 175, 80, 0.12);
  color: #388e3c;
}

.status-archived {
  background-color: rgba(var(--v-theme-on-surface), 0.06);
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Progress Bar */
.progress-bar {
  height: 4px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  margin-top: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 4px;
}

/* Footer */
.card-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Invitation Badge */
.invitation-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.65rem;
  font-weight: 500;
  text-transform: uppercase;
}

.badge-accepted {
  background-color: rgba(76, 175, 80, 0.12);
  color: #388e3c;
}

.badge-rejected {
  background-color: rgba(244, 67, 54, 0.12);
  color: #c62828;
}

.badge-pending {
  background-color: rgba(255, 152, 0, 0.12);
  color: #e65100;
}

/* Rejected Card Styling */
.scenario-card.is-rejected {
  position: relative;
  opacity: 0.7;
  cursor: default;
}

.scenario-card.is-rejected:hover {
  transform: none;
  box-shadow: none;
  border-color: rgba(var(--v-theme-on-surface), 0.1);
}

.rejected-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(var(--v-theme-surface), 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 12px;
}

.rejected-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  padding: 16px;
}

.rejected-text {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 4px;
}
</style>
