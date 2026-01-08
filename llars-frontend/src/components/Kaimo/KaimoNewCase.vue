<template>
<v-container class="kaimo-new-case">
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
              <v-avatar color="secondary" size="42" class="mr-3">
                <LIcon color="white">mdi-clipboard-plus-outline</LIcon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">KAIMO Fall anlegen</div>
                <div class="text-subtitle-2 text-medium-emphasis">
                  Researcher Panel für neue Fallvignetten
                </div>
              </div>
            </div>
            <div class="text-body-2 text-medium-emphasis">
              Bereit zum Aufsetzen neuer Fälle nach dem Konzept unter docs/docs/projekte/kaimo.
            </div>
          </div>
          <v-spacer />
          <div class="d-flex align-center gap-2 flex-wrap">
            <v-chip color="secondary" variant="flat" prepend-icon="mdi-account-cowboy-hat">
              Nur Researcher
            </v-chip>
            <v-btn
              variant="text"
              color="secondary"
              prepend-icon="mdi-arrow-left"
              @click="router.push({ name: 'KaimoHub' })"
            >
              Zurück zum KAIMO Hub
            </v-btn>
          </div>
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-skeleton-loader
          v-if="isLoading('content')"
          type="card@2"
          class="mb-4"
        />
        <v-alert
          v-else-if="!canManageKaimo"
          type="error"
          variant="tonal"
          icon="mdi-lock"
        >
          Diese Seite ist nur für Researcher mit <code>admin:kaimo:manage</code> zugänglich.
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

    <v-row v-if="!isLoading('content') && canManageKaimo" class="align-stretch">
      <v-col cols="12" md="7">
        <v-card class="pa-4" elevation="2">
          <v-card-title class="px-0">
            <LIcon class="mr-2" color="secondary">mdi-clipboard-text-outline</LIcon>
            Neuen Fall anlegen
          </v-card-title>
          <v-card-text class="px-0">
            <v-form @submit.prevent="submit" ref="formRef">
              <v-text-field
                v-model="form.name"
                label="Name (intern, unique)"
                hint="z.B. fall-malaika"
                prepend-inner-icon="mdi-identifier"
                :rules="[v => !!v || 'Pflichtfeld']"
                class="mb-3"
                required
              />
              <v-text-field
                v-model="form.display_name"
                label="Anzeigename"
                prepend-inner-icon="mdi-format-title"
                :rules="[v => !!v || 'Pflichtfeld']"
                class="mb-3"
                required
              />
              <v-textarea
                v-model="form.description"
                label="Beschreibung"
                rows="3"
                prepend-inner-icon="mdi-text-long"
                class="mb-3"
              />
              <v-row>
                <v-col cols="6">
                  <v-text-field
                    v-model="form.icon"
                    label="Icon (optional)"
                    prepend-inner-icon="mdi-emoticon-outline"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="form.color"
                    label="Farbe (Hex)"
                    prepend-inner-icon="mdi-palette"
                  />
                </v-col>
              </v-row>
              <v-alert type="info" variant="tonal" class="mt-2">
                Kategorien: Wenn leer, werden Standard-Kategorien automatisch verknüpft.
              </v-alert>
              <div class="d-flex justify-end mt-4">
                <v-btn variant="text" class="mr-2" @click="router.push({ name: 'KaimoHub' })">
                  Abbrechen
                </v-btn>
                <v-btn
                  color="secondary"
                  type="submit"
                  :loading="submitting"
                  :disabled="!canSubmit"
                  prepend-icon="mdi-content-save"
                >
                  Fall anlegen
                </v-btn>
              </div>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card class="pa-4" color="secondary" variant="tonal" elevation="2">
          <div class="d-flex align-center mb-3">
            <v-avatar color="secondary" size="40" class="mr-3">
              <LIcon color="white">mdi-shield-key-outline</LIcon>
            </v-avatar>
            <div>
              <div class="text-subtitle-1 font-weight-bold">Berechtigungen</div>
              <div class="text-body-2 text-medium-emphasis">
                Researcher + admin:kaimo:manage erhalten die Kachel „Fall anlegen“.
              </div>
            </div>
          </div>
          <v-chip-group column class="mb-4">
            <v-chip color="secondary" variant="flat" prepend-icon="mdi-check-decagram">
              Zugriff bestätigt
            </v-chip>
            <v-chip color="secondary" variant="outlined" prepend-icon="mdi-book-open-variant">
              Konzept: docs/docs/projekte/kaimo
            </v-chip>
          </v-chip-group>
          <LBtn variant="secondary" block prepend-icon="mdi-refresh" @click="refresh">
            Berechtigungen neu laden
          </LBtn>
          <v-alert
            v-if="successMessage"
            type="success"
            variant="tonal"
            class="mt-4"
            icon="mdi-check"
          >
            {{ successMessage }}
          </v-alert>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { usePermissions } from '@/composables/usePermissions';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { createKaimoCase } from '@/services/kaimoApi';

const router = useRouter();
const { hasPermission, isResearcher, fetchPermissions } = usePermissions();
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['hero', 'content']);

const canManageKaimo = computed(() => {
  return isResearcher.value || hasPermission('admin:kaimo:manage');
});

const formRef = ref(null);
const form = reactive({
  name: '',
  display_name: '',
  description: '',
  icon: '',
  color: '#4CAF50'
});
const submitting = ref(false);
const successMessage = ref('');
const loadError = ref(null);

const canSubmit = computed(() => form.name.trim().length > 0 && form.display_name.trim().length > 0 && !submitting.value);

const submit = async () => {
  if (!canSubmit.value) return;
  submitting.value = true;
  successMessage.value = '';
  loadError.value = '';
  try {
    await createKaimoCase({
      name: form.name.trim(),
      display_name: form.display_name.trim(),
      description: form.description,
      icon: form.icon,
      color: form.color
    });
    successMessage.value = 'Fall wurde angelegt (Draft).';
    // optional redirect to panel
    router.push({ name: 'KaimoPanel' });
  } catch (err) {
    console.error('KAIMO create error', err);
    loadError.value = 'Fall konnte nicht angelegt werden.';
  } finally {
    submitting.value = false;
  }
};

const refresh = async () => {
  await withLoading('content', async () => {
    await fetchPermissions(true);
  });
  setLoading('hero', false);
};

onMounted(refresh);
</script>

<style scoped>
.kaimo-new-case {
  max-width: 1100px;
}

.gap-3 {
  gap: 12px;
}

.gap-2 {
  gap: 8px;
}
</style>
