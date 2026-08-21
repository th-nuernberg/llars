/**
 * useRAGDocuments Composable Tests
 *
 * Tests for RAG document management (state, API calls, helpers).
 * Test IDs: RAG_DOC_001 - RAG_DOC_055
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock logI18n
vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

import { useRAGDocuments } from '@/components/Admin/RAG/composables/useRAGDocuments'

describe('useRAGDocuments', () => {
  let rag

  beforeEach(() => {
    vi.clearAllMocks()
    rag = useRAGDocuments()
  })

  // ==================== Initial State Tests ====================

  describe('initial state', () => {
    it('RAG_DOC_001: starts with empty documents', () => {
      expect(rag.documents.value).toEqual([])
    })

    it('RAG_DOC_002: starts with empty search', () => {
      expect(rag.documentSearch.value).toBe('')
    })

    it('RAG_DOC_003: starts with null collection filter', () => {
      expect(rag.collectionFilter.value).toBeNull()
    })

    it('RAG_DOC_004: starts not loading', () => {
      expect(rag.loadingDocuments.value).toBe(false)
    })

    it('RAG_DOC_005: starts with empty upload files', () => {
      expect(rag.filesToUpload.value).toEqual([])
    })

    it('RAG_DOC_006: starts with default upload collection', () => {
      expect(rag.uploadCollection.value).toBe('default')
    })

    it('RAG_DOC_007: has correct accepted file types', () => {
      expect(rag.acceptedFileTypes).toBe('.pdf,.txt,.md,.docx,.doc')
    })

    it('RAG_DOC_008: has correct document headers', () => {
      expect(rag.documentHeaders).toHaveLength(6)
      expect(rag.documentHeaders[0].key).toBe('filename')
    })
  })

  // ==================== filteredDocuments Tests ====================

  describe('filteredDocuments', () => {
    it('RAG_DOC_009: returns all documents when no filter', () => {
      rag.documents.value = [
        { filename: 'test.pdf', collection_name: 'A' },
        { filename: 'doc.txt', collection_name: 'B' }
      ]
      expect(rag.filteredDocuments.value).toHaveLength(2)
    })

    it('RAG_DOC_010: filters by search term', () => {
      rag.documents.value = [
        { filename: 'report.pdf', collection_name: 'A' },
        { filename: 'notes.txt', collection_name: 'A' }
      ]
      rag.documentSearch.value = 'report'
      expect(rag.filteredDocuments.value).toHaveLength(1)
      expect(rag.filteredDocuments.value[0].filename).toBe('report.pdf')
    })

    it('RAG_DOC_011: search is case-insensitive', () => {
      rag.documents.value = [{ filename: 'Report.PDF', collection_name: 'A' }]
      rag.documentSearch.value = 'report'
      expect(rag.filteredDocuments.value).toHaveLength(1)
    })

    it('RAG_DOC_012: filters by collection', () => {
      rag.documents.value = [
        { filename: 'a.pdf', collection_name: 'Collection A' },
        { filename: 'b.pdf', collection_name: 'Collection B' }
      ]
      rag.collectionFilter.value = 'Collection A'
      expect(rag.filteredDocuments.value).toHaveLength(1)
    })

    it('RAG_DOC_013: "Alle" collection filter shows all', () => {
      rag.documents.value = [
        { filename: 'a.pdf', collection_name: 'A' },
        { filename: 'b.pdf', collection_name: 'B' }
      ]
      rag.collectionFilter.value = 'Alle'
      expect(rag.filteredDocuments.value).toHaveLength(2)
    })

    it('RAG_DOC_014: combines search and collection filter', () => {
      rag.documents.value = [
        { filename: 'report.pdf', collection_name: 'A' },
        { filename: 'report.txt', collection_name: 'B' },
        { filename: 'notes.txt', collection_name: 'A' }
      ]
      rag.documentSearch.value = 'report'
      rag.collectionFilter.value = 'A'
      expect(rag.filteredDocuments.value).toHaveLength(1)
    })
  })

  // ==================== fetchDocuments Tests ====================

  describe('fetchDocuments', () => {
    it('RAG_DOC_015: fetches documents from API', async () => {
      axios.get.mockResolvedValue({
        data: { documents: [{ id: 1, filename: 'test.pdf' }] }
      })

      const result = await rag.fetchDocuments()
      expect(axios.get).toHaveBeenCalledWith('/api/rag/documents')
      expect(result.success).toBe(true)
      expect(rag.documents.value).toHaveLength(1)
    })

    it('RAG_DOC_016: sets loading state during fetch', async () => {
      let loadingDuringFetch = null
      axios.get.mockImplementation(() => {
        loadingDuringFetch = rag.loadingDocuments.value
        return Promise.resolve({ data: { documents: [] } })
      })

      await rag.fetchDocuments()
      expect(loadingDuringFetch).toBe(true)
      expect(rag.loadingDocuments.value).toBe(false)
    })

    it('RAG_DOC_017: handles fetch error', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))
      const result = await rag.fetchDocuments()
      expect(result.success).toBe(false)
      expect(rag.loadingDocuments.value).toBe(false)
    })

    it('RAG_DOC_018: defaults to empty array if documents missing', async () => {
      axios.get.mockResolvedValue({ data: {} })
      await rag.fetchDocuments()
      expect(rag.documents.value).toEqual([])
    })
  })

  // ==================== uploadFiles Tests ====================

  describe('uploadFiles', () => {
    it('RAG_DOC_019: returns error when no files selected', async () => {
      const result = await rag.uploadFiles()
      expect(result.success).toBe(false)
      expect(result.error).toBe('No files selected')
    })

    it('RAG_DOC_020: uploads files via API', async () => {
      axios.post.mockResolvedValue({ data: { uploaded: 1 } })
      axios.get.mockResolvedValue({ data: { documents: [] } })

      const mockFiles = [new File(['content'], 'test.pdf')]
      const result = await rag.uploadFiles(mockFiles, 'my-collection')

      expect(axios.post).toHaveBeenCalled()
      expect(result.success).toBe(true)
    })

    it('RAG_DOC_021: sets uploading state', async () => {
      let uploadingDuring = null
      axios.post.mockImplementation(() => {
        uploadingDuring = rag.uploading.value
        return Promise.resolve({ data: {} })
      })
      axios.get.mockResolvedValue({ data: { documents: [] } })

      await rag.uploadFiles([new File([''], 'f.pdf')])
      expect(uploadingDuring).toBe(true)
      expect(rag.uploading.value).toBe(false)
    })

    it('RAG_DOC_022: handles upload error', async () => {
      axios.post.mockRejectedValue(new Error('Upload failed'))
      const result = await rag.uploadFiles([new File([''], 'f.pdf')])
      expect(result.success).toBe(false)
      expect(rag.uploading.value).toBe(false)
    })

    it('RAG_DOC_023: clears filesToUpload after successful upload when using internal files', async () => {
      rag.filesToUpload.value = [new File([''], 'test.pdf')]
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { documents: [] } })

      await rag.uploadFiles()
      expect(rag.filesToUpload.value).toEqual([])
    })
  })

  // ==================== deleteDocument Tests ====================

  describe('deleteDocument', () => {
    it('RAG_DOC_024: returns error when no document selected', async () => {
      const result = await rag.deleteDocument()
      expect(result.success).toBe(false)
    })

    it('RAG_DOC_025: deletes document by ID', async () => {
      axios.delete.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { documents: [] } })

      const result = await rag.deleteDocument(42)
      expect(axios.delete).toHaveBeenCalledWith('/api/rag/documents/42')
      expect(result.success).toBe(true)
    })

    it('RAG_DOC_026: deletes document from dialog state', async () => {
      rag.documentToDelete.value = { id: 7 }
      rag.deleteDocDialog.value = true
      axios.delete.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { documents: [] } })

      await rag.deleteDocument()
      expect(axios.delete).toHaveBeenCalledWith('/api/rag/documents/7')
      expect(rag.deleteDocDialog.value).toBe(false)
      expect(rag.documentToDelete.value).toBeNull()
    })

    it('RAG_DOC_027: handles delete error', async () => {
      axios.delete.mockRejectedValue(new Error('Delete failed'))
      const result = await rag.deleteDocument(1)
      expect(result.success).toBe(false)
      expect(rag.deletingDocument.value).toBe(false)
    })
  })

  // ==================== loadTextContent Tests ====================

  describe('loadTextContent', () => {
    it('RAG_DOC_028: loads content from API', async () => {
      axios.get.mockResolvedValue({ data: { content: 'Hello World' } })
      const result = await rag.loadTextContent({ id: 5 })
      expect(axios.get).toHaveBeenCalledWith('/api/rag/documents/5/content')
      expect(result.success).toBe(true)
      expect(result.content).toBe('Hello World')
      expect(rag.previewContent.value).toBe('Hello World')
    })

    it('RAG_DOC_029: handles missing content', async () => {
      axios.get.mockResolvedValue({ data: {} })
      const result = await rag.loadTextContent({ id: 5 })
      expect(rag.previewContent.value).toBe('Inhalt konnte nicht geladen werden.')
    })

    it('RAG_DOC_030: handles load error', async () => {
      axios.get.mockRejectedValue(new Error('Failed'))
      const result = await rag.loadTextContent({ id: 5 })
      expect(result.success).toBe(false)
      expect(rag.previewContent.value).toBe('Fehler beim Laden des Inhalts.')
    })
  })

  // ==================== UI Helper Tests ====================

  describe('UI helpers', () => {
    it('RAG_DOC_031: handleFileSelect sets files', () => {
      const files = [new File([''], 'a.pdf')]
      rag.handleFileSelect(files)
      expect(rag.filesToUpload.value).toHaveLength(1)
      expect(rag.filesToUpload.value[0].name).toBe('a.pdf')
    })

    it('RAG_DOC_032: confirmDeleteDocument opens dialog', () => {
      const doc = { id: 3, filename: 'test.pdf' }
      rag.confirmDeleteDocument(doc)
      expect(rag.deleteDocDialog.value).toBe(true)
      expect(rag.documentToDelete.value).toEqual(doc)
    })

    it('RAG_DOC_033: closeDeleteDialog resets state', () => {
      rag.deleteDocDialog.value = true
      rag.documentToDelete.value = { id: 1 }
      rag.closeDeleteDialog()
      expect(rag.deleteDocDialog.value).toBe(false)
      expect(rag.documentToDelete.value).toBeNull()
    })

    it('RAG_DOC_034: closeDocumentPreview resets state', () => {
      rag.documentPreviewDialog.value = true
      rag.previewDocument.value = { id: 1 }
      rag.previewContent.value = 'content'
      rag.closeDocumentPreview()
      expect(rag.documentPreviewDialog.value).toBe(false)
      expect(rag.previewDocument.value).toBeNull()
      expect(rag.previewContent.value).toBe('')
    })
  })

  // ==================== Helper Function Tests ====================

  describe('helper functions', () => {
    it('RAG_DOC_035: getFileExtension extracts extension', () => {
      expect(rag.getFileExtension('test.pdf')).toBe('pdf')
      expect(rag.getFileExtension('report.final.docx')).toBe('docx')
    })

    it('RAG_DOC_036: getFileExtension handles edge cases', () => {
      expect(rag.getFileExtension('')).toBe('')
      expect(rag.getFileExtension(null)).toBe('')
      expect(rag.getFileExtension('noext')).toBe('')
    })

    it('RAG_DOC_037: getFileTypeIcon returns correct icons', () => {
      expect(rag.getFileTypeIcon('pdf')).toBe('mdi-file-pdf-box')
      expect(rag.getFileTypeIcon('txt')).toBe('mdi-file-document-outline')
      expect(rag.getFileTypeIcon('md')).toBe('mdi-language-markdown')
      expect(rag.getFileTypeIcon('docx')).toBe('mdi-file-word')
      expect(rag.getFileTypeIcon('doc')).toBe('mdi-file-word')
    })

    it('RAG_DOC_038: getFileTypeIcon returns fallback for unknown type', () => {
      expect(rag.getFileTypeIcon('xyz')).toBe('mdi-file')
    })

    it('RAG_DOC_039: getFileTypeColor returns correct colors', () => {
      expect(rag.getFileTypeColor('pdf')).toBe('red')
      expect(rag.getFileTypeColor('txt')).toBe('grey')
      expect(rag.getFileTypeColor('md')).toBe('blue')
    })

    it('RAG_DOC_040: getFileTypeColor returns fallback', () => {
      expect(rag.getFileTypeColor('xyz')).toBe('grey')
    })

    it('RAG_DOC_041: getStatusColor maps status correctly', () => {
      expect(rag.getStatusColor('processed')).toBe('success')
      expect(rag.getStatusColor('indexed')).toBe('success')
      expect(rag.getStatusColor('pending')).toBe('warning')
      expect(rag.getStatusColor('processing')).toBe('info')
      expect(rag.getStatusColor('error')).toBe('error')
      expect(rag.getStatusColor('unknown')).toBe('grey')
    })

    it('RAG_DOC_042: getStatusIcon maps status correctly', () => {
      expect(rag.getStatusIcon('processed')).toBe('mdi-check-circle')
      expect(rag.getStatusIcon('pending')).toBe('mdi-clock-outline')
      expect(rag.getStatusIcon('processing')).toBe('mdi-cog-sync')
      expect(rag.getStatusIcon('error')).toBe('mdi-alert-circle')
      expect(rag.getStatusIcon('unknown')).toBe('mdi-help-circle')
    })

    it('RAG_DOC_043: isPdfDocument detects PDFs', () => {
      expect(rag.isPdfDocument({ file_type: 'pdf' })).toBe(true)
      expect(rag.isPdfDocument({ filename: 'doc.pdf' })).toBe(true)
      expect(rag.isPdfDocument({ mime_type: 'application/pdf' })).toBe(true)
      expect(rag.isPdfDocument({ file_type: 'txt' })).toBe(false)
      expect(rag.isPdfDocument(null)).toBe(false)
    })

    it('RAG_DOC_044: isTextDocument detects text files', () => {
      expect(rag.isTextDocument({ file_type: 'txt' })).toBe(true)
      expect(rag.isTextDocument({ file_type: 'md' })).toBe(true)
      expect(rag.isTextDocument({ file_type: 'markdown' })).toBe(true)
      expect(rag.isTextDocument({ mime_type: 'text/plain' })).toBe(true)
      expect(rag.isTextDocument({ mime_type: 'text/markdown' })).toBe(true)
      expect(rag.isTextDocument({ file_type: 'pdf' })).toBe(false)
      expect(rag.isTextDocument(null)).toBe(false)
    })

    it('RAG_DOC_045: getDocumentPreviewUrl constructs correct URL', () => {
      expect(rag.getDocumentPreviewUrl({ id: 42 })).toBe('/api/rag/documents/42/download')
      expect(rag.getDocumentPreviewUrl(null)).toBe('')
      expect(rag.getDocumentPreviewUrl({})).toBe('')
    })

    it('RAG_DOC_046: formatFileSize formats bytes correctly', () => {
      expect(rag.formatFileSize(0)).toBe('0 B')
      expect(rag.formatFileSize(null)).toBe('0 B')
      expect(rag.formatFileSize(512)).toBe('512 B')
      expect(rag.formatFileSize(1024)).toBe('1 KB')
      expect(rag.formatFileSize(1048576)).toBe('1 MB')
      expect(rag.formatFileSize(1073741824)).toBe('1 GB')
    })

    it('RAG_DOC_047: formatDate formats dates', () => {
      expect(rag.formatDate(null)).toBe('-')
      expect(rag.formatDate('')).toBe('-')
      const result = rag.formatDate('2025-06-15T14:30:00Z')
      expect(result).toContain('15')
      expect(result).toContain('06')
      expect(result).toContain('2025')
    })
  })
})
