/**
 * Session Socket Composable
 *
 * Handles WebSocket communication for live session updates.
 */

import { getSocket } from '@/services/socketService';

export function useSessionSocket(sessionId, state, api, helpers) {
  const {
    session,
    currentComparison,
    socket,
    llmStreamContent,
    expandedPanels,
    autoScrollEnabled,
    streamOutput,
    fullscreenStreamOutput,
    workerCount,
    workerStreams,
    incrementCompleted,
    resetProgressTracking
  } = state;

  const {
    loadSession,
    loadQueue,
    loadCurrentComparison,
    loadCompletedComparisons,
    loadWorkerStreams,
    loadThreadMessagesForWorker
  } = api;

  const { getPillarName } = helpers;

  let pollInterval = null;

  // Setup Socket.IO for Live Updates
  const setupSocket = () => {
    socket.value = getSocket();
    console.log('[Judge Socket] Setting up socket, connected:', socket.value.connected, 'id:', socket.value.id);

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

    // Helper function to join session room
    const joinSessionRoom = () => {
      console.log('[Judge Socket] Joining session room:', sessionId);
      socket.value.emit('judge:join_session', { session_id: parseInt(sessionId) });
    };

    // Re-join room when socket reconnects
    socket.value.on('connect', async () => {
      console.log('[Judge Socket] Connected/Reconnected, socket id:', socket.value.id);
      joinSessionRoom();
      // Restore accumulated stream content from workers
      await loadWorkerStreams();
      loadSession();
      loadQueue();
    });

    // Handle disconnection
    socket.value.on('disconnect', (reason) => {
      console.warn('[Judge Socket] Disconnected:', reason);
    });

    // Handle reconnect event
    socket.value.on('reconnect', async (attemptNumber) => {
      console.log(`[Judge Socket] Reconnected after ${attemptNumber} attempts`);
      joinSessionRoom();
      // Restore accumulated stream content from workers
      await loadWorkerStreams();
      loadSession();
      loadQueue();
    });

    // Join immediately if already connected
    if (socket.value.connected) {
      console.log('[Judge Socket] Already connected, joining room immediately');
      joinSessionRoom();
      // Restore accumulated stream content from workers
      loadWorkerStreams();
    }

    // Handle join confirmation
    socket.value.on('judge:joined', (data) => {
      console.log('[Judge Socket] Joined session room:', data);
    });

    // Handle errors
    socket.value.on('judge:error', (data) => {
      console.error('[Judge Socket] Error:', data.message);
    });

    // Progress updates from worker (only used for status updates, not counting)
    socket.value.on('judge:progress', (data) => {
      console.log('[Judge Socket] Progress:', data);
      if (data.session_id == sessionId) {
        // Only update status - we count completions ourselves via comparison_complete events
        const newStatus = data.status || session.value?.status;
        if (session.value) {
          session.value = {
            ...session.value,
            status: newStatus
          };
        }
      }
    });

    // Comparison started
    socket.value.on('judge:comparison_start', async (data) => {
      console.log('[Judge Socket] Comparison started:', data);
      if (!data.session_id || data.session_id == sessionId) {
        const workerId = data.worker_id ?? 0;

        // Multi-worker mode: update specific worker stream
        if (workerCount.value > 1) {
          if (!workerStreams[workerId]) {
            workerStreams[workerId] = {
              content: '',
              comparison: null,
              isStreaming: false
            };
          }
          workerStreams[workerId].content = '';
          workerStreams[workerId].isStreaming = true;
          workerStreams[workerId].comparison = {
            thread_a_id: data.thread_a_id,
            thread_b_id: data.thread_b_id,
            pillar_a: data.pillar_a,
            pillar_b: data.pillar_b,
            pillar_a_name: getPillarName(data.pillar_a),
            pillar_b_name: getPillarName(data.pillar_b)
          };

          // Load thread messages for this worker
          loadThreadMessagesForWorker(workerId, data.thread_a_id, data.thread_b_id);
        }

        // Reset stream content for new comparison
        llmStreamContent.value = '';
        autoScrollEnabled.value = true;

        // Update comparison status
        if (currentComparison.value) {
          currentComparison.value = {
            ...currentComparison.value,
            llm_status: 'running',
            winner: null,
            confidence_score: null
          };
        }

        // Expand stream panel
        expandedPanels.value = ['stream', 'prompt'];
        loadCurrentComparison();
        // Refresh queue to show updated running count
        loadQueue();
      }
    });

    // LLM streaming tokens
    socket.value.on('judge:llm_stream', (data) => {
      if (data.session_id == sessionId) {
        const workerId = data.worker_id ?? 0;
        const token = data.token || data.content || '';

        // Multi-worker mode: update specific worker stream
        if (workerCount.value > 1) {
          if (!workerStreams[workerId]) {
            workerStreams[workerId] = {
              content: '',
              comparison: null,
              isStreaming: true
            };
          }
          workerStreams[workerId].content += token;
          workerStreams[workerId].isStreaming = true;
        }

        // Single-worker mode: append to main stream
        llmStreamContent.value += token;

        // Update llm_status
        if (currentComparison.value) {
          currentComparison.value = {
            ...currentComparison.value,
            llm_status: 'running'
          };
        }

        // Auto-scroll
        if (autoScrollEnabled.value) {
          if (streamOutput.value) {
            streamOutput.value.scrollTop = streamOutput.value.scrollHeight;
          }
          if (fullscreenStreamOutput.value) {
            fullscreenStreamOutput.value.scrollTop = fullscreenStreamOutput.value.scrollHeight;
          }
        }
      }
    });

    // Comparison completed - INCREMENT our counter (not trusting reported values)
    socket.value.on('judge:comparison_complete', async (data) => {
      console.log('[Judge Socket] Comparison complete:', data, 'for session:', sessionId);
      if (data.session_id == sessionId) {
        console.log('[Judge Socket] Session ID matches, processing...');
        const workerId = data.worker_id ?? 0;

        // Multi-worker mode: mark worker as not streaming
        if (workerCount.value > 1 && workerStreams[workerId]) {
          workerStreams[workerId].isStreaming = false;
          workerStreams[workerId].comparison = null;
        }

        // INCREMENT our counter - this is the key change!
        // We count events ourselves instead of trusting reported values
        console.log('[Judge Socket] Calling incrementCompleted...');
        incrementCompleted();

        // Update current comparison with result
        if (currentComparison.value) {
          currentComparison.value = {
            ...currentComparison.value,
            llm_status: 'completed',
            winner: data.winner,
            confidence_score: data.confidence
          };
        }
        await loadCompletedComparisons();
        await loadQueue();
      }
    });

    // Session completed - session is done, reload to get final state
    socket.value.on('judge:session_complete', async (data) => {
      console.log('[Judge Socket] Session complete:', data);
      if (data.session_id == sessionId) {
        // Reload session to get authoritative final state (will set counter to total)
        await loadSession();
      }
    });

    // Status response (only used for status updates, not counting)
    socket.value.on('judge:status', (data) => {
      console.log('[Judge Socket] Status:', data);
      if (data.session_id == sessionId) {
        // Only update status - we count completions ourselves
        const newStatus = data.status || session.value?.status;
        if (session.value) {
          session.value = {
            ...session.value,
            status: newStatus,
            current_comparison_id: data.current_comparison_id
          };
        }
      }
    });
  };

  // Start fallback polling
  const startPolling = () => {
    if (pollInterval) return;
    pollInterval = setInterval(async () => {
      if (session.value?.status === 'running') {
        await loadCurrentComparison();
        await loadQueue();
      } else {
        stopPolling();
      }
    }, 30000);
  };

  // Stop polling
  const stopPolling = () => {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  };

  // Reconnect to live stream
  const reconnectToStream = async () => {
    socket.value = getSocket();
    socket.value.emit('judge:join_session', { session_id: parseInt(sessionId) });

    // Restore accumulated stream content from workers
    const restored = await loadWorkerStreams();

    // Only clear if we couldn't restore
    if (!restored) {
      llmStreamContent.value = '';
    }

    await loadCurrentComparison();
    if (!expandedPanels.value.includes('stream')) {
      expandedPanels.value = ['stream', 'prompt'];
    }
    if (currentComparison.value) {
      currentComparison.value = {
        ...currentComparison.value,
        llm_status: 'running'
      };
    }
    console.log('[Judge] Reconnected to live stream, restored:', restored);
  };

  // Cleanup socket
  const cleanupSocket = () => {
    stopPolling();
    if (socket.value) {
      socket.value.emit('judge:leave_session', { session_id: parseInt(sessionId) });
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
    }
  };

  // Handle user scroll
  const handleStreamScroll = (event) => {
    const el = event.target;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    if (!isNearBottom && autoScrollEnabled.value) {
      autoScrollEnabled.value = false;
      console.log('[Stream] Auto-scroll disabled - user scrolled');
    }
  };

  // Re-enable auto-scroll
  const enableAutoScroll = () => {
    autoScrollEnabled.value = true;
    if (fullscreenStreamOutput.value) {
      fullscreenStreamOutput.value.scrollTop = fullscreenStreamOutput.value.scrollHeight;
    }
    if (streamOutput.value) {
      streamOutput.value.scrollTop = streamOutput.value.scrollHeight;
    }
    console.log('[Stream] Auto-scroll re-enabled');
  };

  return {
    setupSocket,
    cleanupSocket,
    startPolling,
    stopPolling,
    reconnectToStream,
    handleStreamScroll,
    enableAutoScroll
  };
}
