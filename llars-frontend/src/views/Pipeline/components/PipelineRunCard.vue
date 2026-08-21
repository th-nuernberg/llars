<template>
  <div class="pipeline-run-card" @click="$emit('click')">
    <div class="card-header">
      <div class="card-title-row">
        <span class="card-title">{{ run.name }}</span>
        <LStatusChip :status="statusChipValue" size="small" />
      </div>
      <div class="card-meta">
        <span class="meta-item">
          <v-icon size="14" class="mr-1">mdi-account</v-icon>
          {{ run.created_by }}
        </span>
        <span class="meta-item">
          <v-icon size="14" class="mr-1">mdi-clock-outline</v-icon>
          {{ formatDate(run.created_at) }}
        </span>
      </div>
    </div>

    <div class="card-body">
      <div v-if="run.description" class="card-description">
        {{ run.description }}
      </div>

      <div class="card-stats">
        <div class="stat">
          <span class="stat-label">{{ $t('pipeline.iteration') }}</span>
          <span class="stat-value">{{ run.current_iteration }} / {{ run.max_iterations }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ $t('pipeline.budget') }}</span>
          <span class="stat-value">{{ run.budget_percent || 0 }}%</span>
        </div>
        <div class="stat">
          <span class="stat-label">{{ $t('pipeline.models') }}</span>
          <span class="stat-value">{{ (run.candidate_models || []).length }}</span>
        </div>
      </div>

      <v-progress-linear
        v-if="isActive"
        :model-value="iterationProgress"
        color="primary"
        height="4"
        rounded
        class="mt-2"
      />
    </div>

    <div v-if="run.best_config" class="card-footer">
      <LTag variant="success" size="sm">
        {{ $t('pipeline.bestScore') }}: {{ run.best_config.avg_score?.toFixed(2) || '—' }}
      </LTag>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import LStatusChip from '@/components/common/LStatusChip.vue'
import LTag from '@/components/common/LTag.vue'

const props = defineProps({
  run: { type: Object, required: true },
})

defineEmits(['click'])

const isActive = computed(() =>
  ['running', 'waiting_for_review'].includes(props.run.status)
)

const iterationProgress = computed(() => {
  if (!props.run.max_iterations) return 0
  return Math.round((props.run.current_iteration / props.run.max_iterations) * 100)
})

const statusChipValue = computed(() => {
  const map = {
    created: 'pending',
    running: 'active',
    paused: 'warning',
    waiting_for_review: 'warning',
    completed: 'done',
    failed: 'error',
    cancelled: 'inactive',
  }
  return map[props.run.status] || 'pending'
})

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.pipeline-run-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 16px 4px 16px 4px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pipeline-run-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-title {
  font-weight: 600;
  font-size: 0.95rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.card-meta {
  display: flex;
  gap: 12px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 4px;
}

.meta-item {
  display: flex;
  align-items: center;
}

.card-description {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-stats {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 0.85rem;
  font-weight: 600;
}

.card-footer {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  padding-top: 8px;
}
</style>
