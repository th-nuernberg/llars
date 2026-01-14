/**
 * Admin RAG Actions Composable
 *
 * All API calls and data operations.
 */

import axios from 'axios';
import { logI18n } from '@/utils/logI18n';

export function useAdminRAGActions(state) {
  const {
    loadingDocuments,
    loadingCollections,
    uploading,
    creatingCollection,
    deleting,
    documents,
    collections,
    stats,
    popularDocuments,
    searchQuery,
    filterCollection,
    filterStatus,
    filesToUpload,
    uploadCollectionId,
    uploadResults,
    showCreateCollectionDialog,
    showDeleteDialog,
    documentToDelete,
    newCollection,
    resetNewCollection,
    showSnackbar
  } = state;

  /**
   * Load documents with optional filters.
   */
  async function loadDocuments() {
    loadingDocuments.value = true;
    try {
      const params = new URLSearchParams();
      if (searchQuery.value) params.append('search', searchQuery.value);
      if (filterCollection.value) params.append('collection_id', filterCollection.value);
      if (filterStatus.value) params.append('status', filterStatus.value);
      params.append('per_page', 100);

      const response = await axios.get(`/api/rag/documents?${params}`);
    if (response.data.success) {
      documents.value = response.data.documents;
    }
  } catch (error) {
    logI18n('error', 'logs.admin.ragActions.loadDocumentsFailed', error);
    showSnackbar('Fehler beim Laden der Dokumente', 'error');
  } finally {
      loadingDocuments.value = false;
    }
  }

  /**
   * Load all collections.
   */
  async function loadCollections() {
    loadingCollections.value = true;
    try {
      const response = await axios.get('/api/rag/collections');
    if (response.data.success) {
      collections.value = response.data.collections;
    }
  } catch (error) {
    logI18n('error', 'logs.admin.ragActions.loadCollectionsFailed', error);
    showSnackbar('Fehler beim Laden der Collections', 'error');
  } finally {
      loadingCollections.value = false;
    }
  }

  /**
   * Load overview statistics.
   */
  async function loadStats() {
    try {
      const response = await axios.get('/api/rag/stats/overview');
    if (response.data.success) {
      stats.value = response.data.stats;
    }
  } catch (error) {
    logI18n('error', 'logs.admin.ragActions.loadStatsFailed', error);
  }
  }

  /**
   * Load popular documents.
   */
  async function loadPopularDocuments() {
    try {
      const response = await axios.get('/api/rag/stats/popular-documents?limit=5');
    if (response.data.success) {
      popularDocuments.value = response.data.documents;
    }
  } catch (error) {
    logI18n('error', 'logs.admin.ragActions.loadPopularDocumentsFailed', error);
  }
  }

  /**
   * Upload multiple files.
   */
  async function uploadFiles() {
    if (!filesToUpload.value || filesToUpload.value.length === 0) return;

    uploading.value = true;
    uploadResults.value = null;

    try {
      const formData = new FormData();
      for (const file of filesToUpload.value) {
        formData.append('files', file);
      }
      if (uploadCollectionId.value) {
        formData.append('collection_id', uploadCollectionId.value);
      }

      const response = await axios.post('/api/rag/documents/upload-multiple', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

    if (response.data.success) {
      uploadResults.value = response.data.results;
      showSnackbar(response.data.message, 'success');
        filesToUpload.value = [];
        // Reload data
        loadDocuments();
        loadCollections();
        loadStats();
    }
  } catch (error) {
    logI18n('error', 'logs.admin.ragActions.uploadFilesFailed', error);
    showSnackbar('Fehler beim Hochladen', 'error');
  } finally {
      uploading.value = false;
    }
  }

  /**
   * Create a new collection.
   */
  async function createCollection() {
    if (!newCollection.value.name || !newCollection.value.display_name) return;

    creatingCollection.value = true;
    try {
      const response = await axios.post('/api/rag/collections', newCollection.value);
    if (response.data.success) {
      showSnackbar('Collection erstellt', 'success');
        showCreateCollectionDialog.value = false;
        resetNewCollection();
        loadCollections();
    }
  } catch (error) {
    logI18n('error', 'logs.admin.ragActions.createCollectionFailed', error);
    showSnackbar(error.response?.data?.error || 'Fehler beim Erstellen', 'error');
  } finally {
      creatingCollection.value = false;
    }
  }

  /**
   * Download a document.
   */
  async function downloadDocument(doc) {
    try {
      const response = await axios.get(`/api/rag/documents/${doc.id}/download`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
      link.setAttribute('download', doc.original_filename || doc.filename);
      document.body.appendChild(link);
      link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    logI18n('error', 'logs.admin.ragActions.downloadDocumentFailed', error);
    showSnackbar('Fehler beim Download', 'error');
  }
  }

  /**
   * Delete a document.
   */
  async function deleteDocument() {
    if (!documentToDelete.value) return;

    deleting.value = true;
    try {
      const response = await axios.delete(`/api/rag/documents/${documentToDelete.value.id}`);
      if (response.data.success) {
        showSnackbar('Dokument gelöscht', 'success');
        showDeleteDialog.value = false;
        documentToDelete.value = null;
        loadDocuments();
        loadCollections();
        loadStats();
      }
    } catch (error) {
      logI18n('error', 'logs.admin.ragActions.deleteDocumentFailed', error);
      showSnackbar('Fehler beim Löschen', 'error');
    } finally {
      deleting.value = false;
    }
  }

  /**
   * Load all initial data.
   */
  function loadAllData() {
    loadDocuments();
    loadCollections();
    loadStats();
    loadPopularDocuments();
  }

  return {
    loadDocuments,
    loadCollections,
    loadStats,
    loadPopularDocuments,
    uploadFiles,
    createCollection,
    downloadDocument,
    deleteDocument,
    loadAllData
  };
}
