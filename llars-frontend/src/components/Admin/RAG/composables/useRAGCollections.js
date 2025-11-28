import { ref, computed } from 'vue';
import axios from 'axios';

/**
 * Composable for RAG Collections management
 * Handles collection state, CRUD operations, and related API calls
 */
export function useRAGCollections() {
  // State
  const collections = ref([]);
  const loadingCollections = ref(false);
  const creatingCollection = ref(false);
  const deletingCollection = ref(false);
  const newCollectionName = ref('');

  // Selected collection state
  const selectedCollection = ref(null);
  const collectionDetailDialog = ref(false);
  const collectionDocuments = ref([]);
  const loadingCollectionDocs = ref(false);

  // Delete dialog state
  const deleteCollDialog = ref(false);
  const collectionToDelete = ref(null);

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

  // Computed
  const collectionOptions = computed(() => {
    const options = ['Alle', ...collections.value.map(c => c.name)];
    return options;
  });

  // API Functions
  const fetchCollections = async () => {
    loadingCollections.value = true;
    try {
      const response = await axios.get('/api/rag/collections');
      collections.value = response.data.collections || [];
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching collections:', error);
      return { success: false, error };
    } finally {
      loadingCollections.value = false;
    }
  };

  const createCollection = async (name = null) => {
    const collectionName = name || newCollectionName.value;
    if (!collectionName) {
      return { success: false, error: 'Collection name is required' };
    }

    creatingCollection.value = true;
    try {
      const response = await axios.post('/api/rag/collections', { name: collectionName });
      if (name === null) {
        newCollectionName.value = '';
      }
      await fetchCollections();
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating collection:', error);
      return { success: false, error };
    } finally {
      creatingCollection.value = false;
    }
  };

  const deleteCollection = async (force = false) => {
    if (!collectionToDelete.value) {
      return { success: false, error: 'No collection selected for deletion' };
    }

    deletingCollection.value = true;
    try {
      const url = `/api/rag/collections/${collectionToDelete.value.id}${force ? '?force=true' : ''}`;
      const response = await axios.delete(url);

      if (response.data.success) {
        deleteCollDialog.value = false;
        collectionToDelete.value = null;
        await fetchCollections();
        return { success: true, data: response.data };
      }
      return { success: false, error: 'Delete operation failed' };
    } catch (error) {
      console.error('Error deleting collection:', error);
      const errorMsg = error.response?.data?.error || 'Fehler beim Löschen der Collection';
      return { success: false, error: errorMsg };
    } finally {
      deletingCollection.value = false;
    }
  };

  const fetchCollectionDocuments = async (collectionId = null) => {
    const targetId = collectionId || selectedCollection.value?.id;
    if (!targetId) {
      return { success: false, error: 'No collection selected' };
    }

    loadingCollectionDocs.value = true;
    try {
      const response = await axios.get(`/api/rag/collections/${targetId}`);

      // Update selectedCollection with detailed info (including chunk_size, chunk_overlap)
      if (response.data.collection) {
        if (selectedCollection.value) {
          selectedCollection.value = {
            ...selectedCollection.value,
            ...response.data.collection
          };
        }
        collectionDocuments.value = response.data.collection.documents || [];
        return { success: true, data: response.data };
      } else {
        collectionDocuments.value = [];
        return { success: true, data: { documents: [] } };
      }
    } catch (error) {
      console.error('Error fetching collection documents:', error);
      collectionDocuments.value = [];
      return { success: false, error };
    } finally {
      loadingCollectionDocs.value = false;
    }
  };

  // UI Helper Functions
  const openCollectionDetail = async (collection) => {
    selectedCollection.value = collection;
    collectionDetailDialog.value = true;
    await fetchCollectionDocuments();
  };

  const confirmDeleteCollection = (collection) => {
    collectionToDelete.value = collection;
    deleteCollDialog.value = true;
  };

  const closeCollectionDetail = () => {
    collectionDetailDialog.value = false;
    selectedCollection.value = null;
    collectionDocuments.value = [];
  };

  const closeDeleteDialog = () => {
    deleteCollDialog.value = false;
    collectionToDelete.value = null;
  };

  return {
    // State
    collections,
    loadingCollections,
    creatingCollection,
    deletingCollection,
    newCollectionName,
    selectedCollection,
    collectionDetailDialog,
    collectionDocuments,
    loadingCollectionDocs,
    deleteCollDialog,
    collectionToDelete,

    // Computed
    collectionOptions,

    // Table headers
    collectionHeaders,
    collectionDocHeaders,

    // API Functions
    fetchCollections,
    createCollection,
    deleteCollection,
    fetchCollectionDocuments,

    // UI Helpers
    openCollectionDetail,
    confirmDeleteCollection,
    closeCollectionDetail,
    closeDeleteDialog
  };
}
