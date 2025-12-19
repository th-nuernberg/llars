<template>
  <v-container class="evaluation-hub">
    <v-row class="mb-4">
      <v-col cols="12" class="d-flex align-center">
        <LBtn variant="tonal" prepend-icon="mdi-arrow-left" @click="goHome">Home</LBtn>
        <div class="ml-4">
          <h1 class="text-h5 font-weight-bold mb-1">
            <span class="mr-2">🧪</span>
            Evaluierung
          </h1>
          <div class="text-body-2 text-medium-emphasis">
            Wähle ein Evaluierungstool aus und starte den normalen Workflow.
          </div>
        </div>
        <v-spacer />
        <LTag v-if="availableTools.length > 0" variant="primary" size="sm">
          {{ availableTools.length }} verfügbar
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
          Für deinen Account sind aktuell keine Evaluierungstools freigeschaltet.
        </v-alert>
        <LBtn variant="primary" prepend-icon="mdi-home" @click="goHome">Zurück</LBtn>
      </div>

      <div v-else class="features-grid">
        <div
          v-for="tool in availableTools"
          :key="tool.title"
          class="feature-card"
          @click="navigateTo(tool.route)"
        >
          <div class="feature-icon">
            <v-icon size="32" color="primary">{{ tool.icon }}</v-icon>
          </div>
          <div class="feature-title">
            <span v-if="tool.emoji" class="feature-emoji">{{ tool.emoji }}</span>
            {{ tool.title }}
          </div>
          <div class="feature-description">{{ tool.description }}</div>
          <div class="feature-badge" v-if="tool.badge">
            <LTag :variant="getBadgeVariant(tool.badgeColor)" size="sm">
              {{ tool.badge }}
            </LTag>
          </div>
        </div>
      </div>
    </template>
  </v-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const router = useRouter()

const { hasPermission, fetchPermissions } = usePermissions()
const { isLoading, withLoading } = useSkeletonLoading(['permissions'])

const allTools = ref([
  {
    title: 'Ranking',
    description: 'Features nach Qualität sortieren und vergleichen',
    route: '/Ranker',
    icon: 'mdi-chart-bar-stacked',
    emoji: '🏆',
    permission: 'feature:ranking:view'
  },
  {
    title: 'Verlaufsbewertung',
    description: 'Bewertung von KI generierten Mail-Verläufen (Säule 4)',
    route: '/HistoryGeneration',
    icon: 'mdi-timeline-text-outline',
    emoji: '✉️',
    permission: 'feature:mail_rating:view'
  },
  {
    title: 'Fake/Echt',
    description: 'Abstimmung: Ist ein Verlauf echt oder fake?',
    route: '/authenticity',
    icon: 'mdi-shield-search',
    emoji: '🕵️',
    permission: 'feature:authenticity:view',
    badge: 'New',
    badgeColor: 'info'
  },
  {
    title: 'Rating',
    description: 'Features einzeln mit Sternen/Skala bewerten',
    route: '/Rater',
    icon: 'mdi-star-outline',
    emoji: '⭐️',
    permission: 'feature:rating:view'
  },
  {
    title: 'Gegenüberstellung',
    description: 'Zwei KI-Modelle direkt vergleichen und bewerten',
    route: '/comparison',
    icon: 'mdi-compare-horizontal',
    emoji: '⚖️',
    permission: 'feature:comparison:view'
  }
])

const availableTools = computed(() => {
  return allTools.value.filter((t) => {
    if (!t.permission) return true
    return hasPermission(t.permission)
  })
})

function navigateTo(route) {
  router.push(route)
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
    await fetchPermissions()
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

.feature-card:hover {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.15);
  transform: translateY(-2px);
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

