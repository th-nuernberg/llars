<template>
  <div class="calendar-view">
    <!-- Legend (matching Timeline style) -->
    <div class="calendar-legend">
      <div class="legend-item">
        <span class="legend-chip legend-chip--deadline">
          <v-icon size="12">mdi-file-document-outline</v-icon>
        </span>
        <span class="legend-text">{{ t('conferenceManager.calendar.deadline') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-chip legend-chip--notification">
          <v-icon size="12">mdi-bell-outline</v-icon>
        </span>
        <span class="legend-text">{{ t('conferenceManager.calendar.notification') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-chip legend-chip--conference">
          <v-icon size="12">mdi-account-group-outline</v-icon>
        </span>
        <span class="legend-text">{{ t('conferenceManager.calendar.conference') }}</span>
      </div>
    </div>

    <!-- Calendar Skeleton -->
    <div v-if="!calendarReady" class="calendar-skeleton">
      <div class="skeleton-toolbar">
        <div class="skeleton-nav">
          <div class="skeleton-btn shimmer" />
          <div class="skeleton-btn shimmer" />
          <div class="skeleton-btn-wide shimmer" />
        </div>
        <div class="skeleton-month-title shimmer" />
      </div>
      <div class="skeleton-weekdays">
        <div v-for="n in 7" :key="n" class="skeleton-weekday shimmer" />
      </div>
      <div class="skeleton-grid">
        <div v-for="n in 35" :key="n" class="skeleton-day">
          <div class="skeleton-day-number shimmer" />
          <div v-if="n % 5 === 2" class="skeleton-event shimmer" />
          <div v-if="n % 7 === 4" class="skeleton-event short shimmer" />
        </div>
      </div>
    </div>

    <!-- Real Calendar -->
    <div v-show="calendarReady" class="calendar-real" :class="{ 'calendar-visible': calendarReady }">
      <FullCalendar ref="calendarRef" :options="calendarOptions" />
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
import { computed, ref, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import { useConferenceManager } from '../composables/useConferenceManager'
import ConferenceFormDialog from './ConferenceFormDialog.vue'

const { t, locale } = useI18n()
const { conferences, fetchConferences } = useConferenceManager()

const showEditDialog = ref(false)
const selectedConference = ref(null)
const calendarReady = ref(false)
const calendarRef = ref(null)
let eventIndex = 0

const calendarEvents = computed(() => {
  const events = []
  for (const conf of conferences.value) {
    if (conf.submission_deadline) {
      events.push({
        title: `${conf.acronym} Deadline`,
        date: conf.submission_deadline.slice(0, 10),
        color: '#c4735a',
        extendedProps: { conferenceId: conf.id, type: 'deadline' },
      })
    }
    if (conf.notification_date) {
      events.push({
        title: `${conf.acronym} Notification`,
        date: conf.notification_date.slice(0, 10),
        color: '#4a8e93',
        extendedProps: { conferenceId: conf.id, type: 'notification' },
      })
    }
    if (conf.start_date) {
      events.push({
        title: conf.acronym,
        start: conf.start_date.slice(0, 10),
        end: conf.end_date ? conf.end_date.slice(0, 10) : undefined,
        color: '#4a9e7e',
        extendedProps: { conferenceId: conf.id, type: 'conference' },
      })
    }
  }
  return events
})

const calendarOptions = computed(() => ({
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  events: calendarEvents.value,
  locale: locale.value,
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: '',
  },
  eventClick: handleEventClick,
  eventDidMount: handleEventDidMount,
  datesSet: onDatesSet,
  height: 'auto',
  dayMaxEvents: 3,
}))

function onDatesSet() {
  if (!calendarReady.value) {
    nextTick(() => {
      eventIndex = 0
      calendarReady.value = true
    })
  }
}

const TYPE_ICONS = {
  deadline: 'mdi-file-document-outline',
  notification: 'mdi-bell-outline',
  conference: 'mdi-account-group-outline',
}

function handleEventDidMount(info) {
  const el = info.el
  const type = info.event.extendedProps?.type || 'conference'

  // Add icon to event
  const iconEl = document.createElement('span')
  iconEl.className = 'fc-event-icon'
  iconEl.innerHTML = `<svg style="width:12px;height:12px;vertical-align:middle;opacity:0.8" viewBox="0 0 24 24"><path fill="currentColor" d="${getIconPath(type)}"/></svg>`

  const titleEl = el.querySelector('.fc-event-title') || el.querySelector('.fc-event-title-container')
  if (titleEl) {
    titleEl.insertBefore(iconEl, titleEl.firstChild)
  }

  // Staggered animation
  el.style.opacity = '0'
  el.style.transform = 'translateY(-4px) scale(0.97)'
  el.style.transition = 'opacity 0.35s ease, transform 0.35s ease'
  el.style.transitionDelay = `${eventIndex * 40}ms`
  eventIndex++
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      el.style.opacity = '1'
      el.style.transform = 'translateY(0) scale(1)'
    })
  })
}

