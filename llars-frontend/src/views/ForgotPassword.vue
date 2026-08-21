<template>
  <div class="login-page" :class="{ 'dark-mode': isDarkMode, 'is-mobile': isMobile, 'is-ios': isIOS }">
    <div class="paint-strokes">
      <div v-for="n in 10" :key="n"></div>
    </div>

    <div class="login-container">
      <div class="login-card">
        <!-- Settings Bar (Theme + Language) -->
        <div class="login-settings-bar">
          <LThemeToggle />
          <LLanguageToggle />
        </div>

        <!-- Header with Logo -->
        <div class="login-header">
          <img src="@/assets/logo/llars-logo.png" alt="LLARS Logo" class="login-logo" />
          <h1 class="login-title">{{ $t('auth.passwordReset.requestTitle') }}</h1>
          <p class="login-subtitle">{{ $t('auth.passwordReset.requestSubtitle') }}</p>
        </div>

        <!-- Request Form -->
        <div class="login-form">
          <template v-if="!submitted">
            <v-form @submit.prevent="handleRequest">
              <v-text-field
                v-model="identifier"
                :label="$t('auth.passwordReset.identifierLabel')"
                data-testid="reset-identifier-input"
                autocomplete="username"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-account-key"
                :disabled="isSubmitting"
                @keyup.enter="handleRequest"
                class="login-field"
                hide-details="auto"
              />

              <LBtn
                variant="primary"
                block
                size="large"
                @click="handleRequest"
                :loading="isSubmitting"
                :disabled="isSubmitting || !identifier"
                prepend-icon="mdi-email-arrow-right"
                class="login-button"
                data-testid="reset-request-btn"
              >
                {{ $t('auth.passwordReset.requestSubmit') }}
              </LBtn>
            </v-form>
          </template>

          <!-- Neutral confirmation (shown regardless of whether the account exists) -->
          <v-alert
            v-else
            type="success"
            variant="tonal"
            density="comfortable"
            class="login-error"
          >
            {{ $t('auth.passwordReset.requestSent') }}
          </v-alert>

          <div class="login-forgot">
            <router-link to="/login" class="login-link">{{ $t('auth.passwordReset.backToLogin') }}</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useTheme } from 'vuetify';
import axios from 'axios';
import { useMobile } from '@/composables/useMobile';

const theme = useTheme();
const isDarkMode = computed(() => theme.global.current.value.dark);
const { isMobile, isIOS } = useMobile();

const identifier = ref('');
const isSubmitting = ref(false);
const submitted = ref(false);

async function handleRequest() {
  if (!identifier.value || isSubmitting.value) return;
  isSubmitting.value = true;
  try {
    // The endpoint always returns a neutral 200 (anti-enumeration); we show
    // the same confirmation no matter what so the UI cannot leak account
    // existence either.
    await axios.post('/auth/password-reset/request', {
      email_or_username: identifier.value,
    });
  } catch {
    // Even on a transport error we present the neutral confirmation rather
    // than surfacing details that could aid enumeration.
  } finally {
    isSubmitting.value = false;
    submitted.value = true;
  }
}
</script>

<style scoped>
.login-page {
  height: calc(100vh - 94px);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: rgb(var(--v-theme-background));
  overflow: hidden;
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 16px;
}

.login-card {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  box-shadow: var(--llars-shadow-lg, 0 8px 32px rgba(0, 0, 0, 0.12));
  overflow: hidden;
}

.login-settings-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.1);
}

.login-header {
  background: var(--llars-gradient-primary);
  padding: 24px 20px;
  text-align: center;
  color: white;
}

.login-logo {
  width: 56px;
  height: 56px;
  margin-bottom: 8px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.login-title {
  font-size: 1.35rem;
  font-weight: 600;
  margin: 0 0 2px 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.login-subtitle {
  font-size: 0.85rem;
  margin: 0;
  opacity: 0.9;
}

.login-form {
  padding: 20px;
}

.login-field {
  margin-bottom: 12px;
}

.login-field :deep(.v-field) {
  border-radius: var(--llars-radius-sm);
}

.login-button {
  margin-top: 4px;
}

.login-error {
  margin-top: 4px;
  border-radius: var(--llars-radius-xs);
}

.login-forgot {
  margin-top: 16px;
  text-align: center;
}

.login-link {
  font-size: 0.85rem;
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}

.login-link:hover {
  text-decoration: underline;
}

/* Paint Strokes Background */
.paint-strokes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.paint-strokes div {
  position: absolute;
  filter: blur(55px);
  opacity: 0.55;
}

.paint-strokes div:nth-child(1) { background: rgba(176, 202, 151, 0.7); top: -24%; left: -22%; width: 62%; height: 56%; border-radius: 65% 35% 70% 30% / 55% 45% 60% 40%; }
.paint-strokes div:nth-child(2) { background: rgba(209, 188, 138, 0.6); top: -22%; right: -24%; width: 66%; height: 60%; border-radius: 40% 60% 55% 45% / 60% 40% 50% 50%; }
.paint-strokes div:nth-child(3) { background: rgba(136, 196, 200, 0.55); top: 12%; left: -26%; width: 56%; height: 50%; border-radius: 55% 45% 60% 40% / 45% 55% 65% 35%; }
.paint-strokes div:nth-child(4) { background: rgba(232, 200, 122, 0.5); top: 12%; right: -26%; width: 54%; height: 56%; border-radius: 60% 40% 65% 35% / 35% 65% 45% 55%; }
.paint-strokes div:nth-child(5) { background: rgba(152, 212, 187, 0.6); bottom: -24%; left: -22%; width: 62%; height: 56%; border-radius: 70% 30% 50% 50% / 50% 50% 70% 30%; }
.paint-strokes div:nth-child(6) { background: rgba(168, 197, 226, 0.55); bottom: -22%; right: -24%; width: 60%; height: 62%; border-radius: 45% 55% 40% 60% / 40% 60% 70% 30%; }
.paint-strokes div:nth-child(7) { background: rgba(232, 160, 135, 0.45); top: -22%; left: 4%; width: 45%; height: 42%; border-radius: 35% 65% 45% 55% / 55% 45% 60% 40%; }
.paint-strokes div:nth-child(8) { background: rgba(201, 168, 226, 0.4); bottom: -22%; left: 52%; width: 50%; height: 45%; border-radius: 45% 55% 35% 65% / 65% 35% 55% 45%; }
.paint-strokes div:nth-child(9) { background: rgba(235, 206, 148, 0.45); top: -30%; left: 14%; width: 72%; height: 52%; border-radius: 50% 50% 60% 40% / 55% 45% 50% 50%; }
.paint-strokes div:nth-child(10) { background: rgba(180, 210, 240, 0.45); bottom: -32%; left: 10%; width: 78%; height: 58%; border-radius: 55% 45% 50% 50% / 60% 40% 55% 45%; }

.login-page.dark-mode .paint-strokes div { filter: blur(80px); opacity: 0.35; }

.login-page.is-mobile {
  height: 100vh;
  height: 100dvh;
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.login-page.is-ios .login-field :deep(input) {
  font-size: 16px !important;
}

@media (max-width: 600px) {
  .login-page { padding: 0; }
  .paint-strokes div { filter: blur(40px); opacity: 0.35; }
}
</style>
