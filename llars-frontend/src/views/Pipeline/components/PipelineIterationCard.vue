<template>
  <div
    class="iteration-card"
    :class="{
      'is-live': isLive,
      'is-failed': iteration.status === 'failed',
      'is-expanded': expanded,
    }"
  >
    <!-- Clickable Header -->
    <div class="iteration-header" @click="toggleExpand">
      <div class="iteration-number">
        <v-icon v-if="iteration.status === 'completed'" size="18" color="success">mdi-check-circle</v-icon>
        <v-icon v-else-if="iteration.status === 'failed'" size="18" color="error">mdi-alert-circle</v-icon>
        <v-progress-circular v-else-if="isLive" :size="18" :width="2" indeterminate color="primary" />
        <v-icon v-else size="18" color="grey">mdi-circle-outline</v-icon>
        <span>{{ $t('pipeline.iterationLabel', { n: iteration.iteration_number }) }}</span>
      </div>
      <div class="header-right">
        <!-- Collapsed: compact score + delta -->
        <template v-if="!expanded && iteration.scores">
          <LTag
            :variant="(iteration.scores.avg_score || 0) >= 3.5 ? 'success' : (iteration.scores.avg_score || 0) >= 2.5 ? 'warning' : 'danger'"
            size="sm"
          >
            {{ (iteration.scores.avg_score || 0).toFixed(2) }}
          </LTag>
          <span v-if="iteration.delta_to_best != null" class="header-delta" :class="iteration.delta_to_best > 0 ? 'delta-positive' : 'delta-neutral'">
            {{ iteration.delta_to_best > 0 ? '+' : '' }}{{ iteration.delta_to_best.toFixed(3) }}
          </span>
        </template>
        <LTag v-if="isLive" variant="info" size="sm">LIVE</LTag>
        <v-icon size="18" class="expand-icon">{{ expanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
      </div>
    </div>

    <!-- Collapsed body: phases + live indicator -->
    <div v-if="!expanded" class="iteration-body-collapsed">
      <div v-if="iteration.prompt_variants" class="phase-item">
        <v-icon size="14" class="mr-1" color="success">mdi-check</v-icon>
        {{ $t('pipeline.phases.prompts') }}: {{ iteration.prompt_variants.length }}
        {{ $t('pipeline.variantsGenerated') }}
      </div>
      <div v-if="iteration.generation_job_id" class="phase-item">
        <v-icon size="14" class="mr-1" color="success">mdi-check</v-icon>
        {{ $t('pipeline.phases.generation') }}
      </div>
      <div v-if="iteration.eval_scenario_id" class="phase-item">
        <v-icon size="14" class="mr-1" color="success">mdi-check</v-icon>
        {{ $t('pipeline.phases.evaluation') }}
      </div>
      <div v-if="isLive && livePhase" class="phase-item live-phase">
        <v-progress-circular :size="14" :width="2" indeterminate color="primary" class="mr-1" />
        {{ getPhaseLabel(livePhase.phase) }}
      </div>
      <div v-if="iteration.status === 'completed' && !iteration.scores" class="phase-hint">
        {{ $t('pipeline.session.clickToExpand') }}
      </div>
    </div>

    <!-- Expanded body: full details -->
    <div v-if="expanded" class="iteration-body-expanded">
      <!-- Live phase indicator -->
      <div v-if="isLive && livePhase" class="phase-item live-phase mb-3">
        <v-progress-circular :size="14" :width="2" indeterminate color="primary" class="mr-1" />
        {{ getPhaseLabel(livePhase.phase) }}
      </div>

      <!-- A: Prompt Variants -->
      <div v-if="iteration.prompt_variants?.length" class="detail-block">
        <div class="detail-header">
          <v-icon size="16" class="mr-1">mdi-text-box-outline</v-icon>
          {{ $t('pipeline.session.promptVariants') }} ({{ iteration.prompt_variants.length }})
        </div>
        <div v-for="(pv, idx) in iteration.prompt_variants" :key="idx" class="prompt-variant-block">
          <div class="prompt-variant-name">{{ pv.variant_name || pv.name || `Variant ${idx + 1}` }}</div>
          <div v-if="pv.system_prompt" class="prompt-section">
            <span class="prompt-label">{{ $t('pipeline.session.systemPrompt') }}</span>
            <pre class="prompt-code">{{ pv.system_prompt }}</pre>
          </div>
          <div v-if="pv.user_prompt_template || pv.user_template" class="prompt-section">
            <span class="prompt-label">{{ $t('pipeline.session.userTemplate') }}</span>
            <pre class="prompt-code">{{ pv.user_prompt_template || pv.user_template }}</pre>
          </div>
        </div>
      </div>

      <!-- B: Scores with threshold comparison -->
      <div v-if="iteration.scores" class="detail-block">
        <div class="detail-header">
          <v-icon size="16" class="mr-1">mdi-chart-bar</v-icon>
          {{ $t('pipeline.session.dimensions') }}
        </div>

        <!-- Avg score prominent -->
        <div class="avg-score-row">
          <span class="avg-score-label">{{ $t('pipeline.avgScore') }}</span>
          <span class="avg-score-value">{{ (iteration.scores.avg_score || 0).toFixed(2) }} / 5.00</span>
          <LTag v-if="iteration.scores.total_ratings" variant="info" size="sm">
            {{ iteration.scores.total_ratings }} {{ $t('pipeline.session.totalRatings') }}
          </LTag>
        </div>

        <!-- Dimension scores table -->
        <table v-if="iteration.scores.dimensions && Object.keys(iteration.scores.dimensions).length" class="dim-table">
          <thead>
            <tr>
              <th>{{ $t('pipeline.session.dimension') }}</th>
              <th>{{ $t('pipeline.session.score') }}</th>
              <th>{{ $t('pipeline.threshold') }}</th>
              <th>{{ $t('pipeline.session.status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(score, dimId) in iteration.scores.dimensions" :key="dimId">
              <td>{{ dimId }}</td>
              <td class="score-cell">{{ score.toFixed(2) }}</td>
              <td class="threshold-cell">{{ getDimThreshold(dimId) ?? '—' }}</td>
              <td>
                <v-icon
                  v-if="getDimThreshold(dimId) != null"
                  :color="score >= getDimThreshold(dimId) ? 'success' : 'error'"
                  size="18"
                >
                  {{ score >= getDimThreshold(dimId) ? 'mdi-check-circle' : 'mdi-close-circle' }}
                </v-icon>
                <span v-else class="dim-na">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- C: Convergence Decision -->
      <div v-if="iteration.convergence_decision || iteration.agent_reasoning" class="detail-block">
        <div class="detail-header">
          <v-icon size="16" class="mr-1">mdi-head-cog-outline</v-icon>
          {{ $t('pipeline.session.convergenceDecision') }}
        </div>

        <!-- Decision badge -->
        <div class="decision-row">
          <LTag
            v-if="iteration.convergence_decision"
            :variant="decisionVariant"
            size="sm"
          >
            {{ decisionLabel }}
          </LTag>

          <!-- Delta -->
          <span v-if="iteration.delta_to_best != null" class="delta-inline" :class="iteration.delta_to_best > 0 ? 'delta-positive' : 'delta-neutral'">
            {{ iteration.delta_to_best > 0 ? '+' : '' }}{{ iteration.delta_to_best.toFixed(3) }} vs. previous best
          </span>
        </div>

        <!-- Agent reasoning (full text) -->
        <div v-if="iteration.agent_reasoning" class="reasoning-block">
          <span class="reasoning-label">{{ $t('pipeline.session.agentReasoning') }}</span>
          <div class="reasoning-text">{{ iteration.agent_reasoning }}</div>
        </div>
      </div>

      <!-- D: Meta Info -->
      <div class="detail-block meta-block">
        <div class="detail-header">
          <v-icon size="16" class="mr-1">mdi-information-outline</v-icon>
          {{ $t('pipeline.session.metaInfo') }}
        </div>
        <div class="meta-grid">
          <div v-if="iteration.tokens_used" class="meta-item">
            <span class="meta-key">{{ $t('pipeline.session.tokensUsed') }}</span>
            <span class="meta-val">{{ iteration.tokens_used.toLocaleString() }}</span>
          </div>
          <div v-if="iterationDuration" class="meta-item">
            <span class="meta-key">{{ $t('pipeline.session.duration') }}</span>
            <span class="meta-val">{{ iterationDuration }}</span>
          </div>
          <div v-if="iteration.generation_job_id" class="meta-item">
            <span class="meta-key">{{ $t('pipeline.session.generationJobId') }}</span>
            <LTag variant="info" size="sm">{{ iteration.generation_job_id }}</LTag>
          </div>
          <div v-if="iteration.eval_scenario_id" class="meta-item">
            <span class="meta-key">{{ $t('pipeline.session.evalScenarioId') }}</span>
            <LTag variant="info" size="sm">{{ iteration.eval_scenario_id }}</LTag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import LTag from '@/components/common/LTag.vue'

const { t } = useI18n()

const props = defineProps({
  iteration: { type: Object, required: true },
  isLive: { type: Boolean, default: false },
  livePhase: { type: Object, default: null },
  thresholds: { type: Object, default: null },
})

const expanded = ref(false)

function toggleExpand() {
  if (!props.isLive) expanded.value = !expanded.value
}

function getPhaseLabel(phase) {
  const labels = {
    prompt_generation: t('pipeline.phases.promptGeneration'),
    batch_generation: t('pipeline.phases.batchGeneration'),
    evaluation: t('pipeline.phases.evaluating'),
    analysis: t('pipeline.phases.analyzing'),
  }
  return labels[phase] || phase
}

function getDimThreshold(dimId) {
  if (!props.thresholds) return null
  const dims = props.thresholds.dimension_thresholds || props.thresholds.dimensions || {}
  return dims[dimId] ?? props.thresholds.global_threshold ?? props.thresholds.global ?? null
}

const decisionVariant = computed(() => {
  const d = props.iteration.convergence_decision
  if (d === 'converged') return 'success'
  if (d === 'escalate') return 'warning'
  return 'info'
})

const decisionLabel = computed(() => {
  const d = props.iteration.convergence_decision
  if (d === 'converged') return t('pipeline.session.decisionConverged')
  if (d === 'escalate') return t('pipeline.session.decisionEscalate')
  return t('pipeline.session.decisionContinue')
})

const iterationDuration = computed(() => {
  const { started_at, completed_at } = props.iteration
  if (!started_at || !completed_at) return null
  const ms = new Date(completed_at) - new Date(started_at)
  if (ms < 1000) return `${ms}ms`
  const sec = Math.round(ms / 1000)
  if (sec < 60) return `${sec}s`
  const min = Math.floor(sec / 60)
  const remSec = sec % 60
  return `${min}m ${remSec}s`
})
</script>

<style scoped>
.iteration-card {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 3px 12px 3px;
  background: rgb(var(--v-theme-surface));
  transition: border-color 0.2s, box-shadow 0.2s;
  overflow: hidden;
}

.iteration-card:not(.is-live) {
  cursor: pointer;
}

.iteration-card:not(.is-live):hover {
  border-color: rgba(var(--v-theme-on-surface), 0.15);
}

.iteration-card.is-expanded {
  border-color: rgba(var(--v-theme-primary), 0.25);
}

.iteration-card.is-live {
  border-color: rgba(var(--v-theme-primary), 0.4);
  background: rgba(var(--v-theme-primary), 0.03);
}

.iteration-card.is-failed {
  border-color: rgba(var(--v-theme-error), 0.3);
}

/* Header */
.iteration-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  user-select: none;
}

.iteration-number {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.9rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-delta {
  font-size: 0.75rem;
  font-weight: 600;
}

.expand-icon {
  color: rgba(var(--v-theme-on-surface), 0.35);
  transition: transform 0.2s;
}

/* Collapsed body */
.iteration-body-collapsed {
  padding: 0 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
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

.phase-hint {
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.35);
  margin-top: 2px;
}

/* Expanded body */
.iteration-body-expanded {
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.detail-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-header {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  padding-top: 4px;
}

/* Prompt variants */
.prompt-variant-block {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 8px;
  padding: 10px 12px;
}

.prompt-variant-name {
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.prompt-section {
  margin-bottom: 6px;
}

.prompt-section:last-child {
  margin-bottom: 0;
}

.prompt-label {
  font-size: 0.68rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  font-weight: 600;
  display: block;
  margin-bottom: 3px;
}

.prompt-code {
  font-size: 0.73rem;
  line-height: 1.5;
  background: rgba(var(--v-theme-on-surface), 0.04);
  padding: 6px 8px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 150px;
  overflow-y: auto;
}

/* Scores table */
.avg-score-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avg-score-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.avg-score-value {
  font-size: 1rem;
  font-weight: 700;
}

.dim-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

.dim-table th {
  text-align: left;
  font-weight: 600;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  padding: 4px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.dim-table td {
  padding: 5px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.score-cell {
  font-weight: 600;
}

.threshold-cell {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.dim-na {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

/* Convergence decision */
.decision-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.delta-inline {
  font-size: 0.8rem;
  font-weight: 600;
}

.delta-positive {
  color: rgb(var(--v-theme-success));
}

.delta-neutral {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.reasoning-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.reasoning-label {
  font-size: 0.68rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  font-weight: 600;
}

.reasoning-text {
  font-size: 0.82rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.5;
  background: rgba(var(--v-theme-on-surface), 0.02);
  padding: 8px 10px;
  border-radius: 6px;
  border-left: 3px solid rgba(var(--v-theme-primary), 0.3);
}

/* Meta info */
.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-key {
  font-size: 0.68rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  font-weight: 600;
}

.meta-val {
  font-size: 0.82rem;
  font-weight: 500;
}

@media (max-width: 600px) {
  .meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
