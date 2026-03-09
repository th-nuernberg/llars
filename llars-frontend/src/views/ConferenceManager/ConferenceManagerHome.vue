<template>
  <div class="conference-manager" :class="{ 'is-mobile': isMobile }">
    <!-- Mobile Header -->
    <div v-if="isMobile" class="mobile-header">
      <v-btn icon variant="text" size="small" @click="drawerOpen = true">
        <v-icon>mdi-menu</v-icon>
      </v-btn>
      <span class="mobile-title">{{ t('conferenceManager.title') }}</span>
      <v-spacer />
      <ResearchGroupTag v-if="currentGroup" :group="currentGroup" />
    </div>

    <!-- Desktop Header -->
    <div v-else class="page-header">
      <div class="header-left">
        <v-icon size="28" color="primary">mdi-school-outline</v-icon>
        <h1 class="title">{{ t('conferenceManager.title') }}</h1>
      </div>
      <div class="header-right">
        <ResearchGroupTag v-if="currentGroup" :group="currentGroup" />
      </div>
    </div>

    <!-- Desktop Stats Summary -->
    <div v-if="stats && !isMobile" class="stats-bar mb-4">
      <v-chip variant="tonal" class="stat-chip mr-2" @click="goTab('conferences')">
        <v-icon start size="16">mdi-school-outline</v-icon>
        {{ stats.total_conferences }} {{ t('conferenceManager.stats.conferences') }}
      </v-chip>
      <v-chip variant="tonal" class="stat-chip mr-2" @click="goTab('papers')">
        <v-icon start size="16">mdi-file-document-outline</v-icon>
        {{ stats.total_papers }} {{ t('conferenceManager.stats.papers') }}
      </v-chip>
      <v-chip
        v-for="(count, status) in stats.papers_by_status"
        :key="status"
        variant="tonal"
        size="small"
        class="stat-chip mr-1"
        @click="goTab('papers', { status })"
      >
        {{ t(`conferenceManager.paper.statuses.${statusKeyMap[status] || status}`) }}: {{ count }}
      </v-chip>
      <v-chip
        v-if="stats.upcoming_deadlines?.length"
        variant="tonal"
        color="warning"
        size="small"
        class="stat-chip mr-1"
        @click="goTab('conferences', { sort: 'submission_deadline' })"
      >
        <v-icon start size="14">mdi-clock-alert-outline</v-icon>
        {{ stats.upcoming_deadlines.length }} {{ t('conferenceManager.stats.upcomingDeadlines') }}
      </v-chip>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-bar" :class="{ 'mb-4': !isMobile }">
      <v-tabs v-model="activeTab" color="primary" :show-arrows="isMobile">
        <v-tab value="conferences">
          <v-icon :start="!isMobile">mdi-school-outline</v-icon>
          <span v-if="!isMobile">{{ t('conferenceManager.tabs.conferences') }}</span>
        </v-tab>
        <v-tab value="papers">
          <v-icon :start="!isMobile">mdi-file-document-outline</v-icon>
          <span v-if="!isMobile">{{ t('conferenceManager.tabs.papers') }}</span>
        </v-tab>
        <v-tab value="calendar">
          <v-icon :start="!isMobile">mdi-calendar</v-icon>
          <span v-if="!isMobile">{{ t('conferenceManager.tabs.calendar') }}</span>
        </v-tab>
        <v-tab value="timeline">
          <v-icon :start="!isMobile">mdi-timeline-outline</v-icon>
          <span v-if="!isMobile">{{ t('conferenceManager.tabs.timeline') }}</span>
        </v-tab>
        <v-tab value="kanban">
          <v-icon :start="!isMobile">mdi-view-column-outline</v-icon>
          <span v-if="!isMobile">{{ t('conferenceManager.tabs.kanban') }}</span>
        </v-tab>
      </v-tabs>
    </div>

    <!-- Tab Content -->
    <v-window v-model="activeTab">
      <v-window-item value="conferences">
        <ConferenceListView :is-mobile="isMobile" />
      </v-window-item>
      <v-window-item value="papers">
        <PaperListView :is-mobile="isMobile" />
      </v-window-item>
      <v-window-item value="calendar">
        <CalendarView />
      </v-window-item>
      <v-window-item value="timeline">
        <TimelineView />
      </v-window-item>
      <v-window-item value="kanban">
        <KanbanView />
      </v-window-item>
    </v-window>

    <!-- Mobile Drawer -->
    <v-navigation-drawer
      v-model="drawerOpen"
      temporary
      width="300"
      class="mobile-drawer"
    >
      <div class="drawer-content">
        <!-- Group Info -->
        <div class="drawer-section">
          <div class="drawer-group-header">
            <v-icon size="24" color="primary">mdi-school-outline</v-icon>
            <span class="drawer-title">{{ t('conferenceManager.title') }}</span>
          </div>
          <ResearchGroupTag v-if="currentGroup" :group="currentGroup" class="mt-2" />
        </div>

        <!-- Stats -->
        <div v-if="stats" class="drawer-section">
          <div class="drawer-section-label">{{ t('conferenceManager.stats.overview') || 'Overview' }}</div>
          <div class="drawer-stats">
            <div class="drawer-stat" @click="goTabAndClose('conferences')">
              <v-icon size="18" color="primary">mdi-school-outline</v-icon>
              <span class="drawer-stat-value">{{ stats.total_conferences }}</span>
              <span class="drawer-stat-label">{{ t('conferenceManager.stats.conferences') }}</span>
            </div>
            <div class="drawer-stat" @click="goTabAndClose('papers')">
              <v-icon size="18" color="primary">mdi-file-document-outline</v-icon>
              <span class="drawer-stat-value">{{ stats.total_papers }}</span>
              <span class="drawer-stat-label">{{ t('conferenceManager.stats.papers') }}</span>
            </div>
          </div>

          <!-- Status chips -->
          <div class="drawer-status-chips">
            <v-chip
              v-for="(count, status) in stats.papers_by_status"
              :key="status"
              variant="tonal"
              size="small"
              class="drawer-chip"
              @click="goTabAndClose('papers', { status })"
            >
              {{ t(`conferenceManager.paper.statuses.${statusKeyMap[status] || status}`) }}: {{ count }}
            </v-chip>
          </div>

          <!-- Upcoming deadlines -->
          <div
            v-if="stats.upcoming_deadlines?.length"
            class="drawer-deadlines"
            @click="goTabAndClose('conferences', { sort: 'submission_deadline' })"
          >
            <v-icon size="16" color="warning">mdi-clock-alert-outline</v-icon>
            <span>{{ stats.upcoming_deadlines.length }} {{ t('conferenceManager.stats.upcomingDeadlines') }}</span>
          </div>
        </div>

        <!-- Navigation -->
        <div class="drawer-section">
          <div class="drawer-section-label">Navigation</div>
          <v-list density="compact" nav>
            <v-list-item
              v-for="tab in tabItems"
              :key="tab.value"
              :active="activeTab === tab.value"
              color="primary"
              @click="goTabAndClose(tab.value)"
            >
              <template #prepend>
                <v-icon>{{ tab.icon }}</v-icon>
              </template>
              <v-list-item-title>{{ tab.label }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </div>
      </div>
    </v-navigation-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useMobile } from '@/composables/useMobile'
