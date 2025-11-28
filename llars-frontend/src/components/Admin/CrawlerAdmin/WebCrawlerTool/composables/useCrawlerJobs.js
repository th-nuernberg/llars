/**
 * Crawler Jobs Composable
 *
 * Handles job listing, watching, and progress tracking.
 * Extracted from WebCrawlerTool.vue for better maintainability.
 */

import { ref, computed } from 'vue';
import axios from 'axios';

export function useCrawlerJobs() {
  // State
  const jobs = ref([]);
  const loadingJobs = ref(false);
  const watchingJob = ref(null);
  const liveProgress = ref({});
  const recentPages = ref([]);

  // Computed
  const runningJobs = computed(() => {
    return jobs.value.filter(j => j.status === 'running' || j.status === 'queued');
  });

  const progressPercent = computed(() => {
    if (!liveProgress.value.max_pages) return 0;
    return Math.min(100, Math.round((liveProgress.value.pages_crawled / liveProgress.value.max_pages) * 100));
  });

  // Methods
  const loadJobs = async () => {
    loadingJobs.value = true;
    try {
      const response = await axios.get('/api/crawler/jobs');
      if (response.data.success) {
        const newJobs = response.data.jobs || [];
        for (const newJob of newJobs) {
          const existingIdx = jobs.value.findIndex(j => j.job_id === newJob.job_id);
          if (existingIdx !== -1) {
            Object.assign(jobs.value[existingIdx], newJob);
          } else {
            jobs.value.push(newJob);
          }

          // Update watchingJob if applicable
          if (watchingJob.value && watchingJob.value.job_id === newJob.job_id) {
            watchingJob.value = { ...watchingJob.value, ...newJob };
            liveProgress.value = {
              pages_crawled: newJob.pages_crawled || 0,
              max_pages: newJob.max_pages || liveProgress.value.max_pages || 50,
              current_url: newJob.current_url || liveProgress.value.current_url,
              current_url_index: liveProgress.value.current_url_index || 1,
              total_urls: newJob.urls?.length || liveProgress.value.total_urls || 1
            };
          }
        }
        sortJobs();
      }
    } catch (error) {
      console.error('Error loading jobs:', error);
    } finally {
      loadingJobs.value = false;
    }
  };

  const sortJobs = () => {
    jobs.value.sort((a, b) => {
      const dateA = new Date(b.started_at || b.queued_at || 0);
      const dateB = new Date(a.started_at || a.queued_at || 0);
      return dateA - dateB;
    });
  };

  const updateJobsList = (newJobs) => {
    for (const newJob of newJobs) {
      const existingIdx = jobs.value.findIndex(j => j.job_id === newJob.job_id);
      if (existingIdx !== -1) {
        Object.assign(jobs.value[existingIdx], newJob);
      } else {
        jobs.value.push(newJob);
      }

      // Update watchingJob and liveProgress
      if (watchingJob.value && watchingJob.value.job_id === newJob.job_id) {
        watchingJob.value = { ...watchingJob.value, ...newJob };
        liveProgress.value = {
          pages_crawled: newJob.pages_crawled || 0,
          max_pages: newJob.max_pages || liveProgress.value.max_pages || 50,
          current_url: newJob.current_url || liveProgress.value.current_url,
          current_url_index: liveProgress.value.current_url_index || 1,
          total_urls: newJob.urls?.length || liveProgress.value.total_urls || 1
        };
      }
    }
    sortJobs();
  };

  const watchJob = (job) => {
    watchingJob.value = { ...job };
    liveProgress.value = {
      pages_crawled: job.pages_crawled || 0,
      max_pages: job.max_pages || 50,
      current_url: job.current_url || null,
      current_url_index: 1,
      total_urls: job.urls?.length || 1
    };
    recentPages.value = [];
  };

  const stopWatching = () => {
    watchingJob.value = null;
    liveProgress.value = {};
    recentPages.value = [];
  };

  const updateProgress = (data) => {
    liveProgress.value = {
      pages_crawled: data.pages_crawled || 0,
      max_pages: data.max_pages || liveProgress.value.max_pages,
      current_url: data.current_url,
      current_url_index: data.current_url_index,
      total_urls: data.total_urls
    };

    // Update job in list
    const jobIndex = jobs.value.findIndex(j => j.job_id === data.session_id);
    if (jobIndex !== -1) {
      jobs.value[jobIndex].pages_crawled = data.pages_crawled;
      jobs.value[jobIndex].status = data.status || jobs.value[jobIndex].status;
      if (data.documents_created !== undefined) {
        jobs.value[jobIndex].documents_created = data.documents_created;
      }
    }

    // Update watching job
    if (watchingJob.value && watchingJob.value.job_id === data.session_id) {
      watchingJob.value.pages_crawled = data.pages_crawled;
      watchingJob.value.status = data.status || watchingJob.value.status;
      if (data.documents_created !== undefined) {
        watchingJob.value.documents_created = data.documents_created;
      }
    }
  };

  const addRecentPage = (data) => {
    if (data.url) {
      recentPages.value.push(data);
      if (recentPages.value.length > 50) {
        recentPages.value = recentPages.value.slice(-50);
      }
    }
  };

  const handleComplete = (data) => {
    const jobIndex = jobs.value.findIndex(j => j.job_id === data.session_id);
    if (jobIndex !== -1) {
      jobs.value[jobIndex].status = 'completed';
      jobs.value[jobIndex].pages_crawled = data.pages_crawled;
      jobs.value[jobIndex].documents_created = data.documents_created;
      jobs.value[jobIndex].collection_id = data.collection_id;
      jobs.value[jobIndex].skipped_existing = data.skipped_existing || 0;
      jobs.value[jobIndex].skipped_duplicates = data.skipped_duplicates || 0;
    }

    if (watchingJob.value && watchingJob.value.job_id === data.session_id) {
      watchingJob.value.status = 'completed';
      watchingJob.value.pages_crawled = data.pages_crawled;
      watchingJob.value.documents_created = data.documents_created;
      watchingJob.value.collection_id = data.collection_id;
      watchingJob.value.skipped_existing = data.skipped_existing || 0;
      watchingJob.value.skipped_duplicates = data.skipped_duplicates || 0;
    }

    return data;
  };

  const handleError = (data) => {
    const jobIndex = jobs.value.findIndex(j => j.job_id === data.session_id);
    if (jobIndex !== -1) {
      jobs.value[jobIndex].status = 'failed';
      jobs.value[jobIndex].error = data.error;
    }

    if (watchingJob.value && watchingJob.value.job_id === data.session_id) {
      watchingJob.value.status = 'failed';
      watchingJob.value.error = data.error;
    }

    return data;
  };

  const handleStatus = (data) => {
    if (data && watchingJob.value && watchingJob.value.job_id === data.session_id) {
      liveProgress.value = {
        pages_crawled: data.pages_crawled || 0,
        max_pages: data.max_pages || liveProgress.value.max_pages || 50,
        current_url: data.current_url || null,
        current_url_index: data.current_url_index || 1,
        total_urls: data.urls?.length || liveProgress.value.total_urls || 1
      };

      watchingJob.value = {
        ...watchingJob.value,
        pages_crawled: data.pages_crawled || 0,
        documents_created: data.documents_created || 0,
        status: data.status || watchingJob.value.status,
        errors: data.errors || watchingJob.value.errors
      };
    }
  };

  return {
    // State
    jobs,
    loadingJobs,
    watchingJob,
    liveProgress,
    recentPages,

    // Computed
    runningJobs,
    progressPercent,

    // Methods
    loadJobs,
    updateJobsList,
    watchJob,
    stopWatching,
    updateProgress,
    addRecentPage,
    handleComplete,
    handleError,
    handleStatus
  };
}
