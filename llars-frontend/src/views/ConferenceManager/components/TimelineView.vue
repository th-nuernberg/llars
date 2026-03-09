<template>
  <div class="timeline-view">
    <!-- Controls bar -->
    <div class="timeline-controls">
      <div class="controls-left">
        <v-btn-group density="compact" variant="outlined" divided>
          <v-btn
            v-for="z in zoomLevels"
            :key="z.months"
            size="small"
            :variant="zoom === z.months ? 'flat' : 'outlined'"
            :color="zoom === z.months ? 'primary' : undefined"
            @click="zoom = z.months"
          >
            {{ t(z.labelKey) }}
          </v-btn>
        </v-btn-group>
        <v-btn
          size="small"
          variant="tonal"
          color="primary"
          prepend-icon="mdi-crosshairs"
          :style="{ borderRadius: '8px 2px 8px 2px' }"
          @click="scrollToToday"
        >
          {{ t('conferenceManager.timeline.today') }}
        </v-btn>
      </div>
    </div>

    <!-- Legend -->
    <div class="timeline-legend">
      <div class="legend-item">
        <span class="legend-chip legend-chip--deadline">
          <v-icon size="12">mdi-file-document-outline</v-icon>
        </span>
        <span class="legend-text">{{ t('conferenceManager.timeline.deadline') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-chip legend-chip--notification">
          <v-icon size="12">mdi-bell-outline</v-icon>
        </span>
        <span class="legend-text">{{ t('conferenceManager.timeline.notification') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-chip legend-chip--conference">
          <v-icon size="12">mdi-account-group-outline</v-icon>
        </span>
        <span class="legend-text">{{ t('conferenceManager.timeline.conferencePeriod') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-today-line" />
        <span class="legend-text">{{ t('conferenceManager.timeline.todayMarker') }}</span>
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="!conferences.length && loading" class="timeline-skeleton">
      <div class="skeleton-axis shimmer" />
      <div class="skeleton-months">
        <div v-for="n in 6" :key="n" class="skeleton-month shimmer" />
      </div>
      <div class="skeleton-cards">
        <div v-for="n in 3" :key="n" class="skeleton-card shimmer" :style="{ left: `${12 + n * 22}%`, top: n % 2 === 0 ? '18%' : '22%' }" />
      </div>
    </div>

    <!-- Timeline -->
    <div v-else-if="timelineEvents.length" ref="scrollContainer" class="timeline-container">
      <div class="timeline-track" :style="{ width: trackWidth + 'px' }">
        <!-- Month columns -->
        <div
          v-for="month in visibleMonths"
          :key="month.key"
          class="month-marker"
          :style="{ left: month.position + 'px' }"
        >
          <div class="month-line" />
          <div class="month-label">{{ month.label }}</div>
        </div>

        <!-- Central axis -->
        <div class="axis-line" />

        <!-- Today indicator -->
        <div
          v-if="todayPosition >= 0"
          class="today-marker"
          :style="{ left: todayPosition + 'px' }"
        >
          <div class="today-line" />
          <div class="today-diamond" />
          <div class="today-label">{{ t('conferenceManager.timeline.today') }}</div>
        </div>

        <!-- Conference spans — below axis -->
        <div
          v-for="span in conferenceSpans"
          :key="'span-' + span.id"
          class="conference-span"
          :class="{ 'span-hovered': hoveredSpan === span.id }"
          :style="{
            left: span.startX + 'px',
            width: Math.max(span.endX - span.startX, 80) + 'px',
            top: `calc(60% + 16px + ${span.row * 38}px)`,
          }"
          @mouseenter="onSpanEnter($event, span)"
          @mouseleave="onSpanLeave"
          @click="openDetail(span.conference)"
        >
          <div class="span-icon">
            <v-icon size="13" color="#327a5e">mdi-account-group-outline</v-icon>
          </div>
          <div class="span-content">
            <div class="span-label">{{ span.conference.acronym }}</div>
            <div class="span-dates">{{ formatDateShort(span.date) }} – {{ formatDateShort(span.endDate || span.date) }}</div>
          </div>
        </div>

        <!-- Span tooltip (teleported to body) -->
        <Teleport to="body">
          <Transition name="span-tooltip-fade">
            <div
              v-if="hoveredSpan !== null && tooltipSpan"
              class="span-tooltip"
              :style="spanTooltipStyle"
            >
              <div class="span-tooltip-name">{{ tooltipSpan.conference.name }}</div>
              <div class="span-tooltip-date-row">
                <v-icon size="14" color="#327a5e">mdi-calendar-range</v-icon>
                <span class="span-tooltip-date">{{ formatDate(tooltipSpan.date) }}</span>
                <span class="span-tooltip-arrow">→</span>
                <span class="span-tooltip-date">{{ formatDate(tooltipSpan.endDate || tooltipSpan.date) }}</span>
              </div>
              <div class="span-tooltip-duration">
                {{ getDurationDays(tooltipSpan.date, tooltipSpan.endDate) }}
              </div>
              <div v-if="tooltipSpan.conference.city || tooltipSpan.conference.country" class="span-tooltip-location">
                <v-icon size="12">mdi-map-marker-outline</v-icon>
                {{ [tooltipSpan.conference.city, tooltipSpan.conference.country].filter(Boolean).join(', ') }}
              </div>
              <div v-if="tooltipSpan.conference.core_ranking" class="span-tooltip-core">
                <v-icon size="12">mdi-star-outline</v-icon>
                CORE {{ tooltipSpan.conference.core_ranking }}
              </div>
            </div>
          </Transition>
        </Teleport>

        <!-- Stem lines from cards to axis -->
        <div
          v-for="(evt, i) in eventCards"
          :key="'stem-' + i"
          class="card-stem"
          :class="'stem-' + evt.type"
          :style="{
            left: (evt.x + 55) + 'px',
            top: `calc(60% - ${(evt.row + 1) * 56 + 4}px)`,
            height: `${4 + (evt.row + 1) * 56}px`,
          }"
        />

        <!-- Event cards — above axis -->
        <div
          v-for="(evt, i) in eventCards"
          :key="'card-' + i"
          class="event-card"
          :class="[
            'card-' + evt.type,
            { 'card-hovered': hoveredCard === i, 'card-active': activeDot === i },
          ]"
          :style="{
            left: evt.x + 'px',
            top: `calc(60% - ${48 + (evt.row + 1) * 56}px)`,
            animationDelay: (i * 60) + 'ms',
          }"
          @mouseenter="onCardEnter($event, i, evt)"
          @mouseleave="onCardLeave"
          @click.stop="toggleDetail(i, evt)"
        >
          <div class="card-accent" />
          <div class="card-icon">
            <v-icon size="15">
              {{ evt.type === 'deadline' ? 'mdi-file-document-outline' : 'mdi-bell-outline' }}
            </v-icon>
          </div>
          <div class="card-body">
            <div class="card-title">{{ evt.conference.acronym }}</div>
            <div class="card-date">{{ formatDateShort(evt.date) }}</div>
          </div>
        </div>

        <!-- Card tooltip (teleported to body) -->
        <Teleport to="body">
          <Transition name="card-tooltip-fade">
            <div
              v-if="hoveredCard !== null && tooltipCard"
              class="card-tooltip"
              :class="'card-tooltip--' + tooltipCard.type"
              :style="cardTooltipStyle"
            >
              <div class="card-tooltip-type">
                <v-icon size="13">
                  {{ tooltipCard.type === 'deadline' ? 'mdi-file-document-outline' : 'mdi-bell-outline' }}
                </v-icon>
                {{ t(`conferenceManager.timeline.${tooltipCard.type}`) }}
              </div>
              <div class="card-tooltip-name">{{ tooltipCard.conference.name }}</div>
              <div class="card-tooltip-date-row" :class="'date-row--' + tooltipCard.type">
                <v-icon size="14">mdi-calendar</v-icon>
                <span class="card-tooltip-date">{{ formatDate(tooltipCard.date) }}</span>
              </div>
              <div v-if="tooltipCard.conference.start_date" class="card-tooltip-conf-dates">
                <v-icon size="12">mdi-calendar-range</v-icon>
                {{ t('conferenceManager.timeline.conferencePeriod') }}:
                {{ formatDateShort(tooltipCard.conference.start_date) }} – {{ formatDateShort(tooltipCard.conference.end_date || tooltipCard.conference.start_date) }}
              </div>
              <div v-if="tooltipCard.conference.city || tooltipCard.conference.country" class="card-tooltip-location">
                <v-icon size="12">mdi-map-marker-outline</v-icon>
                {{ [tooltipCard.conference.city, tooltipCard.conference.country].filter(Boolean).join(', ') }}
              </div>
              <div v-if="tooltipCard.conference.core_ranking" class="card-tooltip-core">
                <v-icon size="12">mdi-star-outline</v-icon>
                CORE {{ tooltipCard.conference.core_ranking }}
              </div>
            </div>
          </Transition>
        </Teleport>

        <!-- Detail card (Teleport) -->
        <Teleport to="body">
          <Transition name="detail-fade">
            <div
              v-if="activeDot !== null && detailEvent"
              class="detail-overlay"
              @click="activeDot = null"
            >
              <div
                class="detail-card"
                :style="detailCardStyle"
                @click.stop
              >
                <div class="detail-header">
                  <span class="detail-type" :class="'type-' + detailEvent.type">
                    <v-icon size="14">{{ getTypeIcon(detailEvent.type) }}</v-icon>
                    {{ t(`conferenceManager.timeline.${detailEvent.type}`) }}
                  </span>
                  <v-btn icon size="x-small" variant="text" @click="activeDot = null">
                    <v-icon size="16">mdi-close</v-icon>
                  </v-btn>
                </div>
                <div class="detail-title">{{ detailEvent.conference.acronym }}</div>
                <div class="detail-name">{{ detailEvent.conference.name }}</div>
                <div class="detail-meta">
                  <div class="detail-meta-row">
                    <v-icon size="14">mdi-calendar-outline</v-icon>
                    {{ formatDate(detailEvent.date) }}
                  </div>
                  <div v-if="detailEvent.conference.city || detailEvent.conference.country" class="detail-meta-row">
                    <v-icon size="14">mdi-map-marker-outline</v-icon>
                    {{ [detailEvent.conference.city, detailEvent.conference.country].filter(Boolean).join(', ') }}
                  </div>
                  <div v-if="detailEvent.conference.core_ranking" class="detail-meta-row">
                    <v-icon size="14">mdi-star-outline</v-icon>
                    CORE {{ detailEvent.conference.core_ranking }}
                  </div>
                </div>
                <div class="detail-actions">
                  <v-btn
                    size="small"
                    variant="tonal"
                    color="primary"
                    :style="{ borderRadius: '8px 2px 8px 2px' }"
                    @click="openEdit(detailEvent.conference)"
                  >
                    <v-icon start size="14">mdi-pencil-outline</v-icon>
                    {{ t('conferenceManager.conference.edit') }}
                  </v-btn>
                  <a
                    v-if="detailEvent.conference.website_url"
                    :href="detailEvent.conference.website_url"
                    target="_blank"
                    class="detail-link"
                  >
                    <v-icon size="14">mdi-open-in-new</v-icon>
                    Website
                  </a>
                </div>
              </div>
            </div>
          </Transition>
        </Teleport>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <v-icon size="48" color="primary" class="mb-3" style="opacity: 0.3">mdi-timeline-outline</v-icon>
      <p class="empty-text">{{ t('conferenceManager.timeline.noEvents') }}</p>
    </div>

    <!-- Edit dialog -->
    <ConferenceFormDialog
      v-model="showEditDialog"
      :conference="selectedConference"
      @saved="onSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConferenceManager } from '../composables/useConferenceManager'
import ConferenceFormDialog from './ConferenceFormDialog.vue'

const { t, locale } = useI18n()
const { conferences, loading, fetchConferences } = useConferenceManager()

const showEditDialog = ref(false)
const selectedConference = ref(null)
const scrollContainer = ref(null)
const zoom = ref(6)
const hoveredCard = ref(null)
const tooltipCard = ref(null)
const cardTooltipStyle = ref({})
const hoveredSpan = ref(null)
const tooltipSpan = ref(null)
const spanTooltipStyle = ref({})
const activeDot = ref(null)
const detailEvent = ref(null)
const detailCardStyle = ref({})

const PIXELS_PER_DAY_BASE = 4
const zoomLevels = [
  { months: 3, labelKey: 'conferenceManager.timeline.months3' },
  { months: 6, labelKey: 'conferenceManager.timeline.months6' },
  { months: 12, labelKey: 'conferenceManager.timeline.months12' },
]

const pixelsPerDay = computed(() => {
  if (zoom.value === 3) return PIXELS_PER_DAY_BASE * 3
  if (zoom.value === 12) return PIXELS_PER_DAY_BASE
  return PIXELS_PER_DAY_BASE * 1.5
})

const timeRange = computed(() => {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth() - 1, 1)
  const end = new Date(now.getFullYear(), now.getMonth() + zoom.value + 1, 0)
  return { start, end }
})

const totalDays = computed(() => {
  return Math.ceil((timeRange.value.end - timeRange.value.start) / (1000 * 60 * 60 * 24))
})

const trackWidth = computed(() => totalDays.value * pixelsPerDay.value)

function dateToX(dateStr) {
  const d = new Date(dateStr)
  const diff = (d - timeRange.value.start) / (1000 * 60 * 60 * 24)
  return diff * pixelsPerDay.value
}

const visibleMonths = computed(() => {
  const months = []
  const { start, end } = timeRange.value
  const d = new Date(start.getFullYear(), start.getMonth(), 1)
  while (d <= end) {
    const label = d.toLocaleDateString(locale.value, { month: 'short', year: 'numeric' })
    months.push({
      key: `${d.getFullYear()}-${d.getMonth()}`,
      label,
      position: dateToX(d.toISOString()),
    })
    d.setMonth(d.getMonth() + 1)
  }
  return months
})

const todayPosition = computed(() => dateToX(new Date().toISOString()))

const timelineEvents = computed(() => {
  const events = []
  for (const conf of conferences.value) {
    if (conf.submission_deadline) {
      events.push({ type: 'deadline', date: conf.submission_deadline, conference: conf })
    }
    if (conf.notification_date) {
      events.push({ type: 'notification', date: conf.notification_date, conference: conf })
    }
    if (conf.start_date) {
      events.push({ type: 'span', date: conf.start_date, endDate: conf.end_date, conference: conf })
    }
  }
  return events
})

function assignRows(items, minGap) {
  const sorted = [...items].sort((a, b) => (a.x || dateToX(a.date)) - (b.x || dateToX(b.date)))
  const rowEnds = []
  return sorted.map(item => {
    const x = item.x || dateToX(item.date)
    let row = rowEnds.findIndex(end => x - end > minGap)
    if (row === -1) {
      row = rowEnds.length
      rowEnds.push(0)
    }
    const endX = item.endX || x + 130
    rowEnds[row] = endX
    return { ...item, row, x }
  })
}

const eventCards = computed(() => {
  const cards = timelineEvents.value
    .filter(e => e.type !== 'span')
    .map(e => ({ ...e, x: dateToX(e.date) }))
  return assignRows(cards, 130)
})

const conferenceSpans = computed(() => {
  const spans = timelineEvents.value
    .filter(e => e.type === 'span')
    .map(e => ({
      ...e,
      id: e.conference.id,
      startX: dateToX(e.date),
      endX: e.endDate ? dateToX(e.endDate) : dateToX(e.date) + 80,
    }))
  const sorted = [...spans].sort((a, b) => a.startX - b.startX)
  const rowEnds = []
  return sorted.map(span => {
    let row = rowEnds.findIndex(end => span.startX - end > 10)
    if (row === -1) {
      row = rowEnds.length
      rowEnds.push(0)
    }
    rowEnds[row] = span.endX
    return { ...span, row }
  })
})

function onCardEnter(event, i, evt) {
  hoveredCard.value = i
  tooltipCard.value = evt
  const rect = event.currentTarget.getBoundingClientRect()
  const tooltipWidth = 280
  let left = rect.left + rect.width / 2 - tooltipWidth / 2
  left = Math.max(12, Math.min(left, window.innerWidth - tooltipWidth - 12))
  cardTooltipStyle.value = {
    position: 'fixed',
    left: left + 'px',
    top: (rect.top - 10) + 'px',
    width: tooltipWidth + 'px',
    transform: 'translateY(-100%)',
  }
}

function onCardLeave() {
  hoveredCard.value = null
  tooltipCard.value = null
}

function onSpanEnter(event, span) {
  hoveredSpan.value = span.id
  tooltipSpan.value = span
  const rect = event.currentTarget.getBoundingClientRect()
  const tooltipWidth = 280
  let left = rect.left + rect.width / 2 - tooltipWidth / 2
  left = Math.max(12, Math.min(left, window.innerWidth - tooltipWidth - 12))
  spanTooltipStyle.value = {
    position: 'fixed',
    left: left + 'px',
    top: (rect.top - 10) + 'px',
    width: tooltipWidth + 'px',
    transform: 'translateY(-100%)',
  }
}

function onSpanLeave() {
  hoveredSpan.value = null
  tooltipSpan.value = null
}

function getTypeIcon(type) {
  if (type === 'deadline') return 'mdi-file-document-outline'
  if (type === 'notification') return 'mdi-bell-outline'
  return 'mdi-account-group-outline'
}

function toggleDetail(i, evt) {
  if (activeDot.value === i) {
    activeDot.value = null
    detailEvent.value = null
    return
  }
  activeDot.value = i
  detailEvent.value = evt

  nextTick(() => {
    const allCards = scrollContainer.value?.querySelectorAll('.event-card')
    const cardEl = allCards?.[i]
    if (!cardEl) {
      detailCardStyle.value = { top: '200px', left: '50%', transform: 'translateX(-50%)' }
      return
    }
    const rect = cardEl.getBoundingClientRect()
    const cardWidth = 320
    let left = rect.left + rect.width / 2 - cardWidth / 2
    left = Math.max(16, Math.min(left, window.innerWidth - cardWidth - 16))
    // Place above or below depending on space
    let top = rect.bottom + 10
    if (top + 250 > window.innerHeight) {
      top = rect.top - 260
    }
    detailCardStyle.value = {
      position: 'fixed',
      top: top + 'px',
      left: left + 'px',
      width: cardWidth + 'px',
    }
  })
}

function openDetail(conf) {
  selectedConference.value = conf
  showEditDialog.value = true
}

function openEdit(conf) {
  activeDot.value = null
  detailEvent.value = null
  selectedConference.value = conf
  showEditDialog.value = true
}

function scrollToToday() {
  if (!scrollContainer.value) return
  const containerWidth = scrollContainer.value.clientWidth
  scrollContainer.value.scrollTo({
    left: todayPosition.value - containerWidth / 2,
    behavior: 'smooth',
  })
}

function onSaved() {
  fetchConferences()
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

function getDurationDays(startStr, endStr) {
  if (!startStr || !endStr) return ''
  const start = new Date(startStr)
  const end = new Date(endStr)
  const days = Math.round((end - start) / (1000 * 60 * 60 * 24)) + 1
  if (days <= 1) return t('conferenceManager.timeline.oneDay')
  return t('conferenceManager.timeline.nDays', { n: days })
}

function formatDateShort(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric',
  })
}

