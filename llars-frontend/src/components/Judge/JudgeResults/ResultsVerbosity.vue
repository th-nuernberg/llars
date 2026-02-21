<template>
  <div class="results-card verbosity-card" v-if="analysis">
    <div class="card-header">
      <LIcon class="header-icon">mdi-text-long</LIcon>
      <span class="header-title">{{ $t('judge.results.verbosity.title') }}</span>
      <LTag
        :variant="biasVariant"
        size="small"
        class="ml-auto"
      >
        {{ $t('judge.results.verbosity.longerWinsRate', { rate: Math.round(analysis.verbosity_bias_rate * 100) }) }}
      </LTag>
    </div>

    <div class="card-content">
      <v-skeleton-loader v-if="loading" type="card, table" />
      <template v-else>
        <!-- Alert -->
        <div class="bias-alert" :class="'bias-alert--' + biasType">
          <LIcon class="alert-icon" size="20">{{ alertIcon }}</LIcon>
          <span v-if="analysis.verbosity_bias_rate > 0.6">
            <strong>{{ $t('judge.results.verbosity.alert.warningLabel') }}</strong>
            {{ $t('judge.results.verbosity.alert.warningText') }}
          </span>
          <span v-else-if="analysis.verbosity_bias_rate < 0.4">
            <strong>{{ $t('judge.results.verbosity.alert.infoLabel') }}</strong>
            {{ $t('judge.results.verbosity.alert.infoText') }}
          </span>
          <span v-else>
            <strong>{{ $t('judge.results.verbosity.alert.okLabel') }}</strong>
            {{ $t('judge.results.verbosity.alert.okText') }}
          </span>
        </div>

        <!-- Stats Grid -->
        <div class="stats-row">
          <div class="mini-stat mini-stat--success">
            <div class="mini-stat-value">{{ analysis.longer_wins }}</div>
            <div class="mini-stat-label">{{ $t('judge.results.verbosity.stats.longerWins') }}</div>
          </div>
          <div class="mini-stat mini-stat--danger">
            <div class="mini-stat-value">{{ analysis.shorter_wins }}</div>
            <div class="mini-stat-label">{{ $t('judge.results.verbosity.stats.shorterWins') }}</div>
          </div>
          <div class="mini-stat mini-stat--gray">
            <div class="mini-stat-value">{{ analysis.ties }}</div>
            <div class="mini-stat-label">{{ $t('judge.results.verbosity.stats.ties') }}</div>
          </div>
        </div>

        <!-- Details Grid -->
        <div class="details-grid">
          <!-- Length Stats -->
          <div class="details-section">
            <div class="section-title">{{ $t('judge.results.verbosity.lengthStats.title') }}</div>
            <table class="simple-table">
              <tbody>
                <tr>
                  <td>{{ $t('judge.results.verbosity.lengthStats.winner') }}</td>
                  <td class="text-right">{{ formatNumber(analysis.avg_length_winner) }}</td>
                </tr>
                <tr>
                  <td>{{ $t('judge.results.verbosity.lengthStats.loser') }}</td>
                  <td class="text-right">{{ formatNumber(analysis.avg_length_loser) }}</td>
                </tr>
                <tr>
                  <td>{{ $t('judge.results.verbosity.lengthStats.diff') }}</td>
                  <td class="text-right" :class="lengthDiffClass">{{ lengthDiffFormatted }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Bias Meter -->
          <div class="details-section">
            <div class="section-title">{{ $t('judge.results.verbosity.biasInterpretation') }}</div>
            <div class="bias-meter">
              <div class="bias-bar">
                <div
                  class="bias-fill"
                  :style="{
                    width: (analysis.verbosity_bias_rate * 100) + '%',
                    backgroundColor: biasColor
                  }"
                ></div>
                <span class="bias-value">{{ Math.round(analysis.verbosity_bias_rate * 100) }}%</span>
              </div>
              <div class="bias-labels">
                <span>{{ $t('judge.results.verbosity.biasLabels.shorterPreferred') }}</span>
                <span>{{ $t('judge.results.verbosity.biasLabels.neutral') }}</span>
                <span>{{ $t('judge.results.verbosity.biasLabels.longerPreferred') }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  loading: { type: Boolean, default: false },
  analysis: { type: Object, default: null }
});

const { t, locale } = useI18n();

const formatNumber = (value) => Math.round(value || 0).toLocaleString(locale.value || undefined);

const biasVariant = computed(() => {
  if (!props.analysis) return 'gray';
  const rate = props.analysis.verbosity_bias_rate;
  if (rate > 0.6) return 'warning';
  if (rate < 0.4) return 'info';
  return 'success';
});

