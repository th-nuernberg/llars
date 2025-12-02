<template>
  <div class="documents-view">
    <!-- Top Bar with Search and Filters (exactly like prototype) -->
    <div class="documents-header">
      <div class="search-wrapper">
        <v-icon size="16" class="search-icon">mdi-magnify</v-icon>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Textsuche"
          class="search-input"
        />
      </div>

      <div class="filter-buttons">
        <button class="filter-btn" @click="toggleMerkmale">
          <span>Merkmale</span>
          <v-icon size="16">mdi-chevron-down</v-icon>
        </button>
        <button class="filter-btn" @click="toggleAkteure">
          <span>Akteure</span>
          <v-icon size="16">mdi-chevron-down</v-icon>
        </button>
      </div>

      <v-spacer />

      <!-- Toggle button for document list -->
      <button class="toggle-list-btn" @click="showList = !showList">
        <v-icon size="20">{{ showList ? 'mdi-menu-open' : 'mdi-menu' }}</v-icon>
      </button>
    </div>

    <!-- Content Area -->
    <div class="documents-content">
      <!-- Document List (Left 30%) -->
      <div class="documents-list" :class="{ 'list-hidden': !showList }">
        <v-skeleton-loader
          v-if="isLoading"
          type="list-item-three-line@4"
        />
        <template v-else>
          <div
            v-for="doc in filteredDocuments"
            :key="doc.id"
            class="document-item"
            :class="{ 'document-item-active': selectedDocument?.id === doc.id }"
            @click="selectDocument(doc)"
          >
            <div class="document-item-indicator">
              <v-icon v-if="selectedDocument?.id === doc.id" size="14" color="grey-darken-1">mdi-menu-right</v-icon>
              <v-icon v-else size="14" color="grey-lighten-1">mdi-circle-outline</v-icon>
            </div>
            <div class="document-item-content">
              <div class="document-item-title">{{ doc.title }}</div>
              <div class="document-item-date">{{ formatDate(doc.document_date) }}</div>
            </div>
          </div>

          <div v-if="filteredDocuments.length === 0" class="no-documents">
            <span>Keine Ergebnisse gefunden</span>
          </div>
        </template>
      </div>

      <!-- Document Content (Right - grows to fill) - Shows ALL documents stacked -->
      <div class="document-viewer" :class="{ 'viewer-full': !showList }">
        <div class="document-viewer-scroll">
          <div class="document-viewer-content">
            <v-skeleton-loader
              v-if="isLoading"
              type="heading, paragraph@3"
            />
            <template v-else-if="filteredDocuments.length > 0">
              <div class="documents-stack">
                <template v-for="doc in filteredDocuments" :key="doc.id">
                  <!-- First document type: Main report (no header bar) -->
                  <div
                    v-if="isMainDocument(doc)"
                    :ref="el => setDocRef(doc.id, el)"
                    class="document-card document-card-main"
                    :class="{ 'document-card-highlighted': selectedDocument?.id === doc.id }"
                  >
                    <div class="document-card-header-main">
                      <span class="document-main-title">{{ doc.title }}</span>
                      <span class="document-main-date">{{ formatDateLong(doc.document_date) }}</span>
                    </div>

                    <!-- Document sections -->
                    <div class="document-sections">
                      <template v-for="(section, index) in parseDocContent(doc.content)" :key="index">
                        <h3 class="section-title">{{ section.title }}</h3>
                        <p class="section-content" v-html="section.content"></p>
                      </template>
                    </div>
                  </div>

                  <!-- Other documents: With grey header bar -->
                  <div
                    v-else
                    :ref="el => setDocRef(doc.id, el)"
                    class="document-card document-card-secondary"
                    :class="{ 'document-card-highlighted': selectedDocument?.id === doc.id }"
                  >
                    <div class="document-card-header">
                      <div class="document-card-meta">
                        <span class="document-type">{{ getDocumentTypeLabel(doc.document_type) }}</span>
                        <h3 class="document-title">{{ doc.title }}</h3>
                      </div>
                      <span class="document-date">{{ formatDateLong(doc.document_date) }}</span>
                    </div>

                    <div class="document-body">
                      <p v-for="(para, idx) in splitIntoParagraphs(doc.content)" :key="idx" class="document-paragraph">
                        {{ para }}
                      </p>
                    </div>
                  </div>
                </template>
              </div>
            </template>
            <div v-else class="no-document-selected">
              <span>Keine Dokumente vorhanden</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  caseData: {
    type: Object,
    default: null
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const searchQuery = ref('')
const selectedDocument = ref(null)
const showList = ref(false)  // Hidden by default like prototype
const docRefs = ref({})

const documents = computed(() => props.caseData?.documents || [])

const filteredDocuments = computed(() => {
  if (!searchQuery.value.trim()) {
    return documents.value
  }

  const query = searchQuery.value.toLowerCase()
  return documents.value.filter(doc => {
    return (
      doc.title?.toLowerCase().includes(query) ||
      doc.content?.toLowerCase().includes(query) ||
      doc.document_type?.toLowerCase().includes(query)
    )
  })
})

// Store refs to document elements for scrolling
const setDocRef = (id, el) => {
  if (el) {
    docRefs.value[id] = el
  }
}

// Check if this is the main/first document (Mitteilung)
const isMainDocument = (doc) => {
  return doc.sort_order === 0 ||
         doc.title?.toLowerCase().includes('mitteilung') ||
         documents.value.indexOf(doc) === 0
}

// Get document type label
const getDocumentTypeLabel = (type) => {
  const labels = {
    'aktenvermerk': 'Aktenvermerk',
    'bericht': 'Bericht',
    'protokoll': 'Protokoll',
    'sonstiges': 'Dokument'
  }
  return labels[type] || 'Aktenvermerk'
}

// Parse content into sections (for main document with headers)
const parseDocContent = (content) => {
  if (!content) return []

  const sections = []
  const lines = content.split('\n')
  let currentSection = { title: '', content: '' }

  lines.forEach(line => {
    const trimmedLine = line.trim()

    // Check if line looks like a section header (ends with colon)
    if (trimmedLine.endsWith(':') && trimmedLine.length < 100) {
      if (currentSection.title || currentSection.content.trim()) {
        sections.push({ ...currentSection })
      }
      currentSection = {
        title: trimmedLine,
        content: ''
      }
    } else if (trimmedLine) {
      currentSection.content += (currentSection.content ? '<br>' : '') + trimmedLine
    }
  })

  if (currentSection.title || currentSection.content.trim()) {
    sections.push(currentSection)
  }

  return sections
}

// Split content into paragraphs for secondary documents
const splitIntoParagraphs = (content) => {
  if (!content) return []
  return content
    .split('\n\n')
    .map(p => p.trim())
    .filter(p => p.length > 0)
}

const selectDocument = (doc) => {
  selectedDocument.value = doc
  // Scroll to the selected document in the viewer
  nextTick(() => {
    const el = docRefs.value[doc.id]
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  } catch (e) {
    return dateStr
  }
}

const formatDateLong = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    const weekday = date.toLocaleDateString('de-DE', { weekday: 'long' })
    const day = date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
    return `${weekday}, ${day}`
  } catch (e) {
    return dateStr
  }
}

