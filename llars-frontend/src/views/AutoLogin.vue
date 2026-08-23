<template>
  <!--
    Passwordless magic auto-login landing. The QR-join welcome mail and the
    returning-user sign-in mail link to /auto-login/<token>; on mount we POST
    the token to /auth/magic-login. On success the backend returns an
    Authentik token bundle which we install exactly like Register.vue's
    auto-login block (auth.applyTokenBundle), then route to the server-provided
    redirect_path.

    Sign-in links are MULTI-USE within their 7-day TTL (see the magic_login
    docstring in app/routes/auth/password_reset_routes.py), so the only realistic
    failure a participant hits is an EXPIRED link. The failure state is therefore
    written as a friendly expiry explanation whose primary next step is
    self-service: set your own password via "Passwort vergessen" (/forgot-password),
    with "back to login" kept as the secondary action.
  -->
  <v-container class="auto-login" max-width="640">
    <v-card class="auto-login-card">
      <!-- Working: small centered loading card -->
      <template v-if="working">
        <div class="auto-login-icon">
          <v-progress-circular indeterminate size="44" width="4" color="primary" />
        </div>
        <h1 class="auto-login-h1">{{ $t('autoLogin.signingIn') }}</h1>
      </template>

      <!-- Expired / invalid link: explain + point at the self-service reset -->
      <template v-else>
        <div class="auto-login-icon">
          <v-icon size="44" color="warning">mdi-link-variant-off</v-icon>
        </div>
        <h1 class="auto-login-h1">{{ $t('autoLogin.failedTitle') }}</h1>
        <p class="auto-login-body">{{ $t('autoLogin.failedBody') }}</p>

        <div class="auto-login-next">
          <v-icon size="20" color="primary" class="auto-login-next-icon">mdi-lock-reset</v-icon>
          <p class="auto-login-next-text">{{ $t('autoLogin.failedNextStep') }}</p>
        </div>

        <div class="auto-login-actions">
          <LBtn
            variant="primary"
            prepend-icon="mdi-lock-reset"
            data-testid="auto-login-forgot-password-btn"
            @click="goForgotPassword"
          >
            {{ $t('autoLogin.forgotPassword') }}
          </LBtn>
          <LBtn variant="cancel" prepend-icon="mdi-login" @click="goLogin">
            {{ $t('autoLogin.toLogin') }}
          </LBtn>
        </div>
      </template>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

const props = defineProps({
  token: {
    type: String,
    default: ''
  }
})

const router = useRouter()
const auth = useAuth()

// While true we show the loading card; flipped to false only on failure
// (on success we navigate away before the user sees a state change).
const working = ref(true)

function goLogin() {
  router.push('/login')
}

// Self-service escape hatch for an expired link: same target as the
// "Passwort vergessen?" link on the login page (router.js → ForgotPassword).
function goForgotPassword() {
  router.push('/forgot-password')
}

onMounted(async () => {
  if (!props.token) {
    working.value = false
    return
  }

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    // auth_bp is mounted at /auth (not /api/auth) — same prefix as the
    // password-reset endpoints (see ResetPassword.vue).
    const response = await axios.post(`${baseUrl}/auth/magic-login`, {
      token: props.token
    })

    const payload = response?.data || {}

    // Install the Authentik token bundle exactly like Register.vue's
    // auto-login path, then route to the backend-provided landing path.
    if (payload.success && payload.token) {
      const ok = await auth.applyTokenBundle(payload.token, payload.username)
      if (ok) {
        router.push(payload.redirect_path || '/evaluation')
        return
      }
    }

    // success:false or token install failed → show the failure state.
    working.value = false
  } catch (e) {
    // 4xx/5xx (invalid / expired token) → friendly failure card.
    working.value = false
  }
})
</script>

<style scoped>
.auto-login {
  padding: 60px 24px;
}

.auto-login-card {
  padding: 36px 32px;
  border-radius: 16px 4px 16px 4px;
  text-align: center;
  box-shadow:
    0 16px 48px rgba(60, 80, 45, 0.18),
    0 4px 12px rgba(60, 80, 45, 0.10);
}

.auto-login-icon {
  margin-bottom: 16px;
}

.auto-login-h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 12px;
  color: rgb(var(--v-theme-on-surface));
}

.auto-login-body {
  font-size: 0.95rem;
  line-height: 1.55;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.85;
  margin: 0 0 18px;
}

/* Next-step callout: the self-service password path is the actual way out of
   an expired link, so it gets its own tinted block instead of more body copy. */
.auto-login-next {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  text-align: left;
  padding: 14px 16px;
  margin: 0 0 24px;
  border-radius: 12px 3px 12px 3px;
  background: rgba(var(--v-theme-primary), 0.12);
}

.auto-login-next-icon {
  flex: 0 0 auto;
  margin-top: 2px;
}

.auto-login-next-text {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.9;
}

.auto-login-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
