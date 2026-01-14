/**
 * useJudgeSocket - Socket.IO composable for Judge Sessions
 *
 * Handles all Socket.IO event handling for judge sessions including:
 * - Socket connection and reconnection
 * - Multi-worker stream management
 * - Live updates for session progress, comparisons, and LLM streaming
 * - Browser suspension recovery
 *
 * @param {number|string} sessionId - The judge session ID
 * @param {Object} callbacks - Event callbacks
 * @param {Function} callbacks.onProgress - Called on session progress updates
 * @param {Function} callbacks.onComparisonStart - Called when a comparison starts
 * @param {Function} callbacks.onComparisonComplete - Called when a comparison completes
 * @param {Function} callbacks.onSessionComplete - Called when the session completes
 * @param {Function} callbacks.onError - Called on socket errors
 * @param {Function} callbacks.onReconnect - Called after reconnection
 *
 * @returns {Object} Socket state and control functions
 */

import { ref, reactive, onUnmounted } from 'vue';
import { getSocket } from '@/services/socketService';
import { logI18n, logI18nParams } from '@/utils/logI18n';

export function useJudgeSocket(sessionId, callbacks = {}) {
  // Socket instance
  const socket = ref(null);

  // Multi-worker stream state
  // Structure: { workerId: { content: '', comparison: null, isStreaming: false } }
  const workerStreams = reactive({});

  // Single-worker stream content (for backward compatibility)
  const llmStreamContent = ref('');

  // Reconnection state
  const reconnecting = ref(false);

  // Joined room state
  const isJoined = ref(false);

  /**
   * Initialize a worker stream if it doesn't exist
   * @param {number} workerId - Worker ID
   */
  const initializeWorkerStream = (workerId) => {
    if (!workerStreams[workerId]) {
      logI18nParams('log', 'logs.judge.judgeSocket.initWorkerStream', { workerId });
      workerStreams[workerId] = {
        content: '',
        comparison: null,
        isStreaming: false,
      };
    }
  };

  /**
   * Clear a specific worker's stream content
   * @param {number} workerId - Worker ID
   */
  const clearWorkerStream = (workerId) => {
    if (workerStreams[workerId]) {
      workerStreams[workerId].content = '';
      workerStreams[workerId].isStreaming = false;
      workerStreams[workerId].comparison = null;
    }
  };

  /**
   * Clear all worker streams
   */
  const clearAllWorkerStreams = () => {
    Object.keys(workerStreams).forEach((workerId) => {
      clearWorkerStream(parseInt(workerId));
    });
  };

  /**
   * Join the session room
   */
  const joinSessionRoom = () => {
    if (!socket.value || !socket.value.connected) {
      logI18n('warn', 'logs.judge.judgeSocket.cannotJoinNotConnected');
      return;
    }

    logI18nParams('log', 'logs.judge.judgeSocket.joiningSessionRoom', { sessionId });
    socket.value.emit('judge:join_session', { session_id: parseInt(sessionId) });
  };

  /**
   * Setup all socket event listeners
   */
  const setupEventListeners = () => {
    if (!socket.value) return;

    // Remove existing listeners to prevent duplicates
    socket.value.off('connect');
    socket.value.off('disconnect');
    socket.value.off('reconnect');
    socket.value.off('judge:joined');
    socket.value.off('judge:error');
    socket.value.off('judge:progress');
    socket.value.off('judge:comparison_start');
    socket.value.off('judge:llm_stream');
    socket.value.off('judge:comparison_complete');
    socket.value.off('judge:session_complete');
    socket.value.off('judge:status');

    // Connection event handlers
    socket.value.on('connect', () => {
      logI18n('log', 'logs.judge.judgeSocket.connected', socket.value.id);
      reconnecting.value = false;
      joinSessionRoom();

      // Call reconnect callback if provided
      if (callbacks.onReconnect) {
        callbacks.onReconnect();
      }
    });

    socket.value.on('disconnect', (reason) => {
      logI18n('warn', 'logs.judge.judgeSocket.disconnected', reason);
      reconnecting.value = true;
      isJoined.value = false;
      // Don't clear worker streams - they will be restored on reconnect
    });

    socket.value.on('reconnect', (attemptNumber) => {
      logI18nParams('log', 'logs.judge.judgeSocket.reconnected', { attempts: attemptNumber });
      reconnecting.value = false;
      joinSessionRoom();

      // Call reconnect callback if provided
      if (callbacks.onReconnect) {
        callbacks.onReconnect();
      }
    });

    // Judge-specific event handlers

    // Handle join confirmation
    socket.value.on('judge:joined', (data) => {
      logI18n('log', 'logs.judge.judgeSocket.joinedSessionRoom', data);
      isJoined.value = true;
    });

    // Handle errors
    socket.value.on('judge:error', (data) => {
      logI18n('error', 'logs.judge.judgeSocket.error', data.message);
      if (callbacks.onError) {
        callbacks.onError(data);
      }
    });

    // Progress updates from worker
    socket.value.on('judge:progress', (data) => {
      logI18n('log', 'logs.judge.judgeSocket.progress', data);
      if (data.session_id == sessionId) {
        if (callbacks.onProgress) {
          callbacks.onProgress(data);
        }
      }
    });

    // Comparison started
    socket.value.on('judge:comparison_start', (data) => {
      logI18n('log', 'logs.judge.judgeSocket.comparisonStarted', data);

      // Check session_id if provided, otherwise accept all (room-based filtering)
      if (!data.session_id || data.session_id == sessionId) {
        const workerId = data.worker_id ?? 0; // Default to worker 0 for single-worker mode

        // Initialize worker stream if needed
        initializeWorkerStream(workerId);

        // Update worker stream
        workerStreams[workerId].content = '';
        workerStreams[workerId].isStreaming = true;
        workerStreams[workerId].comparison = {
          thread_a_id: data.thread_a_id,
          thread_b_id: data.thread_b_id,
          pillar_a: data.pillar_a,
          pillar_b: data.pillar_b,
          pillar_a_name: data.pillar_a_name,
          pillar_b_name: data.pillar_b_name,
        };

        // Clear single-worker stream content for new comparison
        llmStreamContent.value = '';

        logI18nParams('log', 'logs.judge.judgeSocket.workerStreamUpdated', { workerId }, workerStreams[workerId]);

        // Call callback if provided
        if (callbacks.onComparisonStart) {
          callbacks.onComparisonStart(data);
        }
      }
    });

    // LLM streaming tokens (show live generation)
    socket.value.on('judge:llm_stream', (data) => {
      if (data.session_id == sessionId) {
        const workerId = data.worker_id ?? 0; // Default to worker 0 for single-worker mode
        const token = data.token || data.content || '';

        // Initialize worker stream if needed (handles race condition)
        initializeWorkerStream(workerId);

        // Update worker stream content
        workerStreams[workerId].content += token;
        workerStreams[workerId].isStreaming = true;

        // Update single-worker stream (for backward compatibility)
        llmStreamContent.value += token;
      }
    });

    // Comparison completed
    socket.value.on('judge:comparison_complete', (data) => {
      logI18n('log', 'logs.judge.judgeSocket.comparisonComplete', data);
      if (data.session_id == sessionId) {
        const workerId = data.worker_id ?? 0;

        // Mark worker as not streaming
        if (workerStreams[workerId]) {
          workerStreams[workerId].isStreaming = false;
          workerStreams[workerId].comparison = null;
        }

        // Call callback if provided
        if (callbacks.onComparisonComplete) {
          callbacks.onComparisonComplete(data);
        }
      }
    });

    // Session completed
    socket.value.on('judge:session_complete', (data) => {
      logI18n('log', 'logs.judge.judgeSocket.sessionComplete', data);
      if (data.session_id == sessionId) {
        // Call callback if provided
        if (callbacks.onSessionComplete) {
          callbacks.onSessionComplete(data);
        }
      }
    });

    // Status response (from get_status request)
    socket.value.on('judge:status', (data) => {
      logI18n('log', 'logs.judge.judgeSocket.status', data);
      if (data.session_id == sessionId) {
        if (callbacks.onProgress) {
          callbacks.onProgress(data);
        }
      }
    });
  };

  /**
   * Join the session and setup listeners
   */
  const joinSession = () => {
    logI18nParams('log', 'logs.judge.judgeSocket.setupForSession', { sessionId });

    // Get or create socket
    socket.value = getSocket();
    logI18nParams('log', 'logs.judge.judgeSocket.socketConnectedState', { connected: socket.value.connected });

    // Setup all event listeners
    setupEventListeners();

    // Join immediately if already connected
    if (socket.value.connected) {
      logI18n('log', 'logs.judge.judgeSocket.alreadyConnected');
      joinSessionRoom();
    } else {
      logI18n('log', 'logs.judge.judgeSocket.waitingForConnect');
    }
  };

  /**
   * Leave the session and cleanup
   */
  const leaveSession = () => {
    if (!socket.value) return;

    logI18nParams('log', 'logs.judge.judgeSocket.leavingSession', { sessionId });

    // Leave the session room
    socket.value.emit('judge:leave_session', { session_id: parseInt(sessionId) });

    // Remove event listeners
    socket.value.off('connect');
    socket.value.off('disconnect');
    socket.value.off('reconnect');
    socket.value.off('judge:joined');
    socket.value.off('judge:error');
    socket.value.off('judge:progress');
    socket.value.off('judge:comparison_start');
    socket.value.off('judge:llm_stream');
    socket.value.off('judge:comparison_complete');
    socket.value.off('judge:session_complete');
    socket.value.off('judge:status');

    isJoined.value = false;
  };

  /**
   * Request session status update
   */
  const requestStatus = () => {
    if (socket.value && socket.value.connected) {
      logI18nParams('log', 'logs.judge.judgeSocket.requestingStatus', { sessionId });
      socket.value.emit('judge:get_status', { session_id: parseInt(sessionId) });
    }
  };

  // Cleanup on unmount
  onUnmounted(() => {
    leaveSession();
  });

  return {
    // State
    socket,
    workerStreams,
    llmStreamContent,
    reconnecting,
    isJoined,

    // Control functions
    joinSession,
    leaveSession,
    clearWorkerStream,
    clearAllWorkerStreams,
    requestStatus,
  };
}
