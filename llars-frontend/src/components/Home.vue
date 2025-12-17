<template>
  <div class="home-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <img src="@/assets/logo/llars-logo.png" alt="LLARS Logo" class="logo" />
        <div class="header-text">
          <h1 class="title">Willkommen bei LLARS</h1>
          <p class="subtitle">Ihre Plattform für Ranking, Labeling, Rating und KI-Analyse</p>
        </div>
      </div>
      <div class="header-right">
        <v-chip color="primary" variant="flat" class="user-chip">
          <v-icon start>mdi-account</v-icon>
          {{ username }}
        </v-chip>
      </div>
    </div>

    <!-- Stats Row -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon">
          <v-icon color="primary">mdi-view-grid</v-icon>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ filteredItems.length }}</span>
          <span class="stat-label">Features</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <v-icon color="success">mdi-folder-multiple</v-icon>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ categories.length }}</span>
          <span class="stat-label">Kategorien</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <v-icon color="info">mdi-flask</v-icon>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ researchCount }}</span>
          <span class="stat-label">Forschung</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <v-icon color="warning">mdi-cog</v-icon>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ adminCount }}</span>
          <span class="stat-label">Admin</span>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div ref="containerRef" class="main-content">
      <!-- Left Panel: Categories -->
      <div class="left-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <v-icon class="mr-2">mdi-filter-variant</v-icon>
          <span>Kategorien</span>
        </div>
        <div class="panel-content">
          <div class="categories-list">
            <div
              v-for="cat in categories"
              :key="cat.id"
              class="category-item"
              :class="{ active: selectedCategory === cat.id }"
              @click="selectCategory(cat.id)"
            >
              <v-icon class="category-icon" :color="selectedCategory === cat.id ? 'primary' : undefined">
                {{ cat.icon }}
              </v-icon>
              <div class="category-info">
                <span class="category-name">{{ cat.name }}</span>
                <span class="category-count">{{ getCategoryCount(cat.id) }} Features</span>
              </div>
              <v-icon v-if="selectedCategory === cat.id" class="category-check" color="primary">
                mdi-check-circle
              </v-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- Resize Divider -->
      <div
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Right Panel: Features Grid -->
      <div class="right-panel" :style="rightPanelStyle()">
        <div class="panel-header">
          <v-icon class="mr-2">mdi-apps</v-icon>
          <span>{{ selectedCategoryName }}</span>
          <v-spacer />
          <LTag variant="primary" size="sm">
            {{ filteredItems.length }} verfügbar
          </LTag>
        </div>
        <div class="panel-content">
          <!-- Skeleton Loading -->
          <div v-if="isSkelLoading('permissions')" class="features-grid">
            <v-skeleton-loader
              v-for="n in 6"
              :key="'skeleton-' + n"
              type="card"
              class="feature-skeleton"
            />
          </div>

          <!-- Features Grid -->
          <div v-else class="features-grid">
            <div
              v-for="item in filteredItems"
              :key="item.title"
              class="feature-card"
              @click="navigateTo(item.route)"
            >
              <div class="feature-icon">
                <v-icon size="32" color="primary">{{ item.icon }}</v-icon>
              </div>
              <div class="feature-title">{{ item.title }}</div>
              <div class="feature-description">{{ item.description }}</div>
              <div class="feature-badge" v-if="item.badge">
                <LTag :variant="getBadgeVariant(item.badgeColor)" size="sm">
                  {{ item.badge }}
                </LTag>
              </div>
            </div>

            <!-- Empty State -->
            <div v-if="filteredItems.length === 0" class="empty-state">
              <v-icon size="64" color="grey">mdi-folder-open-outline</v-icon>
              <p>Keine Features in dieser Kategorie verfügbar</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePanelResize } from '@/composables/usePanelResize'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { hasPermission, fetchPermissions } = usePermissions()
const { isLoading: isSkelLoading, withLoading } = useSkeletonLoading(['permissions'])
const { tokenParsed } = useAuth()

const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 25,
  minLeftPercent: 15,
  maxLeftPercent: 40,
  storageKey: 'home-panel-width'
})

// Categories
const categories = [
  { id: 'all', name: 'Alle Features', icon: 'mdi-view-grid-outline' },
  { id: 'research', name: 'Forschung', icon: 'mdi-flask-outline' },
  { id: 'rating', name: 'Bewertung', icon: 'mdi-star-outline' },
  { id: 'ai', name: 'KI-Tools', icon: 'mdi-robot-outline' },
  { id: 'admin', name: 'Administration', icon: 'mdi-shield-account-outline' }
]

const selectedCategory = ref('all')

