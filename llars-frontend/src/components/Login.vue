<template>
  <div class="login-page" :class="{ 'dark-mode': isDarkMode, 'is-mobile': isMobile, 'is-ios': isIOS }">
    <div class="paint-strokes">
      <div v-for="n in 10" :key="n"></div>
    </div>

    <div class="login-container">
      <div class="login-card">
        <!-- Header with Logo -->
        <div class="login-header">
          <img src="@/assets/logo/llars-logo.png" alt="LLARS Logo" class="login-logo" />
          <h1 class="login-title">{{ $t('appbar.platform') }}</h1>
          <p class="login-subtitle">{{ $t('auth.welcomeBack') }}</p>
        </div>

        <!-- Login Form -->
        <div class="login-form" data-testid="login-form">
          <v-form @submit.prevent="handleLogin" action="/login" method="post">
            <v-text-field
              v-model="username"
              :label="$t('auth.username')"
              name="username"
              id="username"
              data-testid="username-input"
              autocomplete="username"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-account"
              :disabled="isLogging"
              class="login-field"
              hide-details="auto"
            />

            <v-text-field
              v-model="password"
              :label="$t('auth.password')"
              name="password"
              id="password"
              data-testid="password-input"
              autocomplete="current-password"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-lock"
              :type="showPassword ? 'text' : 'password'"
              :disabled="isLogging"
              @keyup.enter="handleLogin"
              class="login-field"
              hide-details="auto"
            >
              <template #append-inner>
                <div
                  class="password-eye-toggle"
                  :class="{ 'is-open': showPassword }"
                  @click="showPassword = !showPassword"
                >
                  <svg
                    class="password-eye-svg"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <!-- Eye shape that morphs -->
                    <path
                      class="password-eye-shape"
                      :d="showPassword
                        ? 'M21 12c-2.4 4-5.4 6-9 6c-3.6 0-6.6-2-9-6c2.4-4 5.4-6 9-6c3.6 0 6.6 2 9 6'
                        : 'M21 12c0 0-4 0-9 0c-5 0-9 0-9 0c0 0 4 0 9 0c5 0 9 0 9 0'"
                    />
                    <!-- Pupil that appears -->
                    <circle
                      class="password-eye-pupil"
                      cx="12"
                      cy="12"
                      r="2"
                    />
                    <!-- Strike line for closed eye -->
                    <path
                      class="password-eye-strike"
                      d="M3 3l18 18"
                    />
                  </svg>
                </div>
              </template>
            </v-text-field>

            <LBtn
              variant="primary"
              block
              size="large"
              @click="handleLogin"
              :loading="isLogging"
              :disabled="isLogging || !username || !password"
              prepend-icon="mdi-login"
              class="login-button"
              data-testid="login-btn"
            >
              {{ $t('auth.login') }}
            </LBtn>
          </v-form>

          <!-- Error Message -->
          <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            density="compact"
            class="login-error"
            closable
            @click:close="errorMessage = ''"
          >
            {{ errorMessage }}
          </v-alert>
        </div>

        <!-- Dev Mode Quick Login -->
        <div v-if="isDevelopment" class="dev-login">
          <div class="dev-login-divider">
            <span>{{ $t('auth.devLabel') }}</span>
          </div>
          <div class="dev-login-buttons">
            <LBtn
              v-for="user in devUsers"
              :key="user.username"
              :data-testid="`dev-login-btn-${user.username}`"
              :variant="user.username === 'admin' ? 'danger' : user.username === 'researcher' ? 'primary' : 'secondary'"
              :prepend-icon="user.icon"
              size="small"
              @click="quickLogin(user)"
              :loading="loadingUser === user.username"
            >
              {{ $t(user.labelKey) }}
            </LBtn>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTheme } from 'vuetify';
import { useI18n } from 'vue-i18n';
import { useAuth } from '@/composables/useAuth';
import { useMobile } from '@/composables/useMobile';

const theme = useTheme();
const isDarkMode = computed(() => theme.global.current.value.dark);
const { isMobile, isIOS, safeAreaInsets } = useMobile();
const { t } = useI18n();

const username = ref('');
const password = ref('');
const showPassword = ref(false);
const errorMessage = ref('');
const isLogging = ref(false);
const loadingUser = ref(null);
const router = useRouter();
const route = useRoute();
const auth = useAuth();

// Development mode detection
// 1. Vite DEV mode (npm run dev)
// 2. Or explicitly enabled via VITE_DEV_LOGIN=true (for testing in built version)
const isDevelopment = import.meta.env.DEV || import.meta.env.VITE_DEV_LOGIN === 'true';

