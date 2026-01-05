/**
 * Chatbot Crawler Composable
 *
 * Handles web crawler functionality with WebSocket for live updates.
 * Extracted from ChatbotEditor.vue for better maintainability.
 */

import { ref, computed, onUnmounted } from 'vue';
import axios from 'axios';
import { io } from 'socket.io-client';

const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true';
const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling'];

export function useChatbotCrawler() {
  // Crawler form state
  const crawlerUrls = ref('');
  const crawlerMaxPages = ref(30);
  const crawlerMaxDepth = ref(2);

  // Crawler status
  const crawling = ref(false);
  const crawlStatus = ref(null);
  const crawlJobId = ref(null);
  const crawlProgress = ref(null);
  const crawledPages = ref([]);

  // WebSocket
  let crawlerSocket = null;

  // Computed
  const parsedCrawlerUrls = computed(() => {
    return crawlerUrls.value
      .split('\n')
      .map(u => u.trim())
      .filter(u => u.length > 0);
  });

  const hasValidCrawlerUrls = computed(() => {
    return parsedCrawlerUrls.value.length > 0 && parsedCrawlerUrls.value.every(u =>
      u.startsWith('http://') || u.startsWith('https://')
    );
  });

  // Initialize WebSocket
  function initCrawlerSocket(callbacks = {}) {
    if (crawlerSocket) return;

    crawlerSocket = io('/', {
      path: '/socket.io',
      transports: socketioTransports,
      upgrade: socketioEnableWebsocket
    });

    crawlerSocket.on('connect', () => {
      console.log('[Crawler Socket] Connected');
    });

    crawlerSocket.on('crawler:joined', (data) => {
      console.log('[Crawler Socket] Joined session:', data);
    });

    crawlerSocket.on('crawler:progress', (data) => {
      console.log('[Crawler Socket] Progress:', data);
      crawlProgress.value = data;
      crawlStatus.value = {
        message: `Crawle ${data.current_url_index}/${data.total_urls} URLs - ${data.pages_crawled} Seiten...`,
        current_url: data.current_url,
        pages_crawled: data.pages_crawled,
        max_pages: data.max_pages
      };
    });

    crawlerSocket.on('crawler:page_crawled', (data) => {
      console.log('[Crawler Socket] Page crawled:', data);
      crawledPages.value.push(data.url);
      // Keep only last 10 pages for display
      if (crawledPages.value.length > 10) {
        crawledPages.value.shift();
      }
    });

    crawlerSocket.on('crawler:complete', (data) => {
      console.log('[Crawler Socket] Complete:', data);
      crawling.value = false;
      crawlStatus.value = {
        success: true,
        message: `Crawl abgeschlossen!`,
        pages_crawled: data.pages_crawled,
        documents_created: data.documents_created,
        collection_id: data.collection_id
      };

      // Callback to parent with crawl result
      if (callbacks.onComplete) {
        callbacks.onComplete({
          ...data
        });
      }

      // Leave the room
      if (crawlJobId.value) {
        crawlerSocket.emit('crawler:leave_session', { session_id: crawlJobId.value });
      }
    });

    crawlerSocket.on('crawler:error', (data) => {
      console.error('[Crawler Socket] Error:', data);
      crawling.value = false;
      crawlStatus.value = {
        error: true,
        message: data.error || 'Crawl fehlgeschlagen'
      };
    });
  }

  // Cleanup WebSocket
  function cleanupCrawlerSocket() {
    if (crawlerSocket) {
      if (crawlJobId.value) {
        crawlerSocket.emit('crawler:leave_session', { session_id: crawlJobId.value });
      }
      crawlerSocket.disconnect();
      crawlerSocket = null;
    }
  }

  // Start crawl
  async function startCrawl(chatbotName, callbacks = {}) {
    if (!hasValidCrawlerUrls.value) return;

    crawling.value = true;
    crawlStatus.value = { message: 'Crawl wird gestartet...' };
    crawledPages.value = [];
    crawlProgress.value = null;

    // Initialize WebSocket
    initCrawlerSocket(callbacks);

    try {
      const response = await axios.post('/api/crawler/start', {
        urls: parsedCrawlerUrls.value,
        collection_name: `${chatbotName} - Web`,
        collection_description: `Automatisch gecrawlt für Chatbot '${chatbotName}'`,
        max_pages_per_site: crawlerMaxPages.value,
        max_depth: crawlerMaxDepth.value
      });

      if (response.data.success && response.data.job_id) {
        crawlJobId.value = response.data.job_id;

        // Join the WebSocket room for this crawl session
        crawlerSocket.emit('crawler:join_session', { session_id: response.data.job_id });

        crawlStatus.value = {
          message: 'Crawl gestartet, warte auf Updates...',
          job_id: response.data.job_id
        };

        return { success: true, jobId: response.data.job_id };
      } else {
        crawling.value = false;
        crawlStatus.value = {
          error: true,
          message: response.data.error || 'Crawl konnte nicht gestartet werden'
        };
        return { success: false, error: crawlStatus.value.message };
      }
    } catch (error) {
      console.error('Crawl error:', error);
      crawling.value = false;
      crawlStatus.value = {
        error: true,
        message: error.response?.data?.error || 'Fehler beim Starten des Crawls'
      };
      return { success: false, error: crawlStatus.value.message };
    }
  }

  // Reset crawler state
  function resetCrawler() {
    crawlerUrls.value = '';
    crawlStatus.value = null;
    crawledPages.value = [];
    crawlProgress.value = null;
    crawlJobId.value = null;
  }

  // Cleanup on unmount
  onUnmounted(() => {
    cleanupCrawlerSocket();
  });

  return {
    // State
    crawlerUrls,
    crawlerMaxPages,
    crawlerMaxDepth,
    crawling,
    crawlStatus,
    crawlProgress,
    crawledPages,

    // Computed
    parsedCrawlerUrls,
    hasValidCrawlerUrls,

    // Methods
    initCrawlerSocket,
    cleanupCrawlerSocket,
    startCrawl,
    resetCrawler
  };
}
