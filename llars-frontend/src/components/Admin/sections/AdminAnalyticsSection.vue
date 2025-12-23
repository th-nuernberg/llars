<template>
  <div class="analytics-section">
    <v-skeleton-loader
      v-if="isLoading('settings')"
      type="card, paragraph, actions"
      height="220"
      class="mb-4"
    />

    <v-card v-else class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-chart-bar</v-icon>
        Matomo Analytics
        <v-spacer></v-spacer>
        <LBtn
          prepend-icon="mdi-open-in-new"
          variant="tonal"
          @click="openMatomo"
        >
          Matomo öffnen
        </LBtn>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <v-alert
          v-if="errorMessage"
          type="error"
          variant="tonal"
          density="compact"
          class="mb-3"
        >
          {{ errorMessage }}
        </v-alert>

        <v-alert
          v-if="!settings.matomo_enabled"
          type="warning"
          variant="tonal"
          density="compact"
          class="mb-3"
        >
          Matomo Tracking ist deaktiviert. Die UI ist trotzdem unter <code>{{ matomoBasePath }}</code> erreichbar.
        </v-alert>

        <v-row>
          <v-col cols="12" md="6">
            <v-switch
              v-model="settings.matomo_enabled"
              label="Tracking aktiv"
              color="primary"
              hide-details
            />
            <v-switch
              v-model="settings.set_user_id"
              label="User-ID setzen (Authentik username/sub)"
              color="primary"
              hide-details
              class="mt-1"
            />
            <v-switch
              v-model="settings.track_clicks"
              label="Button-/Link-Klicks tracken"
              color="primary"
              hide-details
              class="mt-1"
            />
            <v-switch
              v-model="settings.track_hovers"
              label="Hover-Events tracken (Desktop)"
              color="primary"
              hide-details
              class="mt-1"
            />

            <v-text-field
              v-model.number="settings.hover_min_ms"
              type="number"
              label="Hover Mindestdauer (ms)"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mt-3"
              :disabled="!settings.track_hovers"
              min="0"
            />

            <v-slider
              v-model="settings.hover_sample_rate"
              label="Hover Sampling Rate"
              min="0"
              max="1"
              step="0.05"
              thumb-label
              hide-details
              class="mt-2"
              :disabled="!settings.track_hovers"
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              v-model="settings.matomo_base_url"
              label="Matomo Base URL"
              variant="outlined"
              density="comfortable"
              hide-details
              placeholder="/analytics/"
            />

            <v-text-field
              v-model.number="settings.matomo_site_id"
              type="number"
              label="Matomo Site ID"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mt-3"
              min="1"
            />

            <v-switch
              v-model="settings.heartbeat_enabled"
              label="Heartbeat (Time-on-Page)"
              color="primary"
              hide-details
              class="mt-3"
            />

            <v-text-field
              v-model.number="settings.heartbeat_seconds"
              type="number"
              label="Heartbeat Intervall (Sekunden)"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mt-2"
              :disabled="!settings.heartbeat_enabled"
              min="5"
            />

            <v-divider class="my-4" />

            <v-switch
              v-model="settings.include_query"
              label="Querystring in Pageviews einschließen"
              color="primary"
              hide-details
            />
            <v-switch
              v-model="settings.disable_cookies"
              label="Cookies deaktivieren"
              color="primary"
              hide-details
              class="mt-1"
            />
            <v-switch
              v-model="settings.require_consent"
              label="Consent erforderlich (requireConsent)"
              color="primary"
              hide-details
              class="mt-1"
            />
            <v-switch
              v-model="settings.require_cookie_consent"
              label="Cookie-Consent erforderlich (requireCookieConsent)"
              color="primary"
              hide-details
              class="mt-1"
              :disabled="settings.require_consent"
            />

            <v-divider class="my-4" />

            <div class="text-subtitle-2 font-weight-medium mb-2">
              Custom Dimensions (Matomo IDs)
            </div>
            <v-text-field
              v-model.number="settings.dimension_route_id"
              type="number"
              label="Route"
              variant="outlined"
              density="comfortable"
              hide-details
              min="0"
            />
            <v-text-field
              v-model.number="settings.dimension_module_id"
              type="number"
              label="Modul"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mt-2"
              min="0"
            />
            <v-text-field
              v-model.number="settings.dimension_entity_id"
              type="number"
              label="Entity (z. B. Prompt/Doc/Session)"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mt-2"
              min="0"
            />
            <v-text-field
              v-model.number="settings.dimension_view_id"
              type="number"
              label="View/Pane"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mt-2"
              min="0"
            />
            <v-text-field
              v-model.number="settings.dimension_role_id"
              type="number"
              label="Rolle"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mt-2"
              min="0"
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end mt-4">
          <LBtn
            prepend-icon="mdi-content-save"
            variant="primary"
            :loading="saving"
            @click="save"
          >
            Speichern
          </LBtn>
        </div>
      </v-card-text>
    </v-card>

    <v-card v-if="!isLoading('settings')">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-open-in-new</v-icon>
        Matomo Dashboard
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <v-alert type="info" variant="tonal" density="compact" class="mb-3">
          Matomo schützt sich standardmäßig gegen Clickjacking und „bustet“ iFrames. Deshalb öffnen wir Matomo separat.
        </v-alert>

        <LBtn prepend-icon="mdi-open-in-new" variant="primary" @click="openMatomo">
          Matomo öffnen
        </LBtn>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { setAnalyticsConfig } from '@/plugins/llars-metrics'

