<template>
  <div>
    <div class="d-flex align-center mb-2">
      <span class="text-subtitle-2">{{ t('conferenceManager.paper.authors') }}</span>
      <v-spacer />
      <v-btn size="small" variant="text" @click="addAuthor" prepend-icon="mdi-plus">
        {{ t('conferenceManager.paper.addAuthor') }}
      </v-btn>
    </div>

    <div v-for="(author, index) in localAuthors" :key="index" class="d-flex align-center ga-2 mb-2">
      <v-text-field
        v-model="author.external_name"
        :label="t('conferenceManager.paper.authorName')"
        density="compact"
        variant="outlined"
        hide-details
        style="flex: 1"
      />
      <v-checkbox
        v-model="author.is_corresponding"
        :label="t('conferenceManager.paper.corresponding')"
        density="compact"
        hide-details
        class="flex-shrink-0"
      />
      <v-btn icon size="small" variant="text" color="error" @click="removeAuthor(index)">
        <v-icon size="18">mdi-close</v-icon>
      </v-btn>
    </div>

    <div v-if="!localAuthors.length" class="text-body-2 text-medium-emphasis pa-2">
      {{ t('conferenceManager.paper.noAuthors') }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const localAuthors = ref([...props.modelValue])

watch(() => props.modelValue, (val) => {
  localAuthors.value = [...val]
}, { deep: true })

watch(localAuthors, (val) => {
  emit('update:modelValue', val.map((a, i) => ({ ...a, author_order: i })))
}, { deep: true })

function addAuthor() {
  localAuthors.value.push({
    external_name: '',
    user_id: null,
    author_order: localAuthors.value.length,
    is_corresponding: false,
  })
}

function removeAuthor(index) {
  localAuthors.value.splice(index, 1)
}
</script>
