<template>
  <LCard :title="$t('evaluationAssistant.metrics.title')" icon="mdi-chart-line">
    <template #actions>
      <LTooltip :text="$t('evaluationAssistant.metrics.helpText')">
        <LBtn variant="text" size="small" icon>
          <LIcon>mdi-help-circle-outline</LIcon>
        </LBtn>
      </LTooltip>
    </template>

    <div class="metrics-list">
      <!-- Krippendorff's Alpha -->
      <MetricItem
        v-if="metrics.krippendorff_alpha !== undefined"
        :name="$t('evaluationAssistant.metrics.krippendorffAlpha.name')"
        :value="metrics.krippendorff_alpha"
        :interpretation="metrics.krippendorff_alpha_interpretation"
        :description="$t('evaluationAssistant.metrics.krippendorffAlpha.description')"
        :range="$t('evaluationAssistant.metrics.krippendorffAlpha.range')"
        icon="mdi-alpha-k-box"
        color="#b0ca97"
      />

      <!-- Cohen's Kappa -->
      <MetricItem
        v-if="metrics.cohens_kappa !== undefined"
        :name="$t('evaluationAssistant.metrics.cohensKappa.name')"
        :value="metrics.cohens_kappa"
        :interpretation="metrics.cohens_kappa_interpretation"
        :description="$t('evaluationAssistant.metrics.cohensKappa.description')"
        :range="$t('evaluationAssistant.metrics.cohensKappa.range')"
        icon="mdi-alpha-k-circle"
        color="#88c4c8"
      />

      <!-- Fleiss' Kappa -->
      <MetricItem
        v-if="metrics.fleiss_kappa !== undefined"
        :name="$t('evaluationAssistant.metrics.fleissKappa.name')"
        :value="metrics.fleiss_kappa"
        :interpretation="metrics.fleiss_kappa_interpretation"
        :description="$t('evaluationAssistant.metrics.fleissKappa.description')"
        :range="$t('evaluationAssistant.metrics.fleissKappa.range')"
        icon="mdi-alpha-f-box"
        color="#D1BC8A"
      />

      <!-- Spearman's Rho -->
      <MetricItem
        v-if="metrics.spearman_rho !== undefined"
        :name="$t('evaluationAssistant.metrics.spearmanRho.name')"
        :value="metrics.spearman_rho"
        :interpretation="metrics.spearman_rho_interpretation"
        :description="$t('evaluationAssistant.metrics.spearmanRho.description')"
        :range="$t('evaluationAssistant.metrics.spearmanRho.range')"
        icon="mdi-alpha-s-circle"
        color="#98d4bb"
      />

      <!-- Kendall's Tau -->
      <MetricItem
        v-if="metrics.kendall_tau !== undefined"
        :name="$t('evaluationAssistant.metrics.kendallTau.name')"
        :value="metrics.kendall_tau"
        :interpretation="metrics.kendall_tau_interpretation"
        :description="$t('evaluationAssistant.metrics.kendallTau.description')"
        :range="$t('evaluationAssistant.metrics.kendallTau.range')"
        icon="mdi-alpha-t-box"
        color="#e8a087"
      />

      <!-- Percent Agreement -->
      <MetricItem
        v-if="metrics.percent_agreement !== undefined"
        :name="$t('evaluationAssistant.metrics.percentAgreement.name')"
        :value="metrics.percent_agreement"
        :interpretation="metrics.percent_agreement_interpretation"
        :description="$t('evaluationAssistant.metrics.percentAgreement.description')"
        :range="$t('evaluationAssistant.metrics.percentAgreement.range')"
        icon="mdi-percent"
        color="#7986CB"
        :is-percent="true"
      />
    </div>

    <!-- Evaluator Summary -->
    <div v-if="metrics.evaluators" class="evaluators-summary">
      <div class="summary-header">
        <LIcon size="18" class="mr-2">mdi-account-group</LIcon>
        <span class="text-subtitle-2">{{ $t('evaluationAssistant.metrics.evaluatorsSummary') }}</span>
      </div>
      <div class="evaluators-list">
        <div
          v-for="evaluator in metrics.evaluators"
          :key="evaluator.id"
          class="evaluator-chip"
        >
          <LIcon size="14" class="mr-1">{{ evaluator.is_llm ? 'mdi-robot' : 'mdi-account' }}</LIcon>
          <span>{{ evaluator.name }}</span>
          <span class="eval-count">({{ evaluator.evaluation_count }})</span>
        </div>
      </div>
    </div>
  </LCard>
</template>

<script setup>
import MetricItem from './MetricItem.vue'

const props = defineProps({
  metrics: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.metrics-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.evaluators-summary {
  margin-top: 16px;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
}

.summary-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.evaluators-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.evaluator-chip {
  display: flex;
  align-items: center;
  padding: 4px 10px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 16px;
  font-size: 0.75rem;
}

.eval-count {
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-left: 4px;
}
</style>
