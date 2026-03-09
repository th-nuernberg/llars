<template>
  <div class="paper-list-view" :class="{ 'is-mobile': isMobile }">
    <!-- Filter Bar -->
    <div class="filter-bar mb-4">
      <v-text-field
        v-model="search"
        :label="t('conferenceManager.filters.search')"
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="filter-search"
      />

      <div class="status-chips">
        <v-chip
          :variant="filterStatus === null ? 'flat' : 'outlined'"
          :color="filterStatus === null ? 'primary' : undefined"
          size="small"
          :style="{ borderRadius: '6px 2px 6px 2px' }"
          @click="filterStatus = null"
        >
          {{ t('conferenceManager.filters.allStatuses') }}
        </v-chip>
        <v-chip
          v-for="s in PAPER_STATUSES"
          :key="s.value"
          :variant="filterStatus === s.value ? 'flat' : 'outlined'"
          :color="filterStatus === s.value ? s.color : undefined"
          size="small"
          :style="{ borderRadius: '6px 2px 6px 2px' }"
          @click="filterStatus = filterStatus === s.value ? null : s.value"
        >
          <v-icon start size="14">{{ s.icon }}</v-icon>
          <span v-if="!isMobile">{{ t(s.labelKey) }}</span>
        </v-chip>
      </div>

      <v-select
        v-if="!isMobile"
        v-model="filterConference"
        :items="conferenceOptions"
        item-title="label"
        item-value="value"
        :label="t('conferenceManager.paper.conference')"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="filter-conference"
      />

      <v-spacer v-if="!isMobile" />

      <v-btn
        v-if="!isMobile"
        color="primary"
        :style="{ borderRadius: '16px 4px 16px 4px' }"
        prepend-icon="mdi-plus"
        @click="showCreate"
      >
        {{ t('conferenceManager.paper.create') }}
      </v-btn>
    </div>

    <!-- Legend (desktop only) -->
    <div v-if="!isMobile" class="legend mb-3">
      <span class="legend-label">{{ t('conferenceManager.legend.status') }}:</span>
      <span v-for="s in PAPER_STATUSES" :key="s.value" class="legend-item">
        <span class="legend-dot" :style="{ backgroundColor: s.color }" />
        {{ t(s.labelKey) }}
      </span>
    </div>

    <!-- Scrollable Content -->
    <div class="scroll-area">

    <!-- Loading Skeleton -->
    <div v-if="loading" class="list-container">
      <div v-for="n in 6" :key="n" class="skeleton-row">
        <div class="skeleton-cell w60 shimmer" />
        <div class="skeleton-cell w200 shimmer" />
        <div class="skeleton-cell w120 shimmer" />
        <div class="skeleton-cell w100 shimmer" />
        <div class="skeleton-cell w80 shimmer" />
      </div>
    </div>

    <!-- List -->
    <div v-else-if="sortedPapers.length" class="list-container">
      <!-- Header -->
      <div class="list-header">
        <div class="col-status sortable-col" @click="toggleSort('status')">
          {{ t('conferenceManager.paper.status') }}
          <v-icon v-if="sortField === 'status'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
        </div>
        <div class="col-title sortable-col" @click="toggleSort('title')">
          {{ t('conferenceManager.paper.title') }}
          <v-icon v-if="sortField === 'title'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
        </div>
        <div v-if="!isMobile" class="col-conference sortable-col" @click="toggleSort('conference')">
          {{ t('conferenceManager.paper.conference') }}
          <v-icon v-if="sortField === 'conference'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
        </div>
        <div v-if="!isMobile" class="col-authors sortable-col" @click="toggleSort('authors')">
          {{ t('conferenceManager.paper.authors') }}
          <v-icon v-if="sortField === 'authors'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
        </div>
        <div v-if="!isMobile" class="col-updated sortable-col" @click="toggleSort('updated_at')">
          {{ t('conferenceManager.paper.updated') }}
          <v-icon v-if="sortField === 'updated_at'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
        </div>
        <div class="col-actions" />
      </div>

      <!-- Rows -->
      <div
        v-for="paper in sortedPapers"
        :key="paper.id"
        class="list-row"
        @click="editPaper(paper)"
      >
        <div class="col-status">
          <PaperStatusChip :status="paper.status" size="x-small" />
        </div>

        <div class="col-title">
          <span class="row-title">{{ paper.title }}</span>
          <span v-if="paper.keywords?.length" class="row-keywords">
            <span v-for="kw in paper.keywords.slice(0, 3)" :key="kw" class="keyword-tag">{{ kw }}</span>
            <span v-if="paper.keywords.length > 3" class="keyword-overflow">+{{ paper.keywords.length - 3 }}</span>
          </span>
        </div>

        <div v-if="!isMobile" class="col-conference">
          <v-chip
            v-if="paper.conference"
            size="x-small"
            variant="flat"
            :style="{
              borderRadius: '6px 2px 6px 2px',
              backgroundColor: getRankingColor(paper.conference.core_ranking) + '20',
              color: getRankingColor(paper.conference.core_ranking),
            }"
          >
            <span class="conf-ranking-dot" :style="{ backgroundColor: getRankingColor(paper.conference.core_ranking) }" />
            {{ paper.conference.acronym }} {{ paper.conference.year }}
            <span v-if="paper.submissions?.length > 1" class="resubmit-badge">
              (+{{ paper.submissions.length - 1 }})
            </span>
          </v-chip>
          <span v-else class="text-placeholder">—</span>
        </div>

        <div v-if="!isMobile" class="col-authors">
          <template v-if="paper.authors?.length">
            <span class="authors-text">
              {{ paper.authors.map(a => a.display_name || a.external_name || a.username).join(', ') }}
            </span>
          </template>
          <span v-else class="text-placeholder">—</span>
        </div>

        <div v-if="!isMobile" class="col-updated">
          <span v-if="paper.updated_at" class="date-text">{{ formatDate(paper.updated_at) }}</span>
          <span v-else class="text-placeholder">—</span>
        </div>

        <div class="col-actions">
          <a
            v-if="paper.overleaf_url"
            :href="paper.overleaf_url"
            target="_blank"
            class="action-link overleaf"
            title="Overleaf"
            @click.stop
          >
            <v-icon size="15">overleaf</v-icon>
          </a>
          <template v-if="paper.latex_workspace_id">
            <v-tooltip v-if="getLatexAccess(paper.id).hasAccess" :text="t('conferenceManager.paper.openWorkspace')" location="top">
              <template #activator="{ props: tp }">
                <a
                  v-bind="tp"
                  class="action-link llars-latex"
                  @click.stop="router.push(`/LatexCollab/workspace/${paper.latex_workspace_id}`)"
                >
                  <v-icon size="15">llars-latex</v-icon>
                </a>
              </template>
            </v-tooltip>
            <v-tooltip v-else-if="getLatexAccess(paper.id).requestStatus === 'pending'" :text="t('conferenceManager.paper.requestPending')" location="top">
              <template #activator="{ props: tp }">
                <span v-bind="tp" class="action-link disabled">
                  <v-icon size="15">mdi-clock-outline</v-icon>
                </span>
              </template>
            </v-tooltip>
            <v-tooltip v-else :text="t('conferenceManager.paper.requestAccess')" location="top">
              <template #activator="{ props: tp }">
                <a
                  v-bind="tp"
                  class="action-link lock"
                  @click.stop="handleRequestAccess(paper)"
                >
                  <v-icon size="15">mdi-lock-outline</v-icon>
                </a>
              </template>
            </v-tooltip>
          </template>
          <a
            v-if="paper.external_url"
            :href="paper.external_url"
            target="_blank"
            class="action-link"
            @click.stop
          >
            <v-icon size="15">mdi-open-in-new</v-icon>
          </a>
          <v-btn icon size="x-small" variant="text" class="action-btn" @click.stop="editPaper(paper)">
            <v-icon size="15">mdi-pencil-outline</v-icon>
          </v-btn>
          <v-btn icon size="x-small" variant="text" color="error" class="action-btn" @click.stop="confirmDelete(paper)">
            <v-icon size="15">mdi-delete-outline</v-icon>
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <v-icon size="48" color="primary" class="mb-3" style="opacity: 0.3">mdi-file-document-outline</v-icon>
      <p class="empty-text">{{ t('conferenceManager.empty.papers') }}</p>
      <v-btn
        color="primary"
        :style="{ borderRadius: '16px 4px 16px 4px' }"
        prepend-icon="mdi-plus"
        size="small"
        class="mt-2"
        @click="showCreate"
      >
        {{ t('conferenceManager.paper.create') }}
      </v-btn>
    </div>

    </div>

    <!-- Form Dialog -->
    <PaperFormDialog
      v-model="formDialog"
      :paper="editingPaper"
      @saved="onSaved"
    />

    <!-- Mobile FAB -->
    <v-btn
      v-if="isMobile"
      icon
      color="primary"
      size="default"
      class="mobile-fab"
      elevation="4"
      @click="showCreate"
    >
      <v-icon>mdi-plus</v-icon>
    </v-btn>

    <!-- Delete Confirm -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>{{ t('conferenceManager.actions.confirmDelete') }}</v-card-title>
        <v-card-text>
          {{ t('conferenceManager.actions.confirmDeletePaper', { name: deletingPaper?.title }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">{{ t('conferenceManager.actions.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" @click="doDelete">{{ t('conferenceManager.actions.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import { useSnackbar } from '@/composables/useSnackbar'
import { PAPER_STATUSES, getStatusConfig, getRankingColor } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'
import PaperStatusChip from './PaperStatusChip.vue'
import PaperFormDialog from './PaperFormDialog.vue'

const props = defineProps({
  isMobile: { type: Boolean, default: false },
})

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const { showSuccess } = useSnackbar()
const { conferences, papers, loading, fetchPapers, fetchConferences, deletePaper, latexAccessMap, requestLatexAccess } = useConferenceManager()

const search = ref('')
const filterStatus = ref(route.query.status || null)
const sortField = ref(null)
const sortAsc = ref(true)
const filterConference = ref(null)
const formDialog = ref(false)
const editingPaper = ref(null)
const deleteDialog = ref(false)
const deletingPaper = ref(null)

const conferenceOptions = computed(() => [
  { label: t('conferenceManager.filters.allConferences'), value: null },
  ...conferences.value.map(c => ({
    label: `${c.acronym} ${c.year}`,
    value: c.id,
  })),
])

const STATUS_ORDER = { planning: 0, in_progress: 1, submitted: 2, accepted: 3, rejected: 4, published: 5 }

const filteredPapers = computed(() => {
  let result = papers.value
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter(p =>
      p.title?.toLowerCase().includes(q) ||
      p.description?.toLowerCase().includes(q) ||
      p.authors?.some(a => (a.display_name || a.external_name || '').toLowerCase().includes(q))
    )
  }
  return result
})

const sortedPapers = computed(() => {
  const list = [...filteredPapers.value]
  const field = sortField.value
  if (!field) return list
  const asc = sortAsc.value

  return list.sort((a, b) => {
    let va, vb
    if (field === 'status') {
      va = STATUS_ORDER[a.status] ?? 9
      vb = STATUS_ORDER[b.status] ?? 9
    } else if (field === 'title') {
      va = (a.title || '').toLowerCase()
      vb = (b.title || '').toLowerCase()
    } else if (field === 'conference') {
      va = a.conference ? `${a.conference.acronym} ${a.conference.year}` : ''
      vb = b.conference ? `${b.conference.acronym} ${b.conference.year}` : ''
    } else if (field === 'authors') {
      va = (a.authors || []).map(x => x.display_name || x.external_name || '').join(', ').toLowerCase()
      vb = (b.authors || []).map(x => x.display_name || x.external_name || '').join(', ').toLowerCase()
    } else {
      va = a[field] || ''
      vb = b[field] || ''
    }
    if (!va && !vb) return 0
    if (!va) return 1
    if (!vb) return -1
    if (va < vb) return asc ? -1 : 1
    if (va > vb) return asc ? 1 : -1
    return 0
  })
})

function toggleSort(field) {
  if (sortField.value === field) {
    if (!sortAsc.value) {
      sortField.value = null
    } else {
      sortAsc.value = false
    }
  } else {
    sortField.value = field
    sortAsc.value = true
  }
}

onMounted(() => {
  fetchConferences()
  loadData()
})

watch(() => route.query.status, (val) => {
  if (val && val !== filterStatus.value) {
    filterStatus.value = val
  }
})

watch([filterStatus, filterConference], () => loadData())

function loadData() {
  fetchPapers({
    status: filterStatus.value,
    conference_id: filterConference.value,
  })
}

function showCreate() {
  editingPaper.value = null
  formDialog.value = true
}

function editPaper(item) {
  editingPaper.value = { ...item }
  formDialog.value = true
}

function confirmDelete(item) {
  deletingPaper.value = item
  deleteDialog.value = true
}

async function doDelete() {
  if (deletingPaper.value) {
    await deletePaper(deletingPaper.value.id)
  }
  deleteDialog.value = false
  deletingPaper.value = null
}

function onSaved() {
  loadData()
}

function getLatexAccess(paperId) {
  const entry = latexAccessMap.value[String(paperId)]
  return {
    hasAccess: entry?.has_access || false,
    requestStatus: entry?.request_status || null,
  }
}

async function handleRequestAccess(paper) {
  try {
    await requestLatexAccess(paper.latex_workspace_id)
    showSuccess(t('conferenceManager.paper.requestSent'))
  } catch (err) {
    console.error('Request access failed:', err)
  }
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}
</script>

<style scoped>
.paper-list-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.scroll-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.scroll-area::-webkit-scrollbar {
  width: 6px;
}

.scroll-area::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.filter-search {
  max-width: 240px;
  min-width: 160px;
}

.filter-conference {
  max-width: 200px;
}

/* Legend */
.legend {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.legend-label {
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.45);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  font-size: 0.65rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.status-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* List */
.list-container {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(var(--v-theme-on-surface), 0.45);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface), 1);
  user-select: none;
  position: sticky;
  top: 0;
  z-index: 1;
  border-radius: 7px 7px 0 0;
}

.list-row:last-child {
  border-radius: 0 0 7px 7px;
}

.sortable-col {
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: color 0.15s;
}

.sortable-col:hover {
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.sort-icon {
  margin-left: auto;
  opacity: 0.7;
  flex-shrink: 0;
}

.list-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  cursor: pointer;
  transition: background 0.15s;
}

.list-row:last-child {
  border-bottom: none;
}

.list-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.03);
}

/* Columns */
.col-status {
  width: 100px;
  flex-shrink: 0;
}

.col-title {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.col-conference {
  width: 110px;
  flex-shrink: 0;
}

.col-authors {
  width: 160px;
  flex-shrink: 0;
  min-width: 0;
}

.col-updated {
  width: 110px;
  flex-shrink: 0;
}

.col-actions {
  width: 100px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s;
}

.list-row:hover .col-actions {
  opacity: 1;
}

/* Row content */
.row-title {
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-keywords {
  display: flex;
  gap: 4px;
  align-items: center;
  flex-wrap: nowrap;
  overflow: hidden;
}

.keyword-tag {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.45);
  background: rgba(var(--v-theme-on-surface), 0.05);
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.keyword-overflow {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.35);
  white-space: nowrap;
}

.authors-text {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.date-text {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.text-placeholder {
  color: rgba(var(--v-theme-on-surface), 0.2);
}

.action-link {
  color: rgba(var(--v-theme-on-surface), 0.4);
  text-decoration: none;
  display: flex;
  align-items: center;
  padding: 2px;
  transition: color 0.15s;
}

.action-link:hover {
  color: rgb(var(--v-theme-primary));
}

.action-link.overleaf:hover {
  color: #4caf50;
}

.action-link.llars-latex {
  color: #88c4c8;
  cursor: pointer;
}

.action-link.llars-latex:hover {
  color: #6bb0b5;
}

.action-link.lock {
  cursor: pointer;
}

.action-link.lock:hover {
  color: #e8a087;
}

.action-link.disabled {
  color: rgba(var(--v-theme-on-surface), 0.25);
  cursor: default;
  display: flex;
  align-items: center;
  padding: 2px;
}

.conf-ranking-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
  flex-shrink: 0;
}

.resubmit-badge {
  margin-left: 4px;
  opacity: 0.6;
  font-size: 0.7rem;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 56px 24px;
  text-align: center;
}

.empty-text {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
}

/* Skeleton */
.skeleton-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.skeleton-cell {
  height: 14px;
  border-radius: 4px;
}

.w60 { width: 60px; }
.w80 { width: 80px; }
.w100 { width: 100px; }
.w120 { width: 120px; }
.w200 { width: 200px; flex: 1; }

.shimmer {
  background: linear-gradient(
    90deg,
    rgba(var(--v-theme-on-surface), 0.05) 25%,
    rgba(var(--v-theme-on-surface), 0.09) 50%,
    rgba(var(--v-theme-on-surface), 0.05) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Mobile FAB */
.mobile-fab {
  position: absolute;
  bottom: 16px;
  right: 16px;
  z-index: 2;
  border-radius: 16px 4px 16px 4px !important;
}

/* Mobile styles */
.is-mobile .filter-bar {
  gap: 8px;
  margin-bottom: 8px !important;
}

.is-mobile .filter-search {
  max-width: none;
  min-width: 0;
}

.is-mobile .status-chips {
  gap: 4px;
}

.is-mobile .status-chips .v-chip {
  font-size: 0.7rem;
}

.is-mobile .row-title {
  font-size: 0.82rem;
}

.is-mobile .col-status {
  width: 70px;
}

.is-mobile .col-actions {
  width: 60px;
  opacity: 1;
}

.is-mobile .list-header,
.is-mobile .list-row {
  padding: 8px 10px;
  gap: 6px;
}

@media (max-width: 960px) {
  .col-authors,
  .col-updated {
    display: none;
  }
}

@media (max-width: 600px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-search,
  .filter-conference {
    max-width: none;
  }
  .col-conference {
    display: none;
  }
}
</style>
