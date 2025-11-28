/**
 * Judge Helpers Composable
 *
 * Utility functions for formatting, colors, and display.
 * Extracted from JudgeResults.vue for better maintainability.
 */

import axios from 'axios';

export function useJudgeHelpers(sessionId) {
  // Rank and Win Rate colors
  const getRankColor = (index) => {
    const colors = ['warning', 'grey-lighten-1', 'orange-lighten-1', 'grey-lighten-2', 'grey-lighten-3'];
    return colors[index] || 'grey';
  };

  const getWinRateColor = (winRate) => {
    if (winRate >= 0.7) return 'success';
    if (winRate >= 0.5) return 'info';
    if (winRate >= 0.3) return 'warning';
    return 'error';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'info';
    if (confidence >= 0.4) return 'warning';
    return 'error';
  };

  const getScoreColor = (score) => {
    if (score >= 4) return 'success';
    if (score >= 3) return 'info';
    if (score >= 2) return 'warning';
    return 'error';
  };

  // Formatting
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCriterionName = (criterion) => {
    const names = {
      'counsellor_coherence': 'Berater-Kohärenz',
      'client_coherence': 'Klient-Kohärenz',
      'quality': 'Qualität',
      'empathy': 'Empathie',
      'authenticity': 'Authentizität',
      'solution_orientation': 'Lösungsorientierung'
    };
    return names[criterion] || criterion;
  };

  const formatLikertMetric = (metric) => {
    return formatCriterionName(metric);
  };

  // Thread Performance helpers
  const getLikertConsistencyColor = (score) => {
    if (score >= 0.7) return 'success';
    if (score >= 0.5) return 'warning';
    return 'error';
  };

  const getPillarName = (pillarId) => {
    return `Säule ${pillarId}`;
  };

  // Position Swap Analysis helpers
  const getConsistencyQualityColor = (quality) => {
    const colors = {
      'excellent': 'success',
      'good': 'info',
      'fair': 'warning',
      'poor': 'error'
    };
    return colors[quality] || 'grey';
  };

  const getBiasLabel = (bias) => {
    const labels = {
      'primacy': 'Primacy Bias',
      'recency': 'Recency Bias',
      'balanced': 'Ausbalanciert'
    };
    return labels[bias] || 'Unbekannt';
  };

  // Export functions
  const exportCSV = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/export/csv`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `judge_results_${sessionId}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting CSV:', error);
    }
  };

  const exportJSON = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/export/json`
      );

      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `judge_results_${sessionId}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting JSON:', error);
    }
  };

  return {
    // Color helpers
    getRankColor,
    getWinRateColor,
    getConfidenceColor,
    getScoreColor,
    getLikertConsistencyColor,
    getConsistencyQualityColor,

    // Formatting
    formatDate,
    formatCriterionName,
    formatLikertMetric,
    getPillarName,
    getBiasLabel,

    // Export
    exportCSV,
    exportJSON
  };
}
