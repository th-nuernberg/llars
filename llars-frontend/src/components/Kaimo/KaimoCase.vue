<template>
  <div class="kaimo-case-container">
    <!-- Sidebar Navigation -->
    <div class="kaimo-sidebar">
      <!-- Logo -->
      <div class="kaimo-logo">
        <LIcon size="28" color="white">mdi-shield-account</LIcon>
      </div>

      <!-- Navigation Icons -->
      <div class="kaimo-nav">
        <v-tooltip location="end">
          <template v-slot:activator="{ props }">
            <div
              v-bind="props"
              class="nav-item"
              :class="{ 'nav-item-active': activeView === 'documents' }"
              @click="activeView = 'documents'"
            >
              <LIcon size="24">mdi-file-document-multiple-outline</LIcon>
            </div>
          </template>
          <span>{{ $t('kaimo.case.navigation.documents') }}</span>
        </v-tooltip>

        <v-tooltip location="end">
          <template v-slot:activator="{ props }">
            <div
              v-bind="props"
              class="nav-item"
              :class="{ 'nav-item-active': activeView === 'diagram' }"
              @click="activeView = 'diagram'"
            >
              <LIcon size="24">mdi-sitemap</LIcon>
            </div>
          </template>
          <span>{{ $t('kaimo.case.navigation.diagram') }}</span>
        </v-tooltip>

        <v-tooltip location="end">
          <template v-slot:activator="{ props }">
            <div
              v-bind="props"
              class="nav-item"
              :class="{ 'nav-item-active': activeView === 'assessment' }"
              @click="activeView = 'assessment'"
            >
              <LIcon size="24">mdi-scale-unbalanced</LIcon>
            </div>
          </template>
          <span>{{ $t('kaimo.case.navigation.assessment') }}</span>
        </v-tooltip>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="kaimo-content">
      <v-alert
        v-if="loadError"
        type="error"
        variant="tonal"
        class="ma-4"
      >
        {{ loadError }}
      </v-alert>

      <template v-else>
        <KaimoDocumentsView
          v-show="activeView === 'documents'"
          :case-data="caseData"
          :is-loading="isLoading('case')"
        />

        <KaimoDiagramView
          v-show="activeView === 'diagram'"
          :case-data="caseData"
          :assessment="assessment"
          :hint-assignments="hintAssignments"
          :categories="categories"
          :is-loading="isLoading('case') || isLoading('assessment')"
          @open-category="openCategoryDialog"
        />

        <KaimoAssessmentView
          v-show="activeView === 'assessment'"
          :case-data="caseData"
          :assessment="assessment"
          :hint-assignments="hintAssignments"
          :categories="categories"
          :is-loading="isLoading('case') || isLoading('assessment')"
          @complete="handleAssessmentComplete"
        />
      </template>
    </div>

    <!-- Hint Assignment Dialog -->
    <KaimoHintAssignmentDialog
      v-model="showAssignmentDialog"
      :category="selectedCategory"
      :case-data="caseData"
      :assessment="assessment"
      :hint-assignments="hintAssignments"
      :categories="categories"
      @save="handleHintAssignment"
    />

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import {
  getKaimoCase,
  startKaimoAssessment,
  getKaimoAssessment,
  saveHintAssignment,
  getKaimoUserCategories
} from '@/services/kaimoApi'

import KaimoDocumentsView from './KaimoDocumentsView.vue'
import KaimoDiagramView from './KaimoDiagramView.vue'
import KaimoAssessmentView from './KaimoAssessmentView.vue'
import KaimoHintAssignmentDialog from './KaimoHintAssignmentDialog.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { hasPermission, isResearcher, fetchPermissions } = usePermissions()
const { isLoading, withLoading, setLoading } = useSkeletonLoading(['case', 'assessment'])

const caseId = computed(() => Number(route.params.id))

// Valid views for KAIMO
const validViews = ['documents', 'diagram', 'assessment']

// Initialize activeView from URL query parameter or default to 'documents'
const getInitialView = () => {
  const viewParam = route.query.view
  return validViews.includes(viewParam) ? viewParam : 'documents'
}
const activeView = ref(getInitialView())

// State
const caseData = ref(null)
const assessment = ref(null)
const hintAssignments = ref(new Map())
const categories = ref([])
const loadError = ref(null)

// Dialog state
const showAssignmentDialog = ref(false)
const selectedCategory = ref(null)

// Snackbar
const snackbar = reactive({ show: false, text: '', color: 'success' })

