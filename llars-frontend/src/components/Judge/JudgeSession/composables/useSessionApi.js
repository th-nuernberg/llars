/**
 * Session API Composable
 *
 * Handles all API calls for session management.
 */

import axios from 'axios';

export function useSessionApi(sessionId, state, helpers) {
  const {
    session,
    currentComparison,
    completedComparisons,
    queue,
    sessionHealth,
    loading,
    actionLoading,
    queueLoading,
    workerCount,
    workerStreams,
    workerPoolStatus,
    initializeWorkerStreams,
    initializeProgressFromApi,
    resetProgressTracking
  } = state;

  const { getPillarName } = helpers;

  // Load Session Health (for intelligent button state)
  const loadSessionHealth = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/health`
      );
      sessionHealth.value = response.data;
      console.log('[Judge] Session health:', response.data);
    } catch (error) {
      console.error('Error loading session health:', error);
      // Fallback: assume healthy if endpoint fails
      sessionHealth.value = {
        workers_running: session.value?.status === 'running',
        needs_recovery: false
      };
    }
  };

  // Load Session
  const loadSession = async () => {
    loading.value = true;
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}`
      );
      session.value = response.data;

      // Initialize progress counter from authoritative API data
      // API data is the source of truth for initialization
      // Always call initializeProgressFromApi - it handles null/undefined internally
      initializeProgressFromApi(
        response.data.completed_comparisons,
        response.data.total_comparisons
      );

      // Extract worker_count from config
      const sessionConfig = session.value.config || session.value.config_json;
      if (sessionConfig?.worker_count) {
        workerCount.value = sessionConfig.worker_count;
        initializeWorkerStreams(workerCount.value);
      }

      // Load current comparison (always load when running, might have active comparisons)
      if (session.value.status === 'running' || session.value.current_comparison_id || session.value.current_comparison) {
        await loadCurrentComparison();
      }

      // Load completed comparisons and queue
      await loadCompletedComparisons();
      await loadQueue();

      // Load worker pool status and health check for running/paused sessions
      if (session.value.status === 'running' || session.value.status === 'paused') {
        await loadWorkerPoolStatus();
        await loadSessionHealth();
      }
    } catch (error) {
      console.error('Error loading session:', error);
    } finally {
      loading.value = false;
    }
  };

  // Load worker pool status
  const loadWorkerPoolStatus = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/workers`
      );
      workerPoolStatus.value = response.data;

      // Initialize and update worker streams from pool status
      if (response.data.workers) {
        response.data.workers.forEach(worker => {
          if (!workerStreams[worker.worker_id]) {
            workerStreams[worker.worker_id] = {
              content: '',
              comparison: null,
              isStreaming: false
            };
          }
          workerStreams[worker.worker_id].comparison = worker.current_comparison;
          if (worker.status === 'running' || worker.status === 'RUNNING') {
            workerStreams[worker.worker_id].isStreaming = true;
          }
        });
      }
    } catch (error) {
      console.error('Error loading worker pool status:', error);
    }
  };

  // Load worker streams with full accumulated content (for reconnect support)
  const loadWorkerStreams = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/workers/streams`
      );

      console.log('[Judge] Loaded worker streams for reconnect:', response.data);

      if (!response.data.running || !response.data.workers?.length) {
        console.log('[Judge] No active worker pool, skipping stream restore');
        return false;
      }

      // Update worker count from pool
      if (response.data.worker_count) {
        workerCount.value = response.data.worker_count;
        initializeWorkerStreams(response.data.worker_count);
      }

      // Restore each worker's accumulated stream content
      const threadLoadPromises = [];

      response.data.workers.forEach(worker => {
        const workerId = worker.worker_id;

        if (!workerStreams[workerId]) {
          workerStreams[workerId] = {
            content: '',
            comparison: null,
            isStreaming: false
          };
        }

        // Restore accumulated stream content
        if (worker.stream_content) {
          workerStreams[workerId].content = worker.stream_content;
          console.log(`[Judge] Restored ${worker.stream_length} chars for worker ${workerId}`);
        }

        // Restore comparison info
        if (worker.comparison) {
          workerStreams[workerId].comparison = worker.comparison;

          // Queue thread message loading if we have thread IDs
          if (worker.comparison.thread_a_id && worker.comparison.thread_b_id) {
            threadLoadPromises.push(
              loadThreadMessagesForWorker(workerId, worker.comparison.thread_a_id, worker.comparison.thread_b_id)
            );
          }
        }

        // Restore streaming state
        workerStreams[workerId].isStreaming = worker.is_streaming || false;
      });

      // Load thread messages in parallel (don't block return)
      if (threadLoadPromises.length > 0) {
        Promise.all(threadLoadPromises).then(() => {
          console.log('[Judge] Thread messages loaded for all workers');
        });
      }

      return true;
    } catch (error) {
      console.error('Error loading worker streams:', error);
      return false;
    }
  };

  // Load current comparison
  const loadCurrentComparison = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/current`
      );
      currentComparison.value = response.data;
    } catch (error) {
      console.error('Error loading current comparison:', error);
    }
  };

  // Load thread messages for a specific worker's comparison
  const loadThreadMessagesForWorker = async (workerId, threadAId, threadBId) => {
    try {
      // Load both threads in parallel
      const [threadAResponse, threadBResponse] = await Promise.all([
        axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/generations/${threadAId}`),
        axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/generations/${threadBId}`)
      ]);

      // Update worker stream with thread messages
      if (workerStreams[workerId]) {
        workerStreams[workerId].comparison = {
          ...workerStreams[workerId].comparison,
          thread_a_messages: threadAResponse.data.messages || [],
          thread_b_messages: threadBResponse.data.messages || []
        };
      }

      console.log(`[Judge] Loaded thread messages for worker ${workerId}`);
      return true;
    } catch (error) {
      console.error(`Error loading thread messages for worker ${workerId}:`, error);
      return false;
    }
  };

  // Load completed comparisons
  const loadCompletedComparisons = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/comparisons`
      );
      completedComparisons.value = response.data;
    } catch (error) {
      console.error('Error loading comparisons:', error);
    }
  };

  // Load queue
  const loadQueue = async () => {
    queueLoading.value = true;
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/queue`
      );
      queue.value = response.data;
    } catch (error) {
      console.error('Error loading queue:', error);
    } finally {
      queueLoading.value = false;
    }
  };

  // Start session
  const startSession = async (startPolling) => {
    actionLoading.value = true;
    try {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/start`
      );
      await loadSession();
      if (startPolling) startPolling();
    } catch (error) {
      console.error('Error starting session:', error);
    } finally {
      actionLoading.value = false;
    }
  };

  // Pause session
  const pauseSession = async (stopPolling) => {
    actionLoading.value = true;
    try {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/pause`
      );
      if (stopPolling) stopPolling();
      await loadSession();
    } catch (error) {
      console.error('Error pausing session:', error);
    } finally {
      actionLoading.value = false;
    }
  };

  // Resume session
  const resumeSession = async (startPolling) => {
    actionLoading.value = true;
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/resume`
      );
      console.log('[Judge] Session resumed:', response.data);
      await loadSession();
      if (startPolling) startPolling();
    } catch (error) {
      console.error('Error resuming session:', error);
    } finally {
      actionLoading.value = false;
    }
  };

  // Refresh all data including health check
  const refreshAll = async () => {
    await loadSession();
    if (session.value?.status === 'running' || session.value?.status === 'paused') {
      await loadSessionHealth();
    }
  };

  return {
    loadSession,
    loadSessionHealth,
    loadWorkerPoolStatus,
    loadWorkerStreams,
    loadCurrentComparison,
    loadThreadMessagesForWorker,
    loadCompletedComparisons,
    loadQueue,
    startSession,
    pauseSession,
    resumeSession,
    refreshAll
  };
}