// Development test users
// Credentials can be overridden via VITE_DEV_PASSWORD env variable
const devPassword = import.meta.env.VITE_DEV_PASSWORD || 'admin123';
const devUsers = [
  { username: 'admin', password: devPassword, labelKey: 'auth.devUsers.admin', icon: 'mdi-shield-crown', color: 'error' },
  { username: 'researcher', password: devPassword, labelKey: 'auth.devUsers.researcher', icon: 'mdi-flask', color: 'primary' },
  { username: 'evaluator', password: devPassword, labelKey: 'auth.devUsers.evaluator', icon: 'mdi-clipboard-check-outline', color: 'secondary' },
  { username: 'chatbot_manager', password: devPassword, labelKey: 'auth.devUsers.chatbotManager', icon: 'mdi-robot', color: 'info' }
];

// Check if already authenticated on mount
onMounted(() => {
  if (auth.isAuthenticated.value) {
    const redirect = route.query.redirect;
    if (typeof redirect === 'string' && redirect.startsWith('/')) {
      router.push(redirect);
      return;
    }
    router.push('/Home');
  }
});

async function handleLogin() {
  // Clear previous error messages
  errorMessage.value = '';

  // Validate input
  if (!username.value || !password.value) {
    errorMessage.value = t('auth.errors.missingCredentials');
    return;
  }

  // Start loading
  isLogging.value = true;

  try {
    // Attempt login
    const result = await auth.login(username.value, password.value);

    if (result.success) {
      const redirect = route.query.redirect;
      if (typeof redirect === 'string' && redirect.startsWith('/')) {
        router.push(redirect);
      } else {
        router.push('/Home');
      }
    } else {
      // Login failed, show error
      errorMessage.value = result.error;
    }
  } finally {
    // Stop loading
    isLogging.value = false;
  }
}

/**
 * Quick login for development mode
 * Fills in credentials and triggers login
 */
async function quickLogin(user) {
  if (!isDevelopment) return;

  loadingUser.value = user.username;
  errorMessage.value = '';

  // Fill in credentials
  username.value = user.username;
  password.value = user.password;

  // Trigger login
  const result = await auth.login(user.username, user.password);

  loadingUser.value = null;

  if (result.success) {
    const redirect = route.query.redirect;
    if (typeof redirect === 'string' && redirect.startsWith('/')) {
      router.push(redirect);
    } else {
      router.push('/Home');
    }
  } else {
    errorMessage.value = result.error;
  }
}
</script>

