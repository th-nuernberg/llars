<template>
  <div class="home-page" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <img src="@/assets/logo/llars-logo.png" alt="LLARS Logo" class="logo" />
        <div class="header-text">
          <h1 class="title">{{ $t('home.header.title') }}</h1>
          <p class="subtitle" v-if="!isMobile">{{ $t('home.header.subtitle') }}</p>
        </div>
      </div>
      <div class="header-right">
        <!-- Mobile: Category toggle button -->
        <v-btn
          v-if="isMobile"
          icon
          variant="text"
          class="mr-2"
          @click="showMobileCategories = !showMobileCategories"
        >
          <LIcon>{{ showMobileCategories ? 'mdi-close' : 'mdi-filter-variant' }}</LIcon>
        </v-btn>
        <v-chip color="primary" variant="flat" class="user-chip" :size="isMobile ? 'small' : 'default'">
          <LIcon start :size="isMobile ? 16 : 20">mdi-account</LIcon>
          <span v-if="!isMobile">{{ username }}</span>
        </v-chip>
      </div>
    </div>

    <!-- Mobile Categories Overlay -->
    <v-slide-y-transition>
      <div v-if="isMobile && showMobileCategories" class="mobile-categories-overlay">
        <div class="mobile-categories-content">
          <div class="mobile-category-header">
            <LIcon class="mr-2">mdi-filter-variant</LIcon>
            <span>{{ $t('home.categories.title') }}</span>
          </div>
          <div class="mobile-categories-list">
            <div
              v-for="cat in categories"
              :key="cat.id"
              class="mobile-category-item"
              :class="{ active: selectedCategory === cat.id }"
              @click="selectCategory(cat.id)"
            >
              <LIcon :color="selectedCategory === cat.id ? 'primary' : undefined">
                {{ cat.icon }}
              </LIcon>
              <span class="mobile-category-name">{{ cat.name }}</span>
              <span class="mobile-category-count">{{ getCategoryCount(cat.id) }}</span>
              <LIcon v-if="selectedCategory === cat.id" color="primary" size="18">
                mdi-check
              </LIcon>
            </div>
          </div>
        </div>
      </div>
    </v-slide-y-transition>

    <!-- Main Content -->
    <div ref="containerRef" class="main-content">
      <!-- Left Panel: Categories (Desktop only) -->
      <div v-if="!isMobile" class="left-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <LIcon class="mr-2">mdi-filter-variant</LIcon>
          <span>{{ $t('home.categories.title') }}</span>
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
              <LIcon class="category-icon" :color="selectedCategory === cat.id ? 'primary' : undefined">
                {{ cat.icon }}
              </LIcon>
              <div class="category-info">
                <span class="category-name">{{ cat.name }}</span>
                <span class="category-count">{{ $t('home.categories.featuresCount', { count: getCategoryCount(cat.id) }) }}</span>
              </div>
              <LIcon v-if="selectedCategory === cat.id" class="category-check" color="primary">
                mdi-check-circle
              </LIcon>
            </div>
          </div>
        </div>
      </div>

      <!-- Resize Divider (Desktop only) -->
      <div
        v-if="!isMobile"
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Right Panel: Features Grid -->
      <div class="right-panel" :style="isMobile ? {} : rightPanelStyle()">
        <div class="panel-header">
          <LIcon class="mr-2">mdi-apps</LIcon>
          <span>{{ selectedCategoryName }}</span>
          <v-spacer />
          <LTag variant="primary" size="sm">
            {{ $t('home.available', { count: filteredItems.length }) }}
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
                <LIcon size="36" color="primary">{{ item.icon }}</LIcon>
              </div>
              <div class="feature-title">
                <span v-if="item.emoji" class="feature-emoji">{{ item.emoji }}</span>
                {{ item.title }}
              </div>
              <div class="feature-description">{{ item.description }}</div>
              <div class="feature-badge" v-if="item.badge">
                <LTag :variant="getBadgeVariant(item.badgeColor)" size="sm">
                  {{ item.badge }}
                </LTag>
              </div>
            </div>

            <!-- Empty State -->
            <div v-if="filteredItems.length === 0" class="empty-state">
              <LIcon size="64" color="grey">mdi-folder-open-outline</LIcon>
              <p>{{ $t('home.empty.noFeatures') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePanelResize } from '@/composables/usePanelResize'
import { useAuth } from '@/composables/useAuth'
import { useMobile } from '@/composables/useMobile'

const router = useRouter()
const { t } = useI18n()
const { hasPermission, hasAnyPermission, fetchPermissions } = usePermissions()
const { isLoading: isSkelLoading, withLoading } = useSkeletonLoading(['permissions'])
const { tokenParsed } = useAuth()
const { isMobile, isTablet, isSmallScreen, isTouchDevice } = useMobile()

// Mobile UI state
const mobileMenuOpen = ref(false)
const showMobileCategories = ref(false)

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

// All categories (filtered based on available items)
const allCategories = computed(() => [
  { id: 'all', name: t('home.categories.all'), icon: 'mdi-view-grid-outline' },
  { id: 'research', name: t('home.categories.research'), icon: 'mdi-flask-outline' },
  { id: 'rating', name: t('home.categories.rating'), icon: 'mdi-star-outline' },
  { id: 'ai', name: t('home.categories.ai'), icon: 'mdi-robot-outline' },
  { id: 'admin', name: t('home.categories.admin'), icon: 'mdi-shield-account-outline' }
])

// Only show categories that have at least one visible item
const categories = computed(() => {
  return allCategories.value.filter(cat => {
    if (cat.id === 'all') return true
    return items.value.some(item => item.category === cat.id)
  })
})

const selectedCategory = ref('all')

// Close mobile categories panel when category is selected
watch(selectedCategory, () => {
  if (isMobile.value) {
    showMobileCategories.value = false
  }
})

// All available features with their required permissions
const allItems = computed(() => ([
  {
    title: t('home.features.evaluation.title'),
    description: t('home.features.evaluation.description'),
    route: '/evaluation',
    icon: 'llars:evaluation',
    permissionsAny: [
      'feature:ranking:view',
      'feature:rating:view',
      'feature:mail_rating:view',
      'feature:comparison:view',
      'feature:authenticity:view'
    ],
    category: 'rating'
  },
  {
    title: t('home.features.scenarioManager.title'),
    description: t('home.features.scenarioManager.description'),
    route: '/scenarios',
    icon: 'mdi-clipboard-check-multiple-outline',
    permission: 'data:manage_scenarios',
    permissionsAny: ['data:manage_scenarios', 'feature:ranking:view', 'feature:rating:view'],
    category: 'rating',
    badge: t('home.badges.new'),
    badgeColor: 'success'
  },
  {
    title: t('home.features.chatbot.title'),
    description: t('home.features.chatbot.description'),
    route: '/chat',
    icon: 'llars:chatbot',
    permission: null,
    category: 'ai',
    badge: t('home.badges.alpha'),
    badgeColor: 'warning'
  },
  {
    title: t('home.features.promptEngineering.title'),
    description: t('home.features.promptEngineering.description'),
    route: '/PromptEngineering',
    icon: 'llars:prompt-engineering',
    permission: 'feature:prompt_engineering:view',
    category: 'research',
    badge: t('home.badges.beta'),
    badgeColor: 'info'
  },
  {
    title: t('home.features.batchGeneration.title'),
    description: t('home.features.batchGeneration.description'),
    route: '/generation',
    icon: 'mdi-cog-play-outline',
    permission: 'feature:generation:view',
    category: 'research',
    badge: t('home.badges.beta'),
    badgeColor: 'info'
  },
  {
    title: t('home.features.markdownCollab.title'),
    description: t('home.features.markdownCollab.description'),
    route: '/MarkdownCollab',
    icon: 'llars:markdown-collab',
    permission: 'feature:markdown_collab:view',
    category: 'research',
    badge: t('home.badges.beta'),
    badgeColor: 'info'
  },
  {
    title: t('home.features.latexCollab.title'),
    description: t('home.features.latexCollab.description'),
    route: '/LatexCollab',
    icon: 'llars:latex-collab-ai',
    permission: 'feature:latex_collab:view',
    category: 'research',
    badge: t('home.badges.beta'),
    badgeColor: 'info'
  },
  {
    title: t('home.features.chatbotArena.title'),
    description: t('home.features.chatbotArena.description'),
    route: '/judge',
    icon: 'mdi-sword-cross',
    permission: 'feature:judge:view',
    category: 'ai'
  },
  {
    title: t('home.features.anonymization.title'),
    description: t('home.features.anonymization.description'),
    route: '/Anonymize',
    icon: 'llars:anonymize',
    permission: 'feature:anonymize:view',
    category: 'ai',
    badge: t('home.badges.beta'),
    badgeColor: 'info'
  },
  {
    title: t('home.features.kaimo.title'),
    description: t('home.features.kaimo.description'),
    route: '/kaimo',
    icon: 'mdi-account-school-outline',
    permission: 'feature:kaimo:view',
    category: 'research'
  },
  {
    title: t('home.features.oncoco.title'),
    description: t('home.features.oncoco.description'),
    route: '/oncoco',
    icon: 'llars:oncoco',
    permission: 'feature:oncoco:view',
    category: 'ai'
  },
  {
    title: t('home.features.adminDashboard.title'),
    description: t('home.features.adminDashboard.description'),
    route: '/admin?tab=overview',
    icon: 'llars:admin-dashboard',
    permission: 'admin:permissions:manage',
    category: 'admin'
  },
  {
    title: t('home.features.chatbotAdmin.title'),
    description: t('home.features.chatbotAdmin.description'),
    route: '/admin?tab=chatbots',
    icon: 'llars:chatbot-manage',
    permission: 'feature:chatbots:edit',
    category: 'admin'
  },
  {
    title: t('home.features.ragAdmin.title'),
    description: t('home.features.ragAdmin.description'),
    route: '/admin?tab=rag',
    icon: 'llars:rag',
    permission: 'feature:rag:edit',
    category: 'admin'
  },
  {
    title: t('home.features.userSettings.title'),
    description: t('home.features.userSettings.description'),
    route: '/settings',
    icon: 'mdi-account-cog',
    permission: null,
    category: 'all'
  }
]))

// Computed
const username = computed(() => tokenParsed.value?.preferred_username || t('home.user.guest'))

const items = computed(() => {
  return allItems.value.filter(item => {
    const requiresAny = Array.isArray(item.permissionsAny) && item.permissionsAny.length > 0
    if (requiresAny && !hasAnyPermission(...item.permissionsAny)) return false

    if (!item.permission) return true
    return hasPermission(item.permission)
  })
})

const filteredItems = computed(() => {
  if (selectedCategory.value === 'all') return items.value
  return items.value.filter(item => item.category === selectedCategory.value)
})

const selectedCategoryName = computed(() => {
  const cat = categories.value.find(c => c.id === selectedCategory.value)
  return cat ? cat.name : t('home.categories.fallback')
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
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
  pointer-events: auto;
}

.feature-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 16px;
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
  margin-bottom: 12px;
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

/* ========================================
   MOBILE RESPONSIVE STYLES
   ======================================== */

/* Mobile Categories Overlay */
.mobile-categories-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.mobile-categories-content {
  padding: 12px 16px;
}

.mobile-category-header {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.mobile-categories-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mobile-category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  -webkit-tap-highlight-color: transparent;
}

.mobile-category-item:active {
  background-color: rgba(var(--v-theme-primary), 0.15);
}

.mobile-category-item.active {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.mobile-category-name {
  flex: 1;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.mobile-category-count {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  background-color: rgba(var(--v-theme-on-surface), 0.08);
  padding: 2px 8px;
  border-radius: 10px;
}

/* Mobile Home Page */
.home-page.is-mobile {
  /* 64px AppBar + 24px Footer = 88px */
  height: calc(100vh - 88px);
  height: calc(100dvh - 88px);
  position: relative;
  overflow: hidden;
  max-width: 100vw;
}

.home-page.is-mobile .page-header {
  flex-shrink: 0;
  padding: 12px 16px;
}

.home-page.is-mobile .header-left {
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.home-page.is-mobile .header-text {
  min-width: 0;
}

.home-page.is-mobile .logo {
  height: 36px;
  flex-shrink: 0;
}

.home-page.is-mobile .title {
  font-size: 1.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.home-page.is-mobile .main-content {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.home-page.is-mobile .right-panel {
  width: 100%;
  height: 100%;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.home-page.is-mobile .panel-header {
  flex-shrink: 0;
  padding: 10px 16px;
  font-size: 14px;
}

.home-page.is-mobile .panel-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px;
  -webkit-overflow-scrolling: touch;
}

.home-page.is-mobile .features-grid {
  grid-template-columns: 1fr;
  gap: 12px;
}

.home-page.is-mobile .feature-card {
  padding: 16px;
}

.home-page.is-mobile .feature-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
}

.home-page.is-mobile .feature-title {
  font-size: 1rem;
}

.home-page.is-mobile .feature-description {
  font-size: 0.8rem;
}

/* Tablet styles */
.home-page.is-tablet .stats-row {
  flex-wrap: wrap;
}

.home-page.is-tablet .stat-card {
  flex: 1 1 calc(50% - 8px);
}

.home-page.is-tablet .features-grid {
  grid-template-columns: repeat(2, 1fr);
}

/* Legacy responsive (for transition) */
@media (max-width: 768px) {
  .page-header {
    flex-direction: row;
    gap: 12px;
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

/* Extra small devices */
@media (max-width: 380px) {
  .home-page.is-mobile .stat-card {
    min-width: 85px;
    padding: 6px 10px;
    gap: 8px;
  }

  .home-page.is-mobile .stat-icon {
    width: 28px;
    height: 28px;
  }

  .home-page.is-mobile .stat-value {
    font-size: 0.9rem;
  }
}

/* Landscape on mobile */
@media (max-height: 500px) and (orientation: landscape) {
  .home-page.is-mobile {
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
  }

  .home-page.is-mobile .stats-row {
    padding: 4px 12px;
  }

  .home-page.is-mobile .stat-card {
    padding: 4px 8px;
  }
}

/* Touch device optimizations */
.home-page.is-mobile .feature-card {
  -webkit-tap-highlight-color: transparent;
}

.home-page.is-mobile .feature-card:active {
  transform: scale(0.98);
  transition: transform 0.1s;
}
</style>
