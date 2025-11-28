/**
 * Crawler Form Composable
 *
 * Handles crawl form state, validation, and submission.
 * Extracted from WebCrawlerTool.vue for better maintainability.
 */

import { ref, computed } from 'vue';
import axios from 'axios';

export function useCrawlerForm() {
  // Form data
  const crawlForm = ref({
    urlsText: '',
    collectionName: '',
    description: '',
    maxPages: 50,
    maxDepth: 3,
    collectionMode: 'new',
    existingCollectionId: null
  });

  // Collections for dropdown
  const collections = ref([]);
  const loadingCollections = ref(false);

  // State
  const startingCrawl = ref(false);
  const previewing = ref(false);
  const preview = ref(null);
  const urlError = ref(null);

  // Computed
  const urls = computed(() => {
    return crawlForm.value.urlsText
      .split('\n')
      .map(u => u.trim())
      .filter(u => u.length > 0);
  });

  const hasValidUrl = computed(() => {
    return urls.value.length > 0 && urls.value.every(u =>
      u.startsWith('http://') || u.startsWith('https://')
    );
  });

  const canStartCrawl = computed(() => {
    if (!hasValidUrl.value || startingCrawl.value) return false;

    if (crawlForm.value.collectionMode === 'new') {
      return !!crawlForm.value.collectionName?.trim();
    }

    return !!crawlForm.value.existingCollectionId;
  });

  // Methods
  const validateUrls = () => {
    urlError.value = null;
    if (crawlForm.value.urlsText.trim() && !hasValidUrl.value) {
      urlError.value = 'URLs müssen mit http:// oder https:// beginnen';
    }
  };

  const loadCollections = async () => {
    loadingCollections.value = true;
    try {
      const response = await axios.get('/api/rag/collections');
      if (response.data.success) {
        collections.value = response.data.collections;
        console.log('[Crawler] Loaded', collections.value.length, 'collections');
      }
    } catch (error) {
      console.error('[Crawler] Error loading collections:', error);
      throw error;
    } finally {
      loadingCollections.value = false;
    }
  };

  const previewUrl = async () => {
    if (!urls.value.length) return;

    previewing.value = true;
    preview.value = null;

    try {
      const response = await axios.post('/api/crawler/preview', {
        url: urls.value[0]
      });

      if (response.data.success) {
        preview.value = response.data.preview;
      } else {
        throw new Error(response.data.error || 'Vorschau fehlgeschlagen');
      }
    } finally {
      previewing.value = false;
    }
  };

  const startBackgroundCrawl = async () => {
    if (!canStartCrawl.value) return null;

    startingCrawl.value = true;

    try {
      const requestData = {
        urls: urls.value,
        max_pages_per_site: crawlForm.value.maxPages,
        max_depth: crawlForm.value.maxDepth
      };

      if (crawlForm.value.collectionMode === 'existing') {
        requestData.existing_collection_id = crawlForm.value.existingCollectionId;
      } else {
        requestData.collection_name = crawlForm.value.collectionName;
        requestData.collection_description = crawlForm.value.description;
      }

      const response = await axios.post('/api/crawler/start', requestData);

      if (response.data.success) {
        const newJob = {
          job_id: response.data.job_id,
          status: 'queued',
          urls: response.data.urls,
          collection_name: response.data.collection_name,
          pages_crawled: 0,
          documents_created: 0,
          started_at: new Date().toISOString(),
          max_pages: crawlForm.value.maxPages * urls.value.length
        };

        return newJob;
      } else {
        throw new Error(response.data.error || 'Crawl konnte nicht gestartet werden');
      }
    } finally {
      startingCrawl.value = false;
    }
  };

  const resetForm = () => {
    crawlForm.value.urlsText = '';
    crawlForm.value.collectionName = '';
    crawlForm.value.description = '';
    preview.value = null;
  };

  return {
    // State
    crawlForm,
    collections,
    loadingCollections,
    startingCrawl,
    previewing,
    preview,
    urlError,

    // Computed
    urls,
    hasValidUrl,
    canStartCrawl,

    // Methods
    validateUrls,
    loadCollections,
    previewUrl,
    startBackgroundCrawl,
    resetForm
  };
}
