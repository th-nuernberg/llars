<template>
  <div class="analytics-section">
    <v-card class="mb-4">
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
          v-if="!matomoEnabled"
          type="warning"
          variant="tonal"
          density="compact"
          class="mb-3"
        >
          Matomo Tracking ist deaktiviert (`VITE_MATOMO_ENABLED=false`). Die UI ist trotzdem unter
          <code>{{ matomoBasePath }}</code> erreichbar.
        </v-alert>

        <v-row>
          <v-col cols="12" md="6">
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>Base URL</v-list-item-title>
                <v-list-item-subtitle><code>{{ matomoBasePath }}</code></v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Site ID</v-list-item-title>
                <v-list-item-subtitle><code>{{ matomoSiteId }}</code></v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Click Tracking</v-list-item-title>
                <v-list-item-subtitle><code>{{ matomoTrackClicks }}</code></v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>User ID Tracking</v-list-item-title>
                <v-list-item-subtitle><code>{{ matomoSetUserId }}</code></v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>
          <v-col cols="12" md="6">
            <v-alert type="info" variant="tonal" density="compact">
              Hinweise: In Produktion sind Consent-/Cookie-Settings je nach GDPR/CMP nötig
              (`VITE_MATOMO_REQUIRE_CONSENT`, `VITE_MATOMO_REQUIRE_COOKIE_CONSENT`,
              `VITE_MATOMO_DISABLE_COOKIES`).
            </v-alert>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-open-in-new</v-icon>
        Matomo Dashboard
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <v-alert type="info" variant="tonal" density="compact" class="mb-3">
          Matomo schützt sich standardmäßig gegen Clickjacking und „bustet“ iFrames (→ Weiterleitung auf
          <code>{{ matomoBasePath }}</code>). Deshalb öffnen wir Matomo separat.
        </v-alert>

        <LBtn prepend-icon="mdi-open-in-new" variant="primary" @click="openMatomo">
          Matomo öffnen
        </LBtn>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const matomoEnabled = computed(() => String(import.meta.env.VITE_MATOMO_ENABLED || '').toLowerCase() !== 'false')
const matomoSiteId = computed(() => String(import.meta.env.VITE_MATOMO_SITE_ID || '1'))
const matomoTrackClicks = computed(() => String(import.meta.env.VITE_MATOMO_TRACK_CLICKS ?? 'true'))
const matomoSetUserId = computed(() => String(import.meta.env.VITE_MATOMO_SET_USER_ID ?? 'true'))

const matomoBasePath = computed(() => {
  const configured = String(import.meta.env.VITE_MATOMO_BASE_URL || '/matomo/').trim()
  if (configured.startsWith('http://') || configured.startsWith('https://')) {
    return configured.endsWith('/') ? configured : `${configured}/`
  }
  if (!configured.startsWith('/')) {
    return `/${configured.endsWith('/') ? configured : `${configured}/`}`
  }
  return configured.endsWith('/') ? configured : `${configured}/`
})

const openMatomo = () => {
  window.open(matomoBasePath.value, '_blank', 'noopener')
}
</script>

<style scoped>
</style>
