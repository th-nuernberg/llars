/**
 * Session Helpers Composable
 *
 * Utility functions for status colors, icons, text formatting.
 */

import { PILLAR_CONFIG, PILLAR_NAMES } from './useSessionConstants';

export function useSessionHelpers() {
  // Status color mapping
  const getStatusColor = (status) => {
    const colors = {
      created: 'grey',
      queued: 'warning',
      running: 'info',
      paused: 'orange',
      completed: 'success',
      failed: 'error'
    };
    return colors[status] || 'grey';
  };

  // Status icon mapping
  const getStatusIcon = (status) => {
    const icons = {
      created: 'mdi-file-document',
      queued: 'mdi-clock-outline',
      running: 'mdi-play-circle',
      paused: 'mdi-pause-circle',
      completed: 'mdi-check-circle',
      failed: 'mdi-alert-circle'
    };
    return icons[status] || 'mdi-help-circle';
  };

  // Status text mapping (German)
  const getStatusText = (status) => {
    const texts = {
      created: 'Erstellt',
      queued: 'In Warteschlange',
      running: 'Läuft',
      paused: 'Pausiert',
      completed: 'Abgeschlossen',
      failed: 'Fehlgeschlagen'
    };
    return texts[status] || status;
  };

  // Confidence color based on value
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'info';
    if (confidence >= 0.4) return 'warning';
    return 'error';
  };

  // Pillar helpers
  const getPillarName = (pillarId) => {
    return PILLAR_NAMES[pillarId] || `Säule ${pillarId}`;
  };

  const getPillarIcon = (pillarId) => {
    return PILLAR_CONFIG[pillarId]?.icon || 'mdi-help-circle';
  };

  const getPillarColor = (pillarId) => {
    return PILLAR_CONFIG[pillarId]?.color || '#9E9E9E';
  };

  // Queue status helpers
  const getQueueStatusColor = (status) => {
    const colors = {
      'pending': 'grey',
      'running': 'warning',
      'completed': 'success',
      'failed': 'error',
      'PENDING': 'grey',
      'RUNNING': 'warning',
      'COMPLETED': 'success',
      'FAILED': 'error'
    };
    return colors[status] || 'grey';
  };

  const getQueueStatusIcon = (status) => {
    const icons = {
      'pending': 'mdi-clock-outline',
      'running': 'mdi-loading',
      'completed': 'mdi-check',
      'failed': 'mdi-alert',
      'PENDING': 'mdi-clock-outline',
      'RUNNING': 'mdi-loading',
      'COMPLETED': 'mdi-check',
      'FAILED': 'mdi-alert'
    };
    return icons[status] || 'mdi-help';
  };

  const getQueueStatusText = (status) => {
    const texts = {
      'pending': 'Ausstehend',
      'running': 'Läuft',
      'completed': 'Fertig',
      'failed': 'Fehler',
      'PENDING': 'Ausstehend',
      'RUNNING': 'Läuft',
      'COMPLETED': 'Fertig',
      'FAILED': 'Fehler'
    };
    return texts[status] || status;
  };

  // Date formatting
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Format criterion name for display (snake_case to readable)
  const formatCriterionName = (criterion) => {
    const nameMap = {
      'counsellor_coherence': 'Berater-Kohärenz',
      'client_coherence': 'Klienten-Kohärenz',
      'quality': 'Qualität',
      'empathy': 'Empathie',
      'authenticity': 'Authentizität',
      'solution_orientation': 'Lösungsorientierung'
    };
    return nameMap[criterion] || criterion.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Get color based on score (1-5)
  const getScoreColor = (score) => {
    if (score >= 4.5) return 'success';
    if (score >= 3.5) return 'info';
    if (score >= 2.5) return 'warning';
    return 'error';
  };

  // Copy to clipboard
  const copyToClipboard = async (text) => {
    if (!text) return false;
    try {
      await navigator.clipboard.writeText(text);
      console.log('Content copied to clipboard');
      return true;
    } catch (err) {
      console.error('Failed to copy content:', err);
      return false;
    }
  };

  return {
    // Status helpers
    getStatusColor,
    getStatusIcon,
    getStatusText,
    getConfidenceColor,

    // Pillar helpers
    getPillarName,
    getPillarIcon,
    getPillarColor,

    // Queue helpers
    getQueueStatusColor,
    getQueueStatusIcon,
    getQueueStatusText,

    // Format helpers
    formatDate,
    formatCriterionName,
    getScoreColor,

    // Utilities
    copyToClipboard
  };
}
