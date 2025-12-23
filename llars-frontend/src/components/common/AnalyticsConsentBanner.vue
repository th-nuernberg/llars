<template>
  <v-slide-y-reverse-transition>
    <div v-if="shouldShow" class="analytics-consent">
      <v-card class="analytics-consent-card" elevation="6">
        <div class="analytics-consent-content">
          <div class="text">
            <div class="title">Analytics & Datenschutz</div>
            <div class="body">
              Wir nutzen Matomo, um die Nutzung der Plattform zu verbessern. Sie können zustimmen oder ablehnen.
              Details finden Sie in der Datenschutzerklärung.
            </div>
          </div>
          <div class="actions">
            <v-btn variant="text" size="small" @click="openPrivacy">Datenschutz</v-btn>
            <v-btn variant="outlined" size="small" class="ml-2" @click="decline">Ablehnen</v-btn>
            <v-btn color="primary" size="small" class="ml-2" @click="accept">Zustimmen</v-btn>
          </div>
        </div>
      </v-card>
    </div>
  </v-slide-y-reverse-transition>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  useAnalyticsConfig,
  useAnalyticsConsent,
  setAnalyticsConsentState
} from '@/plugins/llars-metrics'

const router = useRouter()
const analyticsConfig = useAnalyticsConfig()
const consentState = useAnalyticsConsent()

const shouldShow = computed(() => {
  const config = analyticsConfig.value || {}
  const requiresConsent = Boolean(config.require_consent || config.require_cookie_consent)
  return Boolean(config.matomo_enabled && requiresConsent && !consentState.value)
})

const accept = () => setAnalyticsConsentState('granted')
const decline = () => setAnalyticsConsentState('denied')

const openPrivacy = () => {
  router.push('/datenschutz')
}
</script>

<style scoped>
.analytics-consent {
  position: fixed;
  bottom: 16px;
  left: 16px;
  right: 16px;
  z-index: 1000;
  display: flex;
  justify-content: center;
}

.analytics-consent-card {
  width: min(880px, 100%);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface), 0.96);
  backdrop-filter: blur(6px);
}

.analytics-consent-content {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
}

.analytics-consent-content .text {
  flex: 1 1 320px;
}

.analytics-consent-content .title {
  font-weight: 600;
  margin-bottom: 4px;
}

.analytics-consent-content .body {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.analytics-consent-content .actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>