<style scoped>
/* Login Page Layout - Fixed viewport, no scroll */
.login-page {
  height: calc(100vh - 94px); /* 64px AppBar + 30px Footer */
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

/* Login Card - LLARS Signature Style */
.login-card {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  box-shadow: var(--llars-shadow-lg, 0 8px 32px rgba(0, 0, 0, 0.12));
  overflow: hidden;
}

/* Header Section */
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

/* Form Section */
.login-form {
  padding: 20px;
}

.login-field {
  margin-bottom: 12px;
}

.login-field :deep(.v-field) {
  border-radius: var(--llars-radius-sm);
}

/* Animated Password Eye Toggle */
.password-eye-toggle {
  cursor: pointer;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.password-eye-toggle:hover {
  opacity: 1;
}

.password-eye-svg {
  width: 20px;
  height: 20px;
}

.password-eye-shape {
  transition: d 0.3s ease;
}

.password-eye-pupil {
  opacity: 0;
  transform: scale(0);
  transform-origin: center;
  transition: opacity 0.3s ease 0.1s, transform 0.3s ease 0.1s;
}

.password-eye-strike {
  opacity: 1;
  transition: opacity 0.2s ease;
}

/* Open state */
.password-eye-toggle.is-open .password-eye-pupil {
  opacity: 1;
  transform: scale(1);
}

.password-eye-toggle.is-open .password-eye-strike {
  opacity: 0;
}

.login-button {
  margin-top: 4px;
}

.login-error {
  margin-top: 12px;
  border-radius: var(--llars-radius-xs);
}

/* Dev Login Section */
.dev-login {
  padding: 0 20px 20px;
}

.dev-login-divider {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.dev-login-divider::before,
.dev-login-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(var(--v-theme-on-surface), 0.12);
}

.dev-login-divider span {
  padding: 0 12px;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dev-login-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* ========================================
   Paint Strokes Background - LIGHT MODE
   Distributed across entire viewport
   ======================================== */
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

/* Top Left - Sage Green */
.paint-strokes div:nth-child(1) {
  background: rgba(176, 202, 151, 0.7);
  top: -24%;
  left: -22%;
  width: 62%;
  height: 56%;
  border-radius: 65% 35% 70% 30% / 55% 45% 60% 40%;
  animation: floatStroke1 26s ease-in-out infinite;
}

/* Top Right - Golden Beige */
.paint-strokes div:nth-child(2) {
  background: rgba(209, 188, 138, 0.6);
  top: -22%;
  right: -24%;
  width: 66%;
  height: 60%;
  border-radius: 40% 60% 55% 45% / 60% 40% 50% 50%;
  animation: floatStroke2 30s ease-in-out infinite;
}

/* Middle Left - Soft Teal */
.paint-strokes div:nth-child(3) {
  background: rgba(136, 196, 200, 0.55);
  top: 12%;
  left: -26%;
  width: 56%;
  height: 50%;
  border-radius: 55% 45% 60% 40% / 45% 55% 65% 35%;
  animation: floatStroke3 28s ease-in-out infinite;
}

/* Middle Right - Soft Gold */
.paint-strokes div:nth-child(4) {
  background: rgba(232, 200, 122, 0.5);
  top: 12%;
  right: -26%;
  width: 54%;
  height: 56%;
  border-radius: 60% 40% 65% 35% / 35% 65% 45% 55%;
  animation: floatStroke4 32s ease-in-out infinite;
}

/* Bottom Left - Soft Mint */
.paint-strokes div:nth-child(5) {
  background: rgba(152, 212, 187, 0.6);
  bottom: -24%;
  left: -22%;
  width: 62%;
  height: 56%;
  border-radius: 70% 30% 50% 50% / 50% 50% 70% 30%;
  animation: floatStroke5 27s ease-in-out infinite;
}

/* Bottom Right - Soft Blue */
.paint-strokes div:nth-child(6) {
  background: rgba(168, 197, 226, 0.55);
  bottom: -22%;
  right: -24%;
  width: 60%;
  height: 62%;
  border-radius: 45% 55% 40% 60% / 40% 60% 70% 30%;
  animation: floatStroke6 34s ease-in-out infinite;
}

/* Top Center - Soft Coral accent */
.paint-strokes div:nth-child(7) {
  background: rgba(232, 160, 135, 0.45);
  top: -22%;
  left: 4%;
  width: 45%;
  height: 42%;
  border-radius: 35% 65% 45% 55% / 55% 45% 60% 40%;
  animation: floatStroke7 24s ease-in-out infinite;
}

/* Bottom Center - Purple accent */
.paint-strokes div:nth-child(8) {
  background: rgba(201, 168, 226, 0.4);
  bottom: -22%;
  left: 52%;
  width: 50%;
  height: 45%;
  border-radius: 45% 55% 35% 65% / 65% 35% 55% 45%;
  animation: floatStroke8 36s ease-in-out infinite;
}

/* Top Middle - Wide warm wash */
.paint-strokes div:nth-child(9) {
  background: rgba(235, 206, 148, 0.45);
  top: -30%;
  left: 14%;
  width: 72%;
  height: 52%;
  border-radius: 50% 50% 60% 40% / 55% 45% 50% 50%;
  animation: floatStroke9 33s ease-in-out infinite;
}

/* Bottom Middle - Wide cool wash */
.paint-strokes div:nth-child(10) {
  background: rgba(180, 210, 240, 0.45);
  bottom: -32%;
  left: 10%;
  width: 78%;
  height: 58%;
  border-radius: 55% 45% 50% 50% / 60% 40% 55% 45%;
  animation: floatStroke10 38s ease-in-out infinite;
}

/* ========================================
   DARK MODE - Different colors
   Warmer, muted tones for dark background
   ======================================== */
.login-page.dark-mode .paint-strokes div {
  filter: blur(80px);
  opacity: 0.35;
}

.login-page.dark-mode .paint-strokes div:nth-child(1) {
  background: rgba(90, 140, 70, 0.9);
}

.login-page.dark-mode .paint-strokes div:nth-child(2) {
  background: rgba(160, 130, 80, 0.85);
}

.login-page.dark-mode .paint-strokes div:nth-child(3) {
  background: rgba(70, 130, 140, 0.85);
}

.login-page.dark-mode .paint-strokes div:nth-child(4) {
  background: rgba(170, 150, 90, 0.8);
}

.login-page.dark-mode .paint-strokes div:nth-child(5) {
  background: rgba(90, 150, 120, 0.85);
}

.login-page.dark-mode .paint-strokes div:nth-child(6) {
  background: rgba(100, 140, 180, 0.8);
}

.login-page.dark-mode .paint-strokes div:nth-child(7) {
  background: rgba(170, 110, 100, 0.7);
}

.login-page.dark-mode .paint-strokes div:nth-child(8) {
  background: rgba(140, 120, 170, 0.65);
}

.login-page.dark-mode .paint-strokes div:nth-child(9) {
  background: rgba(150, 120, 70, 0.7);
}

.login-page.dark-mode .paint-strokes div:nth-child(10) {
  background: rgba(95, 125, 165, 0.65);
}

/* Animationen - sanfte Bewegungen */
@keyframes floatStroke1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(3%, 5%) scale(1.05); }
  66% { transform: translate(-2%, 3%) scale(0.98); }
}

@keyframes floatStroke2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-4%, 3%) scale(1.03); }
  66% { transform: translate(2%, -4%) scale(1.02); }
}