onMounted(async () => {
  await nextTick()
  scrollToToday()
})
</script>

<style scoped>
/* ── Controls ─────────────────────────────────── */
.timeline-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.controls-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.controls-left :deep(.v-btn) {
  font-size: 0.8rem;
}

.controls-left :deep(.v-btn-group) {
  border-radius: 8px 2px 8px 2px;
  overflow: hidden;
}

/* ── Legend ────────────────────────────────────── */
.timeline-legend {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 16px;
  margin-bottom: 12px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 10px 3px 10px 3px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-text {
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
}

.legend-chip {
  width: 28px;
  height: 22px;
  border-radius: 6px 2px 6px 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.legend-chip--deadline {
  background: rgba(196, 115, 90, 0.1);
  border-left: 3px solid #c4735a;
  color: #c4735a;
}

.legend-chip--notification {
  background: rgba(74, 142, 147, 0.1);
  border-left: 3px solid #4a8e93;
  color: #4a8e93;
}

.legend-chip--conference {
  background: rgba(74, 158, 126, 0.1);
  border-left: 3px solid #4a9e7e;
  color: #327a5e;
}

.legend-today-line {
  width: 2px;
  height: 18px;
  background: #c4735a;
  border-radius: 1px;
  flex-shrink: 0;
  position: relative;
  margin: 0 6px;
}

.legend-today-line::after {
  content: '';
  position: absolute;
  top: -3px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 6px;
  height: 6px;
  background: #c4735a;
  border-radius: 1px;
}

/* ── Timeline View Layout ────────────────────── */
.timeline-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Timeline Container ───────────────────────── */
.timeline-container {
  flex: 1;
  min-height: 0;
  overflow-x: auto;
  overflow-y: hidden;
  position: relative;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 14px 4px 14px 4px;
  background: rgb(var(--v-theme-surface));
  scroll-behavior: smooth;
}

.timeline-container::-webkit-scrollbar {
  height: 6px;
}

.timeline-container::-webkit-scrollbar-track {
  background: transparent;
}

.timeline-container::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 3px;
}

.timeline-container::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.2);
}

