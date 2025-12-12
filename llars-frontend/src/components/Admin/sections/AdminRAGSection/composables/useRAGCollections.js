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

  // Table headers
  const collectionHeaders = [
    { title: 'Name', key: 'name', sortable: true },
    { title: 'Dokumente', key: 'document_count', sortable: true },
    { title: 'Erstellt', key: 'created_at', sortable: true },
    { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
  ];

  const collectionDocHeaders = [
    { title: 'Dateiname', key: 'filename', sortable: true },
    { title: 'Größe', key: 'file_size', sortable: true },
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
    collectionHeaders,
    collectionDocHeaders,

    // Methods
    fetchCollections,
    createCollection,
    confirmDeleteCollection,
    deleteCollection,
    openCollectionDetail,
    fetchCollectionDocuments
  };
}
