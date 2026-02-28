<template>
  <div>
    <!-- Filters -->
    <v-row dense class="mb-3">
      <v-col cols="12" sm="4">
        <v-text-field
          v-model="search"
          :label="t('conferenceManager.filters.search')"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="compact"
          hide-details
          clearable
        />
      </v-col>
      <v-col cols="6" sm="3">
        <v-select
          v-model="filterRanking"
          :items="[{ label: t('conferenceManager.filters.allRankings'), value: null }, ...CORE_RANKINGS]"
          item-title="label"
          item-value="value"
          :label="t('conferenceManager.conference.coreRanking')"
          variant="outlined"
          density="compact"
          hide-details
        />
      </v-col>
      <v-col cols="6" sm="2">
        <v-text-field
          v-model.number="filterYear"
          :label="t('conferenceManager.conference.year')"
          type="number"
          variant="outlined"
          density="compact"
          hide-details
          clearable
        />
      </v-col>
      <v-col cols="12" sm="3" class="d-flex justify-end">
        <v-btn
          color="primary"
          :style="{ borderRadius: '16px 4px 16px 4px' }"
          prepend-icon="mdi-plus"
          @click="showCreate"
        >
          {{ t('conferenceManager.conference.create') }}
        </v-btn>
      </v-col>
    </v-row>

    <!-- Table -->
    <v-data-table
      :headers="headers"
      :items="conferences"
      :loading="loading"
      :search="search"
      :items-per-page="15"
      hover
      class="elevation-0"
      @click:row="(_, { item }) => editConference(item)"
    >
      <template #item.core_ranking="{ value }">
        <CoreRankingChip :ranking="value" />
      </template>

      <template #item.submission_deadline="{ value }">
        <span v-if="value" :class="isDeadlineSoon(value) ? 'text-error font-weight-medium' : ''">
          {{ formatDate(value) }}
        </span>
        <span v-else class="text-medium-emphasis">-</span>
      </template>

      <template #item.notification_date="{ value }">
        {{ value ? formatDate(value) : '-' }}
      </template>

      <template #item.start_date="{ value }">
        {{ value ? formatDate(value) : '-' }}
      </template>

      <template #item.location="{ item }">
        {{ [item.city, item.country].filter(Boolean).join(', ') || '-' }}
      </template>

      <template #item.website_url="{ value }">
        <v-btn
          v-if="value"
          icon
          size="small"
          variant="text"
          :href="value"
          target="_blank"
          @click.stop
        >
          <v-icon size="18">mdi-open-in-new</v-icon>
        </v-btn>
      </template>

      <template #item.actions="{ item }">
        <v-btn icon size="small" variant="text" @click.stop="editConference(item)">
          <v-icon size="18">mdi-pencil-outline</v-icon>
        </v-btn>
        <v-btn icon size="small" variant="text" color="error" @click.stop="confirmDelete(item)">
          <v-icon size="18">mdi-delete-outline</v-icon>
        </v-btn>
      </template>

      <template #no-data>
        <div class="text-center pa-8 text-medium-emphasis">
          <v-icon size="48" class="mb-2">mdi-school-outline</v-icon>
          <p>{{ t('conferenceManager.empty.conferences') }}</p>
        </div>
      </template>
    </v-data-table>

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
import { ref, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CORE_RANKINGS } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'
import CoreRankingChip from './CoreRankingChip.vue'
import ConferenceFormDialog from './ConferenceFormDialog.vue'

const { t } = useI18n()
const { conferences, loading, fetchConferences, deleteConference } = useConferenceManager()

const search = ref('')
const filterRanking = ref(null)
const filterYear = ref(null)
const formDialog = ref(false)
const editingConference = ref(null)
const deleteDialog = ref(false)
const deletingConference = ref(null)

const headers = computed(() => [
  { title: t('conferenceManager.conference.acronym'), key: 'acronym', width: '100px' },
  { title: t('conferenceManager.conference.name'), key: 'name' },
  { title: t('conferenceManager.conference.coreRanking'), key: 'core_ranking', width: '120px' },
  { title: t('conferenceManager.conference.submissionDeadline'), key: 'submission_deadline', width: '160px' },
  { title: t('conferenceManager.conference.notificationDate'), key: 'notification_date', width: '140px' },
  { title: t('conferenceManager.conference.startDate'), key: 'start_date', width: '140px' },
  { title: t('conferenceManager.conference.location'), key: 'location', width: '150px', sortable: false },
  { title: '', key: 'website_url', width: '50px', sortable: false },
  { title: '', key: 'actions', width: '90px', sortable: false },
])

onMounted(() => loadData())

watch([filterRanking, filterYear], () => loadData())

function loadData() {
  fetchConferences({
    core_ranking: filterRanking.value,
    year: filterYear.value,
  })
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

function onSaved() {
  loadData()
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
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
