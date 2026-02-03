<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="700"
    persistent
  >
    <v-card>
      <v-card-title class="text-h5 pa-4">
        <LIcon :icon="isEdit ? 'mdi-pencil' : 'mdi-plus'" class="mr-2"></LIcon>
        {{ isEdit ? $t('rag.collectionEditor.titleEdit') : $t('rag.collectionEditor.titleCreate') }}
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4">
        <v-form ref="formRef" v-model="isValid">
          <!-- Basis-Informationen -->
          <div class="mb-4">
            <div class="text-subtitle-1 font-weight-medium mb-3">{{ $t('rag.collectionEditor.basicInfo') }}</div>

            <v-text-field
              v-model="formData.name"
              :label="$t('rag.collectionEditor.technicalName')"
              :hint="$t('rag.collectionEditor.technicalNameHint')"
              persistent-hint
              :rules="[rules.required, rules.nameFormat]"
              variant="outlined"
              density="comfortable"
              class="mb-4"
              :disabled="isEdit"
            ></v-text-field>

            <v-text-field
              v-model="formData.display_name"
              :label="$t('rag.collectionEditor.displayName')"
              :hint="$t('rag.collectionEditor.displayNameHint')"
              persistent-hint
              :rules="[rules.required]"
              variant="outlined"
              density="comfortable"
              class="mb-4"
            ></v-text-field>

            <v-textarea
              v-model="formData.description"
              :label="$t('rag.collectionEditor.description')"
              :hint="$t('rag.collectionEditor.descriptionHint')"
              persistent-hint
              variant="outlined"
              density="comfortable"
              rows="3"
              class="mb-4"
            ></v-textarea>

            <!-- Icon und Farbe -->
            <v-row>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="formData.icon"
                  :label="$t('rag.collectionEditor.icon')"
                  :items="iconOptions"
                  variant="outlined"
                  density="comfortable"
                >
                  <template v-slot:selection="{ item }">
                    <LIcon :icon="item.raw.icon" class="mr-2"></LIcon>
                    {{ item.raw.title }}
                  </template>
                  <template v-slot:item="{ item, props }">
                    <v-list-item v-bind="props">
                      <template v-slot:prepend>
                        <LIcon :icon="item.raw.icon"></LIcon>
                      </template>
                    </v-list-item>
                  </template>
                </v-select>
              </v-col>

              <v-col cols="12" sm="6">
                <v-menu :close-on-content-click="false">
                  <template v-slot:activator="{ props }">
                    <v-text-field
                      v-model="formData.color"
                      :label="$t('rag.collectionEditor.color')"
                      variant="outlined"
                      density="comfortable"
                      readonly
                      v-bind="props"
                    >
                      <template v-slot:prepend-inner>
                        <div
                          :style="{
                            width: '24px',
                            height: '24px',
                            backgroundColor: formData.color,
                            borderRadius: '4px',
                            border: '1px solid rgba(0,0,0,0.2)'
                          }"
                        ></div>
                      </template>
                    </v-text-field>
                  </template>
                  <v-color-picker
                    v-model="formData.color"
                    mode="hex"
                    show-swatches
                    :swatches="colorSwatches"
                  ></v-color-picker>
                </v-menu>
              </v-col>
            </v-row>
          </div>

          <v-divider class="my-4"></v-divider>

          <!-- Erweiterte Einstellungen -->
          <v-expansion-panels variant="accordion">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <LIcon icon="mdi-cog" class="mr-2"></LIcon>
                {{ $t('rag.collectionEditor.advancedSettings') }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-text-field
                  v-model.number="formData.chunk_size"
                  :label="$t('rag.collectionEditor.chunkSize')"
                  :hint="$t('rag.collectionEditor.chunkSizeHint')"
                  persistent-hint
                  type="number"
                  :rules="[rules.positiveNumber]"
                  variant="outlined"
                  density="comfortable"
                  class="mb-4"
                ></v-text-field>

                <v-text-field
                  v-model.number="formData.chunk_overlap"
                  :label="$t('rag.collectionEditor.chunkOverlap')"
                  :hint="$t('rag.collectionEditor.chunkOverlapHint')"
                  persistent-hint
                  type="number"
                  :rules="[rules.positiveNumber]"
                  variant="outlined"
                  density="comfortable"
                  class="mb-4"
                ></v-text-field>

                <v-text-field
                  v-model.number="formData.retrieval_k"
                  :label="$t('rag.collectionEditor.retrievalK')"
                  :hint="$t('rag.collectionEditor.retrievalKHint')"
                  persistent-hint
                  type="number"
                  :rules="[rules.positiveNumber]"
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-form>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          {{ $t('rag.collectionEditor.cancel') }}
        </v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          @click="handleSave"
          :disabled="!isValid"
        >
          {{ isEdit ? $t('rag.collectionEditor.save') : $t('rag.collectionEditor.create') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  collection: {
    type: Object,
    default: null
  },
  isEdit: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

const formRef = ref(null)
const isValid = ref(false)

const formData = ref({
  name: '',
  display_name: '',
  description: '',
  icon: 'folder',
  color: '#1976D2',
  chunk_size: 1000,
  chunk_overlap: 200,
  retrieval_k: 5
})

const iconOptions = computed(() => [
  { value: 'book', title: t('rag.collectionEditor.icons.book'), icon: 'mdi-book' },
  { value: 'folder', title: t('rag.collectionEditor.icons.folder'), icon: 'mdi-folder' },
  { value: 'faq', title: t('rag.collectionEditor.icons.faq'), icon: 'mdi-comment-question' },
  { value: 'database', title: t('rag.collectionEditor.icons.database'), icon: 'mdi-database' },
  { value: 'text', title: t('rag.collectionEditor.icons.text'), icon: 'mdi-text-box' },
  { value: 'email', title: t('rag.collectionEditor.icons.email'), icon: 'mdi-email' },
  { value: 'archive', title: t('rag.collectionEditor.icons.archive'), icon: 'mdi-archive' }
])

const colorSwatches = [
  ['#1976D2', '#2196F3', '#03A9F4', '#00BCD4'],
  ['#4CAF50', '#8BC34A', '#CDDC39', '#FFEB3B'],
  ['#FF9800', '#FF5722', '#F44336', '#E91E63'],
  ['#9C27B0', '#673AB7', '#3F51B5', '#607D8B']
]

const rules = computed(() => ({
  required: v => !!v || t('rag.collectionEditor.validation.required'),
  nameFormat: v => /^[a-z0-9-_]+$/.test(v) || t('rag.collectionEditor.validation.nameFormat'),
  positiveNumber: v => v > 0 || t('rag.collectionEditor.validation.positiveNumber')
}))

watch(() => props.collection, (newVal) => {
  if (newVal && props.isEdit) {
    formData.value = {
      name: newVal.name || '',
      display_name: newVal.display_name || '',
      description: newVal.description || '',
      icon: newVal.icon || 'folder',
      color: newVal.color || '#1976D2',
      chunk_size: newVal.chunk_size || 1000,
      chunk_overlap: newVal.chunk_overlap || 200,
      retrieval_k: newVal.retrieval_k || 5
    }
  } else if (!props.isEdit) {
    formData.value = {
      name: '',
      display_name: '',
      description: '',
      icon: 'folder',
      color: '#1976D2',
      chunk_size: 1000,
      chunk_overlap: 200,
      retrieval_k: 5
    }
  }
}, { immediate: true })

const handleSave = async () => {
  const { valid } = await formRef.value.validate()
  if (valid) {
    emit('save', { ...formData.value })
  }
}
</script>

<style scoped>
.v-expansion-panel-text :deep(.v-expansion-panel-text__wrapper) {
  padding: 16px;
}
</style>
