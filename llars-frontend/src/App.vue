<template>
  <v-app>
    <!-- Unified AppBar -->
    <v-app-bar app class="llars-appbar" :class="{ 'is-mobile': isMobile }">
      <v-toolbar-title @click="goHome" class="toolbar-title" :class="{ 'flex-shrink-1': isMobile }">
        <div class="logo-wrapper">
          <img src="./assets/logo/llars-logo.png" alt="Logo" :height="isMobile ? 24 : 28" class="logo-image">
          <span class="toolbar-text" :class="{ 'mobile-text': isMobile }">{{ isMobile ? 'LLars' : 'LLars Plattform' }}</span>
        </div>
      </v-toolbar-title>
      <v-spacer></v-spacer>

      <!-- Auth Section with Animation -->
      <AnimatePresence mode="wait">
        <!-- User Menu (only when logged in) -->
        <Motion
          v-if="isAuthenticated"
          key="user-menu"
          layout-id="auth-section"
          :initial="{ opacity: 0, scale: 0.8 }"
          :animate="{ opacity: 1, scale: 1 }"
          :exit="{ opacity: 0, scale: 0.8 }"
          :transition="{ duration: 0.35, ease: 'easeOut' }"
          as="div"
          class="auth-section-wrapper"
        >
          <v-menu offset-y :close-on-content-click="true">
            <template v-slot:activator="{ props }">
              <div v-bind="props" class="user-menu-trigger" :class="{ 'mobile-trigger': isMobile }">
                <LAvatar
                  :seed="userAvatarSeed"
                  :src="userAvatarUrl"
                  :username="username"
                  :size="isMobile ? 'xs' : 'sm'"
                  :class="isMobile ? 'mr-1' : 'mr-2'"
                />
                <div v-if="!isMobile" class="user-info">
                  <LTag
                    :variant="isAdminUser ? 'danger' : 'secondary'"
                    size="sm"
                    :prepend-icon="isAdminUser ? 'mdi-shield-account' : ''"
                  >
                    {{ isAdminUser ? 'Admin ' : '' }}{{ username }}
                  </LTag>
                </div>
                <LIcon :size="isMobile ? 16 : 20" :class="['menu-arrow', isMobile ? '' : 'ml-1']" color="white">mdi-menu-down</LIcon>
              </div>
            </template>

            <v-list density="compact" class="user-menu-list">
              <v-list-item @click="openSettings" prepend-icon="mdi-account-cog">
                <v-list-item-title>{{ $t('settings.title') }}</v-list-item-title>
              </v-list-item>
              <v-divider class="my-1" />
              <v-list-item @click="logout" prepend-icon="mdi-logout" class="text-error">
                <v-list-item-title>{{ $t('auth.logout') }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </Motion>

        <!-- Theme Toggle + Register/Login Buttons (when NOT logged in) -->
        <Motion
          v-else
          key="login-buttons"
          layout-id="auth-section"
          :initial="{ opacity: 0, scale: 0.8 }"
          :animate="{ opacity: 1, scale: 1 }"
          :exit="{ opacity: 0, scale: 0.8 }"
          :transition="{ duration: 0.35, ease: 'easeOut' }"
          as="div"
          class="auth-section-wrapper"
        >
          <LThemeToggle on-primary class="mr-2" />
          <LBtn
            v-if="registrationEnabled"
            variant="text"
            size="small"
            @click="goToRegister"
            prepend-icon="mdi-account-plus"
            class="mr-1"
          >
            {{ isMobile ? '' : $t('auth.register') }}
          </LBtn>
          <LBtn variant="secondary" size="small" @click="goToLogin" prepend-icon="mdi-login">
            {{ $t('auth.login') }}
          </LBtn>
        </Motion>
      </AnimatePresence>
    </v-app-bar>

    <v-main>
      <router-view :key="routerViewKey"></router-view>
    </v-main>

    <AnalyticsConsentBanner />

    <!-- Chatbot wird nur angezeigt, wenn Benutzer eingeloggt ist und ENABLE_CHAT true ist -->
    <FloatingChat v-if="isAuthenticated && ENABLE_CHAT" />

    <!-- User Settings Dialog -->
    <UserSettingsDialog v-model="settingsDialogOpen" />

    <!-- Global Snackbar -->
    <v-snackbar
      v-model="snackbarModel.show"
      :color="snackbarModel.color"
      :timeout="snackbarModel.timeout"
      location="bottom"
      class="global-snackbar"
    >
      <div class="d-flex align-center">
        <LIcon v-if="snackbarModel.icon" class="mr-2">{{ snackbarModel.icon }}</LIcon>
        {{ snackbarModel.message }}
      </div>
      <template v-slot:actions>
        <v-btn variant="text" size="small" @click="snackbarModel.show = false">
          {{ $t('common.close') }}
        </v-btn>
      </template>
    </v-snackbar>

    <v-footer app :height="isMobile ? 24 : 30" class="llars-footer" :class="{ 'is-mobile': isMobile, 'px-2': isMobile, 'px-4': !isMobile }">
      <v-row no-gutters align="center" justify="space-between">
        <v-col cols="auto">
          <span class="copyright">
            © {{ new Date().getFullYear() }} {{ isMobile ? 'LLars' : 'LLars Plattform' }}
          </span>
        </v-col>

        <v-col v-if="!isMobile" cols="auto">
          <span
            v-for="link in footerLinks"
            :key="link.key"
            class="footer-link"
            @click="navigateTo(link.route)"
          >
            {{ $t(`footer.${link.key}`) }}
          </span>
        </v-col>
      </v-row>
    </v-footer>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Motion, AnimatePresence } from 'motion-v';
