/**
 * Color Helper Functions
 *
 * Shared color utilities for consistent styling across components.
 * Extracted from Judge and OnCoCo components to eliminate duplication.
 */

/**
 * Get color based on score value (1-5 scale)
 * Used for Likert scores and other 1-5 rating systems
 *
 * @param {number} score - Score value (1-5)
 * @returns {string} Vuetify color name
 */
export const getScoreColor = (score) => {
  if (score >= 4.5) return 'success';
  if (score >= 3.5) return 'info';
  if (score >= 2.5) return 'warning';
  return 'error';
};

/**
 * Get color based on win rate (0-1 scale)
 *
 * @param {number} winRate - Win rate as decimal (0-1)
 * @returns {string} Vuetify color name
 */
export const getWinRateColor = (winRate) => {
  if (winRate >= 0.7) return 'success';
  if (winRate >= 0.5) return 'info';
  if (winRate >= 0.3) return 'warning';
  return 'error';
};

/**
 * Get color based on confidence value (0-1 scale)
 *
 * @param {number} confidence - Confidence score as decimal (0-1)
 * @returns {string} Vuetify color name
 */
export const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.6) return 'info';
  if (confidence >= 0.4) return 'warning';
  return 'error';
};

/**
 * Get color based on rank/position
 * Gold, silver, bronze, etc.
 *
 * @param {number} index - Zero-based rank index (0 = first place)
 * @returns {string} Vuetify color name
 */
export const getRankColor = (index) => {
  const colors = ['warning', 'grey-lighten-1', 'orange-lighten-1', 'grey-lighten-2', 'grey-lighten-3'];
  return colors[index] || 'grey';
};

/**
 * Get color for status values
 * Used for job/session/analysis status
 *
 * @param {string} status - Status string (created, queued, running, paused, completed, failed, pending)
 * @returns {string} Vuetify color name
 */
export const getStatusColor = (status) => {
  const colors = {
    created: 'grey',
    queued: 'warning',
    running: 'info',
    paused: 'orange',
    completed: 'success',
    failed: 'error',
    pending: 'grey'
  };
  return colors[status] || 'grey';
};

/**
 * Get color for queue status
 * Similar to getStatusColor but with uppercase variants
 *
 * @param {string} status - Queue status (pending, running, completed, failed - case insensitive)
 * @returns {string} Vuetify color name
 */
export const getQueueStatusColor = (status) => {
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

/**
 * Get color based on Likert consistency score (0-1 scale)
 *
 * @param {number} score - Consistency score as decimal (0-1)
 * @returns {string} Vuetify color name
 */
export const getLikertConsistencyColor = (score) => {
  if (score >= 0.7) return 'success';
  if (score >= 0.5) return 'warning';
  return 'error';
};

/**
 * Get color based on consistency quality label
 *
 * @param {string} quality - Quality label (excellent, good, fair, poor)
 * @returns {string} Vuetify color name
 */
export const getConsistencyQualityColor = (quality) => {
  const colors = {
    'excellent': 'success',
    'good': 'info',
    'fair': 'warning',
    'poor': 'error'
  };
  return colors[quality] || 'grey';
};

/**
 * Pick a readable text color (near-black or white) for a given background hex,
 * using the WCAG relative-luminance heuristic. Used so a colored badge (e.g. a
 * referral-link origin pill) stays legible whatever brand color it carries.
 *
 * @param {string} hex - Background color (#rgb, #rrggbb, with or without '#')
 * @returns {string} '#1a1a1a' for light backgrounds, '#ffffff' for dark ones
 */
export const getReadableTextColor = (hex) => {
  if (!hex || typeof hex !== 'string') return '#1a1a1a';
  let h = hex.replace('#', '').trim();
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  if (h.length !== 6 || /[^0-9a-fA-F]/.test(h)) return '#1a1a1a';
  const r = parseInt(h.slice(0, 2), 16) / 255;
  const g = parseInt(h.slice(2, 4), 16) / 255;
  const b = parseInt(h.slice(4, 6), 16) / 255;
  // sRGB -> linear, then relative luminance (per WCAG 2.x)
  const lin = (c) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const luminance = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  return luminance > 0.55 ? '#1a1a1a' : '#ffffff';
};
