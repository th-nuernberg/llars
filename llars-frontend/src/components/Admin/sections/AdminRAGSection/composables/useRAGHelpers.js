/**
 * RAG Helpers Composable
 *
 * Utility functions for file handling, formatting, and status display.
 * Extracted from AdminRAGSection.vue for better maintainability.
 */

import axios from 'axios';
import { logI18n } from '@/utils/logI18n';

export function useRAGHelpers() {
  // File size formatting
  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Date formatting
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

  // File type helpers - supports both extensions and mime types
  const mimeToExt = {
    'application/pdf': 'pdf',
    'text/plain': 'txt',
    'text/markdown': 'md',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc'
  };

  const getFileTypeIcon = (type) => {
    const icons = {
      'pdf': 'mdi-file-pdf-box',
      'txt': 'mdi-file-document-outline',
      'md': 'mdi-language-markdown',
      'docx': 'mdi-file-word',
      'doc': 'mdi-file-word'
    };
    const ext = mimeToExt[type] || type;
    return icons[ext] || 'mdi-file';
  };

  const getFileTypeColor = (type) => {
    const colors = {
      'pdf': 'red',
      'txt': 'grey',
      'md': 'blue',
      'docx': 'blue',
      'doc': 'blue'
    };
    const ext = mimeToExt[type] || type;
    return colors[ext] || 'grey';
  };

  const getFileExtension = (filename) => {
    if (!filename) return '';
    const parts = filename.split('.');
    return parts.length > 1 ? parts.pop().toLowerCase() : '';
  };

  // Webcrawl detection (for better iconography)
  const isWebcrawlDocument = (doc) => {
    if (!doc) return false;
    if (doc.source_url) return true;
    const name = doc.filename || '';
    return name.startsWith('webcrawl_') || name.startsWith('crawl_');
  };

  const getDocumentIcon = (doc) => {
    if (isWebcrawlDocument(doc)) return 'mdi-spider-web';
    const ext = doc?.file_type || getFileExtension(doc?.filename);
    return getFileTypeIcon(ext);
  };

  const getDocumentColor = (doc) => {
    if (isWebcrawlDocument(doc)) return 'info';
    const ext = doc?.file_type || getFileExtension(doc?.filename);
    return getFileTypeColor(ext);
  };

  // Status helpers
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

  // Document type detection
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

  // Document URL helper
  const getDocumentPreviewUrl = (doc) => {
    if (!doc || !doc.id) return '';
    return `/api/rag/documents/${doc.id}/download`;
  };

  // Document download
  const downloadDocument = async (doc) => {
    try {
      const response = await axios.get(`/api/rag/documents/${doc.id}/download`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.filename || 'document');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      logI18n('error', 'logs.admin.ragSectionHelpers.downloadDocumentFailed', error);
    }
  };

  // Accepted file types
  const acceptedFileTypes = '.pdf,.txt,.md,.docx,.doc';

  return {
    // Formatting
    formatFileSize,
    formatDate,

    // File type helpers
    getFileTypeIcon,
    getFileTypeColor,
    getFileExtension,
    isWebcrawlDocument,
    getDocumentIcon,
    getDocumentColor,

    // Status helpers
    getStatusColor,
    getStatusIcon,

    // Document type detection
    isPdfDocument,
    isTextDocument,

    // Document helpers
    getDocumentPreviewUrl,
    downloadDocument,

    // Constants
    acceptedFileTypes
  };
}