import { useAuth } from '@/composables/useAuth';
import { useAppTheme } from '@/composables/useAppTheme';
import { usePermissions } from '@/composables/usePermissions';
import { useMobile } from '@/composables/useMobile';
import { useSnackbar } from '@/composables/useSnackbar';
import { usePresenceHeartbeat } from '@/composables/usePresenceHeartbeat';
import FloatingChat from './components/FloatingChat.vue';
import UserSettingsDialog from './components/UserSettingsDialog.vue';
import AnalyticsConsentBanner from './components/common/AnalyticsConsentBanner.vue';
import { useReferralSystem } from '@/composables/useReferralSystem';
import { logI18n } from '@/utils/logI18n';

const { t } = useI18n();

// Global Snackbar
const { snackbarModel } = useSnackbar();

// Globale Konstante für Chat-Aktivierung (kann der Entwickler ändern)
const ENABLE_CHAT = false; // hier auf true/false setzen um Chat global zu aktivieren/deaktivieren

const router = useRouter();
const route = useRoute();
const auth = useAuth();
const permissions = usePermissions();
const { applyTheme } = useAppTheme();
const { isMobile } = useMobile();
const { registrationEnabled, checkRegistrationStatus } = useReferralSystem();
const { start: startPresence, stop: stopPresence } = usePresenceHeartbeat();

/**
 * Smart router-view key that prevents full remount on document switches.
 * For collab workspaces (LaTeX, Markdown), use workspace-level key so switching
 * documents only updates editor content, not the entire workspace component.
 */
const routerViewKey = computed(() => {
  const path = route.path
  // Match LaTeX/Markdown collab workspace routes with document IDs
  // Pattern: /LatexCollab/workspace/:id/document/:docId or /LatexCollabAI/workspace/:id/document/:docId
  const collabMatch = path.match(/^\/(LatexCollab|LatexCollabAI|MarkdownCollab)\/workspace\/(\d+)/)
  if (collabMatch) {
    // Return workspace-level key, ignoring document ID changes
    return `${collabMatch[1]}-workspace-${collabMatch[2]}`
  }
  // For all other routes, use full path as before
  return route.fullPath
})

const isAuthenticated = computed(() => auth.isAuthenticated.value);
const username = computed(() => {
  const fromToken =
    auth.tokenParsed.value?.preferred_username ||
    auth.tokenParsed.value?.username ||
    auth.tokenParsed.value?.name ||
    '';
  if (fromToken) return fromToken;
  try {
    return localStorage.getItem('username') || '';
  } catch {
    return '';
  }
});

watch(
  isAuthenticated,
  (value) => {
    if (value) {
      startPresence();
    } else {
      stopPresence();
    }
  },
  { immediate: true }
);
const isAdminUser = computed(() => auth.isAdmin.value);
const footerLinks = [
  { key: 'documentation', route: '/docs' },
  { key: 'imprint', route: '/impressum' },
  { key: 'privacy', route: '/datenschutz' },
  { key: 'contact', route: '/kontakt' }
];
const settingsDialogOpen = ref(false);

// Avatar seed from auth composable
const userAvatarSeed = computed(() => auth.avatarSeed.value);
const userAvatarUrl = computed(() => auth.avatarUrl.value);

