/**
 * Judge Config Actions Composable
 *
 * API calls and session creation.
 */

import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { logI18n, logI18nParams } from '@/utils/logI18n';

export function useJudgeConfigActions(config, estimate, limitThreadsEnabled, minPillarsRequired, updateThreadCounts) {
  const { t, locale } = useI18n();
  let estimateDebounceTimer = null;

  /**
   * Format number for display.
   */
  const formatNumber = (num) => {
    if (num === null || num === undefined) return '0';
    return num.toLocaleString(locale.value || undefined);
  };

  /**
   * Format duration in minutes to human-readable string.
   */
  const formatDuration = (minutes) => {
    if (minutes < 1) return t('judge.duration.lessThanMinute');
    if (minutes < 60) return t('judge.duration.minutes', { count: Math.round(minutes) });
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (mins === 0) return t('judge.duration.hours', { count: hours });
    return t('judge.duration.hoursMinutes', { hours, minutes: mins });
  };

  /**
   * Get pillar name by ID.
   */
  const getPillarName = (id, availablePillars) => {
    const pillar = availablePillars.value.find(p => p.id === id);
    if (pillar?.nameKey) return t(pillar.nameKey);
    return t('judge.pillars.defaultLabel', { id });
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
      logI18n('error', 'logs.judge.config.fetchEstimateFailed', error);
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
        logI18nParams('log', 'logs.judge.config.sessionAutoStarted', { sessionId });
      } catch (startError) {
        logI18n('warn', 'logs.judge.config.autoStartFailed', startError);
      }

      // Navigate directly to the new session
      router.push({ name: 'JudgeSession', params: { id: sessionId } });
    } catch (error) {
      logI18n('error', 'logs.judge.config.createSessionFailed', error);
      alert(t('judge.config.errors.createFailed'));
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
