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
          <h1 class="login-title">{{ $t('auth.passwordReset.resetTitle') }}</h1>
          <p class="login-subtitle">{{ $t('auth.passwordReset.resetSubtitle') }}</p>
        </div>

        <!-- Reset Form -->
        <div class="login-form">
          <!-- Success state -->
          <template v-if="done">
            <v-alert
              type="success"
              variant="tonal"
              density="comfortable"
              class="login-error"
            >
              {{ $t('auth.passwordReset.resetSuccess') }}
            </v-alert>
            <LBtn
              variant="primary"
              block
              size="large"
              prepend-icon="mdi-login"
              class="login-button"
              data-testid="reset-to-login-btn"
              @click="goToLogin"
            >
              {{ $t('auth.login') }}
            </LBtn>
          </template>

          <!-- Invalid / expired token -->
          <template v-else-if="invalidToken">
            <v-alert
              type="error"
              variant="tonal"
              density="comfortable"
              class="login-error"
            >
              {{ $t('auth.passwordReset.invalidToken') }}
            </v-alert>
            <div class="login-forgot">
              <router-link to="/forgot-password" class="login-link">
                {{ $t('auth.passwordReset.requestNew') }}
              </router-link>
            </div>
          </template>

          <!-- Reset form -->
          <template v-else>
            <v-form @submit.prevent="handleReset">
              <v-text-field
                v-model="newPassword"
                :label="$t('auth.password')"
                data-testid="reset-password-input"
                autocomplete="new-password"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :disabled="isSubmitting"
                :rules="passwordRules"
                :hint="$t('auth.passwordHint')"
                class="login-field"
                hide-details="auto"
              >
                <template #append-inner>
                  <v-icon
                    :icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                    @click="showPassword = !showPassword"
                    class="cursor-pointer"
                  />
                </template>
              </v-text-field>

              <v-text-field
                v-model="passwordConfirm"
                :label="$t('auth.passwordConfirm')"
                data-testid="reset-password-confirm-input"
                autocomplete="new-password"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-lock-check"
                :type="showPassword ? 'text' : 'password'"
                :disabled="isSubmitting"
                :rules="passwordConfirmRules"
                @keyup.enter="handleReset"
                class="login-field"
                hide-details="auto"
              />

              <v-alert
                v-if="errorMessage"
                type="error"
                variant="tonal"
                density="compact"
                class="login-error"
              >
                {{ errorMessage }}
              </v-alert>

              <LBtn
                variant="primary"
                block
                size="large"
                @click="handleReset"
                :loading="isSubmitting"
                :disabled="isSubmitting || !isFormValid"
                prepend-icon="mdi-lock-reset"
                class="login-button"
                data-testid="reset-submit-btn"
              >
                {{ $t('auth.passwordReset.resetSubmit') }}
              </LBtn>
            </v-form>

            <div class="login-forgot">
              <router-link to="/login" class="login-link">{{ $t('auth.passwordReset.backToLogin') }}</router-link>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useTheme } from 'vuetify';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { useMobile } from '@/composables/useMobile';

const props = defineProps({
  token: { type: String, default: '' },
});

const theme = useTheme();
const isDarkMode = computed(() => theme.global.current.value.dark);
const { isMobile, isIOS } = useMobile();
const { t } = useI18n();
const route = useRoute();

const token = computed(() => props.token || route.params.token || '');

// LBtn renders a plain <button> and ignores a router `to` prop, so navigate
// explicitly on the success screen. A full document load to /login guarantees
// a clean, unauthenticated login page after a successful reset, independent of
// any in-memory SPA/auth state.
const goToLogin = () => {
  window.location.href = '/login';
};

const newPassword = ref('');
const passwordConfirm = ref('');
const showPassword = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref('');
const done = ref(false);
const invalidToken = ref(false);

const passwordRules = [
  v => !!v || t('validation.required'),
  v => v.length >= 8 || t('validation.minLength', { min: 8 }),
];

const passwordConfirmRules = [
  v => !!v || t('validation.required'),
  v => v === newPassword.value || t('auth.validation.passwordMismatch'),
];

const isFormValid = computed(() =>
  newPassword.value.length >= 8 &&
  newPassword.value === passwordConfirm.value
);

async function handleReset() {
  if (!isFormValid.value || isSubmitting.value) return;
  errorMessage.value = '';
  isSubmitting.value = true;
  try {
    await axios.post('/auth/password-reset/reset', {
      token: token.value,
      new_password: newPassword.value,
    });
    done.value = true;
  } catch (error) {
    const data = error?.response?.data || {};
    if (data.code === 'INVALID_TOKEN') {
      invalidToken.value = true;
    } else {
      errorMessage.value = data.error || t('auth.passwordReset.resetFailed');
    }
  } finally {
    isSubmitting.value = false;
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
  margin-bottom: 12px;
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

.cursor-pointer {
  cursor: pointer;
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