import { useConferenceManager } from './composables/useConferenceManager'
import { useResearchGroups } from './composables/useResearchGroups'
import ConferenceListView from './components/ConferenceListView.vue'
import PaperListView from './components/PaperListView.vue'
import CalendarView from './components/CalendarView.vue'
import TimelineView from './components/TimelineView.vue'
import KanbanView from './components/KanbanView.vue'
import ResearchGroupTag from './components/ResearchGroupTag.vue'

const props = defineProps({
  groupId: { type: [String, Number], required: true },
})

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { isMobile } = useMobile()
const { stats, fetchStats, fetchConferences, fetchPapers, fetchSeries, setGroupId } = useConferenceManager()
const { fetchGroup, currentGroup } = useResearchGroups()

const drawerOpen = ref(false)
const VALID_TABS = ['conferences', 'papers', 'calendar', 'timeline', 'kanban']

const activeTab = ref(getInitialTab())

const tabItems = computed(() => [
  { value: 'conferences', icon: 'mdi-school-outline', label: t('conferenceManager.tabs.conferences') },
  { value: 'papers', icon: 'mdi-file-document-outline', label: t('conferenceManager.tabs.papers') },
  { value: 'calendar', icon: 'mdi-calendar', label: t('conferenceManager.tabs.calendar') },
  { value: 'timeline', icon: 'mdi-timeline-outline', label: t('conferenceManager.tabs.timeline') },
  { value: 'kanban', icon: 'mdi-view-column-outline', label: t('conferenceManager.tabs.kanban') },
])

