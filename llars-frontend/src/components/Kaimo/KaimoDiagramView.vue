<template>
  <div class="diagram-view">
    <v-skeleton-loader
      v-if="isLoading"
      type="card@4"
      class="pa-8"
    />
    <template v-else>
      <div class="diagram-container">
        <!-- Top Left: Grundversorgung -->
        <div
          class="category-card category-top-left"
          @click="openCategory(categoryMapping.grundversorgung)"
        >
          <span class="category-title">{{ categoryMapping.grundversorgung?.display_name || $t('kaimo.diagram.categories.basicCare') }}</span>
          <span class="category-hints">{{ getOpenHintCount(categoryMapping.grundversorgung?.id) }} {{ $t('kaimo.diagram.hints.open') }}</span>
          <div class="category-stats">
            <span class="stat-chip stat-risk">{{ getRiskCount(categoryMapping.grundversorgung?.id) }} {{ $t('kaimo.ratings.riskPlural') }}</span>
            <span class="stat-chip stat-resource">{{ getResourceCount(categoryMapping.grundversorgung?.id) }} {{ $t('kaimo.ratings.resourcePlural') }}</span>
            <span class="stat-chip stat-unclear">{{ getUnclearCount(categoryMapping.grundversorgung?.id) }} {{ $t('kaimo.ratings.unclear') }}</span>
          </div>
        </div>

        <!-- Top Right: Familiensituation -->
        <div
          class="category-card category-top-right"
          @click="openCategory(categoryMapping.familiensituation)"
        >
          <span class="category-title">{{ categoryMapping.familiensituation?.display_name || $t('kaimo.diagram.categories.family') }}</span>
          <span class="category-hints">{{ getOpenHintCount(categoryMapping.familiensituation?.id) }} {{ $t('kaimo.diagram.hints.open') }}</span>
          <div class="category-stats">
            <span class="stat-chip stat-risk">{{ getRiskCount(categoryMapping.familiensituation?.id) }} {{ $t('kaimo.ratings.riskPlural') }}</span>
            <span class="stat-chip stat-resource">{{ getResourceCount(categoryMapping.familiensituation?.id) }} {{ $t('kaimo.ratings.resourcePlural') }}</span>
            <span class="stat-chip stat-unclear">{{ getUnclearCount(categoryMapping.familiensituation?.id) }} {{ $t('kaimo.ratings.unclear') }}</span>
          </div>
        </div>

        <!-- Center: Child Name -->
        <span class="center-name">{{ childName }}</span>

        <!-- Bottom Left: Entwicklung -->
        <div
          class="category-card category-bottom-left"
          @click="openCategory(categoryMapping.entwicklung)"
        >
          <span class="category-title">{{ categoryMapping.entwicklung?.display_name || $t('kaimo.diagram.categories.development') }}</span>
          <span class="category-hints">{{ getOpenHintCount(categoryMapping.entwicklung?.id) }} {{ $t('kaimo.diagram.hints.open') }}</span>
          <div class="category-stats">
            <span class="stat-chip stat-risk">{{ getRiskCount(categoryMapping.entwicklung?.id) }} {{ $t('kaimo.ratings.riskPlural') }}</span>
            <span class="stat-chip stat-resource">{{ getResourceCount(categoryMapping.entwicklung?.id) }} {{ $t('kaimo.ratings.resourcePlural') }}</span>
            <span class="stat-chip stat-unclear">{{ getUnclearCount(categoryMapping.entwicklung?.id) }} {{ $t('kaimo.ratings.unclear') }}</span>
          </div>
        </div>

        <!-- Bottom Right: Eltern -->
        <div
          class="category-card category-bottom-right"
          @click="openCategory(categoryMapping.eltern)"
        >
          <span class="category-title">{{ categoryMapping.eltern?.display_name || $t('kaimo.diagram.categories.parents') }}</span>
          <span class="category-hints">{{ getOpenHintCount(categoryMapping.eltern?.id) }} {{ $t('kaimo.diagram.hints.open') }}</span>
          <div class="category-stats">
            <span class="stat-chip stat-risk">{{ getRiskCount(categoryMapping.eltern?.id) }} {{ $t('kaimo.ratings.riskPlural') }}</span>
            <span class="stat-chip stat-resource">{{ getResourceCount(categoryMapping.eltern?.id) }} {{ $t('kaimo.ratings.resourcePlural') }}</span>
            <span class="stat-chip stat-unclear">{{ getUnclearCount(categoryMapping.eltern?.id) }} {{ $t('kaimo.ratings.unclear') }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

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

const emit = defineEmits(['open-category'])
const { t } = useI18n()

// Get child name from case data
const childName = computed(() => {
  return props.caseData?.display_name || t('kaimo.common.childFallback')
})

// Get all hints
const hints = computed(() => props.caseData?.hints || [])

// Map categories to fixed positions
const categoryMapping = computed(() => {
  const cats = props.categories || props.caseData?.categories || []

  const findCategory = (searchTerms) => {
    return cats.find(cat =>
      searchTerms.some(term => cat.display_name?.toLowerCase().includes(term.toLowerCase()))
    )
  }

  return {
    grundversorgung: findCategory(['grundversorgung']) || cats[0],
    entwicklung: findCategory(['entwicklung']) || cats[1],
    familiensituation: findCategory(['familiensituation', 'familie']) || cats[2],
    eltern: findCategory(['eltern', 'erziehung']) || cats[3]
  }
})

// Count unassigned hints for a specific category
// Hints can have an expected_category_id that determines which category they belong to
const getOpenHintCount = (categoryId) => {
  if (!categoryId) return 0

  // Count hints that:
  // 1. Have expected_category_id matching this category, OR
  // 2. Are not yet assigned and could belong to this category
  let count = 0
  hints.value.forEach(hint => {
    const isAssigned = props.hintAssignments.has(hint.id)
    const assignment = props.hintAssignments.get(hint.id)

    // If hint has expected_category_id matching this category and not assigned
    if (hint.expected_category_id === categoryId && !isAssigned) {
      count++
    }
    // Or if hint has no expected category and is not assigned (distribute evenly would be complex)
    // For now, only count hints with matching expected_category_id
  })

  // If no expected categories set, fall back to distributing unassigned hints
  if (count === 0) {
    const unassignedHints = hints.value.filter(h => !props.hintAssignments.has(h.id))
    // Distribute unassigned hints across categories based on position
    const cats = props.categories || []
    const catIndex = cats.findIndex(c => c.id === categoryId)
    if (catIndex >= 0 && cats.length > 0) {
      // Simple distribution: divide hints by number of categories
      const hintsPerCat = Math.ceil(unassignedHints.length / cats.length)
      const start = catIndex * hintsPerCat
      const end = Math.min(start + hintsPerCat, unassignedHints.length)
      count = Math.max(0, end - start)
    }
  }

  return count
}

// Get risk count for category
const getRiskCount = (categoryId) => {
  if (!categoryId) return 0

  let count = 0
  props.hintAssignments.forEach((assignment) => {
    if (assignment.category_id === categoryId && assignment.rating === 'risk') {
      count++
    }
  })
  return count
}

// Get resource count for category
const getResourceCount = (categoryId) => {
  if (!categoryId) return 0

  let count = 0
  props.hintAssignments.forEach((assignment) => {
    if (assignment.category_id === categoryId && assignment.rating === 'resource') {
      count++
    }
  })
  return count
}

// Get unclear count for category
const getUnclearCount = (categoryId) => {
  if (!categoryId) return 0

  let count = 0
  props.hintAssignments.forEach((assignment) => {
    if (assignment.category_id === categoryId && assignment.rating === 'unclear') {
      count++
    }
  })
  return count
}

const openCategory = (category) => {
  if (category) {
    emit('open-category', category)
  }
}
</script>

<style scoped>
.diagram-view {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: #f8fafc;
}

.diagram-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Category Cards - exactly like prototype */
.category-card {
  position: absolute;
  max-width: 320px;
  background-color: white;
  padding: 12px 16px;
  border-radius: 6px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.category-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* Position cards exactly like prototype */
.category-top-left {
  bottom: 70%;
  right: 65%;
}

.category-top-right {
  bottom: 70%;
  left: 65%;
}

.category-bottom-left {
  top: 70%;
  right: 65%;
}

.category-bottom-right {
  top: 70%;
  left: 65%;
}

.category-title {
  font-size: 18px;
  font-weight: 500;
  color: #64748b;
}

.category-hints {
  font-size: 16px;
  color: #1e293b;
}

.category-stats {
  display: flex;
  gap: 8px;
}

.stat-chip {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  color: white;
}

.stat-risk {
  background-color: #f43f5e; /* rose-500 */
}

.stat-resource {
  background-color: #10b981; /* emerald-500 */
}

.stat-unclear {
  background-color: #64748b; /* slate-500 */
}

/* Center Name */
.center-name {
  font-size: 24px;
  font-weight: 500;
  color: #94a3b8;
}

/* Responsive adjustments */
@media (max-width: 1400px) {
  .category-card {
    max-width: 260px;
    padding: 10px 14px;
  }

  .category-title {
    font-size: 16px;
  }

  .category-hints {
    font-size: 14px;
  }

  .stat-chip {
    font-size: 12px;
    padding: 3px 6px;
  }
}

@media (max-width: 1100px) {
  .category-top-left,
  .category-top-right {
    bottom: 60%;
  }

  .category-bottom-left,
  .category-bottom-right {
    top: 60%;
  }

  .category-top-left,
  .category-bottom-left {
    right: 55%;
  }

  .category-top-right,
  .category-bottom-right {
    left: 55%;
  }
}
</style>
