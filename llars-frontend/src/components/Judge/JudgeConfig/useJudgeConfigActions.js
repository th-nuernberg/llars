/**
 * Judge Config Actions Composable
 *
 * API calls and session creation.
 */

import { ref } from 'vue';
import axios from 'axios';

export function useJudgeConfigActions(config, estimate, limitThreadsEnabled, minPillarsRequired, updateThreadCounts) {
  let estimateDebounceTimer = null;

  /**
   * Format number for display.
   */
  const formatNumber = (num) => {
    if (num === null || num === undefined) return '0';
    return num.toLocaleString('de-DE');
  };

  /**
   * Format duration in minutes to human-readable string.
   */
  const formatDuration = (minutes) => {
    if (minutes < 1) return '< 1 min';
    if (minutes < 60) return `${Math.round(minutes)} min`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (mins === 0) return `${hours}h`;
    return `${hours}h ${mins}m`;
  };

  /**
   * Get pillar name by ID.
   */
  const getPillarName = (id, availablePillars) => {
    const pillar = availablePillars.value.find(p => p.id === id);
    return pillar ? `Säule ${id}` : `Säule ${id}`;
  };

  /**
   * Debounced estimate fetch.
   */
  const debouncedFetchEstimate = (fetchFn) => {
    if (estimateDebounceTimer) {
      clearTimeout(estimateDebounceTimer);
    }
    estimateDebounceTimer = setTimeout(() => {
      fetchFn();
    }, 300);
  };

  /**
   * Fetch estimate from API.
   */
  const fetchEstimate = async (estimateLoading) => {
    if (config.value.selectedPillars.length < minPillarsRequired.value) {
      estimate.value = null;
      return;
    }

    estimateLoading.value = true;
    try {
      const payload = {
        pillar_ids: config.value.selectedPillars,
        comparison_mode: config.value.comparisonMode,
        samples_per_pillar: config.value.samplesPerPillar,
        position_swap: config.value.positionSwap
      };

      // Only include max_threads_per_pillar if limit is enabled
      if (limitThreadsEnabled.value && config.value.maxThreadsPerPillar) {
        payload.max_threads_per_pillar = config.value.maxThreadsPerPillar;
      }

      const response = await axios.post('/api/judge/estimate', payload);
      estimate.value = response.data;

      // Update thread counts from estimate
      updateThreadCounts(response.data.threads_per_pillar);
    } catch (error) {
      console.error('Error fetching estimate:', error);
      estimate.value = null;
    } finally {
      estimateLoading.value = false;
    }
  };

  /**
   * Create session via API.
   */
  const createSession = async (form, creating, router) => {
    // Validate form
    if (form.value) {
      const { valid: isValid } = await form.value.validate();
      if (!isValid) return;
    }

    creating.value = true;
    try {
      const payload = {
        session_name: config.value.sessionName,
        pillar_ids: config.value.selectedPillars,
        comparison_mode: config.value.comparisonMode,
        samples_per_pillar: config.value.samplesPerPillar,
        position_swap: config.value.positionSwap,
        repetitions_per_pair: config.value.repetitionsPerPair,
        worker_count: config.value.workerCount
      };

      // Only include max_threads_per_pillar if enabled
      if (limitThreadsEnabled.value && config.value.maxThreadsPerPillar) {
        payload.max_threads_per_pillar = config.value.maxThreadsPerPillar;
      }

      // Use debug endpoint in development mode
      const isDev = import.meta.env.DEV || import.meta.env.MODE === 'development';
      const createEndpoint = isDev
        ? '/api/judge/sessions-debug'
        : '/api/judge/sessions';

      const response = await axios.post(createEndpoint, payload);
      const sessionId = response.data.session_id;

      // Auto-start the session immediately after creation
      try {
        const startEndpoint = isDev
          ? `/api/judge/sessions/${sessionId}/start-debug`
          : `/api/judge/sessions/${sessionId}/start`;
        await axios.post(startEndpoint);
        console.log(`Session ${sessionId} auto-started`);
      } catch (startError) {
        console.warn('Auto-start failed, session can be started manually:', startError);
      }

      // Navigate directly to the new session
      router.push({ name: 'JudgeSession', params: { id: sessionId } });
    } catch (error) {
      console.error('Error creating session:', error);
      alert('Fehler beim Erstellen der Session. Bitte versuchen Sie es erneut.');
    } finally {
      creating.value = false;
    }
  };

  return {
    formatNumber,
    formatDuration,
    getPillarName,
    debouncedFetchEstimate,
    fetchEstimate,
    createSession
  };
}
