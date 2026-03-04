<template>
  <div class="conference-manager">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <v-icon size="28" color="primary">mdi-school-outline</v-icon>
        <h1 class="title">{{ t('conferenceManager.title') }}</h1>
      </div>
      <div class="header-right">
        <ResearchGroupTag v-if="currentGroup" :group="currentGroup" />
      </div>
    </div>

    <!-- Stats Summary -->
    <div v-if="stats" class="stats-bar mb-4">
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
    <div class="tab-bar mb-4">
      <v-tabs v-model="activeTab" color="primary">
        <v-tab value="conferences">
          <v-icon start>mdi-school-outline</v-icon>
          {{ t('conferenceManager.tabs.conferences') }}
        </v-tab>
        <v-tab value="papers">
          <v-icon start>mdi-file-document-outline</v-icon>
          {{ t('conferenceManager.tabs.papers') }}
        </v-tab>
        <v-tab value="calendar">
          <v-icon start>mdi-calendar</v-icon>
          {{ t('conferenceManager.tabs.calendar') }}
        </v-tab>
        <v-tab value="timeline">
          <v-icon start>mdi-timeline-outline</v-icon>
          {{ t('conferenceManager.tabs.timeline') }}
        </v-tab>
        <v-tab value="kanban">
          <v-icon start>mdi-view-column-outline</v-icon>
          {{ t('conferenceManager.tabs.kanban') }}
        </v-tab>
      </v-tabs>
    </div>

    <!-- Tab Content -->
    <v-window v-model="activeTab">
      <v-window-item value="conferences">
        <ConferenceListView />
      </v-window-item>
      <v-window-item value="papers">
        <PaperListView />
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
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
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
const { stats, fetchStats, fetchConferences, fetchPapers, fetchSeries, setGroupId } = useConferenceManager()
const { fetchGroup, currentGroup } = useResearchGroups()

const VALID_TABS = ['conferences', 'papers', 'calendar', 'timeline', 'kanban']

const activeTab = ref(getInitialTab())

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
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
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

.stats-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.stat-chip {
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.15s;
}

.stat-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}
</style>
