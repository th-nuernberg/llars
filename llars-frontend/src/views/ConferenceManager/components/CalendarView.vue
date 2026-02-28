<template>
  <div class="calendar-view">
    <!-- Legend -->
    <div class="calendar-legend mb-3">
      <span class="legend-item">
        <span class="legend-dot" :style="{ backgroundColor: '#e8a087' }" />
        {{ t('conferenceManager.calendar.deadline') }}
      </span>
      <span class="legend-item">
        <span class="legend-dot" :style="{ backgroundColor: '#88c4c8' }" />
        {{ t('conferenceManager.calendar.notification') }}
      </span>
      <span class="legend-item">
        <span class="legend-dot" :style="{ backgroundColor: '#98d4bb' }" />
        {{ t('conferenceManager.calendar.conference') }}
      </span>
    </div>

    <!-- Calendar -->
    <FullCalendar :options="calendarOptions" />

    <!-- Edit dialog -->
    <ConferenceFormDialog
      v-model="showEditDialog"
      :conference="selectedConference"
      @saved="onSaved"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
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

const calendarEvents = computed(() => {
  const events = []
  for (const conf of conferences.value) {
    if (conf.submission_deadline) {
      events.push({
        title: `${conf.acronym} Deadline`,
        date: conf.submission_deadline.slice(0, 10),
        color: '#e8a087',
        extendedProps: { conferenceId: conf.id },
      })
    }
    if (conf.notification_date) {
      events.push({
        title: `${conf.acronym} Notification`,
        date: conf.notification_date.slice(0, 10),
        color: '#88c4c8',
        extendedProps: { conferenceId: conf.id },
      })
    }
    if (conf.start_date) {
      events.push({
        title: conf.acronym,
        start: conf.start_date.slice(0, 10),
        end: conf.end_date ? conf.end_date.slice(0, 10) : undefined,
        color: '#98d4bb',
        extendedProps: { conferenceId: conf.id },
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
  height: 'auto',
  dayMaxEvents: 3,
}))

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
.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  padding: 8px 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.calendar-view :deep(.fc) {
  font-family: inherit;
}

.calendar-view :deep(.fc .fc-toolbar-title) {
  font-size: 1.2rem;
  font-weight: 500;
}

.calendar-view :deep(.fc .fc-button) {
  border-radius: 8px 2px 8px 2px;
  font-size: 0.85rem;
}

.calendar-view :deep(.fc .fc-button-primary) {
  background-color: #b0ca97;
  border-color: #b0ca97;
}

.calendar-view :deep(.fc .fc-button-primary:hover) {
  background-color: #9dba80;
  border-color: #9dba80;
}

.calendar-view :deep(.fc .fc-button-primary:not(:disabled).fc-button-active),
.calendar-view :deep(.fc .fc-button-primary:not(:disabled):active) {
  background-color: #8aaa6e;
  border-color: #8aaa6e;
}

.calendar-view :deep(.fc .fc-event) {
  border-radius: 4px;
  border: none;
  padding: 2px 4px;
  font-size: 0.8rem;
  cursor: pointer;
}

.calendar-view :deep(.fc .fc-daygrid-day-number) {
  font-size: 0.85rem;
}

@media (max-width: 600px) {
  .calendar-view :deep(.fc .fc-col-header-cell) {
    font-size: 0.75rem;
  }
}
</style>
