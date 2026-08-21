<template>
  <div class="overview-tab">
    <!-- Quick Actions -->
    <div class="section">
      <h3 class="section-title">{{ $t('scenarioManager.overview.quickActions') }}</h3>
      <div class="actions-grid">
        <div class="action-card" @click="$emit('import-data')">
          <div class="action-icon" style="background-color: rgba(136, 196, 200, 0.15);">
            <LIcon color="#88c4c8" size="28">mdi-database-import-outline</LIcon>
          </div>
          <div class="action-content">
            <h4>{{ $t('scenarioManager.overview.importData') }}</h4>
            <p>{{ $t('scenarioManager.overview.importDataDesc') }}</p>
          </div>
          <LIcon class="action-arrow">mdi-chevron-right</LIcon>
        </div>

        <div class="action-card" @click="$emit('start-evaluation')">
          <div class="action-icon" style="background-color: rgba(176, 202, 151, 0.15);">
            <LIcon color="#b0ca97" size="28">mdi-robot-outline</LIcon>
          </div>
          <div class="action-content">
            <h4>{{ $t('scenarioManager.overview.llmEvaluation') }}</h4>
            <p>{{ $t('scenarioManager.overview.llmEvaluationDesc') }}</p>
          </div>
          <LIcon class="action-arrow">mdi-chevron-right</LIcon>
        </div>

        <div class="action-card" @click="$emit('view-results')">
          <div class="action-icon" style="background-color: rgba(209, 188, 138, 0.15);">
            <LIcon color="#D1BC8A" size="28">mdi-chart-bar</LIcon>
          </div>
          <div class="action-content">
            <h4>{{ $t('scenarioManager.overview.viewResults') }}</h4>
            <p>{{ $t('scenarioManager.overview.viewResultsDesc') }}</p>
          </div>
          <LIcon class="action-arrow">mdi-chevron-right</LIcon>
        </div>
      </div>
    </div>

    <!-- Progress Overview -->
    <div class="section">
      <div class="section-header">
        <h3 class="section-title">{{ $t('scenarioManager.overview.progress') }}</h3>
        <span v-if="liveStats?.connected" class="live-badge">
          <span class="live-dot"></span>
          Live
        </span>
      </div>
      <div class="progress-cards">
        <!-- Human Evaluators Progress -->
        <div class="progress-card" v-if="hasHumans">
          <div class="progress-header">
            <LIcon color="primary">mdi-account-multiple-outline</LIcon>
            <span>{{ $t('scenarioManager.overview.humanEvaluators') }}</span>
          </div>
          <div class="progress-bar-large">
            <div
              class="progress-fill"
              :style="{ width: humanProgress + '%' }"
            ></div>
          </div>
          <div class="progress-details">
            <span>{{ humanDone }} / {{ humanTotal }}</span>
            <span class="progress-percent">{{ humanProgress }}%</span>
          </div>
        </div>

        <!-- LLM Evaluators Progress -->
        <div class="progress-card" v-if="hasLLMs">
          <div class="progress-header">
            <LIcon color="accent">mdi-robot-outline</LIcon>
            <span>{{ $t('scenarioManager.overview.llmEvaluators') }}</span>
          </div>
          <div class="progress-bar-large">
            <div
              class="progress-fill llm"
              :style="{ width: llmProgressPercent + '%' }"
            ></div>
            <div
              v-if="llmErrors > 0"
              class="progress-fill error"
              :style="{ width: llmErrorPercent + '%' }"
            ></div>
          </div>
          <div class="progress-details">
            <span>{{ llmDone }} / {{ llmTotal }}</span>
            <span v-if="llmErrors > 0" class="progress-errors">
              <LIcon size="14" color="#e8a087">mdi-alert-circle</LIcon>
              {{ llmErrors }} {{ $t('scenarioManager.overview.failed') }}
            </span>
            <span class="progress-percent">{{ llmProgressPercent }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Parts / Phases (labeling, manager view only): read-only structure +
         per-part progress. The endpoint enforces management access, so this
         section can never render for assessors (invisibility invariant);
         lock/unlock lives in the settings tab. -->
    <div class="section" v-if="partsStatus?.enabled && partsStatus.parts?.length">
      <div class="section-header">
        <h3 class="section-title">
          {{ $t('scenarioManager.evalConfig.labeling.parts.title') }}
        </h3>
        <LTooltip :text="$t('scenarioManager.evalConfig.labeling.parts.settingsTooltip')" location="left">
          <LIcon size="16" class="section-help-icon">mdi-help-circle-outline</LIcon>
        </LTooltip>
      </div>
      <div class="parts-overview-list">
        <div
          v-for="(part, index) in partsStatus.parts"
          :key="part.id"
          class="parts-overview-row"
        >
          <LTag size="small" variant="info">{{ index + 1 }}</LTag>
          <span class="parts-overview-name">{{ part.name }}</span>
          <LTag size="small" variant="default">
            {{ part.item_count }} {{ $t('scenarioManager.evalConfig.labeling.parts.items') }}
          </LTag>
          <LTag v-if="part.order === 'random'" size="small" variant="info">
            {{ $t('scenarioManager.evalConfig.labeling.parts.orderRandom') }}
          </LTag>
          <LTag v-if="part.copilot" size="small" variant="info">
            <LIcon size="12" class="mr-1">mdi-robot-outline</LIcon>
            {{ $t('scenarioManager.evalConfig.labeling.copilot.title') }}
          </LTag>
          <LTag :variant="part.locked ? 'warning' : 'success'" size="small">
            <LIcon size="12" class="mr-1">
              {{ part.locked ? 'mdi-lock-outline' : 'mdi-lock-open-variant-outline' }}
            </LIcon>
            {{ part.locked
              ? $t('scenarioManager.evalConfig.labeling.parts.locked')
              : $t('scenarioManager.evalConfig.labeling.parts.open') }}
          </LTag>
          <div class="parts-overview-progress">
            <div class="progress-bar-large">
              <div class="progress-fill" :style="{ width: partProgressPercent(part) + '%' }"></div>
            </div>
            <span class="parts-overview-count">{{ partProgressLabel(part) }}</span>
          </div>
          <!-- Lock/unlock the phase directly here (study gate between phases).
               Same management-gated PUT as the settings tab; the section only
               renders for managers, so no extra role check is needed. -->
          <LBtn
            class="parts-overview-action"
            size="small"
            :variant="part.locked ? 'primary' : 'secondary'"
            :loading="partsUpdating === part.id"
            @click="updatePartLocked(part)"
          >
            <LIcon size="16" class="mr-1">
              {{ part.locked ? 'mdi-lock-open-variant-outline' : 'mdi-lock-outline' }}
            </LIcon>
            {{ part.locked
              ? $t('scenarioManager.evalConfig.labeling.parts.unlock')
              : $t('scenarioManager.evalConfig.labeling.parts.lock') }}
          </LBtn>
        </div>
      </div>
    </div>

    <!-- Evaluator Progress Details -->
    <div class="section" v-if="userStatsList.length > 0">
      <div class="section-title-row" style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
        <h3 class="section-title">{{ $t('scenarioManager.overview.evaluatorProgress') || 'Evaluator Progress' }}</h3>
        <!-- Origin legend: referral-link color -> source label -->
        <LOriginLegend :origins="humanOrigins" />
      </div>
      <div class="evaluators-list">
        <div
          v-for="user in userStatsList"
          :key="user.id"
          class="evaluator-row"
        >
          <div class="evaluator-info">
            <div class="evaluator-avatar" :class="{ 'is-llm': user.isLLM }">
              <LIcon size="18">{{ user.isLLM ? 'mdi-robot-outline' : 'mdi-account' }}</LIcon>
            </div>
            <div class="evaluator-name">
              <span class="name">{{ user.name }}</span>
              <span class="role-badge" :class="user.role.toLowerCase()">{{ user.role }}</span>
              <!-- Where this human evaluator came from (LLMs have no origin) -->
              <LUserOrigin v-if="!user.isLLM" :origin="originFor(user.name)" size="sm" />
            </div>
          </div>
          <div class="evaluator-stats">
            <div class="stat">
              <span class="stat-value">{{ user.completed }}</span>
              <span class="stat-label">{{ $t('scenarioManager.overview.done') || 'Done' }}</span>
            </div>
            <div class="stat" v-if="user.inProgress > 0">
              <span class="stat-value in-progress">{{ user.inProgress }}</span>
              <span class="stat-label">{{ $t('scenarioManager.overview.inProgress') || 'In Progress' }}</span>
            </div>
            <div class="stat">
              <span class="stat-value pending">{{ user.notStarted }}</span>
              <span class="stat-label">{{ $t('scenarioManager.overview.pending') || 'Pending' }}</span>
            </div>
            <div class="stat" v-if="user.isLLM && user.errorCount > 0">
              <span class="stat-value failed">{{ user.errorCount }}</span>
              <span class="stat-label">{{ $t('scenarioManager.overview.failed') || 'Failed' }}</span>
            </div>
            <div class="stat" v-if="user.accuracy !== null && user.accuracy !== undefined">
              <span class="stat-value accuracy" :class="getAccuracyClass(user.accuracy)">{{ user.accuracy }}%</span>
              <span class="stat-label">{{ $t('scenarioManager.overview.accuracy') || 'Accuracy' }}</span>
            </div>
            <div class="stat" v-if="user.f1Score !== null && user.f1Score !== undefined">
              <span class="stat-value f1" :class="getF1Class(user.f1Score)">{{ user.f1Score }}%</span>
              <span class="stat-label">F1</span>
            </div>
          </div>
          <div class="evaluator-progress">
            <div class="progress-bar-small">
              <div
                class="progress-fill"
                :class="{ 'is-llm': user.isLLM }"
                :style="{ width: user.progress + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ user.progress }}%</span>
          </div>
        </div>

        <div v-if="userStatsList.length === 0" class="empty-state">
          <LIcon size="40" color="grey-lighten-1">mdi-account-group-outline</LIcon>
          <p>{{ $t('scenarioManager.overview.noEvaluators') || 'No evaluators yet' }}</p>
        </div>
      </div>
    </div>

    <!-- Scenario Details -->
    <div class="section">
      <h3 class="section-title">{{ $t('scenarioManager.overview.details') }}</h3>
      <div class="details-card">
        <div class="detail-row">
          <span class="detail-label">{{ $t('scenarioManager.overview.type') }}</span>
          <span class="detail-value">{{ typeName }}</span>
        </div>
        <div class="detail-row" v-if="scenario?.description">
          <span class="detail-label">{{ $t('scenarioManager.overview.description') }}</span>
          <div class="detail-value detail-value--markdown">
            <LMarkdownContent :markdown="scenario.description" compact />
          </div>
        </div>
        <div class="detail-row" v-if="scenarioTaskDescription">
          <span class="detail-label">{{ $t('scenarioManager.overview.taskDescription') }}</span>
          <span class="detail-value">{{ scenarioTaskDescription }}</span>
        </div>
        <div class="detail-row" v-if="scenarioEvaluationCriteria.length > 0">
          <span class="detail-label">{{ $t('scenarioManager.overview.evaluationCriteria') }}</span>
          <span class="detail-value">
            <div class="d-flex flex-wrap gap-1 justify-end">
              <v-chip
                v-for="criterion in scenarioEvaluationCriteria"
                :key="criterion"
                size="x-small"
                variant="tonal"
              >
                {{ criterion }}
              </v-chip>
            </div>
          </span>
        </div>
        <div class="detail-row">
          <span class="detail-label">{{ $t('scenarioManager.overview.created') }}</span>
          <span class="detail-value">{{ formatDate(scenario?.created_at) }}</span>
        </div>
        <div class="detail-row" v-if="scenario?.begin || scenario?.end">
          <span class="detail-label">{{ $t('scenarioManager.overview.period') }}</span>
          <span class="detail-value">
            {{ formatDate(scenario?.begin) || '-' }} – {{ formatDate(scenario?.end) || '-' }}
          </span>
        </div>
        <div class="detail-row">
          <span class="detail-label">{{ $t('scenarioManager.overview.distribution') }}</span>
          <span class="detail-value">
            {{ $t(`scenarioManager.distribution.${scenario?.config_json?.distribution_mode || 'all'}`) }}
          </span>
        </div>
        <div class="detail-row" v-if="scenario?.thread_count">
          <span class="detail-label">{{ $t('scenarioManager.overview.threads') || 'Threads' }}</span>
          <span class="detail-value">{{ scenario.thread_count }}</span>
        </div>
        <div class="detail-row" v-if="scenario?.user_count">
          <span class="detail-label">{{ $t('scenarioManager.overview.users') || 'Users' }}</span>
          <span class="detail-value">{{ scenario.user_count }}</span>
        </div>
      </div>
    </div>

    <!-- Agreement Metrics (if available) -->
    <div class="section" v-if="agreementMetrics?.alpha !== null && agreementMetrics?.alpha !== undefined">
      <h3 class="section-title">{{ $t('scenarioManager.overview.agreementMetrics') || 'Agreement Metrics' }}</h3>
      <div class="metrics-grid">
        <div class="metric-card">
          <span class="metric-value" :class="getAlphaClass(agreementMetrics.alpha)">
            {{ agreementMetrics.alpha?.toFixed(3) || '-' }}
          </span>
          <span class="metric-label">Krippendorff's Alpha</span>
          <span class="metric-interpretation">{{ agreementMetrics.interpretation || '' }}</span>
        </div>
        <div class="metric-card" v-if="agreementMetrics.accuracy !== null && agreementMetrics.accuracy !== undefined">
          <span class="metric-value" :class="getAccuracyClass(agreementMetrics.accuracy)">
            {{ agreementMetrics.accuracy }}%
          </span>
          <span class="metric-label">{{ $t('scenarioManager.overview.overallAccuracy') || 'Overall Accuracy' }}</span>
        </div>
        <div class="metric-card" v-if="agreementMetrics.f1Score !== null && agreementMetrics.f1Score !== undefined">
          <span class="metric-value" :class="getF1Class(agreementMetrics.f1Score)">
            {{ agreementMetrics.f1Score }}%
          </span>
          <span class="metric-label">{{ $t('scenarioManager.overview.f1Score') || 'F1 Score' }}</span>
          <span class="metric-interpretation">{{ $t('scenarioManager.overview.f1Hint') || 'Fake-Erkennung' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const props = defineProps({
  scenario: {
    type: Object,
    default: null
  },
  liveStats: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['import-data', 'start-evaluation', 'view-results'])

const { t } = useI18n()

// Parts / Phases (labeling): read-only structure for the overview. The
// owner-only endpoint 403/404s for assessors -> partsStatus stays null and
// the section never renders (fail closed, invisibility invariant).
const partsStatus = ref(null)

async function loadPartsStatus(scenarioId) {
  partsStatus.value = null
  if (!scenarioId) return
  const typeId = Number(props.scenario?.function_type_id)
  const typeName = String(props.scenario?.function_type_name || '').toLowerCase()
  if (typeId !== 7 && typeName !== 'labeling') return
  try {
    const response = await axios.get(`/api/scenarios/${scenarioId}/parts`)
    partsStatus.value = response.data
  } catch {
    partsStatus.value = null
  }
}

watch(() => props.scenario?.id, id => loadPartsStatus(id), { immediate: true })

// Owner action: unlock/lock a phase straight from the overview (the study gate
// between calibration phases). Uses the same management-gated endpoint as the
// settings tab; the PUT re-checks access server-side. partsUpdating holds the
// part id being written so only that button shows a spinner.
const partsUpdating = ref(null)
async function updatePartLocked(part) {
  const sid = props.scenario?.id
  if (!sid || partsUpdating.value) return
  partsUpdating.value = part.id
  try {
    await axios.put(`/api/scenarios/${sid}/parts/${part.id}`, { locked: !part.locked })
    await loadPartsStatus(sid)
  } finally {
    partsUpdating.value = null
  }
}

function partProgressPercent(part) {
  const assessors = part.assessors || []
  const total = assessors.reduce((sum, a) => sum + (a.total || 0), 0)
  const labeled = assessors.reduce((sum, a) => sum + (a.labeled || 0), 0)
  return total ? Math.round((labeled / total) * 100) : 0
}

function partProgressLabel(part) {
  const assessors = part.assessors || []
  const total = assessors.reduce((sum, a) => sum + (a.total || 0), 0)
  const labeled = assessors.reduce((sum, a) => sum + (a.labeled || 0), 0)
  return `${labeled}/${total}`
}

// Origin map (username/display_name -> origin) provided by ScenarioWorkspace.
// userStatsList carries names, not the full team payload, so look origins up.
const scenarioOrigins = inject('scenarioOrigins', ref({}))
const originFor = (name) => (name ? (scenarioOrigins.value || {})[name] : null)
const humanOrigins = computed(() =>
  userStatsList.value.filter(u => !u.isLLM).map(u => originFor(u.name)).filter(Boolean)
)

// Type mapping
const typeConfig = {
  1: { name: 'ranking' },
  2: { name: 'rating' },
  3: { name: 'mailRating' },
  4: { name: 'comparison' },
  5: { name: 'authenticity' },
  7: { name: 'labeling' },
  8: { name: 'communicationComparison' },
  // 9 = conversation_labeling: item is a conversation, the vote is a span in it
  9: { name: 'conversationLabeling' }
}

const hasHumans = computed(() => props.liveStats?.hasHumans !== false)
const hasLLMs = computed(() => props.liveStats?.hasLLMs === true)

const typeName = computed(() => {
  const key = typeConfig[props.scenario?.function_type_id]?.name || 'unknown'
  return t(`scenarioManager.types.${key}`)
})

// Use live stats if available, fallback to scenario stats
const humanDone = computed(() => {
  if (props.liveStats?.humanProgress?.done !== undefined) {
    return props.liveStats.humanProgress.done
  }
  return props.scenario?.stats?.human_completed || 0
})

const humanTotal = computed(() => {
  if (props.liveStats?.humanProgress?.total !== undefined) {
    return props.liveStats.humanProgress.total
  }
  return props.scenario?.stats?.human_total || 0
})

const humanProgress = computed(() => {
  if (props.liveStats?.humanProgress?.percent !== undefined) {
    return props.liveStats.humanProgress.percent
  }
  if (!props.scenario?.stats) return 0
  const { human_completed, human_total } = props.scenario.stats
  if (!human_total) return 0
  return Math.round((human_completed / human_total) * 100)
})

const llmDone = computed(() => {
  if (props.liveStats?.llmProgress?.done !== undefined) {
    return props.liveStats.llmProgress.done
  }
  return props.scenario?.stats?.llm_completed || 0
})

const llmTotal = computed(() => {
  if (props.liveStats?.llmProgress?.total !== undefined) {
    return props.liveStats.llmProgress.total
  }
  return props.scenario?.stats?.llm_total || 0
})

const llmProgressPercent = computed(() => {
  if (props.liveStats?.llmProgress?.percent !== undefined) {
    return props.liveStats.llmProgress.percent
  }
  if (!props.scenario?.stats) return 0
  const { llm_completed, llm_total } = props.scenario.stats
  if (!llm_total) return 0
  return Math.round((llm_completed / llm_total) * 100)
})

const llmErrors = computed(() => {
  return props.liveStats?.llmProgress?.errors || 0
})

const llmErrorPercent = computed(() => {
  const total = llmTotal.value
  if (total === 0) return 0
  return Math.round((llmErrors.value / total) * 100)
})

const userStatsList = computed(() => {
  return props.liveStats?.userStatsList || []
})

const agreementMetrics = computed(() => {
  return props.liveStats?.agreementMetrics || null
})

const scenarioConfig = computed(() => {
  const raw = props.scenario?.config_json || {}
  if (!raw) return {}
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw)
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch {
      return {}
    }
  }
  return typeof raw === 'object' ? raw : {}
})

const scenarioTaskDescription = computed(() => {
  return scenarioConfig.value.task_description || ''
})

const scenarioEvaluationCriteria = computed(() => {
  const value = scenarioConfig.value.evaluation_criteria
  if (Array.isArray(value)) {
    return value
      .map(item => (typeof item === 'string' ? item.trim() : String(item || '').trim()))
      .filter(Boolean)
  }
  if (typeof value === 'string') {
    return value.split(/[,\n;]/).map(item => item.trim()).filter(Boolean)
  }
  return []
})

function formatDate(dateStr) {
  if (!dateStr) return null
  const date = new Date(dateStr)
  return date.toLocaleDateString()
}

function getAccuracyClass(accuracy) {
  if (accuracy >= 80) return 'excellent'
  if (accuracy >= 60) return 'good'
  if (accuracy >= 40) return 'moderate'
  return 'poor'
}

function getAlphaClass(alpha) {
  if (alpha >= 0.8) return 'excellent'
  if (alpha >= 0.667) return 'good'
  if (alpha >= 0.4) return 'moderate'
  return 'poor'
}

function getF1Class(f1) {
  if (f1 >= 80) return 'excellent'
  if (f1 >= 60) return 'good'
  if (f1 >= 40) return 'moderate'
  return 'poor'
}
</script>

<style scoped>
.overview-tab {
  /* Fills the full tab-content width — the wrapping .tab-content
     in ScenarioWorkspace.vue already provides horizontal padding,
     so capping the width here just wastes screen real estate on
     wider displays. */
  width: 100%;
}

.section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header .section-title {
  margin-bottom: 0;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 16px;
}

.live-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #4caf50;
}

.live-dot {
  width: 6px;
  height: 6px;
  background-color: #4caf50;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(76, 175, 80, 0); }
  100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
}

/* Actions Grid */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-card:hover {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.1);
}

