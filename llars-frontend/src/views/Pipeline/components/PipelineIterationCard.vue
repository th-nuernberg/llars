<template>
  <div
    class="iteration-card"
    :class="{ 'is-live': isLive, 'is-failed': iteration.status === 'failed' }"
  >
    <div class="iteration-header">
      <div class="iteration-number">
        <v-icon v-if="iteration.status === 'completed'" size="18" color="success">mdi-check-circle</v-icon>
        <v-icon v-else-if="iteration.status === 'failed'" size="18" color="error">mdi-alert-circle</v-icon>
        <v-progress-circular v-else-if="isLive" :size="18" :width="2" indeterminate color="primary" />
        <v-icon v-else size="18" color="grey">mdi-circle-outline</v-icon>
        <span>{{ $t('pipeline.iterationLabel', { n: iteration.iteration_number }) }}</span>
      </div>
      <LTag v-if="isLive" variant="info" size="sm">LIVE</LTag>
    </div>

    <div class="iteration-body">
      <!-- Prompt variants -->
      <div v-if="iteration.prompt_variants" class="phase-item">
        <v-icon size="14" class="mr-1" color="success">mdi-check</v-icon>
        {{ $t('pipeline.phases.prompts') }}: {{ iteration.prompt_variants.length }}
        {{ $t('pipeline.variantsGenerated') }}
      </div>

      <!-- Generation -->
      <div v-if="iteration.generation_job_id" class="phase-item">
        <v-icon size="14" class="mr-1" color="success">mdi-check</v-icon>
        {{ $t('pipeline.phases.generation') }}
      </div>

      <!-- Evaluation -->
      <div v-if="iteration.eval_scenario_id" class="phase-item">
        <v-icon size="14" class="mr-1" color="success">mdi-check</v-icon>
        {{ $t('pipeline.phases.evaluation') }}
      </div>

      <!-- Live phase indicator -->
      <div v-if="isLive && livePhase" class="phase-item live-phase">
        <v-progress-circular :size="14" :width="2" indeterminate color="primary" class="mr-1" />
        {{ getPhaseLabel(livePhase.phase) }}
      </div>

      <!-- Scores -->
      <div v-if="iteration.scores" class="scores-row">
        <LTag
          v-for="(score, dimId) in iteration.scores.dimensions || {}"
          :key="dimId"
          :variant="score >= 3.5 ? 'success' : score >= 2.5 ? 'warning' : 'danger'"
          size="sm"
        >
          {{ dimId }}: {{ score.toFixed(1) }}
        </LTag>
      </div>

      <!-- Agent reasoning -->
      <div v-if="iteration.agent_reasoning" class="agent-reasoning">
        {{ iteration.agent_reasoning }}
      </div>

      <!-- Delta -->
      <div v-if="iteration.delta_to_best != null" class="delta">
        <span :class="iteration.delta_to_best > 0 ? 'delta-positive' : 'delta-neutral'">
          {{ iteration.delta_to_best > 0 ? '+' : '' }}{{ iteration.delta_to_best?.toFixed(3) || '—' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import LTag from '@/components/common/LTag.vue'

const { t } = useI18n()

defineProps({
  iteration: { type: Object, required: true },
  isLive: { type: Boolean, default: false },
  livePhase: { type: Object, default: null },
})

function getPhaseLabel(phase) {
  const labels = {
    prompt_generation: t('pipeline.phases.promptGeneration'),
    batch_generation: t('pipeline.phases.batchGeneration'),
    evaluation: t('pipeline.phases.evaluating'),
    analysis: t('pipeline.phases.analyzing'),
  }
  return labels[phase] || phase
}
</script>

<style scoped>
.iteration-card {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 3px 12px 3px;
  padding: 12px 16px;
  background: rgb(var(--v-theme-surface));
  transition: border-color 0.2s;
}

.iteration-card.is-live {
  border-color: rgba(var(--v-theme-primary), 0.4);
  background: rgba(var(--v-theme-primary), 0.03);
}

.iteration-card.is-failed {
  border-color: rgba(var(--v-theme-error), 0.3);
}

.iteration-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.iteration-number {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.9rem;
}

.iteration-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.phase-item {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.live-phase {
  color: rgb(var(--v-theme-primary));
  font-weight: 500;
}

.scores-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.agent-reasoning {
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-style: italic;
  line-height: 1.4;
  margin-top: 4px;
}

.delta {
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 2px;
}

.delta-positive {
  color: rgb(var(--v-theme-success));
}

.delta-neutral {
  color: rgba(var(--v-theme-on-surface), 0.4);
}
</style>
