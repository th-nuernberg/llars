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
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CORE_RANKINGS } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'

const { t } = useI18n()
const { createConference, updateConference } = useConferenceManager()

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

const defaultForm = () => ({
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
