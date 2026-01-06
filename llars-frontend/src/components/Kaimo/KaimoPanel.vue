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
                <v-icon color="white">mdi-human-child</v-icon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">KAIMO Panel</div>
                <div class="text-subtitle-2 text-medium-emphasis">
                  Fälle durcharbeiten, Hinweise zuordnen, Bewertungen abschließen
                </div>
              </div>
            </div>
            <div class="text-body-2 text-medium-emphasis">
              {{ canManageKaimo ? 'Researcher: Fälle verwalten und bearbeiten.' : 'Evaluator: Freigegebene Fälle bearbeiten.' }}
            </div>
          </div>
          <v-spacer />
          <div class="d-flex align-center gap-2 flex-wrap">
            <v-chip v-if="canManageKaimo" color="secondary" variant="flat" prepend-icon="mdi-shield-account">
              Researcher
            </v-chip>
            <v-chip v-else color="primary" variant="outlined" prepend-icon="mdi-account">
              Evaluator
            </v-chip>
            <v-btn
              v-if="canManageKaimo"
              color="secondary"
              variant="flat"
              prepend-icon="mdi-plus"
              @click="router.push({ name: 'KaimoNewCase' })"
            >
              Neuer Fall
            </v-btn>
            <v-btn
              variant="text"
              color="secondary"
              prepend-icon="mdi-arrow-left"
              @click="router.push({ name: 'KaimoHub' })"
            >
              Zurück
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
          Du benötigst <code>feature:kaimo:view</code>, um das KAIMO Panel zu öffnen.
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
            <v-icon class="mr-2" color="primary">mdi-format-list-bulleted</v-icon>
            Fälle
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
                  <th>Fall</th>
                  <th>Status</th>
                  <th class="text-right">Docs</th>
                  <th class="text-right">Hinweise</th>
                  <th v-if="canManageKaimo" class="text-right">Bewertungen</th>
                  <th class="text-right">Aktionen</th>
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
                          {{ c.description || 'Keine Beschreibung' }}
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
                      <v-tooltip text="Fall öffnen (User-Ansicht)" location="top">
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
                        <v-tooltip text="Fall bearbeiten" location="top">
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
                        <v-tooltip v-if="c.status === 'draft'" text="Veröffentlichen" location="top">
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
                        <v-tooltip text="Löschen" location="top">
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
                    <v-icon class="mr-2">mdi-folder-open-outline</v-icon>
                    Keine KAIMO Fälle verfügbar.
                    <v-btn
                      v-if="canManageKaimo"
                      class="ml-2"
                      color="secondary"
                      size="small"
                      variant="text"
                      @click="router.push({ name: 'KaimoNewCase' })"
                    >
                      Ersten Fall anlegen
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
              <v-icon color="white">mdi-information-outline</v-icon>
            </v-avatar>
            <div>
              <div class="text-subtitle-1 font-weight-bold">Hinweise</div>
              <div class="text-body-2 text-medium-emphasis">
                Öffne einen Fall um ihn zu bearbeiten.
              </div>
            </div>
          </div>
          <v-chip-group column class="mb-4">
            <v-chip color="success" variant="flat" prepend-icon="mdi-check">
              {{ cases.filter(c => c.status === 'published').length }} veröffentlicht
            </v-chip>
            <v-chip color="warning" variant="outlined" prepend-icon="mdi-pencil">
              {{ cases.filter(c => c.status === 'draft').length }} Entwürfe
            </v-chip>
          </v-chip-group>
        </v-card>
      </v-col>
    </v-row>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="450">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon class="mr-2" color="error">mdi-delete-alert</v-icon>
          Fall löschen?
        </v-card-title>
        <v-card-text>
          <p>Möchtest du den Fall <strong>{{ caseToDelete?.display_name }}</strong> wirklich löschen?</p>
          <v-alert v-if="caseToDelete?.assessment_count > 0" type="warning" variant="tonal" class="mt-3">
            <strong>Achtung:</strong> Dieser Fall hat {{ caseToDelete?.assessment_count }} Bewertung(en).
            Beim Löschen gehen alle Daten verloren!
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" variant="flat" :loading="deleting" @click="executeDelete">
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Publish Confirmation Dialog -->
    <v-dialog v-model="publishDialog" max-width="450">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon class="mr-2" color="success">mdi-publish</v-icon>
          Fall veröffentlichen?
        </v-card-title>
        <v-card-text>
          <p>Möchtest du den Fall <strong>{{ caseToPublish?.display_name }}</strong> veröffentlichen?</p>
          <p class="text-medium-emphasis">Nach der Veröffentlichung können Evaluator den Fall bearbeiten.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="publishDialog = false">Abbrechen</v-btn>
          <v-btn color="success" variant="flat" :loading="publishing" @click="executePublish">
            Veröffentlichen
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
import { usePermissions } from '@/composables/usePermissions';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { getKaimoCases, getKaimoAdminCases, deleteKaimoCase, publishKaimoCase } from '@/services/kaimoApi';

const router = useRouter();
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
  switch (status) {
    case 'published': return 'Veröffentlicht';
    case 'draft': return 'Entwurf';
    case 'archived': return 'Archiviert';
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
    showSnackbar(`Fall "${caseToDelete.value.display_name}" wurde gelöscht.`, 'success');
    deleteDialog.value = false;
    await loadCases();
  } catch (err) {
    console.error('Delete error:', err);
    showSnackbar('Fehler beim Löschen des Falls.', 'error');
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
    showSnackbar(`Fall "${caseToPublish.value.display_name}" wurde veröffentlicht.`, 'success');
    publishDialog.value = false;
    await loadCases();
  } catch (err) {
    console.error('Publish error:', err);
    showSnackbar('Fehler beim Veröffentlichen des Falls.', 'error');
  } finally {
    publishing.value = false;
  }
};

onMounted(async () => {
  try {
    await refresh();
  } catch (err) {
    loadError.value = 'KAIMO Fälle konnten nicht geladen werden.';
    console.error('KAIMO load error', err);
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
