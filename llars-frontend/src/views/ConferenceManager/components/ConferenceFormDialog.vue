<template>
  <v-dialog v-model="dialogVisible" max-width="700" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon start>mdi-school-outline</v-icon>
        {{ isEdit ? t('conferenceManager.conference.edit') : t('conferenceManager.conference.create') }}
        <v-spacer />
        <v-btn icon variant="text" @click="close"><v-icon>mdi-close</v-icon></v-btn>
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" @submit.prevent="save">
          <!-- Series Selector -->
          <v-row dense>
            <v-col cols="12">
              <div class="d-flex align-center ga-2">
                <v-autocomplete
                  v-model="form.series_id"
                  :items="seriesItems"
                  item-title="text"
                  item-value="value"
                  :label="t('conferenceManager.series.select')"
                  :hint="t('conferenceManager.series.hint')"
                  variant="outlined"
                  density="compact"
                  clearable
                  persistent-hint
                  prepend-inner-icon="mdi-book-multiple-outline"
                  class="flex-grow-1"
                  @update:model-value="onSeriesSelected"
                />
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  :title="t('conferenceManager.series.create')"
                  @click="showNewSeriesDialog = true"
                >
                  <v-icon>mdi-plus</v-icon>
                </v-btn>
              </div>
            </v-col>
          </v-row>

          <v-row dense>
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="form.name"
                :label="t('conferenceManager.conference.name') + ' *'"
                :rules="[v => !!v || t('conferenceManager.validation.required')]"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6" sm="2">
              <v-text-field
                v-model="form.acronym"
                :label="t('conferenceManager.conference.acronym') + ' *'"
                :rules="[v => !!v || t('conferenceManager.validation.required')]"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6" sm="2">
              <v-text-field
                v-model.number="form.year"
                :label="t('conferenceManager.conference.year') + ' *'"
                :rules="[v => !!v || t('conferenceManager.validation.required')]"
                type="number"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>

          <v-row dense>
            <v-col cols="12" sm="4">
              <v-select
                v-model="form.core_ranking"
                :items="CORE_RANKINGS"
                item-title="label"
                item-value="value"
                :label="t('conferenceManager.conference.coreRanking')"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6" sm="4">
              <v-text-field
                v-model="form.city"
                :label="t('conferenceManager.conference.city')"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="6" sm="4">
              <v-text-field
                v-model="form.country"
                :label="t('conferenceManager.conference.country')"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>

          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.submission_deadline"
                :label="t('conferenceManager.conference.submissionDeadline')"
                type="datetime-local"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.notification_date"
                :label="t('conferenceManager.conference.notificationDate')"
                type="datetime-local"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>

          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.start_date"
                :label="t('conferenceManager.conference.startDate')"
                type="datetime-local"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.end_date"
                :label="t('conferenceManager.conference.endDate')"
                type="datetime-local"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>

          <v-text-field
            v-model="form.website_url"
            :label="t('conferenceManager.conference.website')"
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-link"
          />

          <v-combobox
            v-model="form.keywords"
            :label="t('conferenceManager.conference.keywords')"
            variant="outlined"
            density="compact"
            multiple
            chips
            closable-chips
          />

          <v-textarea
            v-model="form.notes"
            :label="t('conferenceManager.conference.notes')"
            variant="outlined"
            density="compact"
            rows="3"
            auto-grow
          />
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">{{ t('conferenceManager.actions.cancel') }}</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="saving"
          :style="{ borderRadius: '16px 4px 16px 4px' }"
          @click="save"
        >
          {{ isEdit ? t('conferenceManager.actions.save') : t('conferenceManager.actions.create') }}
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Inline New Series Dialog -->
    <v-dialog v-model="showNewSeriesDialog" max-width="440" persistent>
      <v-card>
        <v-card-title>{{ t('conferenceManager.series.create') }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newSeriesName"
            :label="t('conferenceManager.conference.name') + ' *'"
            variant="outlined"
            density="compact"
            class="mb-2"
          />
          <v-text-field
            v-model="newSeriesAcronym"
            :label="t('conferenceManager.conference.acronym') + ' *'"
            variant="outlined"
            density="compact"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showNewSeriesDialog = false">{{ t('conferenceManager.actions.cancel') }}</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="creatingSeries"
            :disabled="!newSeriesName || !newSeriesAcronym"
            :style="{ borderRadius: '16px 4px 16px 4px' }"
            @click="doCreateSeries"
          >
            {{ t('conferenceManager.actions.create') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { CORE_RANKINGS } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'

const { t } = useI18n()
const {
  series,
  createConference,
  updateConference,
  fetchSeries,
  createSeries,
  getNewEditionDefaults,
} = useConferenceManager()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  conference: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.conference?.id)
const saving = ref(false)
const formRef = ref(null)

// Series
const showNewSeriesDialog = ref(false)
const newSeriesName = ref('')
const newSeriesAcronym = ref('')
const creatingSeries = ref(false)

const seriesItems = computed(() =>
  (series.value || []).map((s) => ({
    text: `${s.acronym} — ${s.name}`,
    value: s.id,
  }))
)

const defaultForm = () => ({
  series_id: null,
  name: '',
  acronym: '',
  year: new Date().getFullYear(),
  core_ranking: 'Unranked',
  submission_deadline: '',
  notification_date: '',
  start_date: '',
  end_date: '',
  city: '',
  country: '',
  website_url: '',
  keywords: [],
  notes: '',
})

const form = ref(defaultForm())

watch(() => props.conference, (val) => {
  if (val) {
    form.value = {
      ...defaultForm(),
      ...val,
      series_id: val.series_id || null,
      submission_deadline: formatDateForInput(val.submission_deadline),
      notification_date: formatDateForInput(val.notification_date),
      start_date: formatDateForInput(val.start_date),
      end_date: formatDateForInput(val.end_date),
      keywords: val.keywords || [],
    }
  } else {
    form.value = defaultForm()
  }
}, { immediate: true })

watch(dialogVisible, (open) => {
  if (open) fetchSeries()
})

onMounted(() => fetchSeries())

async function onSeriesSelected(seriesId) {
  if (!seriesId || isEdit.value) return
  try {
    const defaults = await getNewEditionDefaults(seriesId)
    if (defaults) {
      form.value.name = defaults.name || form.value.name
      form.value.acronym = defaults.acronym || form.value.acronym
      form.value.year = defaults.year || form.value.year
      form.value.core_ranking = defaults.core_ranking || form.value.core_ranking
      form.value.keywords = defaults.keywords?.length ? defaults.keywords : form.value.keywords
      form.value.website_url = defaults.website_url || form.value.website_url
      if (defaults.city) form.value.city = defaults.city
      if (defaults.country) form.value.country = defaults.country
    }
  } catch (err) {
    console.error('Failed to get edition defaults:', err)
  }
}

async function doCreateSeries() {
  creatingSeries.value = true
  try {
    const created = await createSeries({
      name: newSeriesName.value,
      acronym: newSeriesAcronym.value,
    })
    form.value.series_id = created.id
    showNewSeriesDialog.value = false
    newSeriesName.value = ''
    newSeriesAcronym.value = ''
    await onSeriesSelected(created.id)
  } catch (err) {
    console.error('Create series failed:', err)
  } finally {
    creatingSeries.value = false
  }
}

function formatDateForInput(isoStr) {
  if (!isoStr) return ''
  return isoStr.slice(0, 16)
}

function close() {
  dialogVisible.value = false
  form.value = defaultForm()
}

async function save() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  saving.value = true
  try {
    if (isEdit.value) {
      await updateConference(props.conference.id, form.value)
    } else {
      await createConference(form.value)
    }
    emit('saved')
    close()
  } catch (err) {
    console.error('Save conference failed:', err)
  } finally {
    saving.value = false
  }
}
</script>