const toggleMerkmale = () => {
  // Placeholder for filter functionality
}

const toggleAkteure = () => {
  // Placeholder for filter functionality
}

// Auto-select first document when data loads
watch(documents, (newDocs) => {
  if (newDocs.length > 0 && !selectedDocument.value) {
    selectedDocument.value = newDocs[0]
  }
}, { immediate: true })
</script>

<style scoped>
.documents-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

/* Header - exactly like prototype */
.documents-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background-color: white;
  border-bottom: 1px solid #e2e8f0;
}

.search-wrapper {
  position: relative;
  width: 20%;
  min-width: 180px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  background-color: #f1f5f9;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.search-input::placeholder {
  color: #94a3b8;
}

.filter-buttons {
  display: flex;
  gap: 0;
  border-left: 1px solid #e2e8f0;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: none;
  border: none;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  border-left: 1px solid #e2e8f0;
}

.filter-btn:first-child {
  border-left: none;
}

.filter-btn:hover {
  color: #111827;
}

.toggle-list-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background-color: rgba(99, 102, 241, 0.1);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #6366f1;
  transition: background-color 0.2s ease;
}

.toggle-list-btn:hover {
  background-color: rgba(99, 102, 241, 0.2);
}

/* Content */
.documents-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Document List */
.documents-list {
  width: 30%;
  overflow-y: auto;
  background-color: white;
  border-right: 1px solid #e2e8f0;
  transition: transform 0.5s ease, margin-left 0.5s ease;
}

