/**
 * Crawler Helpers Composable
 *
 * Utility functions for status display and formatting.
 * Extracted from WebCrawlerTool.vue for better maintainability.
 */

import { ref } from 'vue';

export function useCrawlerHelpers() {
  // Snackbar state
  const snackbar = ref({
    show: false,
    text: '',
    color: 'success'
  });

  // Job table headers
  const jobHeaders = [
    { title: 'Status', key: 'status', width: '140px' },
    { title: 'URLs', key: 'urls', sortable: false },
    { title: 'Seiten', key: 'pages_crawled', width: '90px', align: 'center' },
    { title: 'Dokumente', key: 'documents_created', width: '100px', align: 'center' },
    { title: 'Gestartet', key: 'started_at', width: '160px' },
    { title: '', key: 'actions', width: '80px', sortable: false, align: 'end' }
  ];

  // Status helpers
  const getStatusColor = (status) => {
    const colors = {
      completed: 'success',
      running: 'info',
      queued: 'warning',
      failed: 'error'
    };
    return colors[status] || 'grey';
  };

  const getStatusIcon = (status) => {
    const icons = {
      completed: 'mdi-check-circle',
      running: 'mdi-loading',
      queued: 'mdi-clock-outline',
      failed: 'mdi-alert-circle'
    };
    return icons[status] || 'mdi-clock';
  };

  const getStatusLabel = (status) => {
    const labels = {
      completed: 'Fertig',
      running: 'Läuft',
      queued: 'Wartend',
      failed: 'Fehler'
    };
    return labels[status] || status;
  };

  const getStatusVariant = (status) => {
    const variants = {
      completed: 'success',
      running: 'info',
      queued: 'warning',
      failed: 'danger'
    };
    return variants[status] || 'gray';
  };

  // Formatting helpers
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatNumber = (num) => {
    return num?.toLocaleString('de-DE') || '0';
  };

  // Snackbar helper
  const showSnackbar = (text, color = 'success') => {
    snackbar.value = { show: true, text, color };
  };

  // Navigation helper
  const goToCollection = (collectionId, showSnackbarFn) => {
    // TODO: Navigate to RAG section with collection filter
    if (showSnackbarFn) {
      showSnackbarFn(`Collection ${collectionId} erstellt - siehe RAG Dokumente`, 'info');
    }
  };

  return {
    // State
    snackbar,
    jobHeaders,

    // Status helpers
    getStatusColor,
    getStatusIcon,
    getStatusLabel,
    getStatusVariant,

    // Formatting helpers
    formatDate,
    formatNumber,

    // Snackbar
    showSnackbar,

    // Navigation
    goToCollection
  };
}
