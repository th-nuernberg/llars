<template>
  <v-container class="evaluation-hub">
    <v-row class="mb-4">
      <v-col cols="12" class="d-flex align-center">
        <LBtn variant="tonal" prepend-icon="mdi-arrow-left" @click="goHome">{{ $t('navigation.home') }}</LBtn>
        <div class="ml-4">
          <h1 class="text-h5 font-weight-bold mb-1">
            <span class="mr-2">🧪</span>
            {{ $t('evaluation.title') }}
          </h1>
          <div class="text-body-2 text-medium-emphasis">
            {{ $t('evaluation.subtitle') }}
          </div>
        </div>
        <v-spacer />
        <LTag v-if="availableTools.length > 0" variant="primary" size="sm">
          {{ $t('evaluation.available', { count: availableTools.length }) }}
        </LTag>
      </v-col>
    </v-row>

    <!-- Skeleton Loading -->
    <div v-if="isLoading('permissions')" class="features-grid">
      <v-skeleton-loader
        v-for="n in 5"
        :key="'skeleton-' + n"
        type="card"
        class="feature-skeleton"
      />
    </div>

    <template v-else>
      <div v-if="availableTools.length === 0">
        <v-alert type="info" variant="tonal" class="mb-4">
          {{ $t('evaluation.noToolsAvailable') }}
        </v-alert>
        <LBtn variant="primary" prepend-icon="mdi-home" @click="goHome">{{ $t('navigation.back') }}</LBtn>
      </div>

      <div v-else class="features-grid">
        <v-tooltip
          v-for="tool in availableTools"
          :key="tool.i18nKey"
          :disabled="hasScenarios(tool)"
          location="top"
        >
          <template v-slot:activator="{ props }">
            <div
              v-bind="props"
              class="feature-card"
              :class="{ 'feature-card--disabled': !hasScenarios(tool) }"
              @click="navigateTo(tool.route, tool)"
            >
              <div class="feature-icon" :class="{ 'feature-icon--disabled': !hasScenarios(tool) }">
                <LIcon size="32" :color="hasScenarios(tool) ? 'primary' : 'grey'">{{ tool.icon }}</LIcon>
              </div>
              <div class="feature-title">
                <span v-if="tool.emoji" class="feature-emoji">{{ tool.emoji }}</span>
                {{ $t('evaluation.tools.' + tool.i18nKey + '.title') }}
              </div>
              <div class="feature-description">{{ $t('evaluation.tools.' + tool.i18nKey + '.description') }}</div>
              <div class="feature-badge" v-if="tool.badge && hasScenarios(tool)">
                <LTag :variant="getBadgeVariant(tool.badgeColor)" size="sm">
                  {{ $t('evaluation.badges.' + tool.badge) }}
                </LTag>
              </div>
              <div class="feature-badge" v-if="!hasScenarios(tool)">
                <LTag variant="gray" size="sm">
                  {{ $t('evaluation.noScenarios') }}
                </LTag>
              </div>
            </div>
          </template>
          <span>{{ $t('evaluation.noScenariosAssigned') }}</span>
        </v-tooltip>
      </div>
    </template>
  </v-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const router = useRouter()

const { hasPermission, fetchPermissions } = usePermissions()
const { isLoading, withLoading } = useSkeletonLoading(['permissions'])

// Thread counts per function type (from backend)
const threadCounts = ref({})

const allTools = ref([
  {
    i18nKey: 'ranking',
    route: '/Ranker',
    icon: 'mdi-chart-bar-stacked',
    emoji: '🏆',
    permission: 'feature:ranking:view',
    functionType: 'ranking'
  },
  {
    i18nKey: 'historyRating',
    route: '/HistoryGeneration',
    icon: 'mdi-timeline-text-outline',
    emoji: '✉️',
    permission: 'feature:mail_rating:view',
    functionType: 'mail_rating'
  },
  {
    i18nKey: 'authenticity',
    route: '/authenticity',
    icon: 'mdi-shield-search',
    emoji: '🕵️',
    permission: 'feature:authenticity:view',
    functionType: 'authenticity',
    badge: 'new',
    badgeColor: 'info'
  },
  {
    i18nKey: 'rating',
    route: '/Rater',
    icon: 'mdi-star-outline',
    emoji: '⭐️',
    permission: 'feature:rating:view',
    functionType: 'rating'
  },
  {
    i18nKey: 'comparison',
    route: '/comparison',
    icon: 'mdi-compare-horizontal',
    emoji: '⚖️',
    permission: 'feature:comparison:view',
    functionType: 'comparison'
  }
])

const availableTools = computed(() => {
  return allTools.value.filter((t) => {
    if (!t.permission) return true
    return hasPermission(t.permission)
  })
})

// Check if tool has scenarios assigned
function hasScenarios(tool) {
  if (!tool.functionType) return true
  return (threadCounts.value[tool.functionType] || 0) > 0
}

// Get scenario count for tooltip
function getScenarioCount(tool) {
  if (!tool.functionType) return 0
  return threadCounts.value[tool.functionType] || 0
}

function navigateTo(route, tool) {
  if (!hasScenarios(tool)) return
  router.push(route)
}

async function fetchThreadCounts() {
  try {
    const response = await axios.get('/api/evaluation/thread_counts')
    threadCounts.value = response.data.counts || {}
  } catch (error) {
    console.error('Error fetching thread counts:', error)
  }
}

function goHome() {
  router.push('/Home')
}

function getBadgeVariant(badgeColor) {
  const colorMap = {
    info: 'info',
    warning: 'warning',
    success: 'success',
    error: 'danger',
    primary: 'primary'
  }
  return colorMap[badgeColor] || 'info'
}

onMounted(async () => {
  await withLoading('permissions', async () => {
    await Promise.all([
      fetchPermissions(),
      fetchThreadCounts()
    ])
  })
})
</script>

<style scoped>
.evaluation-hub {
  padding-top: 16px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.feature-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.feature-card:hover:not(.feature-card--disabled) {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.15);
  transform: translateY(-2px);
}

.feature-card--disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

.feature-card--disabled .feature-title,
.feature-card--disabled .feature-description {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.feature-icon--disabled {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background-color: rgba(var(--v-theme-primary), 0.1);
  margin-bottom: 16px;
}

.feature-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 8px;
}

.feature-emoji {
  display: inline-block;
  margin-right: 6px;
  font-size: 1.1rem;
  line-height: 1;
}

.feature-description {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  line-height: 1.5;
  flex: 1;
}

.feature-badge {
  position: absolute;
  top: 12px;
  right: 12px;
}

.feature-skeleton {
  min-height: 160px;
}

@media (max-width: 768px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
}
</style>