const showSnackbar = (text, color = 'success') => {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

// Update URL when view changes
watch(activeView, (newView) => {
  if (route.query.view !== newView) {
    router.replace({
      query: { ...route.query, view: newView }
    })
  }
})

// Update view when URL query changes (e.g., browser back/forward)
watch(() => route.query.view, (newView) => {
  if (validViews.includes(newView) && activeView.value !== newView) {
    activeView.value = newView
  }
})

const canViewKaimo = computed(() => {
  return hasPermission('feature:kaimo:view') || isResearcher.value || hasPermission('admin:kaimo:manage')
})

const loadCase = async () => {
  loadError.value = null
  await withLoading('case', async () => {
    try {
      const data = await getKaimoCase(caseId.value)
      caseData.value = data?.case

      // Start or load assessment
      if (caseData.value) {
        await loadOrStartAssessment()
      }
    } catch (err) {
      console.error('Konnte Fall nicht laden:', err)
      loadError.value = t('kaimo.case.errors.loadCase')
      throw err
    }
  })
}

const loadOrStartAssessment = async () => {
  await withLoading('assessment', async () => {
    try {
      // Try to start assessment (will return existing if already started)
      const result = await startKaimoAssessment(caseId.value)
      assessment.value = result.assessment

      // Load existing hint assignments
      if (assessment.value?.id) {
        const assessmentData = await getKaimoAssessment(assessment.value.id)
        if (assessmentData?.assessment?.hint_assignments) {
          // Convert array to Map for easier lookup
          const assignmentMap = new Map()
          assessmentData.assessment.hint_assignments.forEach(assignment => {
            assignmentMap.set(assignment.hint_id, {
              category_id: assignment.assigned_category_id,
              subcategory_id: assignment.assigned_subcategory_id,
              rating: assignment.rating
            })
          })
          hintAssignments.value = assignmentMap
        }
      }

      // Load categories
      const catData = await getKaimoUserCategories()
      categories.value = catData?.categories || []
    } catch (err) {
      console.error('Konnte Bewertung nicht laden oder starten:', err)
    }
  })
}

const openCategoryDialog = (category) => {
  selectedCategory.value = category
  showAssignmentDialog.value = true
}

const handleHintAssignment = async (hintId, assignmentData) => {
  if (!assessment.value?.id) return

  try {
    await saveHintAssignment(assessment.value.id, hintId, {
      assigned_category_id: assignmentData.category_id,
      assigned_subcategory_id: assignmentData.subcategory_id,
      rating: assignmentData.rating
    })

    // Update local state
    hintAssignments.value.set(hintId, {
      category_id: assignmentData.category_id,
      subcategory_id: assignmentData.subcategory_id,
      rating: assignmentData.rating
    })

    // Force reactivity
    hintAssignments.value = new Map(hintAssignments.value)

    showSnackbar(t('kaimo.case.snackbar.hintSaved'), 'success')
  } catch (err) {
    console.error('Konnte Hinweiszuweisung nicht speichern:', err)
    showSnackbar(t('kaimo.case.snackbar.hintSaveError'), 'error')
  }
}

const handleAssessmentComplete = () => {
  showSnackbar(t('kaimo.case.snackbar.assessmentComplete'), 'success')
  setTimeout(() => {
    router.push({ name: 'KaimoPanel' })
  }, 2000)
}

onMounted(async () => {
  try {
    await fetchPermissions(true)
    if (canViewKaimo.value) {
      await loadCase()
    } else {
      loadError.value = t('kaimo.case.errors.noAccess', { permission: 'feature:kaimo:view' })
    }
  } catch (err) {
    console.error('KAIMO-Fall-Ladefehler:', err)
    loadError.value = t('kaimo.case.errors.loadFailure')
    setLoading('case', false)
    setLoading('assessment', false)
  }
})
</script>

<style scoped>
.kaimo-case-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: #f8fafc; /* slate-50 like prototype */
}

/* Sidebar - exactly like prototype */
.kaimo-sidebar {
  width: 80px;
  flex-shrink: 0;
  background-color: #1f2937; /* gray-800 */
  display: flex;
  flex-direction: column;
}

.kaimo-logo {
  width: 100%;
  aspect-ratio: 1;
  background-color: #6366f1; /* indigo-500 */
  display: flex;
  align-items: center;
  justify-content: center;
}

.kaimo-nav {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 12px;
  aspect-ratio: 1;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  color: #cbd5e1; /* slate-300 */
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.nav-item-active {
  background-color: rgba(255, 255, 255, 0.05);
  color: #6366f1; /* indigo-500 when active */
}

/* Content Area */
.kaimo-content {
  flex-grow: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 100%;
}
</style>
