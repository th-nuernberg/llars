<template>
  <nav
    class="landing-nav"
    :class="{ scrolled: isScrolled, 'dark-mode': isDarkMode }"
    aria-label="Landing page navigation"
  >
    <div class="nav-inner">
      <router-link to="/" class="nav-logo">
        <img
          src="@/assets/logo/llars-logo.png"
          alt="LLARS Logo"
          height="28"
          class="nav-logo-img"
        />
        <span v-if="!isMobile" class="nav-logo-text">LLARS</span>
      </router-link>

      <div class="nav-spacer" />

      <LLanguageToggle class="nav-action" />
      <LThemeToggle class="nav-action" />

      <LBtn
        variant="primary"
        size="small"
        :prepend-icon="isMobile ? '' : 'mdi-login'"
        :aria-label="$t('auth.login')"
        @click="$router.push('/login')"
        class="nav-login-btn"
      >
        {{ isMobile ? '' : $t('auth.login') }}
        <v-icon v-if="isMobile">mdi-login</v-icon>
      </LBtn>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTheme } from 'vuetify'
import { useMobile } from '@/composables/useMobile'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { isMobile } = useMobile()

const isScrolled = ref(false)

function onScroll() {
  isScrolled.value = window.scrollY > 50
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.landing-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 56px;
  transition: background 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease;
  background: transparent;
  border-bottom: 1px solid transparent;
}

.landing-nav.scrolled {
  background: rgba(247, 245, 240, 0.82);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.06);
  border-bottom-color: rgba(176, 202, 151, 0.25);
}

.landing-nav.dark-mode.scrolled {
  background: rgba(30, 30, 30, 0.82);
  border-bottom-color: rgba(176, 202, 151, 0.15);
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 8px;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  padding: 6px 12px 6px 6px;
  border-radius: 8px 2px 8px 2px;
  transition: background 0.2s ease;
}

.nav-logo:hover {
  background: rgba(176, 202, 151, 0.12);
}

.nav-logo-text {
  font-size: 1.15rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: var(--landing-text-primary);
}

.nav-spacer {
  flex: 1;
}

.nav-action {
  flex-shrink: 0;
}

.nav-login-btn {
  margin-left: 4px;
}

@media (max-width: 600px) {
  .nav-inner {
    padding: 0 12px;
    gap: 4px;
  }
}
</style>
