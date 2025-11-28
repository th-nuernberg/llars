import { ref, computed } from 'vue';
import axios from 'axios';

/**
 * Composable for RAG Documents management
 * Handles document state, upload, deletion, preview, and related API calls
 */
export function useRAGDocuments() {
  // State
  const documents = ref([]);
  const documentSearch = ref('');
  const collectionFilter = ref(null);
  const loadingDocuments = ref(false);

  // Upload state
  const filesToUpload = ref([]);
  const uploadCollection = ref('default');
  const uploading = ref(false);
  const uploadProgress = ref(0);
  const acceptedFileTypes = '.pdf,.txt,.md,.docx,.doc';

  // Delete dialog state
  const deleteDocDialog = ref(false);
  const documentToDelete = ref(null);
  const deletingDocument = ref(false);

  // Preview state
  const documentPreviewDialog = ref(false);
  const previewDocument = ref(null);
  const previewContent = ref('');
  const loadingPreviewContent = ref(false);

  // Table headers
  const documentHeaders = [
    { title: 'Dateiname', key: 'filename', sortable: true },
    { title: 'Collection', key: 'collection_name', sortable: true },
    { title: 'Größe', key: 'file_size', sortable: true },
    { title: 'Status', key: 'status', sortable: true },
    { title: 'Hochgeladen', key: 'uploaded_at', sortable: true },
    { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
  ];

  // Computed
  const filteredDocuments = computed(() => {
    return documents.value.filter(doc => {
      const matchesSearch = !documentSearch.value ||
        doc.filename.toLowerCase().includes(documentSearch.value.toLowerCase());
      const matchesCollection = !collectionFilter.value ||
        collectionFilter.value === 'Alle' ||
        doc.collection_name === collectionFilter.value;
      return matchesSearch && matchesCollection;
    });
  });

  // API Functions
  const fetchDocuments = async () => {
    loadingDocuments.value = true;
    try {
      const response = await axios.get('/api/rag/documents');
      documents.value = response.data.documents || [];
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching documents:', error);
      return { success: false, error };
    } finally {
      loadingDocuments.value = false;
    }
  };

  const uploadFiles = async (files = null, collection = null) => {
    const filesToProcess = files || filesToUpload.value;
    const targetCollection = collection || uploadCollection.value || 'default';

    if (!filesToProcess || filesToProcess.length === 0) {
      return { success: false, error: 'No files selected' };
    }

    uploading.value = true;
    uploadProgress.value = 0;

    const formData = new FormData();
    for (const file of filesToProcess) {
      formData.append('files', file);
    }
    formData.append('collection', targetCollection);

    try {
      const response = await axios.post('/api/rag/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      });

      if (files === null) {
        filesToUpload.value = [];
      }

      await fetchDocuments();
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error uploading files:', error);
      return { success: false, error };
    } finally {
      uploading.value = false;
    }
  };

  const deleteDocument = async (docId = null) => {
    const targetDoc = docId ? { id: docId } : documentToDelete.value;
    if (!targetDoc) {
      return { success: false, error: 'No document selected for deletion' };
    }

    deletingDocument.value = true;
    try {
      const response = await axios.delete(`/api/rag/documents/${targetDoc.id}`);

      if (docId === null) {
        deleteDocDialog.value = false;
        documentToDelete.value = null;
      }

      await fetchDocuments();
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error deleting document:', error);
      return { success: false, error };
    } finally {
      deletingDocument.value = false;
    }
  };

  const loadTextContent = async (doc) => {
    loadingPreviewContent.value = true;
    try {
      const response = await axios.get(`/api/rag/documents/${doc.id}/content`);
      previewContent.value = response.data.content || 'Inhalt konnte nicht geladen werden.';
      return { success: true, content: previewContent.value };
    } catch (error) {
      console.error('Error loading document content:', error);
      previewContent.value = 'Fehler beim Laden des Inhalts.';
      return { success: false, error };
    } finally {
      loadingPreviewContent.value = false;
    }
  };

  const downloadDocument = async (doc) => {
    try {
      const response = await axios.get(`/api/rag/documents/${doc.id}/download`, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.filename || 'document');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      return { success: true };
    } catch (error) {
      console.error('Error downloading document:', error);
      return { success: false, error };
    }
  };

  // UI Helper Functions
  const handleFileSelect = (files) => {
    filesToUpload.value = files;
  };

  const confirmDeleteDocument = (doc) => {
    documentToDelete.value = doc;
    deleteDocDialog.value = true;
  };

  const openDocumentPreview = async (doc) => {
    previewDocument.value = doc;
    previewContent.value = '';
    documentPreviewDialog.value = true;

    // Load text content if it's a text document
    if (isTextDocument(doc)) {
      await loadTextContent(doc);
    }
  };

  const closeDocumentPreview = () => {
    documentPreviewDialog.value = false;
    previewDocument.value = null;
    previewContent.value = '';
  };

  const closeDeleteDialog = () => {
    deleteDocDialog.value = false;
    documentToDelete.value = null;
  };

  // Helper Functions
  const getFileExtension = (filename) => {
    if (!filename) return '';
    const parts = filename.split('.');
    return parts.length > 1 ? parts.pop().toLowerCase() : '';
  };

  const getFileTypeIcon = (type) => {
    const icons = {
      'pdf': 'mdi-file-pdf-box',
      'txt': 'mdi-file-document-outline',
      'md': 'mdi-language-markdown',
      'docx': 'mdi-file-word',
      'doc': 'mdi-file-word'
    };
    return icons[type] || 'mdi-file';
  };

  const getFileTypeColor = (type) => {
    const colors = {
      'pdf': 'red',
      'txt': 'grey',
      'md': 'blue',
      'docx': 'blue',
      'doc': 'blue'
    };
    return colors[type] || 'grey';
  };

  const getStatusColor = (status) => {
    const colors = {
      'processed': 'success',
      'indexed': 'success',
      'pending': 'warning',
      'processing': 'info',
      'error': 'error'
    };
    return colors[status] || 'grey';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'processed': 'mdi-check-circle',
      'indexed': 'mdi-check-circle',
      'pending': 'mdi-clock-outline',
      'processing': 'mdi-cog-sync',
      'error': 'mdi-alert-circle'
    };
    return icons[status] || 'mdi-help-circle';
  };

  const isPdfDocument = (doc) => {
    if (!doc) return false;
    const ext = doc.file_type || getFileExtension(doc.filename);
    return ext === 'pdf' || doc.mime_type === 'application/pdf';
  };

  const isTextDocument = (doc) => {
    if (!doc) return false;
    const ext = doc.file_type || getFileExtension(doc.filename);
    const textExtensions = ['txt', 'md', 'markdown', 'text'];
    const textMimeTypes = ['text/plain', 'text/markdown'];
    return textExtensions.includes(ext) || textMimeTypes.includes(doc.mime_type);
  };

  const getDocumentPreviewUrl = (doc) => {
    if (!doc || !doc.id) return '';
    return `/api/rag/documents/${doc.id}/download`;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return {
    // State
    documents,
    documentSearch,
    collectionFilter,
    loadingDocuments,
    filesToUpload,
    uploadCollection,
    uploading,
    uploadProgress,
    acceptedFileTypes,
    deleteDocDialog,
    documentToDelete,
    deletingDocument,
    documentPreviewDialog,
    previewDocument,
    previewContent,
    loadingPreviewContent,

    // Computed
    filteredDocuments,

    // Table headers
    documentHeaders,

    // API Functions
    fetchDocuments,
    uploadFiles,
    deleteDocument,
    loadTextContent,
    downloadDocument,

    // UI Helpers
    handleFileSelect,
    confirmDeleteDocument,
    openDocumentPreview,
    closeDocumentPreview,
    closeDeleteDialog,

    // Helper Functions
    getFileExtension,
    getFileTypeIcon,
    getFileTypeColor,
    getStatusColor,
    getStatusIcon,
    isPdfDocument,
    isTextDocument,
    getDocumentPreviewUrl,
    formatFileSize,
    formatDate
  };
}
