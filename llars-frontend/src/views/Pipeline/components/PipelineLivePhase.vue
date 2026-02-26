<template>
  <div v-if="livePhase" class="live-phase-indicator">
    <v-progress-circular :size="20" :width="2" indeterminate color="primary" />
    <span class="phase-label">{{ phaseLabel }}</span>
    <span class="phase-detail">
      {{ $t('pipeline.iterationLabel', { n: livePhase.iteration }) }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  livePhase: { type: Object, default: null },
})

const phaseLabel = computed(() => {
  if (!props.livePhase) return ''
  const labels = {
    prompt_generation: t('pipeline.phases.promptGeneration'),
    batch_generation: t('pipeline.phases.batchGeneration'),
    evaluation: t('pipeline.phases.evaluating'),
    analysis: t('pipeline.phases.analyzing'),
  }
  return labels[props.livePhase.phase] || props.livePhase.phase
})
</script>

<style scoped>
.live-phase-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(var(--v-theme-primary), 0.06);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  border-radius: 12px 3px 12px 3px;
}

.phase-label {
  font-weight: 600;
  font-size: 0.85rem;
  color: rgb(var(--v-theme-primary));
}

.phase-detail {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}
</style>
