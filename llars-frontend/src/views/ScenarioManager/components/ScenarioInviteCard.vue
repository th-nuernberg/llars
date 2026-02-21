<template>
  <div class="invite-card" :class="{ pending: isPending, rejected: isRejected }">
    <!-- Header -->
    <div class="card-header">
      <div class="type-icon" :style="{ backgroundColor: typeConfig.bgColor }">
        <LIcon :color="typeConfig.color" size="20">{{ typeConfig.icon }}</LIcon>
      </div>
      <div class="card-title">
        <h3>{{ scenario.scenario_name }}</h3>
        <div class="card-meta">
          <span class="type-label">{{ typeConfig.label }}</span>
          <LTag :variant="invitationStatus.variant" size="sm">
            {{ invitationStatus.label }}
          </LTag>
        </div>
      </div>
    </div>

    <!-- Invited By -->
    <div class="invited-by">
      <LIcon size="14" color="grey">mdi-account-outline</LIcon>
      <span>{{ $t('scenarioManager.invitation.invitedBy', { name: invitedByName }) }}</span>
    </div>

    <!-- Your Progress (only if accepted) -->
    <div v-if="isAccepted && hasProgress" class="your-progress">
      <div class="progress-label">
        <span>{{ $t('scenarioManager.card.yourProgress') }}</span>
        <span class="progress-count">{{ myCompleted }}/{{ myTotal }}</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: myProgressPercent + '%' }"></div>
      </div>
    </div>

    <!-- Actions -->
    <div class="card-actions">
      <!-- Pending: Accept/Reject buttons -->
      <template v-if="isPending">
        <LBtn variant="secondary" size="small" @click.stop="$emit('reject', scenario)">
          {{ $t('scenarioManager.invitation.reject') }}
        </LBtn>
        <LBtn variant="primary" size="small" @click.stop="$emit('accept', scenario)">
          {{ $t('scenarioManager.invitation.accept') }}
        </LBtn>
      </template>

      <!-- Accepted: Go to evaluation + Leave option -->
      <template v-else-if="isAccepted">
        <LBtn variant="text" size="small" color="error" @click.stop="$emit('leave', scenario)">
          <LIcon start size="16">mdi-exit-run</LIcon>
          {{ $t('scenarioManager.invitation.leave') }}
        </LBtn>
        <LBtn variant="primary" size="small" @click.stop="$emit('evaluate', scenario)">
          <LIcon start size="16">mdi-clipboard-edit-outline</LIcon>
          {{ $t('scenarioManager.card.goToEvaluation') }}
        </LBtn>
      </template>

      <!-- Rejected: Option to accept again -->
      <template v-else-if="isRejected">
        <LBtn variant="text" size="small" @click.stop="$emit('accept', scenario)">
          {{ $t('scenarioManager.invitation.acceptAgain') }}
        </LBtn>
      </template>
    </div>

    <!-- Footer -->
    <div class="card-footer">
      <span class="date">
        {{ $t('scenarioManager.invitation.invitedAt', { date: formatDate(scenario.invitation?.invited_at) }) }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  scenario: {
    type: Object,
    required: true
  }
})

defineEmits(['accept', 'reject', 'evaluate', 'leave'])

const { t } = useI18n()

// Type configuration
const typeConfigs = {
  1: { icon: 'mdi-podium', color: '#b0ca97', bgColor: 'rgba(176, 202, 151, 0.15)', label: 'Ranking' },
  2: { icon: 'mdi-star-outline', color: '#D1BC8A', bgColor: 'rgba(209, 188, 138, 0.15)', label: 'Rating' },
  3: { icon: 'mdi-email-outline', color: '#e8a087', bgColor: 'rgba(232, 160, 135, 0.15)', label: 'Mail Rating' },
  4: { icon: 'mdi-compare-horizontal', color: '#88c4c8', bgColor: 'rgba(136, 196, 200, 0.15)', label: 'Comparison' },
  5: { icon: 'mdi-shield-search', color: '#c4a0d4', bgColor: 'rgba(196, 160, 212, 0.15)', label: 'Authenticity' },
  7: { icon: 'mdi-tag-outline', color: '#98d4bb', bgColor: 'rgba(152, 212, 187, 0.15)', label: 'Labeling' }
}

const typeConfig = computed(() => {
  return typeConfigs[props.scenario.function_type_id] || typeConfigs[1]
})

// Invitation status
const isPending = computed(() => props.scenario.invitation?.status === 'pending')
const isAccepted = computed(() => props.scenario.invitation?.status === 'accepted')
const isRejected = computed(() => props.scenario.invitation?.status === 'rejected')

// Invited by name (from invitation.invited_by or fallback to owner_name)
const invitedByName = computed(() => {
  return props.scenario.invitation?.invited_by || props.scenario.owner_name || 'System'
})

const invitationStatus = computed(() => {
  if (isPending.value) return { variant: 'warning', label: t('scenarioManager.invitation.pending') }
  if (isAccepted.value) return { variant: 'success', label: t('scenarioManager.invitation.accepted') }
  if (isRejected.value) return { variant: 'gray', label: t('scenarioManager.invitation.rejected') }
  return { variant: 'gray', label: '-' }
})

// User's own progress (from invitation or user_progress field)
const myCompleted = computed(() => {
  return props.scenario.user_progress?.completed || 0
})

const myTotal = computed(() => {
  return props.scenario.user_progress?.total || props.scenario.thread_count || 0
})

const hasProgress = computed(() => myTotal.value > 0)

const myProgressPercent = computed(() => {
  if (!myTotal.value) return 0
  return Math.round((myCompleted.value / myTotal.value) * 100)
})

// Date formatter
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
</script>

<style scoped>
.invite-card {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  transition: all 0.2s ease;
}

.invite-card.pending {
  border-color: rgba(255, 152, 0, 0.3);
  background-color: rgba(255, 152, 0, 0.02);
}

.invite-card.rejected {
  opacity: 0.7;
}

.invite-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.invite-card.pending:hover {
  border-color: rgba(255, 152, 0, 0.5);
}

/* Header */
.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.type-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px 3px 8px 3px;
}

.card-title {
  flex: 1;
  min-width: 0;
}

.card-title h3 {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Invited By */
.invited-by {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 12px;
}

/* Your Progress */
.your-progress {
  margin-bottom: 16px;
  padding: 12px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.progress-count {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.progress-bar {
  height: 6px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* Actions */
.card-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-bottom: 12px;
}

/* Footer */
.card-footer {
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.date {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}
</style>
