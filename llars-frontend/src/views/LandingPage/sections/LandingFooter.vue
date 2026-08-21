<template>
  <footer class="landing-footer" :class="{ 'dark-mode': isDarkMode }">
    <div class="footer-inner">
      <div class="footer-brand">
        <img src="@/assets/logo/llars-logo.png" alt="LLARS" height="24" />
        <span class="footer-brand-text">LLARS</span>
      </div>

      <div class="footer-links">
        <a
          href="https://github.com/th-nuernberg/llars"
          target="_blank"
          rel="noopener noreferrer"
          class="footer-link footer-link-github"
        >
          <v-icon size="16">mdi-github</v-icon>
          GitHub
        </a>
        <router-link to="/video" class="footer-link">
          {{ $t('landing.footer.demo') }}
        </router-link>
        <a :href="mkdocsUrl" target="_blank" rel="noopener" class="footer-link">
          {{ $t('landing.footer.docs') }}
        </a>
        <router-link to="/Impressum" class="footer-link">{{ $t('footer.imprint') }}</router-link>
        <router-link to="/Datenschutz" class="footer-link">{{ $t('footer.privacy') }}</router-link>
        <router-link to="/Nutzungsbedingungen" class="footer-link">{{ $t('footer.terms') }}</router-link>
        <router-link to="/Kontakt" class="footer-link">{{ $t('footer.contact') }}</router-link>
      </div>

      <div class="footer-copy">
        &copy; {{ new Date().getFullYear() }} LLARS &mdash; MIT License
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import { useI18n } from 'vue-i18n'
import { docsUrlForLocale } from '@/utils/docsUrl'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { locale } = useI18n()

// Doku in der aktuellen UI-Sprache (DE -> /mkdocs/, EN -> /mkdocs/en/).
const mkdocsUrl = computed(() => docsUrlForLocale(locale.value))
</script>

<style scoped>
.landing-footer {
  background: var(--llars-appbar-gradient);
  border-top: 2px solid var(--llars-appbar-border);
  padding: 32px 24px;
  color: #fff;
}

.footer-inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-brand-text {
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: 0.5px;
}

.footer-links {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.footer-link {
  color: rgba(255, 255, 255, 0.85);
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: #fff;
  text-decoration: underline;
}

.footer-link-github {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.footer-copy {
  font-size: 0.75rem;
  opacity: 0.65;
}

@media (max-width: 600px) {
  .footer-inner {
    flex-direction: column;
    text-align: center;
  }

  .footer-links {
    justify-content: center;
  }

  .landing-footer {
    padding: 24px 16px;
  }
}
</style>
