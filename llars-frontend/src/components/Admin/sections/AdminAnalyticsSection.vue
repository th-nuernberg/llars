<template>
  <div class="analytics-section">
    <!-- Loading State -->
    <template v-if="isLoading('settings')">
      <div class="analytics-header">
        <LSkeleton type="box" height="40px" width="200px" />
        <LSkeleton type="box" height="36px" width="140px" />
      </div>
      <div class="analytics-content">
        <div class="settings-panel">
          <LSkeleton type="panel" :count="6" />
        </div>
        <div class="settings-panel">
          <LSkeleton type="panel" :count="6" />
        </div>
      </div>
    </template>

    <!-- Loaded State -->
    <template v-else>
      <!-- Header Row -->
      <div class="analytics-header">
        <div class="header-title">
          <div class="title-icon" :class="{ 'title-icon--active': settings.matomo_enabled }">
            <LIcon size="20" color="white">mdi-chart-bar</LIcon>
          </div>
          <div>
            <h2 class="text-subtitle-1 font-weight-bold">Matomo Analytics</h2>
            <span class="text-caption" :class="settings.matomo_enabled ? 'text-success' : 'text-warning'">
              {{ settings.matomo_enabled ? 'Tracking aktiv' : 'Tracking deaktiviert' }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <LBtn variant="secondary" size="small" prepend-icon="mdi-open-in-new" @click="openMatomo">
            Matomo öffnen
          </LBtn>
          <LBtn variant="primary" size="small" prepend-icon="mdi-content-save" :loading="saving" @click="save">
            Speichern
          </LBtn>
        </div>
      </div>

      <!-- Error Message -->
      <v-alert v-if="errorMessage" type="error" variant="tonal" density="compact" class="error-alert" closable @click:close="errorMessage = ''">
        {{ errorMessage }}
      </v-alert>

      <!-- Main Content -->
      <div class="analytics-content">
        <!-- Left Column: Tracking Settings -->
        <div class="settings-panel">
          <div class="panel-header">
            <LIcon size="16" class="mr-2">mdi-radar</LIcon>
            <span class="panel-title">Tracking</span>
          </div>
          <div class="panel-content">
            <div class="settings-group">
              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">Tracking aktiv</span>
                  <span class="setting-desc">Aktiviert das Matomo-Tracking</span>
                </div>
                <v-switch v-model="settings.matomo_enabled" color="primary" hide-details density="compact" />
              </div>

              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">User-ID setzen</span>
                  <span class="setting-desc">Authentik username/sub tracken</span>
                </div>
                <v-switch v-model="settings.set_user_id" color="primary" hide-details density="compact" />
              </div>

              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">Klick-Tracking</span>
                  <span class="setting-desc">Button- und Link-Klicks erfassen</span>
                </div>
                <v-switch v-model="settings.track_clicks" color="primary" hide-details density="compact" />
              </div>

              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">Hover-Tracking</span>
                  <span class="setting-desc">Hover-Events erfassen (Desktop)</span>
                </div>
                <v-switch v-model="settings.track_hovers" color="primary" hide-details density="compact" />
              </div>

              <div v-if="settings.track_hovers" class="sub-settings">
                <v-text-field
                  v-model.number="settings.hover_min_ms"
                  type="number"
                  label="Hover Mindestdauer (ms)"
                  variant="outlined"
                  density="compact"
                  hide-details
                  min="0"
                />
                <div class="slider-setting">
                  <span class="slider-label">Sampling Rate: {{ (settings.hover_sample_rate * 100).toFixed(0) }}%</span>
                  <v-slider
                    v-model="settings.hover_sample_rate"
                    min="0"
                    max="1"
                    step="0.05"
                    hide-details
                    color="primary"
                  />
                </div>
              </div>
            </div>

            <div class="settings-divider" />

            <div class="settings-group">
              <div class="group-title">Heartbeat</div>

              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">Heartbeat aktiv</span>
                  <span class="setting-desc">Time-on-Page Messung</span>
                </div>
                <v-switch v-model="settings.heartbeat_enabled" color="primary" hide-details density="compact" />
              </div>

              <div v-if="settings.heartbeat_enabled" class="sub-settings">
                <v-text-field
                  v-model.number="settings.heartbeat_seconds"
                  type="number"
                  label="Intervall (Sekunden)"
                  variant="outlined"
                  density="compact"
                  hide-details
                  min="5"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Middle Column: Privacy & Config -->
        <div class="settings-panel">
          <div class="panel-header">
            <LIcon size="16" class="mr-2">mdi-shield-lock</LIcon>
            <span class="panel-title">Privacy & Config</span>
          </div>
          <div class="panel-content">
            <div class="settings-group">
              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">Cookies deaktivieren</span>
                  <span class="setting-desc">Tracking ohne Cookies</span>
                </div>
                <v-switch v-model="settings.disable_cookies" color="primary" hide-details density="compact" />
              </div>

              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">Consent erforderlich</span>
                  <span class="setting-desc">requireConsent aktivieren</span>
                </div>
                <v-switch v-model="settings.require_consent" color="primary" hide-details density="compact" />
              </div>

              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">Cookie-Consent</span>
                  <span class="setting-desc">requireCookieConsent aktivieren</span>
                </div>
                <v-switch v-model="settings.require_cookie_consent" color="primary" hide-details density="compact" :disabled="settings.require_consent" />
              </div>

              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-label">Query in Pageviews</span>
                  <span class="setting-desc">Querystring einschließen</span>
                </div>
                <v-switch v-model="settings.include_query" color="primary" hide-details density="compact" />
              </div>
            </div>

            <div class="settings-divider" />

            <div class="settings-group">
              <div class="group-title">Matomo Server</div>
              <v-text-field
                v-model="settings.matomo_base_url"
                label="Base URL"
                variant="outlined"
                density="compact"
                hide-details
                placeholder="/analytics/"
                class="mb-2"
              />
              <v-text-field
                v-model.number="settings.matomo_site_id"
                type="number"
                label="Site ID"
                variant="outlined"
                density="compact"
                hide-details
                min="1"
              />
            </div>
          </div>
        </div>

        <!-- Right Column: Dimensions -->
        <div class="settings-panel">
          <div class="panel-header">
            <LIcon size="16" class="mr-2">mdi-ruler-square</LIcon>
            <span class="panel-title">Custom Dimensions</span>
          </div>
          <div class="panel-content">
            <div class="settings-group dimensions-grid">
              <div class="dimension-item">
                <v-text-field
                  v-model.number="settings.dimension_route_id"
                  type="number"
                  label="Route"
                  variant="outlined"
                  density="compact"
                  hide-details
                  min="0"
                >
                  <template #prepend-inner>
                    <LIcon size="16" color="primary">mdi-routes</LIcon>
                  </template>
                </v-text-field>
              </div>

              <div class="dimension-item">
                <v-text-field
                  v-model.number="settings.dimension_module_id"
                  type="number"
                  label="Modul"
                  variant="outlined"
                  density="compact"
                  hide-details
                  min="0"
                >
                  <template #prepend-inner>
                    <LIcon size="16" color="secondary">mdi-puzzle</LIcon>
                  </template>
                </v-text-field>
              </div>

              <div class="dimension-item">
                <v-text-field
                  v-model.number="settings.dimension_entity_id"
                  type="number"
                  label="Entity"
                  variant="outlined"
                  density="compact"
                  hide-details
                  min="0"
                >
                  <template #prepend-inner>
                    <LIcon size="16" color="accent">mdi-database</LIcon>
                  </template>
                </v-text-field>
              </div>

              <div class="dimension-item">
                <v-text-field
                  v-model.number="settings.dimension_view_id"
                  type="number"
                  label="View/Pane"
                  variant="outlined"
                  density="compact"
                  hide-details
                  min="0"
                >
                  <template #prepend-inner>
                    <LIcon size="16" color="info">mdi-view-dashboard</LIcon>
                  </template>
                </v-text-field>
              </div>

              <div class="dimension-item">
                <v-text-field
                  v-model.number="settings.dimension_role_id"
                  type="number"
                  label="Rolle"
                  variant="outlined"
                  density="compact"
                  hide-details
                  min="0"
                >
                  <template #prepend-inner>
                    <LIcon size="16" color="warning">mdi-account-key</LIcon>
                  </template>
                </v-text-field>
              </div>
            </div>

            <div class="settings-divider" />

            <!-- Info Box -->
            <div class="info-box">
              <LIcon size="16" class="mr-2" color="info">mdi-information</LIcon>
              <div class="info-text">
                <span class="info-title">Matomo iFrame</span>
                <span class="info-desc">Matomo schützt sich gegen Clickjacking. Dashboard wird extern geöffnet.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
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
  disable_cookies: true,
  require_consent: true,
  require_cookie_consent: false,
  set_user_id: false,
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
.analytics-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
  overflow: hidden;
}