// Funktion zum Prüfen und Löschen alter Chat-Nachrichten
const cleanupOldChatMessages = () => {
  try {
    const chatData = localStorage.getItem('chat_messages');
    if (chatData) {
      const storedTimestamp = localStorage.getItem('chat_messages_timestamp');
      const currentTime = new Date().getTime();

      if (!storedTimestamp) {
        localStorage.setItem('chat_messages_timestamp', currentTime.toString());
        return;
      }

      const timestampDiff = currentTime - parseInt(storedTimestamp);
      const oneDayInMs = 24 * 60 * 60 * 1000;

      if (timestampDiff > oneDayInMs) {
        localStorage.removeItem('chat_messages');
        localStorage.removeItem('chat_messages_timestamp');
      }
    }
  } catch (error) {
    logI18n('error', 'logs.app.cleanupChatMessagesError', error);
  }
};

onMounted(() => {
  cleanupOldChatMessages();
  applyTheme(); // Apply theme on app mount
  checkRegistrationStatus(); // Check if self-registration is enabled
});

function logout() {
  // Prüfen, ob es unsichere Änderungen gibt
  if (containsLocalStorageItemWithString('hasUnsaved_ratingChanges_')) {
    const confirmLogout = window.confirm(t('auth.logoutConfirmation'));

    if (!confirmLogout) {
      // Abbrechen, wenn der Benutzer das Logout ablehnt
      return;
    }
  }

  // Logout via useAuth (löscht sessionStorage: auth_token, auth_refreshToken, auth_idToken)
  auth.logout();
  permissions.clearPermissions();

  // Alte localStorage-Items löschen (für Kompatibilität mit altem System)
  try {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('api_key');
    localStorage.removeItem('chat_messages');
    localStorage.removeItem('chat_messages_timestamp');

    Object.keys(localStorage).forEach((key) => {
      if (
        key.startsWith('featureOrder_') ||
        key.startsWith('featureRating_') ||
        key.startsWith('rankerDetail_data_') ||
        key.startsWith('hasUnsaved_ratingChanges_') ||
        key.startsWith('local_rating_changes_') ||
        key.startsWith('local_messageRating_changes')
      ) {
        localStorage.removeItem(key);
      }
    });
  } catch (e) {
    // ignore (e.g., Safari private mode / blocked storage)
  }

  router.push('/login');
}

function containsLocalStorageItemWithString(string) {
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i); // Holen des Keys an Index i
      if (key.includes(string)) {
        return true; // Ein Item mit dem String im Namen wurde gefunden
      }
    }
    return false; // Kein Item mit dem String im Namen
  } catch (e) {
    return false;
  }
}



function goHome() {
  router.push('/home');
}

function goToLogin() {
  router.push('/login');
}

function goToRegister() {
  router.push('/register');
}

function navigateTo(route) {
  router.push(route);
}

function openSettings() {
  settingsDialogOpen.value = true;
}
</script>

<!-- Global styles (not scoped) for Vuetify component overrides -->
<style>
/* Fix Vuetify Tooltip background - should be dark in light mode, light in dark mode */
.v-tooltip > .v-overlay__content {
  background: rgba(33, 33, 33, 0.95) !important;
  color: #ffffff !important;
}

/* Dark mode tooltip - lighter background */
.v-theme--dark .v-tooltip > .v-overlay__content {
  background: rgba(66, 66, 66, 0.95) !important;
  color: #ffffff !important;
}

/* ============================================
   LIGHT MODE TEXT CONTRAST FIXES
   ============================================
   In Light Mode, text must be dark for readability.
   Vuetify's default medium-emphasis opacity (0.6) is too light.
   We increase it to 0.75 for better contrast.
   ============================================ */

/* Light mode: Increase medium-emphasis opacity for better contrast */
.v-theme--light {
  --v-medium-emphasis-opacity: 0.75;
  --v-high-emphasis-opacity: 0.95;
}

/* Light mode: Ensure text-medium-emphasis is readable */
.v-theme--light .text-medium-emphasis {
  color: rgba(0, 0, 0, 0.75) !important;
}

/* Light mode: Ensure text-caption is readable */
.v-theme--light .text-caption {
  color: rgba(0, 0, 0, 0.7);
}

/* Light mode: Ensure v-card-text content is readable */
.v-theme--light .v-card-text {
  color: rgba(0, 0, 0, 0.87);
}

/* Light mode: Fix expansion panels text */
.v-theme--light .v-expansion-panel-title,
.v-theme--light .v-expansion-panel-text {
  color: rgba(0, 0, 0, 0.87);
}

/* Light mode: Fix slider tick labels and values */
.v-theme--light .v-slider .v-slider__tick-label {
  color: rgba(0, 0, 0, 0.7);
}

