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

      <!-- Sektions-Anker (nur Desktop) — Smooth-Scroll via CSS in LandingPage.vue -->
      <div v-if="!isMobile" class="nav-links">
        <a v-for="link in navLinks" :key="link.anchor" :href="link.anchor" class="nav-link">
          {{ $t(link.label) }}
        </a>
      </div>

      <div class="nav-spacer" />

      <LLanguageToggle class="nav-action" />
      <LThemeToggle class="nav-action" />

      <a
        href="https://github.com/th-nuernberg/llars"
        target="_blank"
        rel="noopener noreferrer"
        class="nav-github"
        aria-label="GitHub"
      >
        <v-icon size="22">mdi-github</v-icon>
      </a>

      <LBtn
        variant="text"
        size="small"
        :prepend-icon="isMobile ? '' : 'mdi-login'"
        :aria-label="$t('auth.login')"
        @click="$router.push('/login')"
        class="nav-login-btn"
      >
        {{ isMobile ? '' : $t('auth.login') }}
        <v-icon v-if="isMobile">mdi-login</v-icon>
      </LBtn>

      <LBtn
        variant="primary"
        size="small"
        :prepend-icon="isMobile ? '' : 'mdi-account-plus'"
        :aria-label="$t('landing.cta.register')"
        @click="$router.push('/register')"
        class="nav-register-btn"
      >
        {{ isMobile ? '' : $t('landing.cta.register') }}
        <v-icon v-if="isMobile">mdi-account-plus</v-icon>
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

const navLinks = [
  { anchor: '#features', label: 'landing.nav.features' },
  { anchor: '#live-demo', label: 'landing.nav.demo' },
  { anchor: '#eval-types', label: 'landing.nav.evalTypes' },
  { anchor: '#open-source', label: 'landing.nav.openSource' },
]

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

.nav-links {
  display: flex;
  gap: 4px;
  margin-left: 12px;
}

/* Underline wächst von links (Akteon-Muster) */
.nav-link {
  position: relative;
  padding: 6px 10px;
  font-size: 0.88rem;
  color: var(--landing-text-secondary);
  text-decoration: none;
  transition: color 0.2s ease;
}

.nav-link::after {
  content: '';
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 2px;
  height: 2px;
  border-radius: 999px;
  background: #b0ca97;
  transform: scaleX(0);
  transform-origin: left center;
  transition: transform 0.2s ease;
}

.nav-link:hover {
  color: var(--landing-text-primary);
}

.nav-link:hover::after {
  transform: scaleX(1);
}

.nav-spacer {
  flex: 1;
}

.nav-action {
  flex-shrink: 0;
}

.nav-github {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px 2px 8px 2px;
  color: var(--landing-text-secondary);
  transition: background 0.2s ease, color 0.2s ease;
}

.nav-github:hover {
  background: rgba(176, 202, 151, 0.12);
  color: var(--landing-text-primary);
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

@media (prefers-reduced-motion: reduce) {
  .nav-link::after {
    transition: none;
  }
}
</style>
