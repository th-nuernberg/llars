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
