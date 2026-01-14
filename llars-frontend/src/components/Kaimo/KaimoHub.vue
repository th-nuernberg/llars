<template>
  <v-container class="kaimo-hub">
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
              <v-avatar color="primary" size="44" class="mr-3">
                <LIcon color="white">mdi-shield-account</LIcon>
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">KAIMO</div>
                <div class="text-subtitle-1 text-medium-emphasis">
                  {{ $t('kaimo.hub.subtitle') }}
                </div>
              </div>
            </div>
            <div class="text-body-2 text-medium-emphasis">
              {{ $t('kaimo.hub.description') }}
            </div>
          </div>
          <v-spacer />
          <div class="d-flex align-center flex-wrap gap-2">
            <v-chip color="primary" variant="flat" prepend-icon="mdi-flask-outline">
              {{ $t('kaimo.hub.chips.phase') }}
            </v-chip>
            <v-chip color="secondary" variant="outlined" prepend-icon="mdi-account-badge-outline">
              {{ $t('kaimo.hub.chips.roles') }}
            </v-chip>
            <v-chip v-if="canViewKaimo" color="primary" variant="outlined" prepend-icon="mdi-folder">
              {{ $t('kaimo.hub.chips.cases', { total: caseStats.total, published: caseStats.published, draft: caseStats.draft }) }}
            </v-chip>
          </div>
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-skeleton-loader
          v-if="isLoading('cards')"
          type="card@2"
          class="mb-4"
        />
        <v-alert
          v-else-if="!canViewKaimo"
          type="warning"
          variant="tonal"
          icon="mdi-lock-alert"
        >
          {{ $t('kaimo.hub.alerts.noAccess') }}
        </v-alert>
        <v-alert
          v-else-if="loadingError"
          type="error"
          variant="tonal"
          icon="mdi-alert"
          class="mb-4"
        >
          {{ loadingError }}
        </v-alert>
      </v-col>
    </v-row>

    <v-row v-if="!isLoading('cards') && canViewKaimo" class="kaimo-card-grid">
      <v-col
        v-for="card in visibleCards"
        :key="card.title"
        cols="12"
        md="6"
        class="d-flex"
      >
        <v-card
          class="pa-4 hover-card flex-grow-1"
          variant="tonal"
          :color="card.color"
          @click="card.action()"
        >
          <div class="d-flex align-center mb-3">
            <v-avatar :color="card.avatarColor" size="46" class="mr-3">
              <LIcon color="white">{{ card.icon }}</LIcon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">{{ card.title }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">
                {{ card.subtitle }}
              </div>
            </div>
            <v-spacer />
            <v-chip size="small" color="primary" variant="flat" v-if="card.badge">
              {{ card.badge }}
            </v-chip>
          </div>
          <div class="text-body-2 text-medium-emphasis mb-4">
            {{ card.description }}
          </div>
          <div class="d-flex align-center gap-2">
            <v-btn
              color="primary"
              variant="flat"
              :append-icon="card.buttonIcon || 'mdi-arrow-right'"
            >
              {{ card.cta }}
            </v-btn>
            <v-chip
              v-if="card.permissionHint"
              color="primary"
              size="small"
              variant="outlined"
              prepend-icon="mdi-shield-key-outline"
            >
              {{ card.permissionHint }}
            </v-chip>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { usePermissions } from '@/composables/usePermissions';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { getKaimoCases } from '@/services/kaimoApi';

const router = useRouter();
const { t, locale } = useI18n();
const { hasPermission, isResearcher, fetchPermissions } = usePermissions();
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['hero', 'cards']);

const canViewKaimo = computed(() => {
  return hasPermission('feature:kaimo:view') || isResearcher.value || hasPermission('admin:kaimo:manage');
});

const showCreateCard = computed(() => isResearcher.value || hasPermission('admin:kaimo:manage'));

const caseStats = ref({
  total: 0,
  published: 0,
  draft: 0,
});

const loadingError = ref(null);

const visibleCards = computed(() => {
  locale.value;
  const cards = [
    {
      title: t('kaimo.hub.cards.panel.title'),
      subtitle: t('kaimo.hub.cards.panel.subtitle'),
      description: t('kaimo.hub.cards.panel.description'),
      icon: 'mdi-human-child',
      color: 'primary',
      avatarColor: 'primary',
      cta: t('kaimo.hub.cards.panel.cta'),
      action: () => router.push({ name: 'KaimoPanel' }),
      permissionHint: t('kaimo.hub.cards.panel.permission')
    }
  ];

  if (showCreateCard.value) {
    cards.push({
      title: t('kaimo.hub.cards.newCase.title'),
      subtitle: t('kaimo.hub.cards.newCase.subtitle'),
      description: t('kaimo.hub.cards.newCase.description'),
      icon: 'mdi-clipboard-plus-outline',
      color: 'secondary',
      avatarColor: 'secondary',
      cta: t('kaimo.hub.cards.newCase.cta'),
      buttonIcon: 'mdi-pencil-outline',
      action: () => router.push({ name: 'KaimoNewCase' }),
      badge: t('kaimo.hub.cards.newCase.badge'),
      permissionHint: t('kaimo.hub.cards.newCase.permission')
    });
  }

  return cards;
});

async function loadStats() {
  try {
    loadingError.value = null;
    const data = await getKaimoCases();
    const cases = data?.cases || [];
    caseStats.value.total = cases.length;
    caseStats.value.published = cases.filter(c => c.status === 'published').length;
    caseStats.value.draft = cases.filter(c => c.status === 'draft').length;
  } catch (err) {
    loadingError.value = t('kaimo.hub.errors.load');
    console.error('KAIMO-Statistikfehler', err);
  }
}

onMounted(async () => {
  await withLoading('cards', async () => {
    await fetchPermissions(true);
    if (canViewKaimo.value) {
      await loadStats();
    }
  });
  setLoading('hero', false);
});
</script>

<style scoped>
.kaimo-hub {
  max-width: 1100px;
}

.hover-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
  border: 1px solid rgba(var(--v-theme-primary), 0.18);
}

.hover-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.kaimo-card-grid {
  row-gap: 16px;
}

.gap-3 {
  gap: 12px;
}

.gap-2 {
  gap: 8px;
}
</style>
