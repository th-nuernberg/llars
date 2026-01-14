/**
 * OnCoCo Helpers Composable
 *
 * Utility functions for status display, formatting, and pillar helpers.
 * Extracted from OnCoCoResults.vue for better maintainability.
 */

import { useI18n } from 'vue-i18n';

export function useOnCoCoHelpers() {
  const { t, locale } = useI18n();

  // Status helpers
  const getStatusColor = (status) => {
    const colors = {
      pending: 'grey',
      running: 'info',
      completed: 'success',
      failed: 'error'
    };
    return colors[status] || 'grey';
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: 'mdi-clock-outline',
      running: 'mdi-play-circle',
      completed: 'mdi-check-circle',
      failed: 'mdi-alert-circle'
    };
    return icons[status] || 'mdi-help-circle';
  };

  const getStatusText = (status) => {
    const texts = {
      pending: t('oncoco.status.pending'),
      running: t('oncoco.status.running'),
      completed: t('oncoco.status.completed'),
      failed: t('oncoco.status.failed')
    };
    return texts[status] || status;
  };

  // Formatting helpers
  const formatDate = (dateString) => {
    if (!dateString) return t('oncoco.results.placeholders.date');
    const date = new Date(dateString);
    return date.toLocaleString(locale.value || undefined, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds || seconds < 0) return '0s';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.round(seconds % 60);
      return `${mins}m ${secs}s`;
    }
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${mins}m`;
  };

  // Pillar helpers
  const getPillarName = (pillarNum) => {
    const names = {
      1: t('oncoco.pillars.one'),
      3: t('oncoco.pillars.three'),
      5: t('oncoco.pillars.five')
    };
    return names[pillarNum] || t('oncoco.pillars.default', { id: pillarNum });
  };

  // Table headers
  const distributionHeaders = [
    { title: t('oncoco.results.distribution.headers.label'), key: 'label', sortable: true },
    { title: t('oncoco.results.distribution.headers.role'), key: 'role', sortable: true },
    { title: t('oncoco.results.distribution.headers.count'), key: 'count', sortable: true, width: '300px' }
  ];

  const comparisonHeaders = [
    { title: t('oncoco.results.comparison.headers.pillar'), key: 'pillar_name', sortable: true },
    { title: t('oncoco.results.comparison.headers.sentences'), key: 'metrics.total_sentences', sortable: true },
    { title: t('oncoco.results.comparison.headers.counselorRatio'), key: 'counselor_ratio', sortable: true, width: '200px' },
    { title: t('oncoco.results.comparison.headers.impactFactor'), key: 'impact_factor_ratio', sortable: true },
    { title: t('oncoco.results.comparison.headers.resourceActivation'), key: 'resource_activation_score', sortable: true },
    { title: t('oncoco.results.comparison.headers.miScore'), key: 'mi_score', sortable: true },
    { title: t('oncoco.results.comparison.headers.confidence'), key: 'avg_confidence', sortable: true }
  ];

  const sentenceHeaders = [
    { title: t('oncoco.results.sentences.headers.sentence'), key: 'sentence_text', sortable: false, width: '40%' },
    { title: t('oncoco.results.sentences.headers.role'), key: 'role', sortable: true },
    { title: t('oncoco.results.sentences.headers.label'), key: 'label', sortable: true },
    { title: t('oncoco.results.sentences.headers.confidence'), key: 'confidence', sortable: true, width: '150px' },
    { title: t('oncoco.results.sentences.headers.pillar'), key: 'pillar_number', sortable: true }
  ];

  return {
    // Status helpers
    getStatusColor,
    getStatusIcon,
    getStatusText,

    // Formatting helpers
    formatDate,
    formatDuration,

    // Pillar helpers
    getPillarName,

    // Table headers
    distributionHeaders,
    comparisonHeaders,
    sentenceHeaders
  };
}