@keyframes floatStroke3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(5%, -3%) scale(1.04); }
  66% { transform: translate(2%, 4%) scale(0.97); }
}

@keyframes floatStroke4 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-3%, 4%) scale(1.02); }
  66% { transform: translate(-5%, -2%) scale(1.05); }
}

@keyframes floatStroke5 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(4%, -4%) scale(1.03); }
  66% { transform: translate(-3%, -2%) scale(0.98); }
}

@keyframes floatStroke6 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-2%, -5%) scale(1.04); }
  66% { transform: translate(3%, 3%) scale(1.01); }
}

@keyframes floatStroke7 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(6%, 4%) scale(1.06); }
  66% { transform: translate(-4%, -3%) scale(0.96); }
}

@keyframes floatStroke8 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-5%, -4%) scale(1.02); }
  66% { transform: translate(4%, 5%) scale(1.04); }
}

@keyframes floatStroke9 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(4%, 3%) scale(1.03); }
  66% { transform: translate(-3%, 2%) scale(0.99); }
}

@keyframes floatStroke10 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-3%, -4%) scale(1.02); }
  66% { transform: translate(4%, 3%) scale(1.03); }
}

/* ========================================
   MOBILE RESPONSIVE STYLES
   Optimized for phones and touch devices
   ======================================== */

/* Mobile Layout - full screen on small devices */
.login-page.is-mobile {
  height: 100vh;
  height: 100dvh; /* Dynamic viewport height for iOS */
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.login-page.is-mobile .login-container {
  max-width: 100%;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-page.is-mobile .login-card {
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
}

/* iOS-specific fixes */
.login-page.is-ios {
  /* Prevent iOS bounce scroll */
  overscroll-behavior: none;
  -webkit-overflow-scrolling: touch;
}

.login-page.is-ios .login-field :deep(input) {
  /* Fix iOS input zoom on focus */
  font-size: 16px !important;
}

/* Tablet and small mobile breakpoint */
@media (max-width: 600px) {
  .login-page {
    padding: 0;
  }

  .login-container {
    padding: 16px;
    width: 100%;
  }

  .login-card {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }

  .login-header {
    padding: 24px 20px;
  }

  .login-logo {
    width: 52px;
    height: 52px;
  }

  .login-title {
    font-size: 1.25rem;
  }

  .login-subtitle {
    font-size: 0.8rem;
  }

  .login-form {
    padding: 20px;
  }

  .login-field {
    margin-bottom: 16px;
  }

  /* Larger touch targets for mobile */
  .login-field :deep(.v-field) {
    min-height: 52px;
  }

  .login-field :deep(.v-field__input) {
    padding-top: 12px;
    padding-bottom: 12px;
  }

  .login-button {
    min-height: 48px;
    margin-top: 8px;
  }

  .dev-login {
    padding: 0 20px 20px;
  }

  .dev-login-buttons {
    gap: 6px;
  }

  .dev-login-buttons > * {
    flex: 1 1 calc(50% - 3px);
    min-width: 0;
  }

  /* Reduce paint strokes on mobile for performance */
  .paint-strokes div {
    filter: blur(40px);
    opacity: 0.35;
  }
}

/* Extra small devices (iPhone SE, etc.) */
@media (max-width: 380px) {
  .login-header {
    padding: 20px 16px;
  }

  .login-logo {
    width: 44px;
    height: 44px;
  }

  .login-title {
    font-size: 1.15rem;
  }

  .login-form {
    padding: 16px;
  }

  .dev-login {
    padding: 0 16px 16px;
  }

  .dev-login-buttons {
    flex-direction: column;
  }

  .dev-login-buttons > * {
    flex: 1 1 100%;
    width: 100%;
  }
}

/* Landscape orientation on mobile */
@media (max-height: 500px) and (orientation: landscape) {
  .login-page {
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
    padding: 16px 0;
  }

  .login-container {
    padding: 8px 16px;
  }

  .login-header {
    padding: 16px;
  }

  .login-logo {
    width: 40px;
    height: 40px;
    margin-bottom: 4px;
  }

  .login-title {
    font-size: 1.1rem;
  }

  .login-subtitle {
    font-size: 0.75rem;
  }

  .login-form {
    padding: 12px 16px;
  }

  .login-field {
    margin-bottom: 8px;
  }

  .paint-strokes {
    display: none; /* Hide animations in landscape for performance */
  }
}

/* Prevent horizontal scroll on any device */
.login-page {
  overflow-x: hidden;
}
</style>
