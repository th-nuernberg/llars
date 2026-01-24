<template>
  <div class="scenario-card" @click="$emit('open', scenario)">
    <!-- Header -->
    <div class="card-header">
      <div class="type-icon" :style="{ backgroundColor: typeConfig.bgColor }">
        <LIcon :color="typeConfig.color" size="20">{{ typeConfig.icon }}</LIcon>
      </div>
      <div class="card-title">
        <h3>{{ scenario.scenario_name }}</h3>
        <div class="card-meta">
          <span class="type-label">{{ typeConfig.label }}</span>
          <LTag :variant="statusConfig.variant" size="sm">
            {{ statusConfig.label }}
          </LTag>
        </div>
      </div>
      <v-menu location="bottom end">
        <template #activator="{ props }">
          <v-btn
            v-bind="props"
            icon
            variant="text"
            size="small"
            @click.stop
          >
            <LIcon>mdi-dots-vertical</LIcon>
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item @click.stop="$emit('settings', scenario)">
            <template #prepend>
              <LIcon size="18" class="mr-2">mdi-cog-outline</LIcon>
            </template>
            <v-list-item-title>{{ $t('scenarioManager.actions.settings') }}</v-list-item-title>
          </v-list-item>
          <v-list-item @click.stop="$emit('duplicate', scenario)">
            <template #prepend>
              <LIcon size="18" class="mr-2">mdi-content-copy</LIcon>
            </template>
            <v-list-item-title>{{ $t('scenarioManager.actions.duplicate') }}</v-list-item-title>
          </v-list-item>
          <v-list-item @click.stop="$emit('archive', scenario)">
            <template #prepend>
              <LIcon size="18" class="mr-2">mdi-archive-outline</LIcon>
            </template>
            <v-list-item-title>{{ $t('scenarioManager.actions.archive') }}</v-list-item-title>
          </v-list-item>
          <v-divider class="my-1" />
          <v-list-item @click.stop="$emit('delete', scenario)" class="text-error">
            <template #prepend>
              <LIcon size="18" class="mr-2" color="error">mdi-delete-outline</LIcon>
            </template>
            <v-list-item-title>{{ $t('scenarioManager.actions.delete') }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </div>

    <!-- Progress -->
    <div class="card-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <span class="progress-text">{{ progressPercent }}%</span>
    </div>

    <!-- Stats -->
    <div class="card-stats">
      <div class="stat">
        <LIcon size="16" color="grey">mdi-account-multiple-outline</LIcon>
        <span>{{ scenario.user_count || 0 }} {{ $t('scenarioManager.card.evaluators') }}</span>
      </div>
      <div class="stat" v-if="scenario.llm_evaluator_count > 0">
        <LIcon size="16" color="grey">mdi-robot-outline</LIcon>
        <span>{{ scenario.llm_evaluator_count }} LLMs</span>
      </div>
    </div>

    <!-- Footer -->
    <div class="card-footer">
      <span class="date">{{ formatDate(scenario.created_at) }}</span>
      <span class="thread-count">{{ scenario.thread_count || 0 }} Threads</span>
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

defineEmits(['open', 'settings', 'duplicate', 'archive', 'delete'])

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

// Status configuration
const statusConfigs = {
  draft: { variant: 'gray', label: t('scenarioManager.status.draft') },
  data_collection: { variant: 'info', label: t('scenarioManager.status.dataCollection') },
  evaluating: { variant: 'primary', label: t('scenarioManager.status.evaluating') },
  analyzing: { variant: 'warning', label: t('scenarioManager.status.analyzing') },
  completed: { variant: 'success', label: t('scenarioManager.status.completed') },
  archived: { variant: 'gray', label: t('scenarioManager.status.archived') }
}

const statusConfig = computed(() => {
  return statusConfigs[props.scenario.status] || statusConfigs.draft
})

// Progress
const progressPercent = computed(() => {
  if (!props.scenario.stats) return 0
  const { completed, total } = props.scenario.stats
  if (!total) return 0
  return Math.round((completed / total) * 100)
})

// Date formatter
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
</script>

<style scoped>
.scenario-card {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.scenario-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

/* Header */
.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
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

/* Progress */
.card-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.progress-bar {
  flex: 1;
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

.progress-text {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  min-width: 36px;
  text-align: right;
}

/* Stats */
.card-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Footer */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.date {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.thread-count {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}
</style>
