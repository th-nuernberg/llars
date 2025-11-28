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
      console.log(`[Judge Socket] Initializing worker stream ${workerId}`);
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
      console.warn('[Judge Socket] Cannot join session - socket not connected');
      return;
    }

    console.log('[Judge Socket] Joining session room:', sessionId);
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
      console.log('[Judge Socket] Connected/Reconnected, socket id:', socket.value.id);
      reconnecting.value = false;
      joinSessionRoom();

      // Call reconnect callback if provided
      if (callbacks.onReconnect) {
        callbacks.onReconnect();
      }
    });

    socket.value.on('disconnect', (reason) => {
      console.warn('[Judge Socket] Disconnected:', reason);
      reconnecting.value = true;
      isJoined.value = false;
      // Don't clear worker streams - they will be restored on reconnect
    });

    socket.value.on('reconnect', (attemptNumber) => {
      console.log(`[Judge Socket] Reconnected after ${attemptNumber} attempts`);
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
      console.log('[Judge Socket] Joined session room:', data);
      isJoined.value = true;
    });

    // Handle errors
    socket.value.on('judge:error', (data) => {
      console.error('[Judge Socket] Error:', data.message);
      if (callbacks.onError) {
        callbacks.onError(data);
      }
    });

    // Progress updates from worker
    socket.value.on('judge:progress', (data) => {
      console.log('[Judge Socket] Progress:', data);
      if (data.session_id == sessionId) {
        if (callbacks.onProgress) {
          callbacks.onProgress(data);
        }
      }
    });

    // Comparison started
    socket.value.on('judge:comparison_start', (data) => {
      console.log('[Judge Socket] Comparison started:', data);

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

        console.log(`[Judge Socket] Worker ${workerId} stream updated for new comparison`, workerStreams[workerId]);

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
      console.log('[Judge Socket] Comparison complete:', data);
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
      console.log('[Judge Socket] Session complete:', data);
      if (data.session_id == sessionId) {
        // Call callback if provided
        if (callbacks.onSessionComplete) {
          callbacks.onSessionComplete(data);
        }
      }
    });

    // Status response (from get_status request)
    socket.value.on('judge:status', (data) => {
      console.log('[Judge Socket] Status:', data);
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
    console.log('[Judge Socket] Setting up socket for session:', sessionId);

    // Get or create socket
    socket.value = getSocket();
    console.log('[Judge Socket] Socket connected:', socket.value.connected);

    // Setup all event listeners
    setupEventListeners();

    // Join immediately if already connected
    if (socket.value.connected) {
      console.log('[Judge Socket] Already connected, joining room immediately');
      joinSessionRoom();
    } else {
      console.log('[Judge Socket] Not yet connected, waiting for connect event');
    }
  };

  /**
   * Leave the session and cleanup
   */
  const leaveSession = () => {
    if (!socket.value) return;

    console.log('[Judge Socket] Leaving session:', sessionId);

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
      console.log('[Judge Socket] Requesting status for session:', sessionId);
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
