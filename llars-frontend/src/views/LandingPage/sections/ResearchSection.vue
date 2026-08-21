<template>
  <section id="open-source" class="research-section" :class="{ 'dark-mode': isDarkMode }">
    <PaintStrokesReveal :strength="0.55" />

    <div class="section-inner">
      <div class="research-layout">
        <!-- Foto (lokal gehostet, siehe assets/landing/ATTRIBUTION.md) -->
        <div class="research-photo" data-reveal>
          <img
            src="@/assets/landing/research-team.jpg"
            :alt="$t('landing.research.photoAlt')"
            loading="lazy"
          />
        </div>

        <!-- Open-Science-Botschaft -->
        <div class="research-copy">
          <h2 class="research-title" data-reveal>{{ $t('landing.research.title') }}</h2>
          <p class="research-text" data-reveal data-reveal-delay="100">
            {{ $t('landing.research.text1') }}
          </p>
          <p class="research-text" data-reveal data-reveal-delay="180">
            {{ $t('landing.research.text2') }}
          </p>

          <ul class="research-points" data-reveal data-reveal-delay="260">
            <li>
              <v-icon size="18" color="#b0ca97">mdi-scale-balance</v-icon>
              <span>{{ $t('landing.research.points.license') }}</span>
            </li>
            <li>
              <v-icon size="18" color="#88c4c8">mdi-server</v-icon>
              <span>{{ $t('landing.research.points.selfHost') }}</span>
            </li>
            <li>
              <v-icon size="18" color="#D1BC8A">mdi-file-document-check-outline</v-icon>
              <span>{{ $t('landing.research.points.reproducible') }}</span>
            </li>
          </ul>

          <div class="research-actions" data-reveal data-reveal-delay="340">
            <LBtn variant="primary" prepend-icon="mdi-github" @click="openGithub">
              {{ $t('landing.research.github') }}
            </LBtn>
            <LBtn variant="secondary" prepend-icon="mdi-book-open-variant" @click="openDocs">
              {{ $t('landing.footer.docs') }}
            </LBtn>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
/**
 * ResearchSection — Open-Science-/Open-Source-Botschaft mit Foto.
 * Zielgruppe sind Forschende: LLARS ist und bleibt MIT-lizenziert,
 * selbst hostbar und von jeder Forschungsgruppe frei einsetzbar.
 */
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import { useI18n } from 'vue-i18n'
import { docsUrlForLocale } from '@/utils/docsUrl'
import PaintStrokesReveal from '../components/PaintStrokesReveal.vue'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { locale } = useI18n()

function openGithub() {
  window.open('https://github.com/th-nuernberg/llars', '_blank', 'noopener,noreferrer')
}

function openDocs() {
  // Doku in der aktuellen UI-Sprache (DE -> /mkdocs/, EN -> /mkdocs/en/).
  window.open(docsUrlForLocale(locale.value), '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.research-section {
  position: relative;
  overflow: hidden;
  padding: 100px 24px;
  background: var(--landing-bg-alt);
}

.section-inner {
  position: relative;
  z-index: 1;
  max-width: 1100px;
  margin: 0 auto;
}

.research-layout {
  display: grid;
  grid-template-columns: 6fr 6fr;
  gap: 48px;
  align-items: center;
}

.research-photo {
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
  box-shadow: 0 16px 40px -16px rgba(44, 62, 45, 0.3);
}

.research-photo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  aspect-ratio: 4 / 3;
  transition: transform 0.6s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.research-photo:hover img {
  transform: scale(1.04);
}

.research-title {
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  font-weight: 300;
  color: var(--landing-text-primary);
  margin: 0 0 16px;
}

.research-text {
  color: var(--landing-text-secondary);
  font-size: 1rem;
  line-height: 1.65;
  margin: 0 0 14px;
}

.research-points {
  list-style: none;
  padding: 0;
  margin: 8px 0 28px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.research-points li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.92rem;
  line-height: 1.5;
  color: var(--landing-text-secondary);
}

.research-points li .v-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.research-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 960px) {
  .research-layout {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .research-photo img {
    aspect-ratio: 16 / 9;
  }

  .research-section {
    padding: 60px 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .research-photo img {
    transition: none;
  }

  .research-photo:hover img {
    transform: none;
  }
}
</style>
