<template>
  <section class="eval-types-section" :class="{ 'dark-mode': isDarkMode }">
    <div class="section-inner">
      <h2 class="section-title" data-reveal>{{ $t('landing.evalTypes.title') }}</h2>
      <p class="section-subtitle" data-reveal data-reveal-delay="100">
        {{ $t('landing.evalTypes.subtitle') }}
      </p>

      <div class="eval-types-row">
        <div
          v-for="(evalType, idx) in evalTypes"
          :key="evalType.key"
          class="eval-type-card"
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

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)

const evalTypes = [
  { key: 'rating',       icon: 'mdi-star-half-full',       color: '#D1BC8A' },
  { key: 'ranking',      icon: 'mdi-sort-variant',         color: '#b0ca97' },
  { key: 'comparison',   icon: 'mdi-compare-horizontal',   color: '#88c4c8' },
  { key: 'labeling',     icon: 'mdi-label-multiple',       color: '#a8c5e2' },
  { key: 'authenticity', icon: 'mdi-shield-search',        color: '#e8a087' },
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
}

.eval-type-card {
  flex: 1 1 180px;
  max-width: 200px;
  background: var(--landing-card-bg);
  border: 1px solid var(--landing-card-border);
  border-radius: 16px 4px 16px 4px;
  padding: 28px 20px;
  text-align: center;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.eval-type-card:hover {
  border-color: var(--accent);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.eval-type-card h3 {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--landing-text-primary);
  margin: 14px 0 8px;
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
