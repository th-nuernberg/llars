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
          v-model="filterStatus"
          :items="statusOptions"
          :item-title="s => s.label"
          item-value="value"
          :label="t('conferenceManager.paper.status')"
          variant="outlined"
          density="compact"
          hide-details
        />
      </v-col>
      <v-col cols="6" sm="3">
        <v-select
          v-model="filterConference"
          :items="conferenceOptions"
          item-title="label"
          item-value="value"
          :label="t('conferenceManager.paper.conference')"
          variant="outlined"
          density="compact"
          hide-details
          clearable
        />
      </v-col>
      <v-col cols="12" sm="2" class="d-flex justify-end">
        <v-btn
          color="primary"
          :style="{ borderRadius: '16px 4px 16px 4px' }"
          prepend-icon="mdi-plus"
          @click="showCreate"
        >
          {{ t('conferenceManager.paper.create') }}
        </v-btn>
      </v-col>
    </v-row>

    <!-- Table -->
    <v-data-table
      :headers="headers"
      :items="papers"
      :loading="loading"
      :search="search"
      :items-per-page="15"
      hover
      class="elevation-0"
      @click:row="(_, { item }) => editPaper(item)"
    >
      <template #item.status="{ value }">
        <PaperStatusChip :status="value" />
      </template>

      <template #item.authors="{ item }">
        <span class="text-body-2">
          {{ item.authors?.map(a => a.display_name).join(', ') || '-' }}
        </span>
      </template>

      <template #item.conference="{ item }">
        <span v-if="item.conference">
          {{ item.conference.acronym }} {{ item.conference.year }}
        </span>
        <span v-else class="text-medium-emphasis">-</span>
      </template>

      <template #item.keywords="{ item }">
        <v-chip
          v-for="kw in (item.keywords || []).slice(0, 3)"
          :key="kw"
          size="x-small"
          class="mr-1"
          variant="outlined"
        >
          {{ kw }}
        </v-chip>
        <span v-if="(item.keywords || []).length > 3" class="text-caption text-medium-emphasis">
          +{{ item.keywords.length - 3 }}
        </span>
      </template>

      <template #item.overleaf_url="{ value }">
        <v-btn
          v-if="value"
          icon
          size="small"
          variant="text"
          :href="value"
          target="_blank"
          @click.stop
        >
          <v-icon size="18">mdi-leaf</v-icon>
        </v-btn>
      </template>

      <template #item.updated_at="{ value }">
        {{ value ? formatDate(value) : '-' }}
      </template>

      <template #item.actions="{ item }">
        <v-btn icon size="small" variant="text" @click.stop="editPaper(item)">
          <v-icon size="18">mdi-pencil-outline</v-icon>
        </v-btn>
        <v-btn icon size="small" variant="text" color="error" @click.stop="confirmDelete(item)">
          <v-icon size="18">mdi-delete-outline</v-icon>
        </v-btn>
      </template>

      <template #no-data>
        <div class="text-center pa-8 text-medium-emphasis">
          <v-icon size="48" class="mb-2">mdi-file-document-outline</v-icon>
          <p>{{ t('conferenceManager.empty.papers') }}</p>
        </div>
      </template>
    </v-data-table>

    <!-- Form Dialog -->
    <PaperFormDialog
      v-model="formDialog"
      :paper="editingPaper"
      @saved="onSaved"
    />

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
import { PAPER_STATUSES } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'
import PaperStatusChip from './PaperStatusChip.vue'
import PaperFormDialog from './PaperFormDialog.vue'

const { t } = useI18n()
const { conferences, papers, loading, fetchPapers, fetchConferences, deletePaper } = useConferenceManager()

const search = ref('')
const filterStatus = ref(null)
const filterConference = ref(null)
const formDialog = ref(false)
const editingPaper = ref(null)
const deleteDialog = ref(false)
const deletingPaper = ref(null)

const statusOptions = computed(() => [
  { label: t('conferenceManager.filters.allStatuses'), value: null },
  ...PAPER_STATUSES.map(s => ({ label: t(s.labelKey), value: s.value })),
])

const conferenceOptions = computed(() => [
  { label: t('conferenceManager.filters.allConferences'), value: null },
  ...conferences.value.map(c => ({
    label: `${c.acronym} ${c.year}`,
    value: c.id,
  })),
])

const headers = computed(() => [
  { title: t('conferenceManager.paper.title'), key: 'title' },
  { title: t('conferenceManager.paper.status'), key: 'status', width: '140px' },
  { title: t('conferenceManager.paper.authors'), key: 'authors', sortable: false },
  { title: t('conferenceManager.paper.conference'), key: 'conference', width: '140px', sortable: false },
  { title: t('conferenceManager.paper.keywords'), key: 'keywords', sortable: false },
  { title: '', key: 'overleaf_url', width: '50px', sortable: false },
  { title: t('conferenceManager.paper.updated'), key: 'updated_at', width: '120px' },
  { title: '', key: 'actions', width: '90px', sortable: false },
])

onMounted(() => {
  fetchConferences()
  loadData()
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

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}
</script>