function getIconPath(type) {
  // Simplified SVG paths for the icons
  if (type === 'deadline') return 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z'
  if (type === 'notification') return 'M21,19V20H3V19L5,17V11C5,7.9 7.03,5.17 10,4.29C10,4.19 10,4.1 10,4A2,2 0 0,1 12,2A2,2 0 0,1 14,4C14,4.1 14,4.19 14,4.29C16.97,5.17 19,7.9 19,11V17L21,19M14,21A2,2 0 0,1 12,23A2,2 0 0,1 10,21'
  return 'M16,13C15.71,13 15.38,13 15.03,13.05C16.19,13.89 17,15 17,16.5V18H22V16.5C22,14.17 18.33,13 16,13M8,13C5.67,13 2,14.17 2,16.5V18H14V16.5C14,14.17 10.33,13 8,13M8,11A3,3 0 0,0 11,8A3,3 0 0,0 8,5A3,3 0 0,0 5,8A3,3 0 0,0 8,11M16,11A3,3 0 0,0 19,8A3,3 0 0,0 16,5A3,3 0 0,0 13,8A3,3 0 0,0 16,11Z'
}

function handleEventClick(info) {
  const conferenceId = info.event.extendedProps?.conferenceId
  if (!conferenceId) return

  const conf = conferences.value.find(c => c.id === conferenceId)
  if (conf) {
    selectedConference.value = conf
    showEditDialog.value = true
  }
}

function onSaved() {
  fetchConferences()
}
</script>

