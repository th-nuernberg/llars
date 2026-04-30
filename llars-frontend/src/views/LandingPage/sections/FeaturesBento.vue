<template>
  <section class="features-section" :class="{ 'dark-mode': isDarkMode }">
    <div class="section-inner">
      <h2 class="section-title" data-reveal>{{ $t('landing.features.title') }}</h2>

      <div class="bento-grid">
        <div
          v-for="(feature, idx) in features"
          :key="feature.key"
          class="bento-card"
          :class="`bento-${feature.span}`"
          :style="{ '--accent': feature.color }"
          data-reveal
          :data-reveal-delay="idx * 80"
          @mouseenter="onCardEnter($event, feature)"
          @mousemove="onCardMove($event)"
          @mouseleave="onCardLeave($event)"
        >
          <div class="card-inner">
            <v-icon :size="28" :color="feature.color">{{ feature.icon }}</v-icon>
            <h3>{{ $t(`landing.features.items.${feature.key}.title`) }}</h3>
            <p>{{ $t(`landing.features.items.${feature.key}.desc`) }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import { useMobile } from '@/composables/useMobile'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { isTouchDevice } = useMobile()

const features = [
  { key: 'rag',          icon: 'mdi-database-search',   color: '#88c4c8', span: 8  },
  { key: 'llmEvaluator', icon: 'mdi-robot',             color: '#D1BC8A', span: 4  },
  { key: 'wizard',       icon: 'mdi-magic-staff',       color: '#b0ca97', span: 6  },
  { key: 'agreement',    icon: 'mdi-chart-scatter-plot', color: '#98d4bb', span: 6  },
  { key: 'collab',       icon: 'mdi-account-group',     color: '#e8c87a', span: 4  },
  { key: 'chatbot',      icon: 'mdi-forum',             color: '#a8c5e2', span: 4  },
  { key: 'auth',         icon: 'mdi-shield-lock',       color: '#e8a087', span: 4  },
  { key: 'designSystem', icon: 'mdi-palette-swatch',    color: '#b0ca97', span: 8  },
]

// prefers-reduced-motion is read once on mount; matchMedia is not reactive here
// because the tilt would otherwise need a listener for a marginal effect.
const prefersReducedMotion = typeof window !== 'undefined'
  && window.matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * Card tilt effect — subtle perspective rotation on hover.
 * Disabled on touch devices and when the user has requested reduced motion.
 */
function onCardEnter(e, feature) {
  if (isTouchDevice.value || prefersReducedMotion) return
  e.currentTarget.style.transition = 'transform 0.15s ease-out, border-color 0.3s ease'
}

function onCardMove(e) {
  if (isTouchDevice.value || prefersReducedMotion) return
  const card = e.currentTarget
  const rect = card.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const rotateY = ((x - centerX) / centerX) * 3
  const rotateX = ((centerY - y) / centerY) * 3
  card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
}

function onCardLeave(e) {
  if (isTouchDevice.value || prefersReducedMotion) return
  const card = e.currentTarget
  card.style.transition = 'transform 0.4s ease, border-color 0.3s ease'
  card.style.transform = 'perspective(800px) rotateX(0) rotateY(0)'
}
</script>

<style scoped>
.features-section {
  padding: 100px 24px;
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
  margin: 0 0 48px;
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}

.bento-4  { grid-column: span 4; }
.bento-6  { grid-column: span 6; }
.bento-8  { grid-column: span 8; }

.bento-card {
  will-change: transform;
  border-radius: 16px 4px 16px 4px;
  background: var(--landing-card-bg);
  border: 1px solid var(--landing-card-border);
  /* opacity/transform must be in this list so the global [data-reveal] fade-up
   * is not stripped by CSS shorthand replacement when the scoped rule wins. */
  transition: opacity 0.6s ease, transform 0.4s ease,
              border-color 0.3s ease, box-shadow 0.3s ease;
}

.bento-card:hover {
  border-color: var(--accent);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06);
}

.card-inner {
  padding: 28px 24px;
}

.card-inner h3 {
  font-size: 1.05rem;
  font-weight: 500;
  color: var(--landing-text-primary);
  margin: 14px 0 8px;
}

.card-inner p {
  font-size: 0.88rem;
  color: var(--landing-text-secondary);
  line-height: 1.55;
  margin: 0;
}

/* Responsive: tablet 6-col, mobile 12-col */
@media (max-width: 960px) {
  .bento-4, .bento-8 { grid-column: span 6; }
}

@media (max-width: 600px) {
  .bento-4, .bento-6, .bento-8 { grid-column: span 12; }

  .features-section {
    padding: 60px 16px;
  }
}

/* Disable tilt on reduced motion. !important is required because the JS
 * handlers also write to element.style.transform inline. */
@media (prefers-reduced-motion: reduce) {
  .bento-card {
    will-change: auto;
    transform: none !important;
  }
}
</style>
