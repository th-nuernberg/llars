<template>
  <div class="documents-view">
    <!-- Top Bar with Search and Filters (exactly like prototype) -->
    <div class="documents-header">
      <div class="search-wrapper">
        <LIcon size="16" class="search-icon">mdi-magnify</LIcon>
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="$t('kaimo.documents.searchPlaceholder')"
          class="search-input"
        />
      </div>

      <div class="filter-buttons">
        <!-- Merkmale Filter Dropdown -->
        <div class="filter-dropdown" ref="merkmaleDropdownRef">
          <button
            class="filter-btn"
            :class="{ 'filter-btn-active': selectedMerkmale.length > 0 }"
            @click="toggleMerkmale"
          >
            <span>{{ $t('kaimo.documents.filters.attributes') }}</span>
            <span v-if="selectedMerkmale.length > 0" class="filter-count">({{ selectedMerkmale.length }})</span>
            <LIcon size="16">mdi-chevron-down</LIcon>
          </button>
          <div v-if="showMerkmaleDropdown" class="dropdown-menu">
            <div class="dropdown-header">
              <span>{{ $t('kaimo.documents.filters.attributes') }}</span>
              <button v-if="selectedMerkmale.length > 0" class="clear-btn" @click.stop="clearMerkmale">
                {{ $t('kaimo.documents.filters.clear') }}
              </button>
            </div>
            <div
              v-for="merkmal in availableMerkmale"
              :key="merkmal.value"
              class="dropdown-item"
              :class="{ 'dropdown-item-selected': selectedMerkmale.includes(merkmal.value) }"
              @click.stop="toggleMerkmalSelection(merkmal.value)"
            >
              <LIcon size="16">{{ selectedMerkmale.includes(merkmal.value) ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline' }}</LIcon>
              <span>{{ merkmal.label }}</span>
            </div>
          </div>
        </div>

        <!-- Akteure Filter Dropdown -->
        <div class="filter-dropdown" ref="akteureDropdownRef">
          <button
            class="filter-btn"
            :class="{ 'filter-btn-active': selectedAkteure.length > 0 }"
            @click="toggleAkteure"
          >
            <span>{{ $t('kaimo.documents.filters.actors') }}</span>
            <span v-if="selectedAkteure.length > 0" class="filter-count">({{ selectedAkteure.length }})</span>
            <LIcon size="16">mdi-chevron-down</LIcon>
          </button>
          <div v-if="showAkteureDropdown" class="dropdown-menu">
            <div class="dropdown-header">
              <span>{{ $t('kaimo.documents.filters.actors') }}</span>
              <button v-if="selectedAkteure.length > 0" class="clear-btn" @click.stop="clearAkteure">
                {{ $t('kaimo.documents.filters.clear') }}
              </button>
            </div>
            <div
              v-for="akteur in availableAkteure"
              :key="akteur.value"
              class="dropdown-item"
              :class="{ 'dropdown-item-selected': selectedAkteure.includes(akteur.value) }"
              @click.stop="toggleAkteurSelection(akteur.value)"
            >
              <LIcon size="16">{{ selectedAkteure.includes(akteur.value) ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline' }}</LIcon>
              <span>{{ akteur.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <v-spacer />

      <!-- Active filters chips -->
      <div v-if="hasActiveFilters" class="active-filters">
        <span
          v-for="filter in activeFilterChips"
          :key="filter.key"
          class="filter-chip"
          @click="removeFilter(filter)"
        >
          {{ filter.label }}
          <LIcon size="14">mdi-close</LIcon>
        </span>
      </div>

      <!-- Toggle button for document list -->
      <button class="toggle-list-btn" @click="showList = !showList">
        <LIcon size="20">{{ showList ? 'mdi-menu-open' : 'mdi-menu' }}</LIcon>
      </button>
    </div>

    <!-- Content Area -->
    <div class="documents-content">
      <!-- Document List (Left 30%) -->
      <div class="documents-list" :class="{ 'list-hidden': !showList }">
        <v-skeleton-loader
          v-if="props.isLoading"
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
              <LIcon v-if="selectedDocument?.id === doc.id" size="14" color="grey-darken-1">mdi-menu-right</LIcon>
              <LIcon v-else size="14" color="grey-lighten-1">mdi-circle-outline</LIcon>
            </div>
            <div class="document-item-content">
              <div class="document-item-title">{{ doc.title }}</div>
              <div class="document-item-date">{{ formatDate(doc.document_date) }}</div>
            </div>
          </div>

          <div v-if="filteredDocuments.length === 0" class="no-documents">
            <span>{{ $t('kaimo.documents.emptySearch') }}</span>
          </div>
        </template>
      </div>

      <!-- Document Content (Right - grows to fill) - Shows ALL documents stacked -->
      <div class="document-viewer" :class="{ 'viewer-full': !showList }">
        <div class="document-viewer-scroll">
          <div class="document-viewer-content">
            <v-skeleton-loader
              v-if="props.isLoading"
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
              <span>{{ $t('kaimo.documents.empty') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

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

const { t, locale } = useI18n()

const searchQuery = ref('')
const selectedDocument = ref(null)
const showList = ref(false)  // Hidden by default like prototype
const docRefs = ref({})

// Filter state
const showMerkmaleDropdown = ref(false)
const showAkteureDropdown = ref(false)
const selectedMerkmale = ref([])
const selectedAkteure = ref([])
const merkmaleDropdownRef = ref(null)
const akteureDropdownRef = ref(null)

const documents = computed(() => props.caseData?.documents || [])

// Available Merkmale (document types and attributes)
const availableMerkmale = computed(() => {
  const merkmale = [
    { value: 'aktenvermerk', label: t('kaimo.documents.types.aktenvermerk') },
    { value: 'bericht', label: t('kaimo.documents.types.bericht') },
    { value: 'protokoll', label: t('kaimo.documents.types.protokoll') },
    { value: 'sonstiges', label: t('kaimo.documents.types.sonstiges') }
  ]
  return merkmale
})

// Extract actors from document content
const availableAkteure = computed(() => {
  const actors = new Set()
  const actorPatterns = [
    { pattern: /mutter|mama|frau\s+\w+/gi, label: t('kaimo.documents.actors.mother') },
    { pattern: /vater|papa|herr\s+\w+/gi, label: t('kaimo.documents.actors.father') },
    { pattern: /kind|malaika|mädchen|junge/gi, label: t('kaimo.documents.actors.child') },
    { pattern: /lehrer(?:in)?|klassenlehr(?:er|erin)/gi, label: t('kaimo.documents.actors.teacher') },
    { pattern: /jugendamt|sozialarbeiter(?:in)?|fachkraft/gi, label: t('kaimo.documents.actors.socialWorker') },
    { pattern: /nachbar(?:n|in)?/gi, label: t('kaimo.documents.actors.neighbor') },
    { pattern: /anruf(?:er|erin)?|mitteilende person/gi, label: t('kaimo.documents.actors.reporter') }
  ]

  documents.value.forEach(doc => {
    const content = (doc.content || '').toLowerCase()
    actorPatterns.forEach(({ pattern, label }) => {
      if (pattern.test(content)) {
        actors.add(label)
      }
    })
  })

  return Array.from(actors).map(label => ({
    value: label.toLowerCase().replace(/\s+/g, '_'),
    label
  }))
})

const filteredDocuments = computed(() => {
  let result = documents.value

  // Filter by search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(doc => {
      return (
        doc.title?.toLowerCase().includes(query) ||
        doc.content?.toLowerCase().includes(query) ||
        doc.document_type?.toLowerCase().includes(query)
      )
    })
  }

  // Filter by Merkmale (document types)
  if (selectedMerkmale.value.length > 0) {
    result = result.filter(doc =>
      selectedMerkmale.value.includes(doc.document_type)
    )
  }

  // Filter by Akteure (actors mentioned in content)
  if (selectedAkteure.value.length > 0) {
    result = result.filter(doc => {
      const content = (doc.content || '').toLowerCase()
      return selectedAkteure.value.some(akteur => {
        const patterns = getActorPatterns(akteur)
        return patterns.some(pattern => pattern.test(content))
      })
    })
  }

  return result
})

// Get regex patterns for actor filtering
const getActorPatterns = (akteurKey) => {
  const patternMap = {
    [t('kaimo.documents.actors.mother').toLowerCase().replace(/\s+/g, '_')]: [/mutter|mama|frau\s+\w+/gi],
    [t('kaimo.documents.actors.father').toLowerCase().replace(/\s+/g, '_')]: [/vater|papa|herr\s+\w+/gi],
    [t('kaimo.documents.actors.child').toLowerCase().replace(/\s+/g, '_')]: [/kind|malaika|mädchen|junge/gi],
    [t('kaimo.documents.actors.teacher').toLowerCase().replace(/\s+/g, '_')]: [/lehrer(?:in)?|klassenlehr(?:er|erin)/gi],
    [t('kaimo.documents.actors.socialWorker').toLowerCase().replace(/\s+/g, '_')]: [/jugendamt|sozialarbeiter(?:in)?|fachkraft/gi],
    [t('kaimo.documents.actors.neighbor').toLowerCase().replace(/\s+/g, '_')]: [/nachbar(?:n|in)?/gi],
    [t('kaimo.documents.actors.reporter').toLowerCase().replace(/\s+/g, '_')]: [/anruf(?:er|erin)?|mitteilende person/gi]
  }
  return patternMap[akteurKey] || []
}

// Check if any filters are active
const hasActiveFilters = computed(() => {
  return selectedMerkmale.value.length > 0 || selectedAkteure.value.length > 0
})

// Generate active filter chips
const activeFilterChips = computed(() => {
  const chips = []
  selectedMerkmale.value.forEach(m => {
    const merkmal = availableMerkmale.value.find(am => am.value === m)
    if (merkmal) {
      chips.push({ key: `merkmal_${m}`, label: merkmal.label, type: 'merkmal', value: m })
    }
  })
  selectedAkteure.value.forEach(a => {
    const akteur = availableAkteure.value.find(aa => aa.value === a)
    if (akteur) {
      chips.push({ key: `akteur_${a}`, label: akteur.label, type: 'akteur', value: a })
    }
  })
  return chips
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
const documentTypeLabels = computed(() => ({
  'aktenvermerk': t('kaimo.documents.types.aktenvermerk'),
  'bericht': t('kaimo.documents.types.bericht'),
  'protokoll': t('kaimo.documents.types.protokoll'),
  'sonstiges': t('kaimo.documents.types.sonstiges')
}))

const getDocumentTypeLabel = (type) => {
  return documentTypeLabels.value[type] || t('kaimo.documents.types.default')
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
  if (!dateStr) return t('kaimo.documents.placeholders.date')
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString(locale.value || undefined, {
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
    const weekday = date.toLocaleDateString(locale.value || undefined, { weekday: 'long' })
    const day = date.toLocaleDateString(locale.value || undefined, { day: '2-digit', month: '2-digit', year: 'numeric' })
    return `${weekday}, ${day}`
  } catch (e) {
    return dateStr
  }
}

const toggleMerkmale = () => {
  showMerkmaleDropdown.value = !showMerkmaleDropdown.value
  showAkteureDropdown.value = false
}

const toggleAkteure = () => {
  showAkteureDropdown.value = !showAkteureDropdown.value
  showMerkmaleDropdown.value = false
}

const toggleMerkmalSelection = (value) => {
  const index = selectedMerkmale.value.indexOf(value)
  if (index === -1) {
    selectedMerkmale.value.push(value)
  } else {
    selectedMerkmale.value.splice(index, 1)
  }
}

const toggleAkteurSelection = (value) => {
  const index = selectedAkteure.value.indexOf(value)
  if (index === -1) {
    selectedAkteure.value.push(value)
  } else {
    selectedAkteure.value.splice(index, 1)
  }
}

const clearMerkmale = () => {
  selectedMerkmale.value = []
}

const clearAkteure = () => {
  selectedAkteure.value = []
}

const removeFilter = (filter) => {
  if (filter.type === 'merkmal') {
    const index = selectedMerkmale.value.indexOf(filter.value)
    if (index !== -1) selectedMerkmale.value.splice(index, 1)
  } else if (filter.type === 'akteur') {
    const index = selectedAkteure.value.indexOf(filter.value)
    if (index !== -1) selectedAkteure.value.splice(index, 1)
  }
}

// Close dropdowns when clicking outside
const handleClickOutside = (event) => {
  if (merkmaleDropdownRef.value && !merkmaleDropdownRef.value.contains(event.target)) {
    showMerkmaleDropdown.value = false
  }
  if (akteureDropdownRef.value && !akteureDropdownRef.value.contains(event.target)) {
    showAkteureDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

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

.filter-dropdown {
  position: relative;
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

.filter-btn-active {
  color: #6366f1;
  font-weight: 500;
}

.filter-count {
  font-size: 12px;
  color: #6366f1;
}

/* Dropdown Menu */
.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 200px;
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  z-index: 100;
  margin-top: 4px;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  font-weight: 500;
  font-size: 14px;
  color: #1e293b;
}

.clear-btn {
  background: none;
  border: none;
  font-size: 12px;
  color: #6366f1;
  cursor: pointer;
}

.clear-btn:hover {
  text-decoration: underline;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  transition: background-color 0.15s ease;
}

.dropdown-item:hover {
  background-color: #f8fafc;
}

.dropdown-item-selected {
  background-color: rgba(99, 102, 241, 0.05);
  color: #6366f1;
}

/* Active Filter Chips */
.active-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-right: 16px;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background-color: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.filter-chip:hover {
  background-color: rgba(99, 102, 241, 0.2);
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