<style scoped>
/* ── Legend (matching Timeline) ────────────────── */
.calendar-legend {
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
  color: rgba(var(--v-theme-on-surface), 0.75);
  font-weight: 500;
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

/* ── Calendar Skeleton ────────────────────────── */
.calendar-skeleton {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 14px 4px 14px 4px;
  overflow: hidden;
}

.skeleton-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.skeleton-nav {
  display: flex;
  gap: 6px;
}

.skeleton-btn {
  width: 36px;
  height: 32px;
  border-radius: 8px 2px 8px 2px;
}

.skeleton-btn-wide {
  width: 56px;
  height: 32px;
  border-radius: 8px 2px 8px 2px;
}

.skeleton-month-title {
  width: 140px;
  height: 22px;
  border-radius: 4px;
}

.skeleton-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.skeleton-weekday {
  height: 14px;
  width: 24px;
  margin: 10px auto;
  border-radius: 4px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.skeleton-day {
  min-height: 90px;
  padding: 8px;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.04);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.skeleton-day:nth-child(7n) {
  border-right: none;
}

.skeleton-day-number {
  width: 20px;
  height: 14px;
  border-radius: 4px;
  margin-bottom: 6px;
}

.skeleton-event {
  width: 85%;
  height: 16px;
  border-radius: 6px 2px 6px 2px;
  margin-top: 4px;
}

.skeleton-event.short {
  width: 60%;
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

/* ── Real Calendar ────────────────────────────── */
.calendar-real {
  opacity: 0;
  transition: opacity 0.4s ease;
}

.calendar-real.calendar-visible {
  opacity: 1;
}

/* ── FullCalendar Overrides ───────────────────── */

/* Container */
.calendar-view :deep(.fc) {
  font-family: inherit;
  --fc-border-color: rgba(var(--v-theme-on-surface), 0.12);
  --fc-today-bg-color: transparent;
  --fc-neutral-bg-color: rgba(var(--v-theme-on-surface), 0.025);
}

/* Toolbar */
.calendar-view :deep(.fc .fc-toolbar) {
  padding: 8px 4px;
  margin-bottom: 4px !important;
}

.calendar-view :deep(.fc .fc-toolbar-title) {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: rgb(var(--v-theme-on-surface));
}

/* Navigation buttons */
.calendar-view :deep(.fc .fc-button) {
  border-radius: 8px 2px 8px 2px !important;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 5px 12px;
  text-transform: capitalize;
  box-shadow: none !important;
  transition: all 0.15s ease;
}

.calendar-view :deep(.fc .fc-button-primary) {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
  border-color: rgba(var(--v-theme-on-surface), 0.15);
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.calendar-view :deep(.fc .fc-button-primary:hover) {
  background-color: rgba(var(--v-theme-on-surface), 0.14);
  border-color: rgba(var(--v-theme-on-surface), 0.2);
  color: rgb(var(--v-theme-on-surface));
}

.calendar-view :deep(.fc .fc-button-primary:not(:disabled).fc-button-active),
.calendar-view :deep(.fc .fc-button-primary:not(:disabled):active) {
  background-color: rgba(var(--v-theme-on-surface), 0.18);
  border-color: rgba(var(--v-theme-on-surface), 0.25);
  color: rgb(var(--v-theme-on-surface));
}

.calendar-view :deep(.fc .fc-button-primary:disabled) {
  opacity: 0.4;
}

.calendar-view :deep(.fc .fc-prev-button),
.calendar-view :deep(.fc .fc-next-button) {
  padding: 5px 8px;
}

/* Column header (weekdays) */
.calendar-view :deep(.fc .fc-col-header) {
  background: rgba(var(--v-theme-on-surface), 0.035);
}

.calendar-view :deep(.fc .fc-col-header-cell) {
  padding: 10px 0;
  border-bottom: 2px solid rgba(var(--v-theme-on-surface), 0.12);
}

.calendar-view :deep(.fc .fc-col-header-cell-cushion) {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(var(--v-theme-on-surface), 0.6);
  padding: 4px 8px;
}

/* Day cells */
.calendar-view :deep(.fc .fc-daygrid-day-frame) {
  min-height: 96px;
  padding: 4px;
}

.calendar-view :deep(.fc .fc-daygrid-day-number) {
  font-size: 0.82rem;
  font-weight: 600;
  padding: 4px 8px;
  color: rgba(var(--v-theme-on-surface), 0.75);
  transition: all 0.15s ease;
}

.calendar-view :deep(.fc .fc-daygrid-day:hover .fc-daygrid-day-number) {
  color: rgb(var(--v-theme-on-surface));
}

/* Other-month days */
.calendar-view :deep(.fc .fc-day-other .fc-daygrid-day-number) {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.calendar-view :deep(.fc .fc-day-other) {
  background: rgba(var(--v-theme-on-surface), 0.02);
}

/* Today */
.calendar-view :deep(.fc .fc-daygrid-day.fc-day-today) {
  background: rgba(125, 163, 98, 0.06);
}

.calendar-view :deep(.fc .fc-daygrid-day.fc-day-today .fc-daygrid-day-number) {
  background: #6b9a45;
  color: white;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.78rem;
  box-shadow: 0 2px 8px rgba(107, 154, 69, 0.35);
}

/* Weekend columns subtle tint */
.calendar-view :deep(.fc .fc-day-sat),
.calendar-view :deep(.fc .fc-day-sun) {
  background: rgba(var(--v-theme-on-surface), 0.02);
}

/* ── Events ───────────────────────────────────── */
.calendar-view :deep(.fc .fc-event) {
  border-radius: 6px 2px 6px 2px;
  border: none;
  border-left: 3px solid transparent;
  padding: 3px 8px 3px 6px;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  margin-bottom: 2px;
}

.calendar-view :deep(.fc .fc-event:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 5 !important;
}

/* Event colors with left accent border — kräftig for light mode */
.calendar-view :deep(.fc .fc-event[style*="background-color: rgb(196, 115, 90)"]),
.calendar-view :deep(.fc .fc-event[style*="background-color: #c4735a"]) {
  background-color: rgba(196, 115, 90, 0.18) !important;
  color: #a5503a !important;
  border-left-color: #c4735a;
}

.calendar-view :deep(.fc .fc-event[style*="background-color: rgb(74, 142, 147)"]),
.calendar-view :deep(.fc .fc-event[style*="background-color: #4a8e93"]) {
  background-color: rgba(74, 142, 147, 0.18) !important;
  color: #33706e !important;
  border-left-color: #4a8e93;
}

.calendar-view :deep(.fc .fc-event[style*="background-color: rgb(74, 158, 126)"]),
.calendar-view :deep(.fc .fc-event[style*="background-color: #4a9e7e"]) {
  background-color: rgba(74, 158, 126, 0.18) !important;
  color: #2a6548 !important;
  border-left-color: #4a9e7e;
}

/* Event icon spacing */
.calendar-view :deep(.fc-event-icon) {
  margin-right: 4px;
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
}

/* Event title */
.calendar-view :deep(.fc .fc-event-title) {
  font-weight: 700;
  letter-spacing: 0.01em;
}

/* More events link */
.calendar-view :deep(.fc .fc-daygrid-more-link) {
  font-size: 0.7rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.55);
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.calendar-view :deep(.fc .fc-daygrid-more-link:hover) {
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.85);
}

/* Scrollgrid / table borders */
.calendar-view :deep(.fc .fc-scrollgrid) {
  border-radius: 14px 4px 14px 4px;
  overflow: hidden;
  border-color: rgba(var(--v-theme-on-surface), 0.12);
}

.calendar-view :deep(.fc .fc-scrollgrid td),
.calendar-view :deep(.fc .fc-scrollgrid th) {
  border-color: rgba(var(--v-theme-on-surface), 0.1);
}

/* ── Dark Mode Overrides ──────────────────────── */

/* Header row: transparent instead of washed-out white tint */
.v-theme--dark .calendar-view :deep(.fc .fc-col-header) {
  background: rgba(255, 255, 255, 0.03);
}

.v-theme--dark .calendar-view :deep(.fc .fc-col-header-cell) {
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .calendar-view :deep(.fc .fc-col-header-cell-cushion) {
  color: rgba(255, 255, 255, 0.55);
}

/* Day numbers brighter */
.v-theme--dark .calendar-view :deep(.fc .fc-daygrid-day-number) {
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .calendar-view :deep(.fc .fc-daygrid-day:hover .fc-daygrid-day-number) {
  color: rgba(255, 255, 255, 0.95);
}

/* Other-month days */
.v-theme--dark .calendar-view :deep(.fc .fc-day-other .fc-daygrid-day-number) {
  color: rgba(255, 255, 255, 0.2);
}

.v-theme--dark .calendar-view :deep(.fc .fc-day-other) {
  background: rgba(255, 255, 255, 0.015);
}

/* Weekend tint */
.v-theme--dark .calendar-view :deep(.fc .fc-day-sat),
.v-theme--dark .calendar-view :deep(.fc .fc-day-sun) {
  background: rgba(255, 255, 255, 0.015);
}

/* Today */
.v-theme--dark .calendar-view :deep(.fc .fc-daygrid-day.fc-day-today) {
  background: rgba(107, 154, 69, 0.08);
}

.v-theme--dark .calendar-view :deep(.fc .fc-daygrid-day.fc-day-today .fc-daygrid-day-number) {
  background: #7da362;
  box-shadow: 0 2px 10px rgba(125, 163, 98, 0.4);
}

/* Borders */
.v-theme--dark .calendar-view :deep(.fc) {
  --fc-border-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .calendar-view :deep(.fc .fc-scrollgrid) {
  border-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .calendar-view :deep(.fc .fc-scrollgrid td),
.v-theme--dark .calendar-view :deep(.fc .fc-scrollgrid th) {
  border-color: rgba(255, 255, 255, 0.06);
}

/* Buttons */
.v-theme--dark .calendar-view :deep(.fc .fc-button-primary) {
  background-color: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .calendar-view :deep(.fc .fc-button-primary:hover) {
  background-color: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.9);
}

/* Events — brighter backgrounds and lighter text for dark mode */
.v-theme--dark .calendar-view :deep(.fc .fc-event[style*="background-color: rgb(196, 115, 90)"]),
.v-theme--dark .calendar-view :deep(.fc .fc-event[style*="background-color: #c4735a"]) {
  background-color: rgba(196, 115, 90, 0.22) !important;
  color: #e8a087 !important;
  border-left-color: #c4735a;
}

.v-theme--dark .calendar-view :deep(.fc .fc-event[style*="background-color: rgb(74, 142, 147)"]),
.v-theme--dark .calendar-view :deep(.fc .fc-event[style*="background-color: #4a8e93"]) {
  background-color: rgba(74, 142, 147, 0.22) !important;
  color: #88c4c8 !important;
  border-left-color: #4a8e93;
}

.v-theme--dark .calendar-view :deep(.fc .fc-event[style*="background-color: rgb(74, 158, 126)"]),
.v-theme--dark .calendar-view :deep(.fc .fc-event[style*="background-color: #4a9e7e"]) {
  background-color: rgba(74, 158, 126, 0.22) !important;
  color: #98d4bb !important;
  border-left-color: #4a9e7e;
}

.v-theme--dark .calendar-view :deep(.fc .fc-event:hover) {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

/* More link */
.v-theme--dark .calendar-view :deep(.fc .fc-daygrid-more-link) {
  color: rgba(255, 255, 255, 0.5);
}

.v-theme--dark .calendar-view :deep(.fc .fc-daygrid-more-link:hover) {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.8);
}

/* Legend dark mode */
.v-theme--dark .calendar-legend {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
}

.v-theme--dark .legend-text {
  color: rgba(255, 255, 255, 0.7);
}

.v-theme--dark .legend-chip--deadline {
  background: rgba(196, 115, 90, 0.15);
}

.v-theme--dark .legend-chip--notification {
  background: rgba(74, 142, 147, 0.15);
}

.v-theme--dark .legend-chip--conference {
  background: rgba(74, 158, 126, 0.15);
}

/* ── Responsive ───────────────────────────────── */
@media (max-width: 600px) {
  .calendar-legend {
    flex-wrap: wrap;
    gap: 12px;
  }

  .calendar-view :deep(.fc .fc-col-header-cell-cushion) {
    font-size: 0.65rem;
  }

  .calendar-view :deep(.fc .fc-daygrid-day-frame) {
    min-height: 60px;
  }

  .calendar-view :deep(.fc .fc-event) {
    font-size: 0.65rem;
    padding: 2px 4px 2px 5px;
  }
}
</style>
