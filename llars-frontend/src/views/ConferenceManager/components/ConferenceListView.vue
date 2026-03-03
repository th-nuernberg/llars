<template>
  <div>
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

      <div class="ranking-chips">
        <v-chip
          :variant="filterRanking === null ? 'flat' : 'outlined'"
          :color="filterRanking === null ? 'primary' : undefined"
          size="small"
          :style="{ borderRadius: '6px 2px 6px 2px' }"
          @click="filterRanking = null"
        >
          {{ t('conferenceManager.filters.allRankings') }}
        </v-chip>
        <v-chip
          v-for="r in CORE_RANKINGS"
          :key="r.value"
          :variant="filterRanking === r.value ? 'flat' : 'outlined'"
          :color="filterRanking === r.value ? r.color : undefined"
          size="small"
          :style="{ borderRadius: '6px 2px 6px 2px' }"
          @click="filterRanking = filterRanking === r.value ? null : r.value"
        >
          {{ r.label }}
        </v-chip>
      </div>

      <v-text-field
        v-model.number="filterYear"
        :label="t('conferenceManager.conference.year')"
        type="number"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="filter-year"
      />

      <v-btn
        :icon="true"
        variant="text"
        size="small"
        :title="t('conferenceManager.series.groupBySeries')"
        :color="groupBySeries ? 'primary' : undefined"
        @click="groupBySeries = !groupBySeries"
      >
        <v-icon>{{ groupBySeries ? 'mdi-format-list-group' : 'mdi-format-list-bulleted' }}</v-icon>
      </v-btn>

      <v-spacer />

      <v-btn
        color="accent"
        variant="outlined"
        :style="{ borderRadius: '16px 4px 16px 4px' }"
        prepend-icon="mdi-auto-fix"
        class="mr-2"
        @click="wizardDialog = true"
      >
        {{ t('conferenceManager.wizard.button') }}
      </v-btn>

      <v-btn
        color="primary"
        :style="{ borderRadius: '16px 4px 16px 4px' }"
        prepend-icon="mdi-plus"
        @click="showCreate"
      >
        {{ t('conferenceManager.conference.create') }}
      </v-btn>
    </div>

    <!-- Legend -->
    <div class="legend mb-3">
      <span class="legend-label">{{ t('conferenceManager.legend.ranking') }}:</span>
      <span v-for="r in CORE_RANKINGS" :key="r.value" class="legend-item">
        <span class="legend-dot" :style="{ backgroundColor: r.color }" />
        {{ r.label }}
      </span>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading" class="list-container">
      <div v-for="n in 6" :key="n" class="skeleton-row">
        <div class="skeleton-cell w40 shimmer" />
        <div class="skeleton-cell w120 shimmer" />
        <div class="skeleton-cell w200 shimmer" />
        <div class="skeleton-cell w100 shimmer" />
        <div class="skeleton-cell w80 shimmer" />
      </div>
    </div>

    <!-- Grouped by Series -->
    <template v-else-if="groupBySeries && filteredConferences.length">
      <div v-for="group in groupedConferences" :key="group.key" class="series-group mb-4">
        <!-- Series Header -->
        <div class="series-header" @click="group.collapsed = !group.collapsed">
          <v-icon size="16" class="mr-2">
            {{ group.collapsed ? 'mdi-chevron-right' : 'mdi-chevron-down' }}
          </v-icon>
          <span class="series-name">{{ group.label }}</span>
          <v-chip size="x-small" variant="tonal" class="ml-2">{{ group.items.length }}</v-chip>
          <v-spacer />
          <v-btn
            v-if="group.seriesId"
            size="x-small"
            variant="text"
            color="primary"
            @click.stop="addEdition(group.seriesId)"
          >
            <v-icon start size="14">mdi-plus</v-icon>
            {{ t('conferenceManager.series.addEdition') }}
          </v-btn>
        </div>

        <!-- Series Rows -->
        <div v-if="!group.collapsed" class="list-container">
          <div class="list-header">
            <div class="col-ranking sortable-col" @click="toggleSort('core_ranking')">
              {{ t('conferenceManager.conference.coreRanking') }}
              <v-icon v-if="sortField === 'core_ranking'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
            </div>
            <div class="col-name sortable-col" @click="toggleSort('acronym')">
              {{ t('conferenceManager.conference.name') }}
              <v-icon v-if="sortField === 'acronym'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
            </div>
            <div class="col-deadline sortable-col" @click="toggleSort('submission_deadline')">
              {{ t('conferenceManager.conference.submissionDeadline') }}
              <v-icon v-if="sortField === 'submission_deadline'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
            </div>
            <div class="col-dates sortable-col" @click="toggleSort('start_date')">
              {{ t('conferenceManager.conference.startDate') }}
              <v-icon v-if="sortField === 'start_date'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
            </div>
            <div class="col-location sortable-col" @click="toggleSort('location')">
              {{ t('conferenceManager.conference.location') }}
              <v-icon v-if="sortField === 'location'" size="12" class="sort-icon">{{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
            </div>
            <div class="col-actions" />
          </div>
          <div
            v-for="conf in group.items"
            :key="conf.id"
            class="list-row"
            @click="editConference(conf)"
          >
            <div class="col-ranking">
              <CoreRankingChip :ranking="conf.core_ranking" size="x-small" />
            </div>
            <div class="col-name">
              <span class="row-title">{{ conf.acronym }} {{ conf.year }}</span>
              <span class="row-subtitle">{{ conf.name }}</span>
            </div>
            <div class="col-deadline">
              <span v-if="conf.submission_deadline" :class="{ 'deadline-soon': isDeadlineSoon(conf.submission_deadline) }">
                {{ formatDate(conf.submission_deadline) }}
              </span>
              <span v-else class="text-placeholder">—</span>
            </div>
            <div class="col-dates">
              <span v-if="conf.start_date">
                {{ formatDateShort(conf.start_date) }}{{ conf.end_date ? ` – ${formatDateShort(conf.end_date)}` : '' }}
              </span>
              <span v-else class="text-placeholder">—</span>
            </div>
            <div class="col-location">
              <template v-if="conf.city || conf.country">
                <span class="location-link" @click.stop="showMap(conf)">
                  <v-icon size="13" class="mr-1" style="opacity: 0.5">mdi-map-marker-outline</v-icon>
                  {{ [conf.city, conf.country].filter(Boolean).join(', ') }}
                </span>
              </template>
              <span v-else class="text-placeholder">—</span>
            </div>
            <div class="col-actions">
              <a v-if="conf.website_url" :href="conf.website_url" target="_blank" class="action-link" @click.stop>
                <v-icon size="15">mdi-open-in-new</v-icon>
              </a>
              <v-btn icon size="x-small" variant="text" class="action-btn" @click.stop="editConference(conf)">
                <v-icon size="15">mdi-pencil-outline</v-icon>
              </v-btn>
              <v-btn icon size="x-small" variant="text" color="error" class="action-btn" @click.stop="confirmDelete(conf)">
                <v-icon size="15">mdi-delete-outline</v-icon>
              </v-btn>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Flat List -->
    <div v-else-if="sortedConferences.length" class="list-container">
      <!-- Header -->
      <div class="list-header">
        <div class="col-ranking sortable-col" @click="toggleSort('core_ranking')">
          {{ t('conferenceManager.conference.coreRanking') }}
          <v-icon v-if="sortField === 'core_ranking'" size="12" class="sort-icon">
            {{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
          </v-icon>
        </div>
        <div class="col-name sortable-col" @click="toggleSort('acronym')">
          {{ t('conferenceManager.conference.name') }}
          <v-icon v-if="sortField === 'acronym'" size="12" class="sort-icon">
            {{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
          </v-icon>
        </div>
        <div class="col-deadline sortable-col" @click="toggleSort('submission_deadline')">
          {{ t('conferenceManager.conference.submissionDeadline') }}
          <v-icon v-if="sortField === 'submission_deadline'" size="12" class="sort-icon">
            {{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
          </v-icon>
        </div>
        <div class="col-dates sortable-col" @click="toggleSort('start_date')">
          {{ t('conferenceManager.conference.startDate') }}
          <v-icon v-if="sortField === 'start_date'" size="12" class="sort-icon">
            {{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
          </v-icon>
        </div>
        <div class="col-location sortable-col" @click="toggleSort('location')">
          {{ t('conferenceManager.conference.location') }}
          <v-icon v-if="sortField === 'location'" size="12" class="sort-icon">
            {{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
          </v-icon>
        </div>
        <div class="col-actions" />
      </div>

      <!-- Rows -->
      <div
        v-for="conf in sortedConferences"
        :key="conf.id"
        class="list-row"
        @click="editConference(conf)"
      >
        <div class="col-ranking">
          <CoreRankingChip :ranking="conf.core_ranking" size="x-small" />
        </div>

        <div class="col-name">
          <div class="d-flex align-center ga-1">
            <span class="row-title">{{ conf.acronym }} {{ conf.year }}</span>
            <v-chip
              v-if="conf.series"
              size="x-small"
              variant="tonal"
              :style="{ borderRadius: '6px 2px 6px 2px' }"
            >
              {{ conf.series.acronym }}
            </v-chip>
          </div>
          <span class="row-subtitle">{{ conf.name }}</span>
        </div>

        <div class="col-deadline">
          <span v-if="conf.submission_deadline" :class="{ 'deadline-soon': isDeadlineSoon(conf.submission_deadline) }">
            {{ formatDate(conf.submission_deadline) }}
          </span>
          <span v-else class="text-placeholder">—</span>
        </div>

        <div class="col-dates">
          <span v-if="conf.start_date">
            {{ formatDateShort(conf.start_date) }}{{ conf.end_date ? ` – ${formatDateShort(conf.end_date)}` : '' }}
          </span>
          <span v-else class="text-placeholder">—</span>
        </div>

        <div class="col-location">
          <template v-if="conf.city || conf.country">
            <span class="location-link" @click.stop="showMap(conf)">
              <v-icon size="13" class="mr-1" style="opacity: 0.5">mdi-map-marker-outline</v-icon>
              {{ [conf.city, conf.country].filter(Boolean).join(', ') }}
            </span>
          </template>
          <span v-else class="text-placeholder">—</span>
        </div>

        <div class="col-actions">
          <a
            v-if="conf.website_url"
            :href="conf.website_url"
            target="_blank"
            class="action-link"
            @click.stop
          >
            <v-icon size="15">mdi-open-in-new</v-icon>
          </a>
          <v-btn icon size="x-small" variant="text" class="action-btn" @click.stop="editConference(conf)">
            <v-icon size="15">mdi-pencil-outline</v-icon>
          </v-btn>
          <v-btn icon size="x-small" variant="text" color="error" class="action-btn" @click.stop="confirmDelete(conf)">
            <v-icon size="15">mdi-delete-outline</v-icon>
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <v-icon size="48" color="primary" class="mb-3" style="opacity: 0.3">mdi-school-outline</v-icon>
      <p class="empty-text">{{ t('conferenceManager.empty.conferences') }}</p>
      <v-btn
        color="primary"
        :style="{ borderRadius: '16px 4px 16px 4px' }"
        prepend-icon="mdi-plus"
        size="small"
        class="mt-2"
        @click="showCreate"
      >
        {{ t('conferenceManager.conference.create') }}
      </v-btn>
    </div>

    <!-- Venue Map Popup -->
    <VenueMapPopup
      v-model="mapPopup"
      :city="mapCity"
      :country="mapCountry"
    />

    <!-- Wizard Dialog -->
    <ConferenceWizardDialog
      v-model="wizardDialog"
      @wizard-result="onWizardResult"
    />

    <!-- Form Dialog -->
    <ConferenceFormDialog
      v-model="formDialog"
      :conference="editingConference"
      @saved="onSaved"
    />

    <!-- Delete Confirm -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>{{ t('conferenceManager.actions.confirmDelete') }}</v-card-title>
        <v-card-text>
          {{ t('conferenceManager.actions.confirmDeleteConference', { name: deletingConference?.acronym }) }}
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
import { ref, reactive, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { CORE_RANKINGS } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'
import CoreRankingChip from './CoreRankingChip.vue'
import ConferenceFormDialog from './ConferenceFormDialog.vue'
import ConferenceWizardDialog from './ConferenceWizardDialog.vue'
import VenueMapPopup from './VenueMapPopup.vue'

const { t } = useI18n()
const route = useRoute()
const { conferences, loading, fetchConferences, deleteConference, getNewEditionDefaults } = useConferenceManager()

const search = ref('')
const filterRanking = ref(null)
const filterYear = ref(null)
const groupBySeries = ref(false)
const sortField = ref(route.query.sort || null)
const sortAsc = ref(true)
const formDialog = ref(false)
const editingConference = ref(null)
const deleteDialog = ref(false)
const deletingConference = ref(null)
const wizardDialog = ref(false)

// Map popup
const mapPopup = ref(false)
const mapCity = ref('')
const mapCountry = ref('')

const filteredConferences = computed(() => {
  let result = conferences.value
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter(c =>
      c.acronym?.toLowerCase().includes(q) ||
      c.name?.toLowerCase().includes(q) ||
      c.city?.toLowerCase().includes(q) ||
      c.country?.toLowerCase().includes(q)
    )
  }
  return result
})

const RANKING_ORDER = { 'A*': 0, 'A': 1, 'B': 2, 'C': 3, 'Unranked': 4 }

function compareFn(a, b, field, asc) {
  let va, vb
  if (field === 'core_ranking') {
    va = RANKING_ORDER[a.core_ranking] ?? 5
    vb = RANKING_ORDER[b.core_ranking] ?? 5
  } else if (field === 'acronym') {
    va = `${a.acronym || ''} ${a.year || 0}`.toLowerCase()
    vb = `${b.acronym || ''} ${b.year || 0}`.toLowerCase()
  } else if (field === 'location') {
    va = [a.city, a.country].filter(Boolean).join(', ').toLowerCase()
    vb = [b.city, b.country].filter(Boolean).join(', ').toLowerCase()
  } else if (field === 'submission_deadline') {
    // Smart deadline sort: future deadlines first (soonest on top), then past
    const da = a.submission_deadline ? new Date(a.submission_deadline) : null
    const db = b.submission_deadline ? new Date(b.submission_deadline) : null
    if (!da && !db) return 0
    if (!da) return 1
    if (!db) return -1
    const now = Date.now()
    const fa = da.getTime() >= now  // future?
    const fb = db.getTime() >= now
    if (fa !== fb) {
      // One future, one past: future always first in asc, past first in desc
      return fa ? (asc ? -1 : 1) : (asc ? 1 : -1)
    }
    if (fa) {
      // Both future: soonest first in asc
      return asc ? da - db : db - da
    }
    // Both past: most recent first in asc
    return asc ? db - da : da - db
  } else {
    va = a[field] || ''
    vb = b[field] || ''
  }
  if (va !== undefined && vb !== undefined) {
    if (!va && !vb) return 0
    if (!va) return 1
    if (!vb) return -1
    if (va < vb) return asc ? -1 : 1
    if (va > vb) return asc ? 1 : -1
  }
  return 0
}

const sortedConferences = computed(() => {
  const list = [...filteredConferences.value]
  if (!sortField.value) return list
  return list.sort((a, b) => compareFn(a, b, sortField.value, sortAsc.value))
})

const groupedConferences = computed(() => {
  const groups = {}
  const standalone = []

  for (const conf of filteredConferences.value) {
    if (conf.series_id && conf.series) {
      const key = `series-${conf.series_id}`
      if (!groups[key]) {
        groups[key] = reactive({
          key,
          seriesId: conf.series_id,
          label: `${conf.series.acronym} — ${conf.series.name}`,
          items: [],
          collapsed: false,
        })
      }
      groups[key].items.push(conf)
    } else {
      standalone.push(conf)
    }
  }

  const result = Object.values(groups).sort((a, b) => a.label.localeCompare(b.label))

  if (standalone.length) {
    result.push(reactive({
      key: 'standalone',
      seriesId: null,
      label: t('conferenceManager.series.standalone'),
      items: standalone,
      collapsed: false,
    }))
  }

  // Apply current sort to items within each group
  if (sortField.value) {
    for (const group of result) {
      group.items.sort((a, b) => compareFn(a, b, sortField.value, sortAsc.value))
    }
  }

  return result
})

onMounted(() => loadData())

watch(() => route.query.sort, (val) => {
  if (val && val !== sortField.value) {
    sortField.value = val
    sortAsc.value = true
  }
})

watch([filterRanking, filterYear], () => loadData())

function loadData() {
  fetchConferences({
    core_ranking: filterRanking.value,
    year: filterYear.value,
  })
}

function toggleSort(field) {
  if (sortField.value === field) {
    if (!sortAsc.value) {
      // Third click: remove sort
      sortField.value = null
    } else {
      // Second click: descending
      sortAsc.value = false
    }
  } else {
    // First click: ascending
    sortField.value = field
    sortAsc.value = true
  }
}

function showCreate() {
  editingConference.value = null
  formDialog.value = true
}

function editConference(item) {
  editingConference.value = { ...item }
  formDialog.value = true
}

function confirmDelete(item) {
  deletingConference.value = item
  deleteDialog.value = true
}

async function doDelete() {
  if (deletingConference.value) {
    await deleteConference(deletingConference.value.id)
  }
  deleteDialog.value = false
  deletingConference.value = null
}

async function addEdition(seriesId) {
  try {
    const defaults = await getNewEditionDefaults(seriesId)
    editingConference.value = defaults ? { ...defaults } : { series_id: seriesId }
    formDialog.value = true
  } catch (err) {
    console.error('Failed to get edition defaults:', err)
    editingConference.value = { series_id: seriesId }
    formDialog.value = true
  }
}

function showMap(conf) {
  mapCity.value = conf.city || ''
  mapCountry.value = conf.country || ''
  mapPopup.value = true
}

function onWizardResult(data) {
  wizardDialog.value = false
  editingConference.value = { ...data }
  formDialog.value = true
}

function onSaved() {
  loadData()
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

function formatDateShort(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric',
  })
}

function isDeadlineSoon(isoStr) {
  if (!isoStr) return false
  const deadline = new Date(isoStr)
  const now = new Date()
  const diffDays = (deadline - now) / (1000 * 60 * 60 * 24)
  return diffDays >= 0 && diffDays <= 14
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-search {
  max-width: 240px;
  min-width: 160px;
}

.filter-year {
  max-width: 110px;
}

.ranking-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
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

/* Series Group */
.series-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  margin-bottom: 4px;
  user-select: none;
  transition: background 0.15s;
}

.series-header:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.series-name {
  font-size: 0.875rem;
  font-weight: 600;
}

/* List */
.list-container {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  overflow: hidden;
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
  background: rgba(var(--v-theme-on-surface), 0.02);
  user-select: none;
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
.col-ranking {
  width: 72px;
  flex-shrink: 0;
}

.col-name {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.col-deadline {
  width: 130px;
  flex-shrink: 0;
  font-size: 0.82rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.col-dates {
  width: 140px;
  flex-shrink: 0;
  font-size: 0.82rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.col-location {
  width: 140px;
  flex-shrink: 0;
  font-size: 0.82rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
  display: flex;
  align-items: center;
}

.col-actions {
  width: 90px;
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
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-subtitle {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.deadline-soon {
  color: #c4735a;
  font-weight: 600;
}

.text-placeholder {
  color: rgba(var(--v-theme-on-surface), 0.2);
}

.location-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: color 0.15s;
}

.location-link:hover {
  color: rgb(var(--v-theme-primary));
  text-decoration: underline;
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

.w40 { width: 40px; }
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

@media (max-width: 960px) {
  .col-dates,
  .col-location {
    display: none;
  }
}

@media (max-width: 600px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-search,
  .filter-year {
    max-width: none;
  }
  .col-deadline {
    display: none;
  }
}
</style>
