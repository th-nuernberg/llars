<template>
  <div class="evaluator-comparison">
    <!-- Header -->
    <div class="comparison-header">
      <h3 class="comparison-title">
        <LIcon size="20" class="mr-2">mdi-compare</LIcon>
        {{ $t('evaluationAssistant.comparison.title') }}
      </h3>
      <LBtn
        variant="text"
        size="small"
        prepend-icon="mdi-refresh"
        @click="fetchComparison"
        :loading="loading"
      >
        {{ $t('common.refresh') }}
      </LBtn>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !comparisonData" class="loading-state">
      <v-progress-circular indeterminate size="32" />
    </div>

    <!-- No Data State -->
    <div v-else-if="!comparisonData || evaluators.length < 2" class="empty-state">
      <LIcon size="48" color="grey">mdi-account-question</LIcon>
      <p class="mt-4 text-medium-emphasis">{{ $t('evaluationAssistant.comparison.needMoreEvaluators') }}</p>
    </div>

    <!-- Comparison Grid -->
    <div v-else class="comparison-content">
      <!-- Evaluator Selector -->
      <div class="evaluator-selectors">
        <v-select
          v-model="selectedEvaluator1"
          :items="evaluators"
          item-title="name"
          item-value="id"
          :label="$t('evaluationAssistant.comparison.evaluator1')"
          variant="outlined"
          density="compact"
          class="evaluator-select"
        >
          <template #selection="{ item }">
            <div class="evaluator-selection">
              <LIcon size="16" class="mr-1">{{ item.raw.is_llm ? 'mdi-robot' : 'mdi-account' }}</LIcon>
              {{ item.raw.name }}
            </div>
          </template>
        </v-select>

        <LIcon size="24" color="grey">mdi-arrow-left-right</LIcon>

        <v-select
          v-model="selectedEvaluator2"
          :items="evaluators"
          item-title="name"
          item-value="id"
          :label="$t('evaluationAssistant.comparison.evaluator2')"
          variant="outlined"
          density="compact"
          class="evaluator-select"
        >
          <template #selection="{ item }">
            <div class="evaluator-selection">
              <LIcon size="16" class="mr-1">{{ item.raw.is_llm ? 'mdi-robot' : 'mdi-account' }}</LIcon>
              {{ item.raw.name }}
            </div>
          </template>
        </v-select>
      </div>

      <!-- Agreement Summary -->
      <div v-if="pairwiseAgreement !== null" class="agreement-summary">
        <div class="agreement-label">{{ $t('evaluationAssistant.comparison.agreementRate') }}</div>
        <div class="agreement-value" :class="agreementClass">{{ pairwiseAgreement }}%</div>
        <v-progress-linear
          :model-value="pairwiseAgreement"
          :color="agreementColor"
          height="6"
          rounded
          class="mt-2"
        />
      </div>

      <!-- Comparison Table -->
      <div v-if="comparisonItems.length > 0" class="comparison-table">
        <div class="table-header">
          <div class="col-thread">{{ $t('evaluationAssistant.comparison.thread') }}</div>
          <div class="col-eval">{{ evaluator1Name }}</div>
          <div class="col-eval">{{ evaluator2Name }}</div>
          <div class="col-match">{{ $t('evaluationAssistant.comparison.match') }}</div>
        </div>
        <div class="table-body">
          <div
            v-for="item in comparisonItems"
            :key="item.thread_id"
            class="table-row"
            :class="{ 'row-match': item.matches, 'row-mismatch': !item.matches }"
          >
            <div class="col-thread">
              <span class="thread-name">{{ item.thread_name || `Thread #${item.thread_id}` }}</span>
            </div>
            <div class="col-eval">
              <ResultBadge v-if="item.eval1" :result="item.eval1" />
              <span v-else class="text-medium-emphasis">-</span>
            </div>
            <div class="col-eval">
              <ResultBadge v-if="item.eval2" :result="item.eval2" />
              <span v-else class="text-medium-emphasis">-</span>
            </div>
            <div class="col-match">
              <LIcon
                :color="item.matches ? 'success' : 'error'"
                size="20"
              >
                {{ item.matches ? 'mdi-check-circle' : 'mdi-close-circle' }}
              </LIcon>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import ResultBadge from './ResultBadge.vue'

const props = defineProps({
  results: {
    type: Array,
    default: () => []
  },
  scenarioId: {
    type: [String, Number],
    required: true
  }
})

const loading = ref(false)
const comparisonData = ref(null)
const selectedEvaluator1 = ref(null)
const selectedEvaluator2 = ref(null)

// Extract unique evaluators from results
const evaluators = computed(() => {
  const evalMap = new Map()
  props.results.forEach(r => {
    const id = r.is_llm_evaluation ? `llm_${r.model_id}` : `user_${r.user_id}`
    if (!evalMap.has(id)) {
      evalMap.set(id, {
        id,
        name: r.evaluator_name || (r.is_llm_evaluation ? r.model_id : `User #${r.user_id}`),
        is_llm: r.is_llm_evaluation
      })
    }
  })
  return Array.from(evalMap.values())
})

const evaluator1Name = computed(() => {
  const eval1 = evaluators.value.find(e => e.id === selectedEvaluator1.value)
  return eval1?.name || '-'
})

const evaluator2Name = computed(() => {
  const eval2 = evaluators.value.find(e => e.id === selectedEvaluator2.value)
  return eval2?.name || '-'
})

