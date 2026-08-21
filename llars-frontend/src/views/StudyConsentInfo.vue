<template>
  <!--
    Study-consent activation page. Reachable at /study-consent and
    linked from the consent pill on /join/:code. The full Art. 13
    disclosure + the actual activation control (LCheckbox + button)
    both live here. On activate, useStudyConsent persists the
    snapshot to sessionStorage and we navigate back to the
    return_to path so the pill on the register form flips to its
    granted state.
  -->
  <v-container class="consent-page" max-width="780">
    <v-btn
      variant="text"
      size="small"
      prepend-icon="mdi-arrow-left"
      class="back-link"
      @click="goBack"
    >
      {{ $t('common.back') }}
    </v-btn>

    <h1 class="consent-page-h1">
      <v-icon size="28" color="primary" class="mr-2">mdi-shield-check-outline</v-icon>
      {{ $t('auth.consent.title') }}
    </h1>

    <p class="consent-page-intro">{{ $t('auth.consent.intro') }}</p>

    <article class="consent-body">
      <h2>{{ $t('auth.consent.details.purpose.title') }}</h2>
      <p>{{ $t('auth.consent.details.purpose.body') }}</p>

      <h2>{{ $t('auth.consent.details.data.title') }}</h2>
      <p>{{ $t('auth.consent.details.data.body') }}</p>

      <h2>{{ $t('auth.consent.details.legal.title') }}</h2>
      <p>{{ $t('auth.consent.details.legal.body') }}</p>

      <h2>{{ $t('auth.consent.details.recipients.title') }}</h2>
      <p>{{ $t('auth.consent.details.recipients.body') }}</p>

      <h2>{{ $t('auth.consent.details.retention.title') }}</h2>
      <p>{{ $t('auth.consent.details.retention.body') }}</p>

      <h2>{{ $t('auth.consent.details.rights.title') }}</h2>
      <p>{{ $t('auth.consent.details.rights.body') }}</p>

      <h2>{{ $t('auth.consent.details.contact.title') }}</h2>
      <p>{{ $t('auth.consent.details.contact.body') }}</p>
    </article>

    <p class="consent-footer">{{ $t('auth.consent.footer') }}</p>

    <!-- Activation block: the LLARS LCheckbox is the consent action.
         Activating it + clicking the primary button persists the
         snapshot and returns to the form. -->
    <section class="consent-activate">
      <LCheckbox
        v-model="mandatory"
        size="small"
        class="consent-activate-checkbox"
        data-testid="consent-mandatory"
      >
        <span class="consent-activate-label">
          {{ $t('auth.consent.activateLabel') }}
        </span>
      </LCheckbox>

      <div class="consent-actions">
        <LBtn variant="cancel" @click="goBack">
          {{ $t('common.cancel') }}
        </LBtn>
        <LBtn
          variant="primary"
          :disabled="!mandatory"
          prepend-icon="mdi-check-circle-outline"
          data-testid="consent-submit"
          @click="grantAndReturn"
        >
          {{ $t('auth.consent.submitButton') }}
        </LBtn>
      </div>
    </section>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useStudyConsent } from '@/composables/useStudyConsent'

const router = useRouter()
const route = useRoute()
const { locale } = useI18n()
const { getConsent, setConsent } = useStudyConsent()

const CONSENT_VERSION = 'study-consent-v3-2026-05'

// Hydrate checkbox from any previously-granted snapshot so the user
// can re-confirm or correct after coming back via the pill's
// "Anpassen" link.
const mandatory = ref(false)
onMounted(() => {
  const existing = getConsent()
  if (existing && existing.version === CONSENT_VERSION) {
    mandatory.value = true
  }
})

function grantAndReturn() {
  if (!mandatory.value) return
  setConsent({
    version: CONSENT_VERSION,
    granted_at: new Date().toISOString(),
    language: locale.value || 'de',
  })
  const returnTo = route.query.return_to
  if (returnTo && typeof returnTo === 'string' && returnTo.startsWith('/')) {
    router.push(returnTo)
  } else {
    router.push('/register')
  }
}

function goBack() {
  const returnTo = route.query.return_to
  if (returnTo && typeof returnTo === 'string' && returnTo.startsWith('/')) {
    router.push(returnTo)
    return
  }
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/register')
  }
}
</script>

<style scoped>
.consent-page {
  padding: 32px 24px 80px;
}

.back-link {
  margin-bottom: 16px;
}

.consent-page-h1 {
  display: flex;
  align-items: center;
  font-size: 1.6rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0 0 12px;
  line-height: 1.25;
}

.consent-page-intro {
  font-size: 1rem;
  line-height: 1.55;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.9;
  margin: 0 0 24px;
}

.consent-body h2 {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 22px 0 6px;
  color: rgb(var(--v-theme-primary));
}

.consent-body p {
  font-size: 0.92rem;
  line-height: 1.6;
  margin: 0 0 4px;
}

.consent-footer {
  margin-top: 28px;
  padding-top: 14px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  font-size: 0.82rem;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
  line-height: 1.5;
}

.consent-activate {
  margin-top: 28px;
  padding: 18px 16px;
  border: 1px solid rgba(var(--v-theme-primary), 0.4);
  border-radius: 12px 4px 12px 4px;
  background: rgba(var(--v-theme-primary), 0.05);
}

.consent-activate-checkbox {
  margin-bottom: 16px;
}

.consent-activate-label {
  font-size: 0.92rem;
  line-height: 1.45;
}

.consent-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
