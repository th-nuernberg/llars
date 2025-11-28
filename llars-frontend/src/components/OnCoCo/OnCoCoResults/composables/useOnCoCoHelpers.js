/**
 * OnCoCo Helpers Composable
 *
 * Utility functions for status display, formatting, and pillar helpers.
 * Extracted from OnCoCoResults.vue for better maintainability.
 */

export function useOnCoCoHelpers() {
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
      pending: 'Ausstehend',
      running: 'Läuft',
      completed: 'Abgeschlossen',
      failed: 'Fehlgeschlagen'
    };
    return texts[status] || status;
  };

  // Formatting helpers
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
      1: 'Rollenspiele',
      3: 'Anonymisierte Daten',
      5: 'Live-Testungen'
    };
    return names[pillarNum] || `Säule ${pillarNum}`;
  };

  // Table headers
  const distributionHeaders = [
    { title: 'Label', key: 'label', sortable: true },
    { title: 'Rolle', key: 'role', sortable: true },
    { title: 'Anzahl', key: 'count', sortable: true, width: '300px' }
  ];

  const comparisonHeaders = [
    { title: 'Säule', key: 'pillar_name', sortable: true },
    { title: 'Sätze', key: 'metrics.total_sentences', sortable: true },
    { title: 'Berater-Anteil', key: 'counselor_ratio', sortable: true, width: '200px' },
    { title: 'Impact Factor', key: 'impact_factor_ratio', sortable: true },
    { title: 'Ressourcen-Aktivierung', key: 'resource_activation_score', sortable: true },
    { title: 'MI Score', key: 'mi_score', sortable: true },
    { title: 'Konfidenz', key: 'avg_confidence', sortable: true }
  ];

  const sentenceHeaders = [
    { title: 'Satz', key: 'sentence_text', sortable: false, width: '40%' },
    { title: 'Rolle', key: 'role', sortable: true },
    { title: 'Label', key: 'label', sortable: true },
    { title: 'Konfidenz', key: 'confidence', sortable: true, width: '150px' },
    { title: 'Säule', key: 'pillar_number', sortable: true }
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
