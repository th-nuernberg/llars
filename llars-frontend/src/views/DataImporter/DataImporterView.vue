<template>
  <div class="data-importer-view">
    <v-container class="py-6">
      <!-- Header -->
      <div class="d-flex align-center mb-6">
        <div>
          <h1 class="text-h4 font-weight-bold">{{ $t('dataImporter.title') }}</h1>
          <p class="text-body-1 text-medium-emphasis mt-1">
            {{ $t('dataImporter.subtitle') }}
          </p>
        </div>
        <v-spacer />
        <LBtn
          v-if="!showWizard"
          variant="primary"
          prepend-icon="mdi-plus"
          @click="showWizard = true"
        >
          {{ $t('dataImporter.newImport') }}
        </LBtn>
      </div>

      <!-- Wizard -->
      <DataImporterWizard
        v-if="showWizard"
        @close="handleClose"
        @complete="handleComplete"
      />

      <!-- Empty State -->
      <v-card v-else variant="outlined" class="empty-state pa-12 text-center">
        <LIcon size="96" color="primary" class="mb-4">llars:evaluation-assistant</LIcon>
        <h2 class="text-h5 mb-2">{{ $t('dataImporter.empty.title') }}</h2>
        <p class="text-body-1 text-medium-emphasis mb-6" style="max-width: 500px; margin: 0 auto;">
          {{ $t('dataImporter.empty.body') }}
        </p>

        <LBtn
          variant="primary"
          size="large"
          prepend-icon="mdi-upload"
          @click="showWizard = true"
        >
          {{ $t('dataImporter.empty.cta') }}
        </LBtn>

        <!-- Feature Highlights -->
        <v-row class="mt-8" justify="center">
          <v-col cols="12" sm="4">
            <v-card variant="tonal" class="pa-4 h-100">
              <LIcon size="32" color="primary" class="mb-2">wand</LIcon>
              <div class="text-body-1 font-weight-medium">{{ $t('dataImporter.highlights.autoDetection.title') }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ $t('dataImporter.highlights.autoDetection.body') }}
              </div>
            </v-card>
          </v-col>
          <v-col cols="12" sm="4">
            <v-card variant="tonal" class="pa-4 h-100">
              <LIcon size="32" color="purple" class="mb-2">mdi-robot</LIcon>
              <div class="text-body-1 font-weight-medium">{{ $t('dataImporter.highlights.aiSupport.title') }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ $t('dataImporter.highlights.aiSupport.body') }}
              </div>
            </v-card>
          </v-col>
          <v-col cols="12" sm="4">
            <v-card variant="tonal" class="pa-4 h-100">
              <LIcon size="32" color="success" class="mb-2">wand</LIcon>
              <div class="text-body-1 font-weight-medium">{{ $t('dataImporter.highlights.wizardFlow.title') }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ $t('dataImporter.highlights.wizardFlow.body') }}
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-card>

      <!-- Recent Imports (future feature) -->
      <!--
      <v-card v-if="!showWizard && recentImports.length" variant="outlined" class="mt-6">
        <v-card-title>Letzte Imports</v-card-title>
        <v-card-text>
          ...
        </v-card-text>
      </v-card>
      -->
    </v-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSnackbar } from '@/composables/useSnackbar'
import DataImporterWizard from '@/components/DataImporter/DataImporterWizard.vue'

const router = useRouter()
const { showSuccess } = useSnackbar()
const { t } = useI18n()

const showWizard = ref(false)

const handleClose = () => {
  showWizard.value = false
}

const handleComplete = (result) => {
  showWizard.value = false
  showSuccess(t('dataImporter.success', { count: result.session?.imported_count || 0 }))

  // Optionally redirect to scenario management
  // router.push('/admin/scenarios')
}
</script>

<style scoped>
.data-importer-view {
  min-height: calc(100vh - 64px);
  background: rgb(var(--v-theme-background));
}

.empty-state {
  border-radius: 16px 4px 16px 4px;
}
</style>
