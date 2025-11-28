/**
 * RAG Stats Composable
 *
 * Handles RAG statistics, embedding info, and processing queue.
 * Extracted from AdminRAGSection.vue for better maintainability.
 */

import { ref, computed } from 'vue';
import axios from 'axios';

export function useRAGStats() {
  // State
  const stats = ref({
    total_documents: 0,
    processed: 0,
    total_collections: 0,
    total_size: 0
  });

  // Embedding Info
  const embeddingInfo = ref({
    model_name: 'Loading...',
    model_type: '-',
    dimensions: 0,
    is_primary: false,
    primary_model: '-',
    fallback_model: '-',
    litellm_configured: false,
    litellm_base_url: '-',
    vectorstore_dir: '-',
    collection_name: '-'
  });
  const loadingEmbeddingInfo = ref(false);

  // Processing Queue
  const processingQueue = ref({
    pending: 0,
    processing: 0,
    indexed: 0,
    error: 0,
    total: 0
  });
  const loadingQueue = ref(false);

  // Computed
  const processingProgress = computed(() => {
    if (processingQueue.value.total === 0) return 0;
    return (processingQueue.value.indexed / processingQueue.value.total) * 100;
  });

  // Methods
  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/rag/stats');
      const data = response.data;
      if (data.stats) {
        stats.value = {
          total_documents: data.stats.documents?.total || 0,
          processed: data.stats.documents?.by_status?.processed || data.stats.documents?.total || 0,
          total_collections: data.stats.collections?.total || 0,
          total_size: data.stats.documents?.total_size_bytes || 0
        };
      } else {
        stats.value = data;
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchEmbeddingInfo = async () => {
    loadingEmbeddingInfo.value = true;
    try {
      const response = await axios.get('/api/rag/embedding-info');
      if (response.data.success && response.data.embedding) {
        embeddingInfo.value = response.data.embedding;
      }
    } catch (error) {
      console.error('Error fetching embedding info:', error);
      embeddingInfo.value = {
        model_name: 'Error loading',
        model_type: 'error',
        dimensions: 0,
        is_primary: false,
        primary_model: '-',
        fallback_model: '-',
        litellm_configured: false,
        litellm_base_url: '-',
        vectorstore_dir: '-',
        collection_name: '-'
      };
    }
    loadingEmbeddingInfo.value = false;
  };

  const fetchProcessingQueue = async () => {
    loadingQueue.value = true;
    try {
      const response = await axios.get('/api/rag/stats');
      const data = response.data;
      if (data.stats?.documents?.by_status) {
        const byStatus = data.stats.documents.by_status;
        processingQueue.value = {
          pending: byStatus.pending || 0,
          processing: byStatus.processing || 0,
          indexed: byStatus.indexed || 0,
          error: byStatus.error || 0,
          total: data.stats.documents?.total || 0
        };
      }
    } catch (error) {
      console.error('Error fetching processing queue:', error);
    }
    loadingQueue.value = false;
  };

  const updateQueueFromWebSocket = (data) => {
    if (data.queue) {
      const byStatus = {
        pending: 0,
        processing: 0,
        indexed: 0,
        error: 0
      };

      data.queue.forEach(item => {
        if (item.status === 'queued') byStatus.pending++;
        else if (item.status === 'processing') byStatus.processing++;
        else if (item.status === 'completed') byStatus.indexed++;
        else if (item.status === 'failed') byStatus.error++;
      });

      processingQueue.value = {
        pending: byStatus.pending,
        processing: byStatus.processing,
        indexed: byStatus.indexed,
        error: byStatus.error,
        total: data.queue.length
      };

      console.log('[RAG] Queue-Update erhalten:', processingQueue.value);
    }
  };

  const handleDocumentProgress = (data) => {
    console.log('[RAG] Dokument-Progress:', data.filename, data.progress + '%', data.step);

    if (data.status === 'processing') {
      if (processingQueue.value.pending > 0) {
        processingQueue.value.pending--;
        processingQueue.value.processing++;
      }
    } else if (data.status === 'indexed') {
      if (processingQueue.value.processing > 0) {
        processingQueue.value.processing--;
        processingQueue.value.indexed++;
      }
      fetchStats();
    } else if (data.status === 'failed') {
      if (processingQueue.value.processing > 0) {
        processingQueue.value.processing--;
        processingQueue.value.error++;
      }
      fetchStats();
    }
  };

  return {
    // State
    stats,
    embeddingInfo,
    loadingEmbeddingInfo,
    processingQueue,
    loadingQueue,

    // Computed
    processingProgress,

    // Methods
    fetchStats,
    fetchEmbeddingInfo,
    fetchProcessingQueue,
    updateQueueFromWebSocket,
    handleDocumentProgress
  };
}