.documents-list.list-hidden {
  transform: translateX(-100%);
  margin-left: -30%;
}

.document-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f1f5f9;
  transition: background-color 0.2s ease;
}

.document-item:hover {
  background-color: #f8fafc;
}

.document-item-active {
  background-color: #f1f5f9;
}

.document-item-indicator {
  flex-shrink: 0;
  padding-top: 4px;
}

.document-item-content {
  flex: 1;
  min-width: 0;
}

.document-item-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
  color: #1e293b;
}

.document-item-date {
  font-size: 12px;
  color: #64748b;
}

.no-documents {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #64748b;
}

/* Document Viewer */
.document-viewer {
  flex: 1;
  overflow: hidden;
  background-color: #f8fafc;
  transition: margin-left 0.5s ease;
}

.document-viewer.viewer-full {
  margin-left: -30%;
}

.document-viewer-scroll {
  height: 100%;
  overflow-y: auto;
}

.document-viewer-content {
  max-width: 768px;
  margin: 0 auto;
  padding: 32px;
}

/* Document Cards */
.document-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
}

/* Main Document (first document - Mitteilung style) */
.document-card-main {
  padding: 20px 24px 32px;
}

.document-card-header-main {
  display: flex;
  justify-content: space-between;
  margin-bottom: 32px;
}

.document-main-title {
  font-size: 24px;
  font-weight: 500;
  line-height: 1.3;
  color: #1e293b;
  max-width: 60%;
}

.document-main-date {
  color: #64748b;
  text-align: right;
  font-size: 14px;
}

.document-sections {
  display: flex;
  flex-direction: column;
}

.section-title {
  font-size: 18px;
  font-weight: 500;
  margin: 16px 0;
  color: #1e293b;
}

.section-content {
  font-size: 16px;
  line-height: 1.6;
  color: #374151;
  margin: 0 0 8px;
}

/* Secondary Documents (Aktenvermerk style) */
.document-card-secondary {
  overflow: hidden;
}

.document-card-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 20px 24px;
  background-color: #f1f5f9;
}

.document-card-meta {
  display: flex;
  flex-direction: column;
}

.document-type {
  font-size: 16px;
  color: #64748b;
}

.document-title {
  font-size: 18px;
  font-weight: 500;
  color: #1e293b;
  margin: 0;
}

.document-date {
  font-size: 14px;
  color: #64748b;
  text-align: right;
}

.document-body {
  padding: 20px 24px 32px;
}

.document-paragraph {
  font-size: 16px;
  line-height: 1.6;
  color: #374151;
  margin: 0 0 16px;
}

.document-paragraph:last-child {
  margin-bottom: 0;
}

.no-document-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #64748b;
}

/* Documents Stack - all documents shown vertically */
.documents-stack {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Highlighted document when selected from list */
.document-card-highlighted {
  box-shadow: 0 0 0 2px #6366f1, 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
</style>
