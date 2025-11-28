/**
 * Admin RAG State Composable
 *
 * Manages all state for the RAG admin panel.
 */

import { ref, computed } from 'vue';

export function useAdminRAGState() {
  // Loading states
  const loadingDocuments = ref(false);
  const loadingCollections = ref(false);
  const uploading = ref(false);
  const creatingCollection = ref(false);
  const deleting = ref(false);

  // Data
  const documents = ref([]);
  const collections = ref([]);
  const stats = ref({});
  const popularDocuments = ref([]);

  // Filters
  const searchQuery = ref('');
  const filterCollection = ref(null);
  const filterStatus = ref(null);
  const statusOptions = ['pending', 'processing', 'indexed', 'error'];

  // Upload
  const filesToUpload = ref([]);
  const uploadCollectionId = ref(null);
  const uploadResults = ref(null);

  // Dialogs
  const activeTab = ref('documents');
  const showDocumentDialog = ref(false);
  const showCreateCollectionDialog = ref(false);
  const showDeleteDialog = ref(false);
  const selectedDocument = ref(null);
  const documentToDelete = ref(null);

  // New collection form
  const newCollection = ref({
    name: '',
    display_name: '',
    description: '',
    icon: ''
  });

  // Snackbar
  const snackbar = ref({
    show: false,
    message: '',
    color: 'success'
  });

  // Computed
  const collectionsForFilter = computed(() => {
    return [{ id: null, display_name: 'Alle' }, ...collections.value];
  });

  // Table headers
  const documentHeaders = [
    { title: 'Titel', key: 'title', sortable: true },
    { title: 'Dateiname', key: 'filename', sortable: true },
    { title: 'Größe', key: 'file_size_mb', sortable: true },
    { title: 'Status', key: 'status', sortable: true },
    { title: 'Collection', key: 'collection_name', sortable: true },
    { title: 'Hochgeladen', key: 'uploaded_at', sortable: true },
    { title: 'Aktionen', key: 'actions', sortable: false, width: '150px' }
  ];

  // File validation rules
  const fileRules = [
    v => !v || v.every(f => f.size <= 50 * 1024 * 1024) || 'Maximale Dateigröße ist 50 MB'
  ];

  /**
   * Reset new collection form.
   */
  const resetNewCollection = () => {
    newCollection.value = { name: '', display_name: '', description: '', icon: '' };
  };

  /**
   * Show snackbar notification.
   */
  const showSnackbar = (message, color = 'success') => {
    snackbar.value = { show: true, message, color };
  };

  return {
    // Loading states
    loadingDocuments,
    loadingCollections,
    uploading,
    creatingCollection,
    deleting,

    // Data
    documents,
    collections,
    stats,
    popularDocuments,

    // Filters
    searchQuery,
    filterCollection,
    filterStatus,
    statusOptions,

    // Upload
    filesToUpload,
    uploadCollectionId,
    uploadResults,

    // Dialogs
    activeTab,
    showDocumentDialog,
    showCreateCollectionDialog,
    showDeleteDialog,
    selectedDocument,
    documentToDelete,

    // Form
    newCollection,

    // Snackbar
    snackbar,

    // Computed
    collectionsForFilter,

    // Constants
    documentHeaders,
    fileRules,

    // Methods
    resetNewCollection,
    showSnackbar
  };
}
