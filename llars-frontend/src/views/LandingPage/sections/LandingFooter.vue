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
        <!-- Citation is a license condition for academic use -> always reachable -->
        <button type="button" class="footer-link footer-link-button" @click="citationOpen = true">
          {{ $t('citation.link') }}
        </button>
      </div>

      <div class="footer-copy">
        <div>&copy; {{ new Date().getFullYear() }} LLARS</div>
        <div class="footer-license">
          {{ $t('landing.footer.license') }}
          <a
            href="https://github.com/th-nuernberg/llars/blob/main/LICENSE"
            target="_blank"
            rel="noopener noreferrer"
            class="footer-license-link"
          >{{ $t('landing.footer.licenseLink') }}</a>
        </div>
      </div>
    </div>

    <LCitationDialog v-model="citationOpen" />
  </footer>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useTheme } from 'vuetify'
import { useI18n } from 'vue-i18n'
import LCitationDialog from '@/components/common/LCitationDialog.vue'
import { docsUrlForLocale } from '@/utils/docsUrl'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { locale } = useI18n()

// "Cite LLARS" dialog — shared with AppFooter (see LCitationDialog docstring).
const citationOpen = ref(false)

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

/* Reset so the citation <button> renders identically to its <a> siblings */
.footer-link-button {
  background: none;
  border: none;
  padding: 0;
  font-family: inherit;
  cursor: pointer;
}

.footer-copy {
  font-size: 0.75rem;
  opacity: 0.65;
  text-align: right;
  line-height: 1.6;
}

.footer-license-link {
  color: inherit;
  text-decoration: underline;
}

.footer-license-link:hover {
  color: #fff;
}

@media (max-width: 600px) {
  .footer-inner {
    flex-direction: column;
    text-align: center;
  }

  .footer-links {
    justify-content: center;
  }

  .footer-copy {
    text-align: center;
  }

  .landing-footer {
    padding: 24px 16px;
  }
}
</style>