const router = useRouter()

const { isLoading, withLoading } = useSkeletonLoading(['settings'])

const settings = ref({
  matomo_enabled: true,
  matomo_base_url: '/analytics/',
  matomo_site_id: 1,
  include_query: false,
  disable_cookies: true,  // Privacy: No cookies by default
  require_consent: true,  // Privacy: Require user consent before tracking
  require_cookie_consent: false,
  set_user_id: false,  // Privacy: Don't track user ID by default
  dimension_route_id: 0,
  dimension_module_id: 0,
  dimension_entity_id: 0,
  dimension_view_id: 0,
  dimension_role_id: 0,
  track_clicks: true,
  track_hovers: false,
  hover_min_ms: 400,
  hover_sample_rate: 1,
  heartbeat_enabled: true,
  heartbeat_seconds: 15
})

const saving = ref(false)
const errorMessage = ref('')

const resolveBasePath = (value) => {
  const configured = String(value || '/analytics/').trim()
  if (!configured) return '/analytics/'
  if (configured.startsWith('http://') || configured.startsWith('https://')) {
    return configured.endsWith('/') ? configured : `${configured}/`
  }
  const path = configured.startsWith('/') ? configured : `/${configured}`
  return path.endsWith('/') ? path : `${path}/`
}

const matomoBasePath = computed(() => resolveBasePath(settings.value.matomo_base_url))

const matomoSsoUrl = computed(() => {
  const base = matomoBasePath.value
  const absolute = base.startsWith('http://') || base.startsWith('https://') ? base : `${window.location.origin}${base}`
  return `${absolute}index.php?module=RebelOIDC&action=signIn&provider=oidc`
})

const openMatomo = () => {
  window.open(matomoSsoUrl.value, '_blank', 'noopener')
}

const load = async () => {
  errorMessage.value = ''
  await withLoading('settings', async () => {
    const { data } = await axios.get('/api/admin/analytics/settings')
    settings.value = data
  })
}

const save = async () => {
  saving.value = true
  errorMessage.value = ''
  try {
    const { data } = await axios.patch('/api/admin/analytics/settings', settings.value)
    settings.value = data
    setAnalyticsConfig(data, { router })
  } catch (e) {
    errorMessage.value = e?.response?.data?.message || e?.message || 'Speichern fehlgeschlagen'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
</style>
