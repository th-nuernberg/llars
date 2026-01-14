<template>
<v-container class="kaimo-panel">
    <v-row class="mb-6">
      <v-col cols="12">
        <v-skeleton-loader
          v-if="isLoading('hero')"
          type="heading, text, chip"
          class="mb-4"
        />
        <div v-else class="d-flex align-start flex-wrap gap-3">
          <div>
            <div class="d-flex align-center mb-1">
              <v-avatar color="primary" size="42" class="mr-3">
                <LIcon color="white">mdi-human-child</LIcon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">{{ $t('kaimo.panel.title') }}</div>
                <div class="text-subtitle-2 text-medium-emphasis">
                  {{ $t('kaimo.panel.subtitle') }}
                </div>
              </div>
            </div>
            <div class="text-body-2 text-medium-emphasis">
              {{ canManageKaimo ? $t('kaimo.panel.roleHint.researcher') : $t('kaimo.panel.roleHint.evaluator') }}
            </div>
          </div>
          <v-spacer />
          <div class="d-flex align-center gap-2 flex-wrap">
            <v-chip v-if="canManageKaimo" color="secondary" variant="flat" prepend-icon="mdi-shield-account">
              {{ $t('kaimo.panel.roles.researcher') }}
            </v-chip>
            <v-chip v-else color="primary" variant="outlined" prepend-icon="mdi-account">
              {{ $t('kaimo.panel.roles.evaluator') }}
            </v-chip>
            <v-btn
              v-if="canManageKaimo"
              color="secondary"
              variant="flat"
              prepend-icon="mdi-plus"
              @click="router.push({ name: 'KaimoNewCase' })"
            >
              {{ $t('kaimo.panel.actions.newCase') }}
            </v-btn>
            <v-btn
              variant="text"
              color="secondary"
              prepend-icon="mdi-arrow-left"
              @click="router.push({ name: 'KaimoHub' })"
            >
              {{ $t('common.back') }}
            </v-btn>
          </div>
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-skeleton-loader
          v-if="isLoading('content')"
          type="table-heading, table-thead, table-tbody"
          class="mb-4"
        />
        <v-alert
          v-else-if="!canViewKaimo"
          type="warning"
          variant="tonal"
          icon="mdi-lock"
        >
          {{ $t('kaimo.panel.alerts.noAccess', { permission: 'feature:kaimo:view' }) }}
        </v-alert>
        <v-alert
          v-else-if="loadError"
          type="error"
          variant="tonal"
          icon="mdi-alert"
          class="mb-4"
        >
          {{ loadError }}
        </v-alert>
      </v-col>
    </v-row>

    <v-row v-if="!isLoading('content') && canViewKaimo" class="align-stretch">
      <v-col cols="12" :md="canManageKaimo ? 12 : 7">
        <v-card class="pa-4" elevation="2">
          <v-card-title class="px-0 d-flex align-center">
            <LIcon class="mr-2" color="primary">mdi-format-list-bulleted</LIcon>
            {{ $t('kaimo.panel.table.title') }}
            <v-chip class="ml-2" size="small" color="primary" variant="outlined">
              {{ cases.length }}
            </v-chip>
            <v-spacer />
            <v-btn
              icon="mdi-refresh"
              variant="text"
              :loading="isLoading('content')"
              @click="refresh"
            />
          </v-card-title>
          <v-card-text class="px-0">
            <v-table density="comfortable">
              <thead>
                <tr>
                  <th>{{ $t('kaimo.panel.table.headers.case') }}</th>
                  <th>{{ $t('kaimo.panel.table.headers.status') }}</th>
                  <th class="text-right">{{ $t('kaimo.panel.table.headers.docs') }}</th>
                  <th class="text-right">{{ $t('kaimo.panel.table.headers.hints') }}</th>
                  <th v-if="canManageKaimo" class="text-right">{{ $t('kaimo.panel.table.headers.assessments') }}</th>
                  <th class="text-right">{{ $t('kaimo.panel.table.headers.actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in cases" :key="c.id">
                  <td>
                    <div class="d-flex align-center">
                      <span v-if="c.icon" class="mr-2 text-h6">{{ c.icon }}</span>
                      <div>
                        <div class="font-weight-medium">{{ c.display_name }}</div>
                        <div class="text-caption text-medium-emphasis text-truncate" style="max-width: 300px;">
                          {{ c.description || $t('kaimo.panel.table.noDescription') }}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <v-chip
                      size="small"
                      :color="getStatusColor(c.status)"
                      variant="flat"
                    >
                      {{ getStatusLabel(c.status) }}
                    </v-chip>
                  </td>
                  <td class="text-right">{{ c.document_count || 0 }}</td>
                  <td class="text-right">{{ c.hint_count || 0 }}</td>
                  <td v-if="canManageKaimo" class="text-right">{{ c.assessment_count || 0 }}</td>
                  <td class="text-right">
                    <div class="d-flex justify-end gap-1">
                      <v-tooltip :text="$t('kaimo.panel.tooltips.openCase')" location="top">
                        <template v-slot:activator="{ props }">
                          <v-btn
                            v-bind="props"
                            size="small"
                            icon="mdi-eye"
                            color="primary"
                            variant="text"
                            @click="openCase(c)"
                          />
                        </template>
                      </v-tooltip>
                      <template v-if="canManageKaimo">
                        <v-tooltip :text="$t('kaimo.panel.tooltips.editCase')" location="top">
                          <template v-slot:activator="{ props }">
                            <v-btn
                              v-bind="props"
                              size="small"
                              icon="mdi-pencil"
                              color="secondary"
                              variant="text"
                              @click="editCase(c)"
                            />
                          </template>
                        </v-tooltip>
                        <v-tooltip v-if="c.status === 'draft'" :text="$t('kaimo.panel.tooltips.publish')" location="top">
                          <template v-slot:activator="{ props }">
                            <v-btn
                              v-bind="props"
                              size="small"
                              icon="mdi-publish"
                              color="success"
                              variant="text"
                              @click="confirmPublish(c)"
                            />
                          </template>
                        </v-tooltip>
                        <v-tooltip :text="$t('common.delete')" location="top">
                          <template v-slot:activator="{ props }">
                            <v-btn
                              v-bind="props"
                              size="small"
                              icon="mdi-delete"
                              color="error"
                              variant="text"
                              @click="confirmDelete(c)"
                            />
                          </template>
                        </v-tooltip>
                      </template>
                    </div>
                  </td>
                </tr>
                <tr v-if="cases.length === 0">
                  <td :colspan="canManageKaimo ? 6 : 5" class="text-center text-medium-emphasis py-4">
                    <LIcon class="mr-2">mdi-folder-open-outline</LIcon>
                    {{ $t('kaimo.panel.table.empty') }}
                    <v-btn
                      v-if="canManageKaimo"
                      class="ml-2"
                      color="secondary"
                      size="small"
                      variant="text"
                      @click="router.push({ name: 'KaimoNewCase' })"
                    >
                      {{ $t('kaimo.panel.table.emptyCta') }}
                    </v-btn>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col v-if="!canManageKaimo" cols="12" md="5">
        <v-card class="pa-4" color="primary" variant="tonal" elevation="2">
          <div class="d-flex align-center mb-3">
            <v-avatar color="primary" size="40" class="mr-3">
              <LIcon color="white">mdi-information-outline</LIcon>
            </v-avatar>
            <div>
              <div class="text-subtitle-1 font-weight-bold">{{ $t('kaimo.panel.sidebar.title') }}</div>
              <div class="text-body-2 text-medium-emphasis">
                {{ $t('kaimo.panel.sidebar.subtitle') }}
              </div>
            </div>
          </div>
          <v-chip-group column class="mb-4">
            <v-chip color="success" variant="flat" prepend-icon="mdi-check">
              {{ $t('kaimo.panel.sidebar.publishedCount', { count: cases.filter(c => c.status === 'published').length }) }}
            </v-chip>
            <v-chip color="warning" variant="outlined" prepend-icon="mdi-pencil">
              {{ $t('kaimo.panel.sidebar.draftCount', { count: cases.filter(c => c.status === 'draft').length }) }}
            </v-chip>
          </v-chip-group>
        </v-card>
      </v-col>
    </v-row>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="450">
      <v-card>
        <v-card-title class="text-h6">
          <LIcon class="mr-2" color="error">mdi-delete-alert</LIcon>
          {{ $t('kaimo.panel.deleteDialog.title') }}
        </v-card-title>
        <v-card-text>
          <p>{{ $t('kaimo.panel.deleteDialog.body', { name: caseToDelete?.display_name }) }}</p>
          <v-alert v-if="caseToDelete?.assessment_count > 0" type="warning" variant="tonal" class="mt-3">
            <strong>{{ $t('kaimo.panel.deleteDialog.warningTitle') }}</strong>
            {{ $t('kaimo.panel.deleteDialog.warningBody', { count: caseToDelete?.assessment_count }) }}
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" :loading="deleting" @click="executeDelete">
            {{ $t('common.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Publish Confirmation Dialog -->
    <v-dialog v-model="publishDialog" max-width="450">
      <v-card>
        <v-card-title class="text-h6">
          <LIcon class="mr-2" color="success">mdi-publish</LIcon>
          {{ $t('kaimo.panel.publishDialog.title') }}
        </v-card-title>
        <v-card-text>
          <p>{{ $t('kaimo.panel.publishDialog.body', { name: caseToPublish?.display_name }) }}</p>
          <p class="text-medium-emphasis">{{ $t('kaimo.panel.publishDialog.note') }}</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="publishDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="success" variant="flat" :loading="publishing" @click="executePublish">
            {{ $t('kaimo.panel.publishDialog.confirm') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>

  </v-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { usePermissions } from '@/composables/usePermissions';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { getKaimoCases, getKaimoAdminCases, deleteKaimoCase, publishKaimoCase } from '@/services/kaimoApi';

const router = useRouter();
const { t, locale } = useI18n();
const { hasPermission, isResearcher, fetchPermissions } = usePermissions();
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['hero', 'content']);

const canViewKaimo = computed(() => {
  return hasPermission('feature:kaimo:view') || isResearcher.value || hasPermission('admin:kaimo:manage');
});

const canManageKaimo = computed(() => {
  return isResearcher.value || hasPermission('admin:kaimo:manage');
});

const cases = ref([]);
const loadError = ref(null);

// Delete dialog
const deleteDialog = ref(false);
const caseToDelete = ref(null);
const deleting = ref(false);

// Publish dialog
const publishDialog = ref(false);
const caseToPublish = ref(null);
const publishing = ref(false);

// Snackbar
const snackbar = ref({ show: false, text: '', color: 'success' });

const showSnackbar = (text, color = 'success') => {
  snackbar.value = { show: true, text, color };
};

const getStatusColor = (status) => {
  switch (status) {
    case 'published': return 'success';
    case 'draft': return 'warning';
    case 'archived': return 'grey';
    default: return 'primary';
  }
};

const getStatusLabel = (status) => {
  locale.value;
  switch (status) {
    case 'published': return t('kaimo.status.published');
    case 'draft': return t('kaimo.status.draft');
    case 'archived': return t('kaimo.status.archived');
    default: return status;
  }
};

const loadCases = async () => {
  loadError.value = null;
  // Researcher sehen alle Fälle mit Admin-API (inkl. assessment_count)
  const data = canManageKaimo.value
    ? await getKaimoAdminCases()
    : await getKaimoCases();
  cases.value = data?.cases || [];
};

const refresh = async () => {
  await withLoading('content', async () => {
    await fetchPermissions(true);
    if (canViewKaimo.value) {
      await loadCases();
    }
  });
  setLoading('hero', false);
};

const openCase = (c) => {
  router.push({ name: 'KaimoCase', params: { id: c.id } });
};

const editCase = (c) => {
  router.push({ name: 'KaimoCaseEditor', params: { id: c.id } });
};

const confirmDelete = (c) => {
  caseToDelete.value = c;
  deleteDialog.value = true;
};

const executeDelete = async () => {
  if (!caseToDelete.value) return;
  deleting.value = true;
  try {
    // Force delete wenn Assessments vorhanden
    const force = (caseToDelete.value.assessment_count || 0) > 0;
    await deleteKaimoCase(caseToDelete.value.id, force);
    showSnackbar(t('kaimo.panel.snackbar.deleteSuccess', { name: caseToDelete.value.display_name }), 'success');
    deleteDialog.value = false;
    await loadCases();
  } catch (err) {
    console.error('Fehler beim Loeschen:', err);
    showSnackbar(t('kaimo.panel.snackbar.deleteError'), 'error');
  } finally {
    deleting.value = false;
  }
};

const confirmPublish = (c) => {
  caseToPublish.value = c;
  publishDialog.value = true;
};

const executePublish = async () => {
  if (!caseToPublish.value) return;
  publishing.value = true;
  try {
    await publishKaimoCase(caseToPublish.value.id);
    showSnackbar(t('kaimo.panel.snackbar.publishSuccess', { name: caseToPublish.value.display_name }), 'success');
    publishDialog.value = false;
    await loadCases();
  } catch (err) {
    console.error('Fehler beim Veroeffentlichen:', err);
    showSnackbar(t('kaimo.panel.snackbar.publishError'), 'error');
  } finally {
    publishing.value = false;
  }
};

onMounted(async () => {
  try {
    await refresh();
  } catch (err) {
    loadError.value = t('kaimo.errors.loadCases');
    console.error('KAIMO-Ladefehler', err);
    setLoading('hero', false);
  }
});
</script>

<style scoped>
.kaimo-panel {
  max-width: 1100px;
}

.gap-3 {
  gap: 12px;
}

.gap-2 {
  gap: 8px;
}
</style>
