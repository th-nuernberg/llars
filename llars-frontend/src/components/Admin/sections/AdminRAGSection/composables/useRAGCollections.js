/**
 * RAG Collections Composable
 *
 * Handles collection listing, creation, deletion, and detail view.
 * Extracted from AdminRAGSection.vue for better maintainability.
 */

import { ref } from 'vue';
import axios from 'axios';

export function useRAGCollections() {
  // State
  const collections = ref([]);
  const loadingCollections = ref(false);
  const newCollectionName = ref('');
  const creatingCollection = ref(false);

  // Delete
  const deleteCollDialog = ref(false);
  const collectionToDelete = ref(null);
  const deletingCollection = ref(false);

  // Detail Dialog
  const collectionDetailDialog = ref(false);
  const selectedCollection = ref(null);
  const collectionDocuments = ref([]);
  const loadingCollectionDocs = ref(false);
  const reindexingCollection = ref(false);

  // Table headers
  const collectionHeaders = [
    { title: 'Name', key: 'name', sortable: true },
    { title: 'Erstellt von', key: 'created_by', sortable: true },
    { title: 'Dokumente', key: 'document_count', sortable: true },
    { title: 'Erstellt', key: 'created_at', sortable: true },
    { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
  ];

  const collectionDocHeaders = [
    { title: 'Dateiname', key: 'filename', sortable: true },
    { title: 'Größe', key: 'file_size_bytes', sortable: true },
    { title: 'Status', key: 'status', sortable: true },
    { title: 'Chunks', key: 'chunk_count', sortable: true },
    { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
  ];

  // Methods
  const fetchCollections = async () => {
    loadingCollections.value = true;
    try {
      const response = await axios.get('/api/rag/collections');
      collections.value = response.data.collections || [];
    } catch (error) {
      console.error('Error fetching collections:', error);
    }
    loadingCollections.value = false;
  };

  const createCollection = async (onSuccess) => {
    if (!newCollectionName.value) return;

    creatingCollection.value = true;
    try {
      const displayName = newCollectionName.value.trim();
      const internalName = displayName
        .toLowerCase()
        .replace(/\s+/g, '_')
        .replace(/[^a-z0-9_-]/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_+|_+$/g, '');

      await axios.post('/api/rag/collections', {
        name: internalName || `collection_${Date.now()}`,
        display_name: displayName
      });
      newCollectionName.value = '';
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Error creating collection:', error);
    }
    creatingCollection.value = false;
  };

  const confirmDeleteCollection = (coll) => {
    collectionToDelete.value = coll;
    deleteCollDialog.value = true;
  };

  const deleteCollection = async (force = false, onSuccess) => {
    if (!collectionToDelete.value) return;

    deletingCollection.value = true;
    try {
      const url = `/api/rag/collections/${collectionToDelete.value.id}${force ? '?force=true' : ''}`;
      const response = await axios.delete(url);
      if (response.data.success) {
        deleteCollDialog.value = false;
        collectionToDelete.value = null;
        if (onSuccess) onSuccess();
      }
    } catch (error) {
      console.error('Error deleting collection:', error);
      const errorMsg = error.response?.data?.error || 'Fehler beim Löschen der Collection';
      alert(errorMsg);
    }
    deletingCollection.value = false;
  };

  const openCollectionDetail = async (collection) => {
    selectedCollection.value = collection;
    collectionDetailDialog.value = true;
    await fetchCollectionDocuments();
  };

  const fetchCollectionDocuments = async () => {
    if (!selectedCollection.value) return;

    loadingCollectionDocs.value = true;
    try {
      const response = await axios.get(`/api/rag/collections/${selectedCollection.value.id}`);
      if (response.data.collection) {
        selectedCollection.value = {
          ...selectedCollection.value,
          ...response.data.collection
        };
        collectionDocuments.value = response.data.collection.documents || [];
      } else {
        collectionDocuments.value = [];
      }
    } catch (error) {
      console.error('Error fetching collection documents:', error);
      collectionDocuments.value = [];
    }
    loadingCollectionDocs.value = false;
  };

  const applyDocumentProgress = (data) => {
    if (!data?.document_id || !selectedCollection.value) return false;
    const docs = collectionDocuments.value || [];
    const index = docs.findIndex(doc => doc.id === data.document_id);
    if (index === -1) return false;

    const next = { ...docs[index] };
    if (data.status) next.status = data.status;
    if (data.progress !== undefined) next.embedding_progress = data.progress;
    if (data.step) next.embedding_step = data.step;

    docs.splice(index, 1, next);
    collectionDocuments.value = [...docs];
    return true;
  };

  const applyDocumentProcessed = (data) => {
    const doc = data?.document;
    if (!doc || !selectedCollection.value) return false;

    const docs = collectionDocuments.value || [];
    const index = docs.findIndex(item => item.id === doc.id);
    const nextDoc = {
      ...doc,
      status: data.status || doc.status
    };

    if (index >= 0) {
      docs.splice(index, 1, { ...docs[index], ...nextDoc });
    } else if (doc.collection_id === selectedCollection.value.id || data.collection_id === selectedCollection.value.id) {
      docs.unshift(nextDoc);
    } else {
      return false;
    }

    collectionDocuments.value = [...docs];
    return true;
  };

  const reindexCollection = async (options = {}) => {
    if (!selectedCollection.value) return;

    reindexingCollection.value = true;
    try {
      await axios.post(
        `/api/rag/collections/${selectedCollection.value.id}/reindex`,
        options
      );
      await fetchCollectionDocuments();
    } catch (error) {
      console.error('Error reindexing collection:', error);
      const errorMsg = error.response?.data?.error || 'Reindexierung fehlgeschlagen';
      alert(errorMsg);
    }
    reindexingCollection.value = false;
  };

  return {
    // State
    collections,
    loadingCollections,
    newCollectionName,
    creatingCollection,
    deleteCollDialog,
    collectionToDelete,
    deletingCollection,
    collectionDetailDialog,
    selectedCollection,
    collectionDocuments,
    loadingCollectionDocs,
    reindexingCollection,
    collectionHeaders,
    collectionDocHeaders,

    // Methods
    fetchCollections,
    createCollection,
    confirmDeleteCollection,
    deleteCollection,
    openCollectionDetail,
    fetchCollectionDocuments,
    applyDocumentProgress,
    applyDocumentProcessed,
    reindexCollection
  };
}
