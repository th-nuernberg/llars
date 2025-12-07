/**
 * Formatting Helper Functions
 *
 * Shared formatting utilities for dates, numbers, and text.
 * Extracted from Judge and OnCoCo components to eliminate duplication.
 */

/**
 * Format date string to German locale format
 * Default format: DD.MM.YYYY, HH:MM
 *
 * @param {string} dateString - ISO date string
 * @param {Object} options - Optional Intl.DateTimeFormat options
 * @returns {string} Formatted date string or '-' if invalid
 */
export const formatDate = (dateString, options = {}) => {
  if (!dateString) return '-';

  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  };

  const date = new Date(dateString);
  return date.toLocaleString('de-DE', { ...defaultOptions, ...options });
};

/**
 * Format date string with seconds
 *
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string with seconds or '-' if invalid
 */
export const formatDateWithSeconds = (dateString) => {
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

/**
 * Format duration in seconds to human-readable string
 * Examples: "45s", "3m 20s", "2h 15m"
 *
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string
 */
export const formatDuration = (seconds) => {
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

/**
 * Format duration in minutes to human-readable string
 * Examples: "30 min", "1h 30 min", "2h 0 min"
 *
 * @param {number} minutes - Duration in minutes
 * @returns {string} Formatted duration string
 */
export const formatDurationMinutes = (minutes) => {
  if (!minutes || minutes < 0) return '0 min';
  if (minutes < 60) return `${Math.round(minutes)} min`;

  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return `${hours}h ${mins} min`;
};

/**
 * Format percentage value (0-1 scale to percentage string)
 *
 * @param {number} value - Decimal value (0-1)
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage (e.g., "75.5%")
 */
export const formatPercentage = (value, decimals = 1) => {
  if (value === null || value === undefined) return '-';
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Format metric value with specified decimal places
 *
 * @param {number} value - Numeric value
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted number or '-' if invalid
 */
export const formatMetric = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-';
  return value.toFixed(decimals);
};

/**
 * Format criterion name from snake_case to German display name
 *
 * @param {string} criterion - Criterion identifier (e.g., 'counsellor_coherence')
 * @returns {string} German display name
 */
export const formatCriterionName = (criterion) => {
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

/**
 * Format Likert metric name (alias for formatCriterionName)
 *
 * @param {string} metric - Metric identifier
 * @returns {string} German display name
 */
export const formatLikertMetric = (metric) => {
  return formatCriterionName(metric);
};

/**
 * Get status icon based on status value
 *
 * @param {string} status - Status string (created, queued, running, paused, completed, failed)
 * @returns {string} Material Design Icon name
 */
export const getStatusIcon = (status) => {
  const icons = {
    created: 'mdi-file-document',
    queued: 'mdi-clock-outline',
    running: 'mdi-play-circle',
    paused: 'mdi-pause-circle',
    completed: 'mdi-check-circle',
    failed: 'mdi-alert-circle',
    pending: 'mdi-clock-outline'
  };
  return icons[status] || 'mdi-help-circle';
};

/**
 * Get queue status icon
 *
 * @param {string} status - Queue status (pending, running, completed, failed - case insensitive)
 * @returns {string} Material Design Icon name
 */
export const getQueueStatusIcon = (status) => {
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

/**
 * Get status text in German
 *
 * @param {string} status - Status string (created, queued, running, paused, completed, failed)
 * @returns {string} German status text
 */
export const getStatusText = (status) => {
  const texts = {
    created: 'Erstellt',
    queued: 'In Warteschlange',
    running: 'Läuft',
    paused: 'Pausiert',
    completed: 'Abgeschlossen',
    failed: 'Fehlgeschlagen',
    pending: 'Ausstehend'
  };
  return texts[status] || status;
};

/**
 * Get queue status text in German
 *
 * @param {string} status - Queue status (pending, running, completed, failed - case insensitive)
 * @returns {string} German status text
 */
export const getQueueStatusText = (status) => {
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

/**
 * Get pillar display name
 *
 * @param {number} pillarId - Pillar ID or number
 * @returns {string} German pillar name
 */
export const getPillarName = (pillarId) => {
  const names = {
    1: 'Rollenspiele',
    3: 'Anonymisierte Daten',
    5: 'Live-Testungen'
  };
  return names[pillarId] || `Säule ${pillarId}`;
};

/**
 * Get bias label in German
 *
 * @param {string} bias - Bias type (primacy, recency, balanced)
 * @returns {string} German bias label
 */
export const getBiasLabel = (bias) => {
  const labels = {
    'primacy': 'Primacy Bias',
    'recency': 'Recency Bias',
    'balanced': 'Ausbalanciert'
  };
  return labels[bias] || 'Unbekannt';
};
