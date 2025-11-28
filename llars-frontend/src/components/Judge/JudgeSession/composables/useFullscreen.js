/**
 * Fullscreen Composable
 *
 * Handles fullscreen mode for single and multi-worker views.
 */

export function useFullscreen(state, api) {
  const {
    session,
    fullscreenMode,
    autoScrollEnabled,
    multiWorkerFullscreenMode,
    multiWorkerDisplayMode,
    focusedWorkerId,
    reconnecting,
    isStreaming
  } = state;

  const { loadWorkerPoolStatus } = api;

  // Open fullscreen mode (single worker)
  const openFullscreen = (reconnectToStream) => {
    fullscreenMode.value = true;
    autoScrollEnabled.value = true;
    // Auto-reconnect to stream when opening fullscreen
    if (session.value?.status === 'running' && !isStreaming.value) {
      if (reconnectToStream) reconnectToStream();
    }
  };

  // Close fullscreen mode
  const closeFullscreen = () => {
    fullscreenMode.value = false;
  };

  // Open multi-worker fullscreen mode
  const openMultiWorkerFullscreen = async () => {
    multiWorkerFullscreenMode.value = true;
    await loadWorkerPoolStatus();
  };

  // Close multi-worker fullscreen mode
  const closeMultiWorkerFullscreen = () => {
    multiWorkerFullscreenMode.value = false;
  };

  // Open fullscreen for a specific worker (from WorkerLane emit)
  const openWorkerFullscreen = async (workerId) => {
    focusedWorkerId.value = workerId;
    multiWorkerDisplayMode.value = 'focus';
    multiWorkerFullscreenMode.value = true;
    await loadWorkerPoolStatus();
  };

  return {
    openFullscreen,
    closeFullscreen,
    openMultiWorkerFullscreen,
    closeMultiWorkerFullscreen,
    openWorkerFullscreen
  };
}
