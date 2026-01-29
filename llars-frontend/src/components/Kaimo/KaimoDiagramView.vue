<template>
  <div class="diagram-view" ref="diagramViewRef">
    <v-skeleton-loader
      v-if="isLoading"
      type="card@4"
      class="pa-8"
    />
    <template v-else>
      <div class="diagram-container" ref="containerRef">
        <!-- SVG for connection lines -->
        <svg class="connection-lines" ref="svgRef">
          <line
            v-for="line in connectionLines"
            :key="line.id"
            :x1="line.x1"
            :y1="line.y1"
            :x2="line.x2"
            :y2="line.y2"
            class="connection-line"
          />
        </svg>

        <!-- Top Left: Grundversorgung -->
        <div
          ref="cardTopLeft"
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
          ref="cardTopRight"
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
        <span ref="centerNameRef" class="center-name">{{ childName }}</span>

        <!-- Bottom Left: Entwicklung -->
        <div
          ref="cardBottomLeft"
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
          ref="cardBottomRight"
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
import { computed, ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'

// Refs for DOM elements
const diagramViewRef = ref(null)
const containerRef = ref(null)
const svgRef = ref(null)
const centerNameRef = ref(null)
const cardTopLeft = ref(null)
const cardTopRight = ref(null)
const cardBottomLeft = ref(null)
const cardBottomRight = ref(null)

// Connection lines data
const connectionLines = ref([])

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

// Calculate connection lines from cards to center
const calculateLines = () => {
  if (!containerRef.value || !centerNameRef.value) return

  const container = containerRef.value.getBoundingClientRect()
  const center = centerNameRef.value.getBoundingClientRect()

  // Calculate center point relative to container
  const centerX = center.left - container.left + center.width / 2
  const centerY = center.top - container.top + center.height / 2

  const cards = [
    { ref: cardTopLeft.value, id: 'topLeft', corner: 'bottomRight' },
    { ref: cardTopRight.value, id: 'topRight', corner: 'bottomLeft' },
    { ref: cardBottomLeft.value, id: 'bottomLeft', corner: 'topRight' },
    { ref: cardBottomRight.value, id: 'bottomRight', corner: 'topLeft' }
  ]

  const lines = []

  cards.forEach(({ ref: cardRef, id, corner }) => {
    if (!cardRef) return

    const card = cardRef.getBoundingClientRect()
    let cardX, cardY

    // Calculate the point on the card closest to center
    switch (corner) {
      case 'bottomRight':
        cardX = card.right - container.left
        cardY = card.bottom - container.top
        break
      case 'bottomLeft':
        cardX = card.left - container.left
        cardY = card.bottom - container.top
        break
      case 'topRight':
        cardX = card.right - container.left
        cardY = card.top - container.top
        break
      case 'topLeft':
        cardX = card.left - container.left
        cardY = card.top - container.top
        break
    }

    lines.push({
      id,
      x1: cardX,
      y1: cardY,
      x2: centerX,
      y2: centerY
    })
  })

  connectionLines.value = lines
}

// Resize observer to recalculate lines on window resize
let resizeObserver = null

onMounted(() => {
  nextTick(() => {
    calculateLines()

    // Set up resize observer
    if (diagramViewRef.value) {
      resizeObserver = new ResizeObserver(() => {
        calculateLines()
      })
      resizeObserver.observe(diagramViewRef.value)
    }
  })

  // Also listen to window resize
  window.addEventListener('resize', calculateLines)
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  window.removeEventListener('resize', calculateLines)
})

// Recalculate when loading state changes
watch(() => props.isLoading, (newVal, oldVal) => {
  if (oldVal && !newVal) {
    nextTick(() => {
      calculateLines()
    })
  }
})
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

/* SVG for connection lines */
.connection-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.connection-line {
  stroke: #cbd5e1; /* slate-300 */
  stroke-width: 2;
  stroke-dasharray: 8 4;
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
  z-index: 1;
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
  z-index: 1;
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