.action-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
}

.action-content {
  flex: 1;
}

.action-content h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 4px;
  color: rgb(var(--v-theme-on-surface));
}

.action-content p {
  font-size: 0.8rem;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.action-arrow {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

/* Progress Cards */
.progress-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.progress-card {
  padding: 20px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.progress-bar-large {
  height: 10px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 5px;
  transition: width 0.3s ease;
}

.progress-fill.llm,
.progress-fill.is-llm {
  background-color: rgb(var(--v-theme-accent));
}

.progress-fill.error {
  background-color: #e8a087;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.progress-percent {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

/* Evaluators List */
.evaluators-list {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.evaluator-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.evaluator-row:last-child {
  border-bottom: none;
}

.evaluator-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 180px;
}

.evaluator-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}

.evaluator-avatar.is-llm {
  background-color: rgba(var(--v-theme-accent), 0.1);
  color: rgb(var(--v-theme-accent));
}

.evaluator-name {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.evaluator-name .name {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.9rem;
}

.role-badge {
  font-size: 0.65rem;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
  text-transform: uppercase;
  width: fit-content;
}

.role-badge.rater {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}

.role-badge.evaluator {
  background-color: rgba(var(--v-theme-info), 0.1);
  color: rgb(var(--v-theme-info));
}

.role-badge.llm {
  background-color: rgba(var(--v-theme-accent), 0.1);
  color: rgb(var(--v-theme-accent));
}

.evaluator-stats {
  display: flex;
  gap: 20px;
  flex: 1;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.stat-value {
  font-weight: 600;
  font-size: 0.95rem;
  color: rgb(var(--v-theme-on-surface));
}

.stat-value.in-progress {
  color: #ff9800;
}

.stat-value.pending {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.stat-value.failed {
  color: #e8a087;
}

.progress-errors {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #e8a087;
  font-size: 0.8rem;
  font-weight: 500;
}

.stat-value.accuracy,
.stat-value.f1 {
  font-size: 0.85rem;
}

.stat-value.excellent { color: #4caf50; }
.stat-value.good { color: #8bc34a; }
.stat-value.moderate { color: #ff9800; }
.stat-value.poor { color: #f44336; }

.stat-label {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.evaluator-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 120px;
}

.progress-bar-small {
  flex: 1;
  height: 6px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-text {
  font-size: 0.8rem;
  font-weight: 500;
  min-width: 36px;
  text-align: right;
}

/* Details Card */
.details-card {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  padding: 8px 0;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.detail-value {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  text-align: right;
  max-width: 60%;
}

.detail-value--markdown {
  text-align: left;
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  text-align: center;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.metric-value.excellent { color: #4caf50; }
.metric-value.good { color: #8bc34a; }
.metric-value.moderate { color: #ff9800; }
.metric-value.poor { color: #f44336; }

.metric-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 4px;
}

.metric-interpretation {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 4px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 24px;
  text-align: center;
}

.empty-state p {
  margin-top: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.875rem;
}

/* ==========================================================================
   Responsive / mobile fixes (additive, desktop unaffected)
   - <=960px: the .evaluator-row's three rigid columns (info 180px +
     evaluator-stats with several min-width:50px stats + progress 120px)
     add up to ~670-732px and force horizontal scroll. Stack the row
     vertically and let the stats wrap so they fit narrow viewports.
   - <=600px: collapse the auto-fit grids (which keep a 280-300px minimum
     track that overflows on phones) to a single column, and bump tiny
     secondary text up to >=0.75rem for legibility.
   ========================================================================== */

@media (max-width: 960px) {
  /* Stack the evaluator row so the rigid 180px/stats/120px columns no
     longer sum past the viewport width and trigger horizontal scroll. */
  .evaluator-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .evaluator-info {
    /* Drop the 180px floor so the info block can shrink with the row. */
    min-width: 0;
  }

  .evaluator-stats {
    /* Allow the stat cells to wrap instead of pushing the row wider. */
    flex-wrap: wrap;
    gap: 12px 16px;
  }

  .stat {
    /* Remove the 50px floor so wrapped stats pack tightly. */
    min-width: 0;
  }

  .evaluator-progress {
    /* Full-width progress bar under the stacked content. */
    min-width: 0;
  }
}

@media (max-width: 600px) {
  /* Single-column grids: the auto-fit minmax tracks (280/300/180px)
     overflow narrow phones, so force one column. */
  .actions-grid,
  .progress-cards {
    grid-template-columns: 1fr;
  }

  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }

  /* Tighter stat spacing once stacked/wrapped on phones. */
  .evaluator-stats {
    gap: 10px 14px;
  }

  /* Raise tiny secondary text to remain legible (>=0.75rem). */
  .stat-label,
  .role-badge {
    font-size: 0.75rem;
  }

  /* Stack detail rows: label above value, full-width value (no 60% cap). */
  .detail-row {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
  }

  .detail-value {
    text-align: left;
    max-width: 100%;
  }

  /* Chips inside a value align left once the row is stacked. */
  .detail-value .justify-end {
    justify-content: flex-start !important;
  }
}

/* Parts / Phases overview */
.parts-overview-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.parts-overview-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px 12px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
}

.parts-overview-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.parts-overview-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 160px;
  margin-left: auto;
}

.parts-overview-progress .progress-bar-large {
  flex: 1;
  margin: 0;
}

.parts-overview-action {
  flex-shrink: 0;
}

.parts-overview-count {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-variant-numeric: tabular-nums;
}

.parts-overview-hint {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-style: italic;
  margin: 8px 0 0;
}
</style>
