/**
 * RAG Documents Composable
 *
 * Handles document listing, upload, and deletion.
 * Extracted from AdminRAGSection.vue for better maintainability.
 */

import { ref, computed } from 'vue';
import axios from 'axios';

export function useRAGDocuments(collectionsRef) {
  // State
  const documents = ref([]);
  const documentSearch = ref('');
  const collectionFilter = ref(null);
  const loadingDocuments = ref(false);

  // Upload
  const filesToUpload = ref([]);
  const uploadCollection = ref(null);
  const uploading = ref(false);
  const uploadProgress = ref(0);

  // Delete
  const deleteDocDialog = ref(false);
  const documentToDelete = ref(null);
  const deletingDocument = ref(false);

  // Table headers
  const documentHeaders = [
    { title: 'Dateiname', key: 'title', sortable: true },
    { title: 'Collection', key: 'collection_name', sortable: true },
    { title: 'Größe', key: 'file_size_bytes', sortable: true },
    { title: 'Status', key: 'status', sortable: true },
    { title: 'Hochgeladen', key: 'uploaded_at', sortable: true },
    { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
  ];

  // Computed - use display_name to match API response (doc.collection_name = display_name)
  const collectionOptions = computed(() => {
    const options = ['Alle', ...collectionsRef.value.map(c => c.display_name || c.name)];
    return options;
  });

  // Collection options for upload (with IDs)
  const uploadCollectionOptions = computed(() => {
    return collectionsRef.value.map(c => ({
      title: c.display_name || c.name,
      value: c.id
    }));
  });

  const filteredDocuments = computed(() => {
    return documents.value.filter(doc => {
      const matchesSearch = doc.filename.toLowerCase().includes(documentSearch.value.toLowerCase());
      const matchesCollection = !collectionFilter.value || collectionFilter.value === 'Alle' ||
        doc.collection_name === collectionFilter.value;
      return matchesSearch && matchesCollection;
    });
  });

  // Methods
  const fetchDocuments = async () => {
    loadingDocuments.value = true;
    try {
      const response = await axios.get('/api/rag/documents');
      documents.value = response.data.documents || [];
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
    loadingDocuments.value = false;
  };

  const handleFileSelect = (files) => {
    filesToUpload.value = files;
  };

  const uploadFiles = async (onSuccess) => {
    if (!filesToUpload.value || filesToUpload.value.length === 0) return;

    uploading.value = true;
    uploadProgress.value = 0;

    const formData = new FormData();
    for (const file of filesToUpload.value) {
      formData.append('files', file);
    }
    if (uploadCollection.value) {
      formData.append('collection_id', uploadCollection.value);
    }

    try {
      await axios.post('/api/rag/documents/upload-multiple', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      });

      filesToUpload.value = [];
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Error uploading files:', error);
    }

    uploading.value = false;
  };

  const confirmDeleteDocument = (doc) => {
    documentToDelete.value = doc;
    deleteDocDialog.value = true;
  };

  const deleteDocument = async (onSuccess) => {
    if (!documentToDelete.value) return;

    deletingDocument.value = true;
    try {
      await axios.delete(`/api/rag/documents/${documentToDelete.value.id}`);
      deleteDocDialog.value = false;
      documentToDelete.value = null;
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Error deleting document:', error);
    }
    deletingDocument.value = false;
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
    deleteDocDialog,
    documentToDelete,
    deletingDocument,
    documentHeaders,

    // Computed
    collectionOptions,
    uploadCollectionOptions,
    filteredDocuments,

    // Methods
    fetchDocuments,
    handleFileSelect,
    uploadFiles,
    confirmDeleteDocument,
    deleteDocument
  };
}