.timeline-track {
  position: relative;
  height: 100%;
}

/* ── Axis ─────────────────────────────────────── */
.axis-line {
  position: absolute;
  top: 60%;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg,
    rgba(var(--v-theme-on-surface), 0.04),
    rgba(var(--v-theme-on-surface), 0.1) 10%,
    rgba(var(--v-theme-on-surface), 0.1) 90%,
    rgba(var(--v-theme-on-surface), 0.04)
  );
}

/* ── Month markers ────────────────────────────── */
.month-marker {
  position: absolute;
  top: 0;
  bottom: 0;
}

.month-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.month-label {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  user-select: none;
  background: rgba(var(--v-theme-surface), 0.85);
  padding: 1px 6px;
  border-radius: 3px;
  z-index: 2;
}

/* ── Today marker ─────────────────────────────── */
.today-marker {
  position: absolute;
  top: 0;
  bottom: 0;
  z-index: 10;
  pointer-events: none;
}

.today-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(180deg,
    rgba(196, 115, 90, 0.08),
    rgba(196, 115, 90, 0.45) 30%,
    rgba(196, 115, 90, 0.45) 70%,
    rgba(196, 115, 90, 0.08)
  );
}

.today-diamond {
  position: absolute;
  top: 60%;
  left: 50%;
  width: 8px;
  height: 8px;
  background: #c4735a;
  border-radius: 1px;
  transform: translate(-50%, -50%) rotate(45deg);
  box-shadow: 0 0 8px rgba(196, 115, 90, 0.4);
}