// All available features with their required permissions
const allItems = ref([
  {
    title: 'Ranking',
    description: 'Features nach Qualität sortieren und vergleichen',
    route: '/Ranker',
    icon: 'mdi-chart-bar-stacked',
    permission: 'feature:ranking:view',
    category: 'rating'
  },
  {
    title: 'Verlaufsbewertung',
    description: 'Bewertung von KI generierten Mail-Verläufen (Säule 4)',
    route: '/HistoryGeneration',
    icon: 'mdi-timeline-text-outline',
    permission: 'feature:mail_rating:view',
    category: 'rating'
  },
  {
    title: 'Rating',
    description: 'Features einzeln mit Sternen/Skala bewerten',
    route: '/Rater',
    icon: 'mdi-star-outline',
    permission: 'feature:rating:view',
    category: 'rating'
  },
  {
    title: 'Chatbot',
    description: 'Interaktiver Chat mit LLars KI-Assistent',
    route: '/chat',
    icon: 'mdi-chat-outline',
    permission: null,
    category: 'ai',
    badge: 'Alpha',
    badgeColor: 'warning'
  },
  {
    title: 'Prompt Engineering',
    description: 'Kollaboratives Entwerfen und Testen von Prompts',
    route: '/PromptEngineering',
    icon: 'mdi-text-search',
    permission: 'feature:prompt_engineering:view',
    category: 'research',
    badge: 'Beta',
    badgeColor: 'info'
  },
  {
    title: 'Markdown Collab',
    description: 'Kollaboratives Arbeiten an Markdown-Dateien mit Live-Preview',
    route: '/MarkdownCollab',
    icon: 'mdi-language-markdown',
    permission: 'feature:markdown_collab:view',
    category: 'research',
    badge: 'Beta',
    badgeColor: 'info'
  },
  {
    title: 'Gegenüberstellung',
    description: 'Zwei KI-Modelle direkt vergleichen und bewerten',
    route: '/comparison',
    icon: 'mdi-compare-horizontal',
    permission: 'feature:comparison:view',
    category: 'research'
  },
  {
    title: 'LLM-as-Judge',
    description: 'Automatisierte Bewertung und Vergleich von Prompt-Säulen',
    route: '/judge',
    icon: 'mdi-gavel',
    permission: null,
    category: 'ai'
  },
  {
    title: 'Anonymisierung',
    description: 'Texte, DOCX und PDFs offline pseudonymisieren',
    route: '/Anonymize',
    icon: 'mdi-incognito',
    permission: 'feature:anonymize:view',
    category: 'ai',
    badge: 'Beta',
    badgeColor: 'info'
  },
  {
    title: 'KAIMO',
    description: 'Fallvignetten durcharbeiten und neue Fälle anlegen',
    route: '/kaimo',
    icon: 'mdi-account-school-outline',
    permission: 'feature:kaimo:view',
    category: 'research'
  },
  {
    title: 'OnCoCo Analyse',
    description: 'Beratungsgespräche auf Satzebene klassifizieren (68 Kategorien)',
    route: '/oncoco',
    icon: 'mdi-chart-timeline-variant-shimmer',
    permission: 'feature:comparison:view',
    category: 'ai'
  },
  {
    title: 'Admin Dashboard',
    description: 'Benutzer, Rollen und Berechtigungen verwalten',
    route: '/admin?tab=permissions',
    icon: 'mdi-shield-account',
    permission: 'admin:permissions:manage',
    category: 'admin'
  },
  {
    title: 'RAG Verwaltung',
    description: 'Dokumente für die RAG-Pipeline verwalten und hochladen',
    route: '/admin?tab=rag',
    icon: 'mdi-database-search',
    permission: 'feature:rag:view',
    category: 'admin'
  }
])

// Computed
const username = computed(() => tokenParsed.value?.preferred_username || 'Gast')

const items = computed(() => {
  return allItems.value.filter(item => {
    if (!item.permission) return true
    return hasPermission(item.permission)
  })
})

const filteredItems = computed(() => {
  if (selectedCategory.value === 'all') return items.value
  return items.value.filter(item => item.category === selectedCategory.value)
})

const selectedCategoryName = computed(() => {
  const cat = categories.find(c => c.id === selectedCategory.value)
  return cat ? cat.name : 'Features'
})

const researchCount = computed(() => {
  return items.value.filter(i => i.category === 'research').length
})

const adminCount = computed(() => {
  return items.value.filter(i => i.category === 'admin').length
})

// Methods
function selectCategory(id) {
  selectedCategory.value = id
}

function getCategoryCount(categoryId) {
  if (categoryId === 'all') return items.value.length
  return items.value.filter(i => i.category === categoryId).length
}

function navigateTo(route) {
  router.push(route)
}

function getBadgeVariant(badgeColor) {
  const colorMap = {
    'info': 'info',
    'warning': 'warning',
    'success': 'success',
    'error': 'danger',
    'primary': 'primary'
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
.home-page {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
}

/* Page Header */
.page-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  height: 48px;
  width: auto;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  line-height: 1.2;
}

.subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
}

.user-chip {
  font-weight: 500;
}

/* Stats Row */
.stats-row {
  flex-shrink: 0;
  display: flex;
  gap: 16px;
  padding: 16px 24px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: rgba(var(--v-theme-primary), 0.04);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Left Panel */
.left-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-surface));
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  min-width: 200px;
}

/* Right Panel */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 400px;
}

/* Panel Header */
.panel-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

/* Panel Content */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Resize Divider */
.resize-divider {
  flex-shrink: 0;
  width: 6px;
  background-color: rgb(var(--v-theme-surface));
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.resize-divider:hover,
.resize-divider.resizing {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.resize-handle {
  width: 2px;
  height: 40px;
  background-color: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 1px;
  transition: background-color 0.2s, height 0.2s;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background-color: rgb(var(--v-theme-primary));
  height: 60px;
}

/* Categories List */
.categories-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.category-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.category-item.active {
  background-color: rgba(var(--v-theme-primary), 0.12);
}

.category-icon {
  font-size: 24px;
}

.category-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.category-name {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.category-count {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.category-check {
  font-size: 20px;
}

/* Features Grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  pointer-events: auto;
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
  z-index: 1;
  pointer-events: auto;
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

/* Empty State */
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-state p {
  margin-top: 16px;
  font-size: 0.9rem;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .header-left {
    flex-direction: column;
  }

  .stats-row {
    flex-wrap: wrap;
  }

  .stat-card {
    flex: 1 1 calc(50% - 8px);
    min-width: 140px;
  }

  .main-content {
    flex-direction: column;
  }

  .left-panel {
    min-width: 100%;
    max-height: 200px;
    border-right: none;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  }

  .resize-divider {
    display: none;
  }

  .right-panel {
    min-width: 100%;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }
}
</style>