const biasColor = computed(() => {
  if (!props.analysis) return 'var(--llars-gray)';
  const rate = props.analysis.verbosity_bias_rate;
  if (rate > 0.6) return 'var(--llars-warning)';
  if (rate < 0.4) return 'var(--llars-info)';
  return 'var(--llars-success)';
});

const biasType = computed(() => {
  if (!props.analysis) return 'info';
  const rate = props.analysis.verbosity_bias_rate;
  if (rate > 0.6) return 'warning';
  if (rate < 0.4) return 'info';
  return 'success';
});

const alertIcon = computed(() => {
  if (!props.analysis) return 'mdi-information';
  const rate = props.analysis.verbosity_bias_rate;
  if (rate > 0.6) return 'mdi-alert';
  if (rate < 0.4) return 'mdi-information';
  return 'mdi-check-circle';
});

const lengthDiffFormatted = computed(() => {
  if (!props.analysis) return t('judge.results.common.placeholder');
  const diff = props.analysis.avg_length_winner - props.analysis.avg_length_loser;
  const sign = diff > 0 ? '+' : '';
  return `${sign}${formatNumber(diff)}`;
});

const lengthDiffClass = computed(() => {
  if (!props.analysis) return '';
  const diff = props.analysis.avg_length_winner - props.analysis.avg_length_loser;
  if (diff > 500) return 'diff-warning';
  if (diff < -500) return 'diff-info';
  return 'diff-success';
});
</script>

<style scoped>
.verbosity-card {
  margin-bottom: var(--llars-spacing-lg);
}

.results-card {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  box-shadow: var(--llars-shadow-sm);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--llars-spacing-sm);
  padding: var(--llars-spacing-md) var(--llars-spacing-lg);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}

.header-icon {
  color: var(--llars-primary);
}

.header-title {
  font-weight: 600;
  font-size: 1rem;
}

.card-content {
  padding: var(--llars-spacing-lg);
}

/* Alert */
.bias-alert {
  display: flex;
  align-items: center;
  gap: var(--llars-spacing-sm);
  padding: var(--llars-spacing-md);
  border-radius: var(--llars-radius-sm);
  margin-bottom: var(--llars-spacing-lg);
}

.bias-alert--success {
  background: rgba(152, 212, 187, 0.15);
  color: #3a7a5e;
}

.bias-alert--warning {
  background: rgba(232, 200, 122, 0.15);
  color: #7a6a2a;
}

.bias-alert--info {
  background: rgba(168, 197, 226, 0.15);
  color: #3a5a7a;
}

.alert-icon {
  flex-shrink: 0;
}

/* Stats Row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--llars-spacing-md);
  margin-bottom: var(--llars-spacing-lg);
}

.mini-stat {
  text-align: center;
  padding: var(--llars-spacing-lg);
  border-radius: var(--llars-radius-sm);
  border: 1px solid rgba(var(--v-border-color), 0.12);
}

.mini-stat--success {
  background: rgba(152, 212, 187, 0.1);
}

.mini-stat--danger {
  background: rgba(232, 160, 135, 0.1);
}

.mini-stat--gray {
  background: rgba(158, 158, 158, 0.1);
}

.mini-stat-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: var(--llars-spacing-xs);
}

.mini-stat--success .mini-stat-value { color: var(--llars-success-active); }
.mini-stat--danger .mini-stat-value { color: var(--llars-danger-active); }
.mini-stat--gray .mini-stat-value { color: var(--llars-gray); }

.mini-stat-label {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Details Grid */
.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--llars-spacing-lg);
}

.details-section {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: var(--llars-radius-sm);
  padding: var(--llars-spacing-md);
}

.section-title {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: var(--llars-spacing-md);
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Simple Table */
.simple-table {
  width: 100%;
  border-collapse: collapse;
}

.simple-table td {
  padding: var(--llars-spacing-sm) 0;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
}

.simple-table tr:last-child td {
  border-bottom: none;
  font-weight: 600;
}

.diff-warning { color: var(--llars-warning-active); }
.diff-info { color: var(--llars-info-active); }
.diff-success { color: var(--llars-success-active); }

/* Bias Meter */
.bias-meter {
  margin-top: var(--llars-spacing-sm);
}

.bias-bar {
  position: relative;
  height: 28px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: var(--llars-radius-xs);
  overflow: hidden;
}

.bias-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: var(--llars-radius-xs);
  transition: width 0.3s ease;
}

.bias-value {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-weight: 700;
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
}

.bias-labels {
  display: flex;
  justify-content: space-between;
  margin-top: var(--llars-spacing-xs);
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}
</style>