function getInitialTab() {
  const tab = route.query.tab
  return VALID_TABS.includes(tab) ? tab : 'conferences'
}

watch(activeTab, (tab) => {
  router.replace({ query: { ...route.query, tab } })
})

const statusKeyMap = {
  planning: 'planning',
  in_progress: 'inProgress',
  submitted: 'submitted',
  accepted: 'accepted',
  rejected: 'rejected',
  published: 'published',
}

function goTab(tab, queryParams = {}) {
  router.replace({ query: { tab, ...queryParams } })
  activeTab.value = tab
}

function goTabAndClose(tab, queryParams = {}) {
  goTab(tab, queryParams)
  drawerOpen.value = false
}

onMounted(() => {
  setGroupId(props.groupId)
  fetchGroup(props.groupId).catch(() => {})
  fetchStats()
  fetchConferences()
  fetchPapers()
  fetchSeries()
})
</script>

<style scoped>
.conference-manager {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  height: calc(100vh - 94px); /* 64px AppBar + 30px Footer */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.conference-manager.is-mobile {
  padding: 8px 12px;
  height: calc(100vh - 88px);
  height: calc(100dvh - 88px);
}

.conference-manager :deep(.v-window) {
  flex: 1;
  min-height: 0;
}

.conference-manager :deep(.v-window__container),
.conference-manager :deep(.v-window-item) {
  height: 100%;
}

/* Desktop Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left .title {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0;
}

/* Mobile Header */
.mobile-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  flex-shrink: 0;
}

.mobile-title {
  font-size: 1.1rem;
  font-weight: 600;
}

/* Stats Bar (Desktop) */
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.tab-bar {
  flex-shrink: 0;
}

.stat-chip {
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.15s;
}

.stat-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* Mobile Drawer */
.mobile-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.drawer-content {
  padding: 16px;
}

.drawer-section {
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.drawer-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.drawer-group-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.drawer-title {
  font-size: 1.15rem;
  font-weight: 600;
}

.drawer-section-label {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(var(--v-theme-on-surface), 0.4);
  margin-bottom: 10px;
}

.drawer-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.drawer-stat {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  cursor: pointer;
  transition: background 0.15s;
}

.drawer-stat:active {
  background: rgba(var(--v-theme-primary), 0.1);
}

.drawer-stat-value {
  font-size: 1.2rem;
  font-weight: 700;
}

.drawer-stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.drawer-status-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.drawer-chip {
  cursor: pointer;
}

.drawer-deadlines {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(var(--v-theme-warning), 0.08);
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.15s;
}

.drawer-deadlines:active {
  background: rgba(var(--v-theme-warning), 0.16);
}

/* Mobile tab adjustments */
.is-mobile .tab-bar {
  margin-bottom: 4px;
}

.is-mobile .tab-bar :deep(.v-tab) {
  min-width: 48px;
  padding: 0 12px;
}
</style>
