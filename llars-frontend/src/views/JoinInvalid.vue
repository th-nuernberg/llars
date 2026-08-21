<template>
  <!--
    Friendly fallback when /join/:code resolves to an unknown, expired
    or revoked referral link. Register.vue redirects to this view
    instead of showing a half-broken form with an inline error so the
    user always sees a clear next step.
  -->
  <v-container class="join-invalid" max-width="640">
    <v-card class="invalid-card">
      <div class="invalid-icon">
        <v-icon size="44" color="warning">mdi-link-variant-off</v-icon>
      </div>
      <h1 class="invalid-h1">{{ $t('auth.joinInvalid.title') }}</h1>
      <p class="invalid-body">{{ $t('auth.joinInvalid.body') }}</p>
      <p v-if="codeAttempted" class="invalid-code">
        {{ $t('auth.joinInvalid.codeLabel') }}
        <code>{{ codeAttempted }}</code>
      </p>

      <div class="invalid-actions">
        <LBtn variant="primary" prepend-icon="mdi-login" @click="goLogin">
          {{ $t('auth.joinInvalid.toLogin') }}
        </LBtn>
        <LBtn variant="text" prepend-icon="mdi-email-outline" @click="contactUs">
          {{ $t('auth.joinInvalid.contact') }}
        </LBtn>
      </div>
    </v-card>
  </v-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// Carry over the attempted code from the query string so the user
// sees which link they tried — useful when they paste the wrong slug
// from an email.
const codeAttempted = computed(() => {
  const raw = route.query.code
  return typeof raw === 'string' ? raw.slice(0, 120) : ''
})

function goLogin() {
  router.push('/login')
}

function contactUs() {
  window.location.href = 'mailto:llars@e-beratungsinstitut.de'
}
</script>

<style scoped>
.join-invalid {
  padding: 60px 24px;
}

.invalid-card {
  padding: 36px 32px;
  border-radius: 16px 4px 16px 4px;
  text-align: center;
  box-shadow:
    0 16px 48px rgba(60, 80, 45, 0.18),
    0 4px 12px rgba(60, 80, 45, 0.10);
}

.invalid-icon {
  margin-bottom: 16px;
}

.invalid-h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 12px;
  color: rgb(var(--v-theme-on-surface));
}

.invalid-body {
  font-size: 0.95rem;
  line-height: 1.55;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.85;
  margin: 0 0 16px;
}

.invalid-code {
  font-size: 0.85rem;
  opacity: 0.7;
  margin: 0 0 24px;
}

.invalid-code code {
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  background: rgba(var(--v-theme-on-surface), 0.08);
  padding: 2px 8px;
  border-radius: 4px;
}

.invalid-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
