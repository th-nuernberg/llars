/**
 * KIA Status Cache Composable
 *
 * Caches KIA sync status in sessionStorage to prevent
 * repeated API calls on every page navigation.
 */

import { ref, reactive } from 'vue';
import axios from 'axios';

const CACHE_KEY = 'kia-status-cache';
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes TTL

// Shared state across component instances
const state = reactive({
  pillars: {},
  totalThreads: 0,
  gitlabConnected: false,
  lastFetched: null,
  loading: false,
  error: null
});

export function useKIAStatusCache() {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

  /**
   * Load cached data from sessionStorage
   */
  const loadFromCache = () => {
    try {
      const cached = sessionStorage.getItem(CACHE_KEY);
      if (cached) {
        const data = JSON.parse(cached);
        const age = Date.now() - (data.timestamp || 0);

        // Check if cache is still valid
        if (age < CACHE_TTL) {
          state.pillars = data.pillars || {};
          state.totalThreads = data.totalThreads || 0;
          state.gitlabConnected = data.gitlabConnected || false;
          state.lastFetched = data.timestamp;
          return true;
        }
      }
    } catch (e) {
      console.warn('Failed to load KIA cache:', e);
    }
    return false;
  };

  /**
   * Save current state to sessionStorage
   */
  const saveToCache = () => {
    try {
      const data = {
        pillars: state.pillars,
        totalThreads: state.totalThreads,
        gitlabConnected: state.gitlabConnected,
        timestamp: Date.now()
      };
      sessionStorage.setItem(CACHE_KEY, JSON.stringify(data));
    } catch (e) {
      console.warn('Failed to save KIA cache:', e);
    }
  };

  /**
   * Clear the cache
   */
  const clearCache = () => {
    sessionStorage.removeItem(CACHE_KEY);
    state.lastFetched = null;
  };

  /**
   * Check if we should fetch fresh data
   */
  const shouldFetch = () => {
    if (!state.lastFetched) return true;
    const age = Date.now() - state.lastFetched;
    return age >= CACHE_TTL;
  };

  /**
   * Fetch status from API (with optional force refresh)
   */
  const fetchStatus = async (force = false) => {
    // Try cache first (unless forced)
    if (!force && loadFromCache()) {
      return { fromCache: true };
    }

    // Don't fetch if we already have recent data
    if (!force && !shouldFetch()) {
      return { fromCache: true };
    }

    state.loading = true;
    state.error = null;

    try {
      const response = await axios.get(`${API_BASE}/api/judge/kia/status`);
      state.pillars = response.data.pillars || {};
      state.totalThreads = response.data.total_threads || 0;
      state.gitlabConnected = response.data.gitlab_connected || false;
      state.lastFetched = Date.now();
      saveToCache();
      return { fromCache: false, data: response.data };
    } catch (error) {
      state.error = error.response?.data?.error || error.message;
      // Don't clear existing data on error
      if (error.response?.status !== 401) {
        console.error('Error fetching KIA status:', error);
      }
      throw error;
    } finally {
      state.loading = false;
    }
  };

  /**
   * Update state after sync operation
   */
  const updateAfterSync = (pillars, totalThreads) => {
    state.pillars = pillars;
    state.totalThreads = totalThreads;
    state.lastFetched = Date.now();
    saveToCache();
  };

  return {
    // State (reactive)
    pillars: ref(state.pillars),
    totalThreads: ref(state.totalThreads),
    gitlabConnected: ref(state.gitlabConnected),
    loading: ref(state.loading),
    error: ref(state.error),

    // Reactive state object for direct binding
    state,

    // Methods
    fetchStatus,
    clearCache,
    updateAfterSync,
    shouldFetch
  };
}
