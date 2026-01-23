<!--
  GenerationJobCard.vue - Job Card Component

  Displays a single generation job with status, progress,
  and quick actions. Used in GenerationHub grid view.
-->
<template>
  <div
    class="job-card"
    :class="{
      'is-active': isActive,
      'is-completed': job.status === JOB_STATUS.COMPLETED,
      'is-failed': job.status === JOB_STATUS.FAILED
    }"
    @click="$emit('click')"
  >
    <!-- Status Badge -->
    <div class="card-status-badge" :style="{ backgroundColor: statusConfig.color }">
      <LIcon size="14" color="white">{{ statusConfig.icon }}</LIcon>
      <span>{{ statusConfig.label }}</span>
    </div>

    <!-- Actions Menu -->
    <v-menu offset-y location="bottom end">
      <template v-slot:activator="{ props }">
        <v-btn
          icon
          variant="text"
          size="small"
          class="card-menu-btn"
          v-bind="props"
          @click.stop
        >
          <LIcon size="20">mdi-dots-vertical</LIcon>
        </v-btn>
      </template>
      <v-list density="compact">
        <!-- Start (if created) -->
        <v-list-item v-if="canStart" @click.stop="$emit('start')">
          <template v-slot:prepend>
            <LIcon size="18" color="success" class="mr-2">mdi-play</LIcon>
          </template>
          <v-list-item-title>{{ $t('generation.actions.start') }}</v-list-item-title>
        </v-list-item>

        <!-- Pause (if running) -->
        <v-list-item v-if="canPause" @click.stop="$emit('pause')">
          <template v-slot:prepend>
            <LIcon size="18" color="warning" class="mr-2">mdi-pause</LIcon>
          </template>
          <v-list-item-title>{{ $t('generation.actions.pause') }}</v-list-item-title>
        </v-list-item>

        <!-- Cancel (if running or paused) -->
        <v-list-item v-if="canCancel" @click.stop="$emit('cancel')">
          <template v-slot:prepend>
            <LIcon size="18" color="error" class="mr-2">mdi-stop</LIcon>
          </template>
          <v-list-item-title>{{ $t('generation.actions.cancel') }}</v-list-item-title>
        </v-list-item>

        <v-divider v-if="canStart || canPause || canCancel" />

        <!-- Delete (if not running) -->
        <v-list-item v-if="canDelete" @click.stop="$emit('delete')">
          <template v-slot:prepend>
            <LIcon size="18" color="error" class="mr-2">mdi-delete</LIcon>
          </template>
          <v-list-item-title>{{ $t('common.delete') }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>

    <!-- Card Content -->
    <div class="card-body">
      <h3 class="card-title">{{ job.name }}</h3>
      <p v-if="job.description" class="card-description">
        {{ job.description }}
      </p>

      <!-- Config Summary -->
      <div class="config-summary">
        <LTag variant="info" size="small">
          <LIcon start size="14">mdi-file-document-outline</LIcon>
          {{ job.total_items }} Items
        </LTag>
        <LTag variant="secondary" size="small">
          <LIcon start size="14">mdi-text-box-outline</LIcon>
          {{ promptCount }} Prompts
        </LTag>
        <LTag variant="accent" size="small">
          <LIcon start size="14">mdi-robot-outline</LIcon>
          {{ modelCount }} Models
        </LTag>
      </div>
    </div>

    <!-- Card Footer -->
    <div class="card-footer">
      <!-- Progress Info -->
      <div class="progress-info">
        <span class="progress-text">
          {{ job.completed_items || 0 }} / {{ job.total_items }}
          <span v-if="job.failed_items" class="failed-count">
            ({{ job.failed_items }} {{ $t('generation.failed') }})
          </span>
        </span>
        <span v-if="job.total_cost_usd" class="cost-text">
          ${{ job.total_cost_usd.toFixed(4) }}
        </span>
      </div>

      <!-- Meta Info -->
      <div class="meta-info">
        <span class="created-at">
          <LIcon size="14" class="mr-1">mdi-clock-outline</LIcon>
          {{ formatDate(job.created_at) }}
        </span>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="card-progress-bar">
      <div
        class="progress-fill"
        :class="{ 'animated': isActive }"
        :style="{ width: progressPercent + '%' }"
      />
      <div
        v-if="job.failed_items"
        class="progress-failed"
        :style="{ width: failedPercent + '%' }"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { JOB_STATUS } from '@/composables/useGeneration'

const props = defineProps({
  job: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'start', 'pause', 'cancel', 'delete'])

const { t } = useI18n()

// Status configuration
const STATUS_CONFIG = {
  [JOB_STATUS.CREATED]: { icon: 'mdi-clock-outline', color: '#9e9e9e', label: t('generation.status.created') },
  [JOB_STATUS.QUEUED]: { icon: 'mdi-timer-sand', color: '#7986cb', label: t('generation.status.queued') },
  [JOB_STATUS.RUNNING]: { icon: 'mdi-play-circle', color: '#b0ca97', label: t('generation.status.running') },
  [JOB_STATUS.PAUSED]: { icon: 'mdi-pause-circle', color: '#d1bc8a', label: t('generation.status.paused') },
  [JOB_STATUS.COMPLETED]: { icon: 'mdi-check-circle', color: '#98d4bb', label: t('generation.status.completed') },
  [JOB_STATUS.FAILED]: { icon: 'mdi-alert-circle', color: '#e8a087', label: t('generation.status.failed') },
  [JOB_STATUS.CANCELLED]: { icon: 'mdi-cancel', color: '#9e9e9e', label: t('generation.status.cancelled') }
}

// Computed
const statusConfig = computed(() =>
  STATUS_CONFIG[props.job.status] || STATUS_CONFIG[JOB_STATUS.CREATED]
)

const isActive = computed(() =>
  props.job.status === JOB_STATUS.RUNNING || props.job.status === JOB_STATUS.QUEUED
)

const progressPercent = computed(() => {
  if (!props.job.total_items) return 0
  return Math.round(((props.job.completed_items || 0) / props.job.total_items) * 100)
})

const failedPercent = computed(() => {
  if (!props.job.total_items || !props.job.failed_items) return 0
  return Math.round((props.job.failed_items / props.job.total_items) * 100)
})

const promptCount = computed(() => {
  const config = props.job.config_json || {}
  return config.prompts?.length || 0
})

const modelCount = computed(() => {
  const config = props.job.config_json || {}
  return config.llm_models?.length || 0
})

// Action availability
const canStart = computed(() =>
  props.job.status === JOB_STATUS.CREATED || props.job.status === JOB_STATUS.PAUSED
)

const canPause = computed(() =>
  props.job.status === JOB_STATUS.RUNNING
)

const canCancel = computed(() =>
  props.job.status === JOB_STATUS.RUNNING || props.job.status === JOB_STATUS.PAUSED
)

const canDelete = computed(() =>
  props.job.status !== JOB_STATUS.RUNNING && props.job.status !== JOB_STATUS.QUEUED
)

// Methods
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.job-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 180px;
  overflow: hidden;
}