// Generate comparison items
const comparisonItems = computed(() => {
  if (!selectedEvaluator1.value || !selectedEvaluator2.value) return []

  const items = []
  const threadMap = new Map()

  // Group results by thread
  props.results.forEach(r => {
    const evalId = r.is_llm_evaluation ? `llm_${r.model_id}` : `user_${r.user_id}`
    if (!threadMap.has(r.thread_id)) {
      threadMap.set(r.thread_id, { thread_id: r.thread_id, thread_name: r.thread_name })
    }
    const thread = threadMap.get(r.thread_id)
    if (evalId === selectedEvaluator1.value) {
      thread.eval1 = r
    } else if (evalId === selectedEvaluator2.value) {
      thread.eval2 = r
    }
  })

  // Calculate matches
  threadMap.forEach((thread) => {
    if (thread.eval1 || thread.eval2) {
      thread.matches = compareResults(thread.eval1, thread.eval2)
      items.push(thread)
    }
  })

  return items
})

// Calculate pairwise agreement
const pairwiseAgreement = computed(() => {
  if (comparisonItems.value.length === 0) return null
  const matches = comparisonItems.value.filter(i => i.matches).length
  return Math.round((matches / comparisonItems.value.length) * 100)
})

const agreementClass = computed(() => {
  if (pairwiseAgreement.value === null) return ''
  if (pairwiseAgreement.value >= 80) return 'agreement-excellent'
  if (pairwiseAgreement.value >= 60) return 'agreement-good'
  if (pairwiseAgreement.value >= 40) return 'agreement-moderate'
  return 'agreement-poor'
})

const agreementColor = computed(() => {
  if (pairwiseAgreement.value === null) return 'grey'
  if (pairwiseAgreement.value >= 80) return 'success'
  if (pairwiseAgreement.value >= 60) return 'info'
  if (pairwiseAgreement.value >= 40) return 'warning'
  return 'error'
})

// Compare two results for match
function compareResults(result1, result2) {
  if (!result1 || !result2) return false

  // Different comparison based on task type
  const taskType = result1.task_type

  switch (taskType) {
    case 'ranking':
      // Compare bucket assignments
      return compareRankings(result1.buckets, result2.buckets)
    case 'rating':
    case 'mail_rating':
      // Compare average ratings (within 0.5)
      const avg1 = getAverageRating(result1)
      const avg2 = getAverageRating(result2)
      return Math.abs(avg1 - avg2) <= 0.5
    case 'authenticity':
      return result1.vote === result2.vote
    case 'comparison':
      return result1.winner === result2.winner
    case 'text_classification':
    case 'labeling':
      return result1.label === result2.label
    default:
      return false
  }
}

function compareRankings(buckets1, buckets2) {
  if (!buckets1 || !buckets2) return false
  // Simplified: check if gut/schlecht classifications match
  const gut1 = new Set(buckets1.gut?.feature_ids || [])
  const gut2 = new Set(buckets2.gut?.feature_ids || [])
  const schlecht1 = new Set(buckets1.schlecht?.feature_ids || [])
  const schlecht2 = new Set(buckets2.schlecht?.feature_ids || [])

  // Check if most items are in same buckets
  const overlap = [...gut1].filter(x => gut2.has(x)).length + [...schlecht1].filter(x => schlecht2.has(x)).length
  const total = Math.max(gut1.size + schlecht1.size, gut2.size + schlecht2.size)

  return total === 0 || (overlap / total) >= 0.6
}

function getAverageRating(result) {
  if (result.task_type === 'mail_rating') {
    return result.overall_rating || 0
  }
  if (result.ratings?.length) {
    return result.ratings.reduce((sum, r) => sum + r.rating, 0) / result.ratings.length
  }
  return result.average_rating || 0
}

async function fetchComparison() {
  loading.value = true
  try {
    const response = await axios.get(`/api/evaluation/${props.scenarioId}/comparison`)
    comparisonData.value = response.data
  } catch (err) {
    console.error('Error fetching comparison:', err)
  } finally {
    loading.value = false
  }
}

// Auto-select first two evaluators
watch(evaluators, (evals) => {
  if (evals.length >= 2) {
    if (!selectedEvaluator1.value) selectedEvaluator1.value = evals[0].id
    if (!selectedEvaluator2.value) selectedEvaluator2.value = evals[1].id
  }
}, { immediate: true })

onMounted(() => {
  if (props.scenarioId) {
    fetchComparison()
  }
})
</script>

<style scoped>
.evaluator-comparison {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.comparison-title {
  display: flex;
  align-items: center;
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.comparison-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.evaluator-selectors {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.evaluator-select {
  flex: 1;
}

.evaluator-selection {
  display: flex;
  align-items: center;
}

.agreement-summary {
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 12px;
  margin-bottom: 16px;
  text-align: center;
}

.agreement-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 4px;
}

.agreement-value {
  font-size: 2rem;
  font-weight: 700;
}

.agreement-excellent { color: #4CAF50; }
.agreement-good { color: #2196F3; }
.agreement-moderate { color: #FFC107; }
.agreement-poor { color: #F44336; }

.comparison-table {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 8px;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr auto;
  gap: 8px;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.table-body {
  flex: 1;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr auto;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  align-items: center;
}

.table-row:last-child {
  border-bottom: none;
}

.row-match {
  background: rgba(76, 175, 80, 0.05);
}

.row-mismatch {
  background: rgba(244, 67, 54, 0.05);
}

.col-thread {
  font-size: 0.875rem;
}

.col-eval {
  display: flex;
  justify-content: center;
}

.col-match {
  display: flex;
  justify-content: center;
}
</style>
