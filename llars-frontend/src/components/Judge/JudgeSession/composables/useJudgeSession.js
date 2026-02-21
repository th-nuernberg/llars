import { ref, computed } from 'vue';
import axios from 'axios';
import { logI18n } from '@/utils/logI18n';

/**
 * Composable for managing Judge Session state and API calls
 *
 * @param {string|number} sessionId - The session ID
 * @returns {Object} Session state and functions
 */
export function useJudgeSession(sessionId) {
  // ===========================
  // State
  // ===========================

  const session = ref(null);
  const loading = ref(false);
  const actionLoading = ref(false);
  const sessionHealth = ref(null);

  // ===========================
  // Computed
  // ===========================

  /**
   * Calculate session progress percentage
   */
  const progress = computed(() => {
    if (!session.value || !session.value.total_comparisons) return 0;
    return (session.value.completed_comparisons / session.value.total_comparisons) * 100;
  });

  /**
   * Check if session is actually running (workers active)
   */
  const isActuallyRunning = computed(() => {
    // Session must be in "running" status AND workers must be actually running
    if (session.value?.status !== 'running') return false;
    return sessionHealth.value?.workers_running === true;
  });

  /**
   * Determine if Resume button should be shown
   */
  const showResumeButton = computed(() => {
    const status = session.value?.status;

    // Show for paused sessions
    if (status === 'paused') return true;

    // Show for "running" sessions that need recovery (workers stopped)
    if (status === 'running' && sessionHealth.value?.needs_recovery) return true;

    // Don't show for actually running or completed sessions
    return false;
  });

  /**
   * Extract worker count from session config
   */
  const workerCount = computed(() => {
    const sessionConfig = session.value?.config || session.value?.config_json;
    return sessionConfig?.worker_count || 1;
  });

  // ===========================
  // API Functions
  // ===========================

  /**
   * Load session health status (for intelligent button logic)
   */
  const loadSessionHealth = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/health`
      );
      sessionHealth.value = response.data;
      logI18n('log', 'logs.judge.session.sessionHealth', response.data);
    } catch (error) {
      logI18n('error', 'logs.judge.session.loadSessionHealthFailed', error);
      // Fallback: assume healthy if endpoint fails
      sessionHealth.value = {
        workers_running: session.value?.status === 'running',
        needs_recovery: false
      };
    }
  };

  /**
   * Load session data from API
   *
   * @param {Object} options - Load options
   * @param {boolean} options.skipLoading - Skip setting loading state
   * @returns {Promise<Object>} Session data
   */
  const loadSession = async (options = {}) => {
    const { skipLoading = false } = options;

    if (!skipLoading) {
      loading.value = true;
    }

    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}`
      );
      session.value = response.data;

      // Load health check for running/paused sessions
      if (session.value.status === 'running' || session.value.status === 'paused') {
        await loadSessionHealth();
      }

      return session.value;
    } catch (error) {
      logI18n('error', 'logs.judge.session.loadSessionFailed', error);
      throw error;
    } finally {
      if (!skipLoading) {
        loading.value = false;
      }
    }
  };

  /**
   * Refresh all session data including health check
   *
   * @returns {Promise<void>}
   */
  const refreshAll = async () => {
    await loadSession();
    if (session.value?.status === 'running' || session.value?.status === 'paused') {
      await loadSessionHealth();
    }
  };

  // ===========================
  // Session Control Functions
  // ===========================

  /**
   * Start the session
   *
   * @returns {Promise<void>}
   */
  const startSession = async () => {
    actionLoading.value = true;
    try {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/start`
      );
      await loadSession();
      logI18n('log', 'logs.judge.session.sessionStarted');
    } catch (error) {
      logI18n('error', 'logs.judge.session.startSessionFailed', error);
      throw error;
    } finally {
      actionLoading.value = false;
    }
  };

  /**
   * Pause the session
   *
   * @returns {Promise<void>}
   */
  const pauseSession = async () => {
    actionLoading.value = true;
    try {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/pause`
      );
      await loadSession();
      logI18n('log', 'logs.judge.session.sessionPaused');
    } catch (error) {
      logI18n('error', 'logs.judge.session.pauseSessionFailed', error);
      throw error;
    } finally {
      actionLoading.value = false;
    }
  };

  /**
   * Resume the session (also handles recovery)
   *
   * @returns {Promise<void>}
   */
  const resumeSession = async () => {
    actionLoading.value = true;
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/resume`
      );
      logI18n('log', 'logs.judge.session.sessionResumed', response.data);
      await loadSession();
    } catch (error) {
      logI18n('error', 'logs.judge.session.resumeSessionFailed', error);
      throw error;
    } finally {
      actionLoading.value = false;
    }
  };

  // ===========================
  // Status Helper Functions
  // ===========================

  /**
   * Get color for session status
   *
   * @param {string} status - Session status
   * @returns {string} Vuetify color name
   */
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

  /**
   * Get icon for session status
   *
   * @param {string} status - Session status
   * @returns {string} Material Design Icon name
   */
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

  /**
   * Get text label for session status
   *
   * @param {string} status - Session status
   * @returns {string} German status text
   */
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

  // ===========================
  // Return Public API
  // ===========================

  return {
    // State
    session,
    loading,
    actionLoading,
    sessionHealth,

    // Computed
    progress,
    isActuallyRunning,
    showResumeButton,
    workerCount,

    // API Functions
    loadSession,
    loadSessionHealth,
    refreshAll,

    // Session Control
    startSession,
    pauseSession,
    resumeSession,

    // Status Helpers
    getStatusColor,
    getStatusText,
    getStatusIcon,
  };
}
