<template>
  <section id="eval-types" class="eval-types-section" :class="{ 'dark-mode': isDarkMode }">
    <div class="section-inner">
      <h2 class="section-title" data-reveal>{{ $t('landing.evalTypes.title') }}</h2>
      <p class="section-subtitle" data-reveal data-reveal-delay="100">
        {{ $t('landing.evalTypes.subtitle') }}
      </p>

      <div class="eval-types-row">
        <div
          v-for="(evalType, idx) in evalTypes"
          :key="evalType.key"
          v-glow
          class="eval-type-card glow-surface"
          :style="{ '--accent': evalType.color }"
          data-reveal
          :data-reveal-delay="idx * 100"
        >
          <v-icon size="32" :color="evalType.color">{{ evalType.icon }}</v-icon>
          <h3>{{ $t(`landing.evalTypes.types.${evalType.key}.title`) }}</h3>
          <p>{{ $t(`landing.evalTypes.types.${evalType.key}.desc`) }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import { glow as vGlow } from '../directives/glow'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)

const evalTypes = [
  { key: 'rating',       icon: 'mdi-star-half-full',       color: '#D1BC8A' },
  { key: 'ranking',      icon: 'mdi-sort-variant',         color: '#b0ca97' },
  { key: 'comparison',   icon: 'mdi-compare-horizontal',   color: '#88c4c8' },
  { key: 'labeling',     icon: 'mdi-label-multiple',       color: '#a8c5e2' },
  { key: 'authenticity', icon: 'mdi-shield-search',        color: '#e8a087' },
  { key: 'mail_rating',  icon: 'mdi-email-check',          color: '#c9a8e2' },
  { key: 'communication_comparison', icon: 'mdi-message-reply-text-outline', color: '#98d4bb' },
  { key: 'conversation_labeling', icon: 'mdi-tag-multiple-outline', color: '#6FA8A0' },
]
</script>

<style scoped>
.eval-types-section {
  padding: 100px 24px;
  background: var(--landing-bg-alt);
}

.section-inner {
  max-width: 1100px;
  margin: 0 auto;
}

.section-title {
  text-align: center;
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  font-weight: 300;
  color: var(--landing-text-primary);
  margin: 0 0 12px;
}

.section-subtitle {
  text-align: center;
  color: var(--landing-text-secondary);
  font-size: 1.05rem;
  margin: 0 0 48px;
  max-width: 550px;
  margin-left: auto;
  margin-right: auto;
}

.eval-types-row {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
  /* Auf 4 Karten pro Zeile begrenzen (4×200px + 3×16px = 848px), damit die
   * 7 Karten symmetrisch als 4+3-Pyramide umbrechen statt als schief
   * wirkendes 5+2 bei voller 1100px-Breite. */
  max-width: 880px;
  margin: 0 auto;
}

.eval-type-card {
  flex: 1 1 180px;
  max-width: 200px;
  background: var(--landing-card-bg);
  border: 1px solid var(--landing-card-border);
  border-radius: 16px 4px 16px 4px;
  padding: 28px 20px;
  text-align: center;
  /* opacity/transform must be in this list so the global [data-reveal] fade-up
   * is not stripped by CSS shorthand replacement when the scoped rule wins.
   * transform bewusst kürzer als opacity: dieselbe Property treibt auch den
   * Hover-Lift, der sonst träge wirkt. */
  transition: opacity 0.6s ease, transform 0.3s ease,
              border-color 0.3s ease, box-shadow 0.3s ease;
}

.eval-type-card:hover {
  border-color: var(--accent);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transform: translateY(-3px);
}

/* Reveal + Hover teilen sich transform: erst wenn revealed, gilt der Lift. */
@media (prefers-reduced-motion: reduce) {
  .eval-type-card:hover {
    transform: none;
  }
}

.eval-type-card h3 {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--landing-text-primary);
  margin: 14px 0 8px;
  /* Lange Komposita ("Kommunikationsvergleich") sauber in der Karte halten */
  hyphens: auto;
  overflow-wrap: break-word;
}

.eval-type-card p {
  font-size: 0.82rem;
  color: var(--landing-text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* Mobile: horizontal scroll with snap */
@media (max-width: 600px) {
  .eval-types-row {
    flex-wrap: nowrap;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 8px;
    gap: 12px;
  }

  .eval-type-card {
    flex: 0 0 160px;
    max-width: none;
    scroll-snap-align: start;
  }

  .eval-types-section {
    padding: 60px 16px;
  }
}
</style>
