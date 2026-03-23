<template>
  <section class="tech-section" :class="{ 'dark-mode': isDarkMode }">
    <div class="section-inner">
      <h2 class="section-title" data-reveal>{{ $t('landing.tech.title') }}</h2>

      <!-- Tech Badges -->
      <div class="tech-badges" data-reveal data-reveal-delay="100">
        <LTag v-for="badge in badges" :key="badge" variant="info" size="md">
          {{ badge }}
        </LTag>
      </div>

      <!-- Animated Counters -->
      <div ref="countersRef" class="counters-grid">
        <div
          v-for="(counter, idx) in counters"
          :key="counter.key"
          class="counter-item"
          data-reveal
          :data-reveal-delay="idx * 100"
        >
          <span class="counter-value">
            {{ counter.prefix }}{{ animatedValues[idx] }}{{ counter.suffix }}
          </span>
          <span class="counter-label">
            {{ $t(`landing.tech.counters.${counter.key}`) }}
          </span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useTheme } from 'vuetify'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)

const badges = [
  'Vue 3.4', 'Vuetify 3.5', 'Flask 3.0', 'MariaDB', 'ChromaDB',
  'Socket.IO', 'YJS', 'Authentik', 'MIT License'
]

const counters = [
  { key: 'components', target: 35,     prefix: '',  suffix: '+' },
  { key: 'evalTypes',  target: 6,      prefix: '',  suffix: ''  },
  { key: 'roles',      target: 5,      prefix: '',  suffix: ''  },
  { key: 'lines',      target: 320,    prefix: '~', suffix: 'k' },
]

const animatedValues = reactive(counters.map(() => 0))
const countersRef = ref(null)
let observer = null

/** Cubic ease-out for smooth deceleration */
function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
}

/** Animate a single counter using requestAnimationFrame */
function animateCounter(index, target, duration = 2000) {
  const start = performance.now()
  function tick(now) {
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    animatedValues[index] = Math.round(easeOutCubic(progress) * target)
    if (progress < 1) {
      requestAnimationFrame(tick)
    }
  }
  requestAnimationFrame(tick)
}

onMounted(() => {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reducedMotion) {
    // Skip animation — show final values immediately
    counters.forEach((c, i) => { animatedValues[i] = c.target })
    return
  }

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          counters.forEach((c, i) => animateCounter(i, c.target))
          observer.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.3 }
  )

  if (countersRef.value) observer.observe(countersRef.value)
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.tech-section {
  padding: 100px 24px;
}

.section-inner {
  max-width: 1000px;
  margin: 0 auto;
  text-align: center;
}

.section-title {
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  font-weight: 300;
  color: var(--landing-text-primary);
  margin: 0 0 32px;
}

.tech-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-bottom: 56px;
}

.counters-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
}

.counter-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.counter-value {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 200;
  color: var(--landing-text-primary);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.counter-label {
  font-size: 0.85rem;
  color: var(--landing-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Responsive: 2x2 grid on mobile */
@media (max-width: 600px) {
  .counters-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
  }

  .tech-section {
    padding: 60px 16px;
  }
}
</style>
