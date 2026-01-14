<template>
  <div class="assessment-view">
    <!-- Skeleton Loading -->
    <v-skeleton-loader v-if="isLoading" type="heading, article"></v-skeleton-loader>

    <template v-else>
    <!-- Header -->
    <div class="assessment-header">
      <h1 class="assessment-title">{{ $t('kaimo.assessment.title') }}</h1>
      <button class="overview-btn" @click="showSidebar = !showSidebar">
        <LIcon size="20">mdi-folder-open-outline</LIcon>
      </button>
    </div>

    <!-- Content -->
    <div class="assessment-content">
      <!-- Left: Matrix (55%) -->
      <div class="matrix-panel" :class="{ 'matrix-hidden': !showMatrix }">
        <div class="matrix-container">
          <!-- Matrix Header -->
          <div class="matrix-header">
            <div class="matrix-header-cell label-cell"></div>
            <div class="matrix-header-cell risk-cell">{{ $t('kaimo.ratings.risk') }}</div>
            <div class="matrix-header-cell resource-cell">{{ $t('kaimo.ratings.resource') }}</div>
            <div class="matrix-header-cell unclear-cell">{{ $t('kaimo.ratings.unclear') }}</div>
          </div>

          <!-- Matrix Body - Categories and Subcategories -->
          <div class="matrix-body">
            <template v-for="category in sortedCategories" :key="category.id">
              <!-- Category Header -->
              <div class="category-section">
                <div class="category-header">
                  <span class="category-name">{{ category.display_name }}</span>
                </div>

                <!-- Subcategory Rows -->
                <div
                  v-for="subcategory in getSubcategories(category.id)"
                  :key="subcategory.id"
                  class="subcategory-row"
                >
                  <div class="subcategory-label">{{ subcategory.display_name }}</div>
                  <div class="subcategory-cell risk-column">
                    <template v-for="hint in getHintsForSubcategory(subcategory.id, 'risk')" :key="hint.id">
                      <div class="hint-chip hint-risk" :title="hint.content">
                        {{ truncateHint(hint.content) }}
                      </div>
                    </template>
                  </div>
                  <div class="subcategory-cell resource-column">
                    <template v-for="hint in getHintsForSubcategory(subcategory.id, 'resource')" :key="hint.id">
                      <div class="hint-chip hint-resource" :title="hint.content">
                        {{ truncateHint(hint.content) }}
                      </div>
                    </template>
                  </div>
                  <div class="subcategory-cell unclear-column">
                    <template v-for="hint in getHintsForSubcategory(subcategory.id, 'unclear')" :key="hint.id">
                      <div class="hint-chip hint-unclear" :title="hint.content">
                        {{ truncateHint(hint.content) }}
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Right: Verdict Panel -->
      <div class="verdict-panel" :class="{ 'verdict-full': !showMatrix }">
        <div class="verdict-container">
          <div class="verdict-card">
            <p class="verdict-instruction">
              {{ $t('kaimo.assessment.verdictInstruction') }} <strong>{{ childName }}</strong>
            </p>

            <!-- Verdict Options -->
            <div class="verdict-options">
              <div
                class="verdict-option"
                :class="{ 'verdict-option-selected': selectedVerdict === 'inconclusive', 'verdict-option-first': true }"
                @click="selectedVerdict = 'inconclusive'"
              >
                <span class="radio-circle" :class="{ 'radio-selected': selectedVerdict === 'inconclusive' }">
                  <span class="radio-dot"></span>
                </span>
                <span class="verdict-label">{{ $t('kaimo.assessment.verdicts.inconclusive') }}</span>
              </div>

              <div
                class="verdict-option"
                :class="{ 'verdict-option-selected': selectedVerdict === 'not_endangered' }"
                @click="selectedVerdict = 'not_endangered'"
              >
                <span class="radio-circle" :class="{ 'radio-selected': selectedVerdict === 'not_endangered' }">
                  <span class="radio-dot"></span>
                </span>
                <span class="verdict-label">{{ $t('kaimo.assessment.verdicts.notEndangered', { name: childName }) }}</span>
              </div>

              <div
                class="verdict-option"
                :class="{ 'verdict-option-selected': selectedVerdict === 'endangered', 'verdict-option-last': true }"
                @click="selectedVerdict = 'endangered'"
              >
                <span class="radio-circle" :class="{ 'radio-selected': selectedVerdict === 'endangered' }">
                  <span class="radio-dot"></span>
                </span>
                <span class="verdict-label">{{ $t('kaimo.assessment.verdicts.endangered', { name: childName }) }}</span>
              </div>
            </div>

            <!-- Additional Notes (optional) -->
            <div v-if="selectedVerdict" class="verdict-notes">
              <textarea
                v-model="additionalNotes"
                :placeholder="$t('kaimo.assessment.notesPlaceholder')"
                class="notes-input"
                rows="4"
              ></textarea>

              <button
                class="submit-btn"
                :disabled="!selectedVerdict || submitting"
                @click="submitAssessment"
              >
                <LIcon v-if="submitting" size="20" class="mr-2">mdi-loading mdi-spin</LIcon>
                <LIcon v-else size="20" class="mr-2">mdi-check</LIcon>
                {{ $t('kaimo.assessment.submit') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Overview Sidebar -->
    <div class="overview-sidebar" :class="{ 'sidebar-open': showSidebar }">
      <div class="sidebar-header">
        <span class="sidebar-title">{{ $t('kaimo.assessment.sidebar.title') }}</span>
        <button class="sidebar-close" @click="showSidebar = false">
          <LIcon size="20">mdi-close</LIcon>
        </button>
      </div>
      <div class="sidebar-content">
        <div class="sidebar-item">
          <span class="sidebar-label">{{ $t('kaimo.assessment.sidebar.caseLabel') }}</span>
          <span class="sidebar-value">{{ caseData?.display_name }}</span>
        </div>
        <div class="sidebar-item">
          <span class="sidebar-label">{{ $t('kaimo.assessment.sidebar.statusLabel') }}</span>
          <span class="sidebar-value">{{ assessment?.status === 'completed' ? $t('kaimo.assessment.sidebar.statusCompleted') : $t('kaimo.assessment.sidebar.statusInProgress') }}</span>
        </div>
        <div class="sidebar-item">
          <span class="sidebar-label">{{ $t('kaimo.assessment.sidebar.hintsAssigned') }}</span>
          <span class="sidebar-value">{{ $t('kaimo.assessment.sidebar.hintsAssignedValue', { assigned: assignedHintCount, total: totalHintCount }) }}</span>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { completeAssessment } from '@/services/kaimoApi'

const props = defineProps({
  caseData: {
    type: Object,
    default: null
  },
  assessment: {
    type: Object,
    default: null
  },
  hintAssignments: {
    type: Map,
    default: () => new Map()
  },
  categories: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

// Use the isLoading prop directly for skeleton loading

const emit = defineEmits(['complete'])

const { t } = useI18n()

const selectedVerdict = ref(null)
const additionalNotes = ref('')
const showSidebar = ref(false)
const showMatrix = ref(false)  // Hidden by default like prototype
const submitting = ref(false)

const childName = computed(() => props.caseData?.display_name || t('kaimo.common.childFallback'))

// Get all hints
const hints = computed(() => props.caseData?.hints || [])

// Sort categories in the order they appear in prototype
const sortedCategories = computed(() => {
  const cats = props.categories || props.caseData?.categories || []
  const order = ['grundversorgung', 'entwicklung', 'familiensituation', 'eltern']

  return [...cats].sort((a, b) => {
    const aIndex = order.findIndex(term => a.display_name?.toLowerCase().includes(term))
    const bIndex = order.findIndex(term => b.display_name?.toLowerCase().includes(term))
    if (aIndex === -1 && bIndex === -1) return 0
    if (aIndex === -1) return 1
    if (bIndex === -1) return -1
    return aIndex - bIndex
  })
})

// Get subcategories for a category
const getSubcategories = (categoryId) => {
  const category = (props.categories || []).find(c => c.id === categoryId)
  return category?.subcategories || []
}

// Get hints assigned to a specific subcategory with a specific rating
const getHintsForSubcategory = (subcategoryId, rating) => {
  const result = []
  hints.value.forEach(hint => {
    const assignment = props.hintAssignments.get(hint.id)
    if (assignment?.subcategory_id === subcategoryId && assignment?.rating === rating) {
      result.push(hint)
    }
  })
  return result
}

// Truncate hint content for display
const truncateHint = (content) => {
  if (!content) return ''
  const maxLength = 30
  return content.length > maxLength ? content.substring(0, maxLength) + '...' : content
}

// Count assigned hints
const assignedHintCount = computed(() => props.hintAssignments.size)
const totalHintCount = computed(() => hints.value.length)

const submitAssessment = async () => {
  if (!props.assessment?.id || !selectedVerdict.value) return

  submitting.value = true
  try {
    await completeAssessment(props.assessment.id, {
      final_verdict: selectedVerdict.value,
      final_comment: additionalNotes.value
    })

    emit('complete')
  } catch (err) {
    console.error('Konnte Bewertung nicht abschliessen:', err)
    alert(t('kaimo.assessment.errors.completeFailed'))
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.assessment-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
  position: relative;
}

/* Header */
.assessment-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background-color: white;
  border-bottom: 1px solid #e2e8f0;
}

.assessment-title {
  font-size: 20px;
  font-weight: 500;
  color: #475569;
  margin: 0;
}

.overview-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background-color: rgba(99, 102, 241, 0.2);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #6366f1;
  transition: background-color 0.2s ease;
}

.overview-btn:hover {
  background-color: rgba(99, 102, 241, 0.3);
}

/* Content */
.assessment-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Matrix Panel (Left 55%) */
.matrix-panel {
  width: 55%;
  height: 100%;
  background-color: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.5s ease, margin-left 0.5s ease;
}

.matrix-panel.matrix-hidden {
  transform: translateX(-100%);
  margin-left: -55%;
}

.matrix-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Matrix Header */
.matrix-header {
  display: flex;
  padding: 12px 16px;
  background-color: white;
  border-bottom: 1px solid #e2e8f0;
  gap: 8px;
}

.matrix-header-cell {
  flex: 0.25;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
  font-weight: 500;
  font-size: 14px;
}

.label-cell {
  background: transparent;
}

.risk-cell {
  background-color: #f43f5e;
  color: white;
}

.resource-cell {
  background-color: #10b981;
  color: white;
}

.unclear-cell {
  background-color: #f1f5f9;
  color: #475569;
}

/* Matrix Body */
.matrix-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.category-section {
  margin-bottom: 40px;
}

.category-header {
  margin-bottom: 32px;
}

.category-name {
  font-size: 20px;
  font-weight: 500;
  color: #475569;
}

.subcategory-row {
  display: flex;
  gap: 8px;
  padding: 8px;
  background-color: #f8fafc;
  border-radius: 6px;
  margin-bottom: 8px;
}

.subcategory-label {
  flex: 0.25;
  padding: 8px;
  font-size: 14px;
  color: #1e293b;
}

.subcategory-cell {
  flex: 0.25;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Hint Chips */
.hint-chip {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hint-risk {
  background-color: #fecdd3;
  color: #be123c;
}

.hint-resource {
  background-color: #d1fae5;
  color: #047857;
}

.hint-unclear {
  background-color: #e2e8f0;
  color: #475569;
}

/* Verdict Panel (Right) */
.verdict-panel {
  flex: 1;
  display: flex;
  overflow: hidden;
  transition: margin-left 0.5s ease;
}

.verdict-panel.verdict-full {
  margin-left: -55%;
}

.verdict-container {
  width: 80%;
  max-width: 600px;
  margin: auto;
  padding: 32px;
}

.verdict-card {
  background-color: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.verdict-instruction {
  font-size: 16px;
  color: #374151;
  margin: 0 0 24px;
}

/* Verdict Options */
.verdict-options {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.verdict-option {
  display: flex;
  align-items: center;
  padding: 16px;
  cursor: pointer;
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s ease;
}

.verdict-option:last-child {
  border-bottom: none;
}

.verdict-option:hover {
  background-color: #f9fafb;
}

.verdict-option-selected {
  background-color: rgba(99, 102, 241, 0.05);
  border-color: #6366f1;
}

.verdict-option-first {
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.verdict-option-last {
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

.radio-circle {
  width: 16px;
  height: 16px;
  border: 2px solid #d1d5db;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12px;
}

.radio-selected {
  border-color: #6366f1;
}

.radio-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: transparent;
}

.radio-selected .radio-dot {
  background-color: #6366f1;
}

.verdict-label {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
}

/* Notes */
.verdict-notes {
  margin-top: 24px;
}

.notes-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  outline: none;
  font-family: inherit;
}

.notes-input:focus {
  border-color: #6366f1;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin-top: 16px;
  padding: 12px 24px;
  background-color: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.submit-btn:hover:not(:disabled) {
  background-color: #4f46e5;
}

.submit-btn:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

/* Overview Sidebar */
.overview-sidebar {
  position: absolute;
  top: 0;
  right: 0;
  width: 320px;
  height: 100%;
  background-color: white;
  box-shadow: -4px 0 8px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.overview-sidebar.sidebar-open {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-title {
  font-size: 18px;
  font-weight: 500;
  color: #1e293b;
}

.sidebar-close {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
}

.sidebar-close:hover {
  color: #1e293b;
}

.sidebar-content {
  padding: 16px;
}

.sidebar-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}

.sidebar-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.sidebar-value {
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
}
</style>