.today-label {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.6rem;
  font-weight: 700;
  color: #c4735a;
  background: rgba(196, 115, 90, 0.08);
  padding: 2px 10px;
  border-radius: 6px 2px 6px 2px;
  white-space: nowrap;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

/* ── Stem lines (card to axis) ────────────────── */
.card-stem {
  position: absolute;
  width: 1px;
  pointer-events: none;
  z-index: 1;
}

.card-stem.stem-deadline {
  background: linear-gradient(180deg, rgba(196, 115, 90, 0.25), rgba(196, 115, 90, 0.04));
}

.card-stem.stem-notification {
  background: linear-gradient(180deg, rgba(74, 142, 147, 0.25), rgba(74, 142, 147, 0.04));
}

/* ── Conference spans — below axis ────────────── */
.conference-span {
  position: absolute;
  height: 28px;
  background: rgba(74, 158, 126, 0.08);
  border: 1px solid rgba(74, 158, 126, 0.2);
  border-left: 3px solid #4a9e7e;
  border-radius: 10px 3px 10px 3px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px 0 6px;
  animation: spanAppear 0.4s ease forwards;
  overflow: hidden;
}

.conference-span:hover,
.conference-span.span-hovered {
  background: rgba(74, 158, 126, 0.16);
  border-color: rgba(74, 158, 126, 0.4);
  box-shadow: 0 2px 12px rgba(74, 158, 126, 0.12);
  height: 32px;
  padding-right: 14px;
  z-index: 8;
}

.span-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(74, 158, 126, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.span-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.span-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #327a5e;
  white-space: nowrap;
  line-height: 1.2;
}

.span-dates {
  font-size: 0.58rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  white-space: nowrap;
  line-height: 1.2;
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition: max-height 0.2s ease, opacity 0.2s ease;
}

.conference-span:hover .span-dates,
.conference-span.span-hovered .span-dates {
  max-height: 16px;
  opacity: 1;
}

/* Span tooltip styles are unscoped (teleported to body) */

/* ── Event cards — above axis ─────────────────── */
.event-card {
  position: absolute;
  width: 110px;
  border-radius: 10px 3px 10px 3px;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0;
  padding: 6px 8px 6px 0;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  animation: cardAppear 0.35s ease forwards;
  opacity: 0;
  z-index: 5;
  overflow: hidden;
}

.event-card.card-deadline {
  background: rgba(196, 115, 90, 0.06);
  border: 1px solid rgba(196, 115, 90, 0.15);
}

.event-card.card-notification {
  background: rgba(74, 142, 147, 0.06);
  border: 1px solid rgba(74, 142, 147, 0.15);
}

/* Left color accent bar */
.card-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  border-radius: 10px 0 0 0;
}