.job-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.job-card.is-active {
  border-color: var(--llars-primary, #b0ca97);
}

.job-card.is-completed {
  border-color: var(--llars-success, #98d4bb);
}

.job-card.is-failed {
  border-color: var(--llars-danger, #e8a087);
}

/* Status Badge */
.card-status-badge {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 11px 0 8px 0;
  font-size: 0.7rem;
  font-weight: 600;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Menu Button */
.card-menu-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.job-card:hover .card-menu-btn {
  opacity: 1;
}

/* Card Body */
.card-body {
  flex: 1;
  padding: 40px 16px 12px 16px;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  padding-right: 32px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-description {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Config Summary */
.config-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* Card Footer */
.card-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.progress-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.progress-text {
  font-size: 0.85rem;
  font-weight: 500;
}

.failed-count {
  color: var(--llars-danger, #e8a087);
  font-size: 0.75rem;
}

.cost-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-family: monospace;
}

.meta-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.created-at {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Progress Bar */
.card-progress-bar {
  height: 3px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  position: relative;
}

.progress-fill {
  height: 100%;
  background: var(--llars-primary, #b0ca97);
  transition: width 0.3s ease;
  position: absolute;
  left: 0;
  top: 0;
}

.progress-fill.animated {
  animation: progress-pulse 1.5s ease-in-out infinite;
}

.progress-failed {
  height: 100%;
  background: var(--llars-danger, #e8a087);
  position: absolute;
  right: 0;
  top: 0;
}

.job-card.is-completed .progress-fill {
  background: var(--llars-success, #98d4bb);
}

@keyframes progress-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