/* Light mode: Fix chip text in outlined variant */
.v-theme--light .v-chip.v-chip--variant-outlined {
  color: rgba(0, 0, 0, 0.87);
}

/* Light mode: Fix radio button and switch labels */
.v-theme--light .v-label {
  color: rgba(0, 0, 0, 0.87);
  opacity: 1;
}

.v-theme--light .v-selection-control .v-label {
  color: rgba(0, 0, 0, 0.87);
  opacity: 1;
}

/* Light mode: Fix text inside radio/switch labels using text-medium-emphasis */
.v-theme--light .v-selection-control .text-medium-emphasis,
.v-theme--light .v-radio .text-medium-emphasis,
.v-theme--light .v-switch .text-medium-emphasis {
  color: rgba(0, 0, 0, 0.7) !important;
}

/* Light mode: Fix text-caption inside form controls */
.v-theme--light .v-selection-control .text-caption,
.v-theme--light .v-radio .text-caption,
.v-theme--light .v-switch .text-caption {
  color: rgba(0, 0, 0, 0.7) !important;
}

/* Light mode: Fix form hint text */
.v-theme--light .v-messages__message {
  color: rgba(0, 0, 0, 0.6);
}

/* Light mode: Fix input labels */
.v-theme--light .v-field__outline,
.v-theme--light .v-field-label {
  color: rgba(0, 0, 0, 0.6);
}
</style>

<style scoped>
/* ============================================
   LLARS AppBar Styling
   ============================================ */
.llars-appbar {
  background: var(--llars-appbar-gradient) !important;
  border-bottom: 3px solid var(--llars-appbar-border) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
}

.llars-appbar :deep(.v-toolbar__content) {
  padding: 0 16px;
}

/* Logo & Title */
.toolbar-title {
  cursor: pointer;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 12px 4px 4px;
  border-radius: 8px 2px 8px 2px;
  transition: background-color 0.2s ease;
}

.logo-wrapper:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.logo-image {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.15));
}

.toolbar-text {
  font-size: 1.2rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* User Menu Trigger */
.user-menu-trigger {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 12px 4px 12px 4px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
  transition: all 0.2s ease;
}

.user-menu-trigger:hover {
  background-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.user-menu-trigger:hover .menu-arrow :deep(.l-its-hover__svg) {
  transform: scale(1.15);
}

.menu-arrow :deep(.l-its-hover__svg) {
  transition: transform 0.2s ease;
}

.user-info {
  display: flex;
  align-items: center;
}

/* Auth Section Animation Wrapper */
.auth-section-wrapper {
  display: flex;
  align-items: center;
}

.user-menu-list {
  min-width: 200px;
  border-radius: 8px 2px 8px 2px !important;
}

/* ============================================
   LLARS Footer Styling
   ============================================ */
.llars-footer {
  background: var(--llars-appbar-gradient) !important;
  border-top: 2px solid var(--llars-appbar-border) !important;
  font-size: 0.75rem;
}

.copyright {
  color: #fff;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.1);
}

.footer-link {
  color: #fff;
  cursor: pointer;
  margin-left: 1rem;
  opacity: 0.9;
  transition: opacity 0.2s ease;
}

.footer-link:hover {
  opacity: 1;
  text-decoration: underline;
}

/* ============================================
   Dark Mode Adjustments
============================================
   AppBar/Footer colors are now handled via CSS variables:
   --llars-appbar-gradient and --llars-appbar-border
   defined in global.css for both light and dark modes
   ============================================ */

/* ============================================
   Mobile Responsive Styles
   ============================================ */
.llars-appbar.is-mobile :deep(.v-toolbar__content) {
  padding: 0 8px;
}

.llars-appbar.is-mobile .toolbar-title {
  min-width: 0;
  flex-shrink: 1;
}

.llars-appbar.is-mobile .logo-wrapper {
  gap: 8px;
  padding: 4px 8px 4px 4px;
}

.mobile-text {
  font-size: 1rem;
}

.mobile-trigger {
  padding: 4px 8px;
}

.flex-shrink-1 {
  flex-shrink: 1;
  min-width: 0;
}

/* Mobile Footer */
.llars-footer.is-mobile {
  font-size: 0.65rem;
  min-height: 24px !important;
  max-height: 24px !important;
}

.llars-footer.is-mobile .copyright {
  font-size: 0.65rem;
  white-space: nowrap;
}

.llars-footer.is-mobile :deep(.v-row) {
  flex-wrap: nowrap;
  min-height: auto;
}
</style>