/* Header */
.analytics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  padding: 8px 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #9E9E9E;
  transition: background 0.2s ease;
}

.title-icon--active {
  background: #4CAF50;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* Error Alert */
.error-alert {
  flex-shrink: 0;
}

/* Main Content */
.analytics-content {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  flex: 1;
  min-height: 0;
}

/* Settings Panel */
.settings-panel {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  min-height: 0;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  flex-shrink: 0;
}

.panel-title {
  font-size: 0.875rem;
  font-weight: 600;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* Settings Groups */
.settings-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-title {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.5);
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.settings-divider {
  height: 1px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  margin: 12px 0;
}

/* Setting Item */
.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-radius: 6px;
  transition: background 0.15s ease;
}

.setting-item:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
  flex: 1;
  margin-right: 8px;
}

.setting-label {
  font-size: 0.8rem;
  font-weight: 500;
}

.setting-desc {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Sub Settings */
.sub-settings {
  padding: 8px 12px;
  margin-left: 8px;
  border-left: 2px solid rgba(var(--v-theme-primary), 0.3);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider-setting {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.slider-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Dimensions Grid */
.dimensions-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dimension-item {
  display: flex;
  align-items: center;
}

/* Info Box */
.info-box {
  display: flex;
  align-items: flex-start;
  padding: 10px 12px;
  background: rgba(var(--v-theme-info), 0.08);
  border-radius: 6px;
  border-left: 3px solid rgb(var(--v-theme-info));
}

.info-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-title {
  font-size: 0.75rem;
  font-weight: 600;
}

.info-desc {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Responsive */
@media (max-width: 1200px) {
  .analytics-content {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 800px) {
  .analytics-content {
    grid-template-columns: 1fr;
  }

  .analytics-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
