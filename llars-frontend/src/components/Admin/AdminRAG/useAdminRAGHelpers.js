/**
 * Admin RAG Helpers Composable
 *
 * UI helper functions and formatters.
 */

export function useAdminRAGHelpers(state) {
  const {
    activeTab,
    showDocumentDialog,
    showDeleteDialog,
    selectedDocument,
    documentToDelete,
    filterCollection
  } = state;

  /**
   * View document details.
   */
  function viewDocument(doc) {
    selectedDocument.value = doc;
    showDocumentDialog.value = true;
  }

  /**
   * View collection's documents.
   */
  function viewCollection(collection, loadDocuments) {
    filterCollection.value = collection.id;
    activeTab.value = 'documents';
    loadDocuments();
  }

  /**
   * Edit collection (placeholder).
   */
  function editCollection(collection) {
    // TODO: Implement edit collection dialog
    console.log('Edit collection:', collection);
  }

  /**
   * Confirm document deletion.
   */
  function confirmDeleteDocument(doc) {
    documentToDelete.value = doc;
    showDeleteDialog.value = true;
  }

  /**
   * Get status color for chips.
   */
  function getStatusColor(status) {
    const colors = {
      'pending': 'warning',
      'processing': 'info',
      'indexed': 'success',
      'error': 'error'
    };
    return colors[status] || 'grey';
  }

  /**
   * Format date for display.
   */
  function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('de-DE');
  }

  return {
    viewDocument,
    viewCollection,
    editCollection,
    confirmDeleteDocument,
    getStatusColor,
    formatDate
  };
}
