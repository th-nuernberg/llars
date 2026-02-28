<template>
  <v-dialog v-model="dialogVisible" max-width="700" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon start>mdi-file-document-outline</v-icon>
        {{ isEdit ? t('conferenceManager.paper.edit') : t('conferenceManager.paper.create') }}
        <v-spacer />
        <v-btn icon variant="text" @click="close"><v-icon>mdi-close</v-icon></v-btn>
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" @submit.prevent="save">
          <v-text-field
            v-model="form.title"
            :label="t('conferenceManager.paper.title') + ' *'"
            :rules="[v => !!v || t('conferenceManager.validation.required')]"
            variant="outlined"
            density="compact"
          />

          <v-row dense>
            <v-col cols="12" sm="6">
              <v-select
                v-model="form.status"
                :items="PAPER_STATUSES"
                :item-title="s => t(s.labelKey)"
                item-value="value"
                :label="t('conferenceManager.paper.status')"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="form.conference_id"
                :items="conferenceOptions"
                item-title="label"
                item-value="value"
                :label="t('conferenceManager.paper.conference')"
                variant="outlined"
                density="compact"
                clearable
              />
            </v-col>
          </v-row>

          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.overleaf_url"
                :label="t('conferenceManager.paper.overleafUrl')"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-leaf"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.external_url"
                :label="t('conferenceManager.paper.externalUrl')"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-link"
              />
            </v-col>
          </v-row>

          <v-combobox
            v-model="form.keywords"
            :label="t('conferenceManager.paper.keywords')"
            variant="outlined"
            density="compact"
            multiple
            chips
            closable-chips
          />

          <v-textarea
            v-model="form.description"
            :label="t('conferenceManager.paper.description')"
            variant="outlined"
            density="compact"
            rows="3"
            auto-grow
          />

          <v-divider class="my-3" />

          <PaperAuthorEditor v-model="form.authors" />

          <v-divider class="my-3" />

          <v-textarea
            v-model="form.notes"
            :label="t('conferenceManager.paper.notes')"
            variant="outlined"
            density="compact"
            rows="2"
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
import { PAPER_STATUSES } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'
import PaperAuthorEditor from './PaperAuthorEditor.vue'

const { t } = useI18n()
const { conferences, createPaper, updatePaper } = useConferenceManager()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  paper: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.paper?.id)
const saving = ref(false)
const formRef = ref(null)

const conferenceOptions = computed(() =>
  conferences.value.map(c => ({
    label: `${c.acronym} ${c.year}`,
    value: c.id,
  }))
)

const defaultForm = () => ({
  title: '',
  status: 'planning',
  conference_id: null,
  overleaf_url: '',
  external_url: '',
  keywords: [],
  description: '',
  notes: '',
  authors: [],
})

const form = ref(defaultForm())

watch(() => props.paper, (val) => {
  if (val) {
    form.value = {
      ...defaultForm(),
      ...val,
      keywords: val.keywords || [],
      authors: val.authors || [],
    }
  } else {
    form.value = defaultForm()
  }
}, { immediate: true })

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
      await updatePaper(props.paper.id, form.value)
    } else {
      await createPaper(form.value)
    }
    emit('saved')
    close()
  } catch (err) {
    console.error('Save paper failed:', err)
  } finally {
    saving.value = false
  }
}
</script>