.card-deadline .card-accent { background: #c4735a; }
.card-notification .card-accent { background: #4a8e93; }

/* Icon circle */
.card-icon {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-left: 8px;
  margin-right: 6px;
}

.card-deadline .card-icon {
  background: rgba(196, 115, 90, 0.1);
  color: #c4735a;
}

.card-notification .card-icon {
  background: rgba(74, 142, 147, 0.1);
  color: #4a8e93;
}

/* Text body */
.card-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.card-title {
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgb(var(--v-theme-on-surface));
}

.card-date {
  font-size: 0.6rem;
  color: rgba(var(--v-theme-on-surface), 0.45);
  line-height: 1.3;
  white-space: nowrap;
}

/* Hover highlight */
.event-card.card-hovered,
.event-card.card-active {
  z-index: 15;
}

.event-card.card-hovered.card-deadline {
  background: rgba(196, 115, 90, 0.1);
  border-color: rgba(196, 115, 90, 0.3);
  box-shadow: 0 4px 16px rgba(196, 115, 90, 0.1);
}

.event-card.card-hovered.card-notification {
  background: rgba(74, 142, 147, 0.1);
  border-color: rgba(74, 142, 147, 0.3);
  box-shadow: 0 4px 16px rgba(74, 142, 147, 0.1);
}

.event-card.card-active {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

/* ── Detail card ──────────────────────────────── */
.detail-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
}

.detail-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 14px 4px 14px 4px;
  padding: 18px;
  box-shadow:
    0 4px 6px rgba(0, 0, 0, 0.04),
    0 12px 40px rgba(0, 0, 0, 0.1);
  z-index: 101;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-type {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-type.type-deadline { color: #c4735a; }
.detail-type.type-notification { color: #4a8e93; }
.detail-type.type-span { color: #4a9e7e; }

.detail-title {
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.detail-name {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  line-height: 1.3;
}

.detail-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.detail-meta-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.detail-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
  padding-top: 10px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.detail-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.45);
  text-decoration: none;
  transition: color 0.15s;
}

.detail-link:hover {
  color: rgb(var(--v-theme-primary));
}

/* ── Transitions ──────────────────────────────── */
.detail-fade-enter-active {
  transition: opacity 0.15s ease;
}
.detail-fade-enter-active .detail-card {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.detail-fade-leave-active {
  transition: opacity 0.1s ease;
}
.detail-fade-enter-from {
  opacity: 0;
}
.detail-fade-enter-from .detail-card {
  opacity: 0;
  transform: translateY(-6px);
}
.detail-fade-leave-to {
  opacity: 0;
}

/* ── Animations ───────────────────────────────── */
@keyframes cardAppear {
  from {
    opacity: 0;
    transform: translateY(6px) scale(0.92);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes spanAppear {
  from {
    opacity: 0;
    transform: scaleX(0);
  }
  to {
    opacity: 1;
    transform: scaleX(1);
  }
}

/* ── Skeleton ─────────────────────────────────── */
.timeline-skeleton {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 14px 4px 14px 4px;
  height: 240px;
  position: relative;
  overflow: hidden;
}

.skeleton-axis {
  position: absolute;
  top: 60%;
  left: 0;
  right: 0;
  height: 2px;
}

.skeleton-months {
  display: flex;
  position: absolute;
  top: 10px;
  left: 24px;
  right: 24px;
  justify-content: space-between;
}

.skeleton-month {
  width: 52px;
  height: 12px;
  border-radius: 4px;
}

.skeleton-cards {
  position: absolute;
  inset: 0;
}

.skeleton-card {
  position: absolute;
  width: 100px;
  height: 40px;
  border-radius: 10px 3px 10px 3px;
}

.shimmer {
  background: linear-gradient(
    90deg,
    rgba(var(--v-theme-on-surface), 0.04) 25%,
    rgba(var(--v-theme-on-surface), 0.08) 50%,
    rgba(var(--v-theme-on-surface), 0.04) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Empty State ──────────────────────────────── */
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

/* ── Responsive ───────────────────────────────── */
@media (max-width: 600px) {
  .timeline-controls {
    flex-direction: column;
    align-items: stretch;
  }
  .timeline-legend {
    flex-wrap: wrap;
    gap: 12px;
  }
}
</style>

<!-- Unscoped styles for teleported tooltip -->
<style>
.span-tooltip {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(74, 158, 126, 0.25);
  border-radius: 12px 3px 12px 3px;
  padding: 12px 16px;
  box-shadow:
    0 4px 6px rgba(0, 0, 0, 0.06),
    0 10px 32px rgba(0, 0, 0, 0.12);
  z-index: 200;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.span-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(74, 158, 126, 0.25);
}

.span-tooltip-name {
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.3;
}

.span-tooltip-date-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(74, 158, 126, 0.06);
  border: 1px solid rgba(74, 158, 126, 0.12);
  border-radius: 8px 2px 8px 2px;
}

.span-tooltip-date {
  font-size: 0.82rem;
  font-weight: 700;
  color: #327a5e;
  white-space: nowrap;
}

.span-tooltip-arrow {
  font-size: 0.82rem;
  opacity: 0.35;
}

.span-tooltip-duration {
  font-size: 0.68rem;
  opacity: 0.5;
  font-weight: 500;
}

.span-tooltip-location,
.span-tooltip-core {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.72rem;
  opacity: 0.55;
}

/* Transition */
.span-tooltip-fade-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.span-tooltip-fade-leave-active {
  transition: opacity 0.1s ease;
}
.span-tooltip-fade-enter-from {
  opacity: 0;
  transform: translateY(calc(-100% + 6px)) !important;
}
.span-tooltip-fade-leave-to {
  opacity: 0;
}

/* ── Card tooltip (deadline / notification) ──── */
.card-tooltip {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px 3px 12px 3px;
  padding: 12px 16px;
  box-shadow:
    0 4px 6px rgba(0, 0, 0, 0.06),
    0 10px 32px rgba(0, 0, 0, 0.12);
  z-index: 200;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-tooltip--deadline {
  border: 1px solid rgba(196, 115, 90, 0.25);
}
.card-tooltip--notification {
  border: 1px solid rgba(74, 142, 147, 0.25);
}

.card-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
}
.card-tooltip--deadline::after {
  border-top-color: rgba(196, 115, 90, 0.25);
}
.card-tooltip--notification::after {
  border-top-color: rgba(74, 142, 147, 0.25);
}

.card-tooltip-type {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.card-tooltip--deadline .card-tooltip-type { color: #c4735a; }
.card-tooltip--notification .card-tooltip-type { color: #4a8e93; }

.card-tooltip-name {
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.3;
}

.card-tooltip-date-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 8px 2px 8px 2px;
}
.date-row--deadline {
  background: rgba(196, 115, 90, 0.06);
  border: 1px solid rgba(196, 115, 90, 0.12);
}
.date-row--notification {
  background: rgba(74, 142, 147, 0.06);
  border: 1px solid rgba(74, 142, 147, 0.12);
}

.card-tooltip-date {
  font-size: 0.82rem;
  font-weight: 700;
  white-space: nowrap;
}
.card-tooltip--deadline .card-tooltip-date { color: #c4735a; }
.card-tooltip--notification .card-tooltip-date { color: #4a8e93; }

.card-tooltip-conf-dates,
.card-tooltip-location,
.card-tooltip-core {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.72rem;
  opacity: 0.55;
}

/* Transition */
.card-tooltip-fade-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.card-tooltip-fade-leave-active {
  transition: opacity 0.1s ease;
}
.card-tooltip-fade-enter-from {
  opacity: 0;
  transform: translateY(calc(-100% + 6px)) !important;
}
.card-tooltip-fade-leave-to {
  opacity: 0;
}
</style>
