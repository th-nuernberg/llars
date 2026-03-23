<template>
  <div class="landing-page" :class="{ 'dark-mode': isDarkMode }">
    <!-- Skip to content link for accessibility -->
    <a href="#landing-main" class="skip-link">Skip to content</a>

    <LandingNav />

    <main id="landing-main">
      <HeroSection />
      <PipelineSection />
      <FeaturesBento />
      <EvalTypesSection />
      <TechSection />
      <CtaSection />
    </main>

    <LandingFooter />
  </div>
</template>

<script setup>
/**
 * Landing Page orchestrator.
 * Composes all landing page sections and initializes scroll-reveal animations.
 * Renders without the App-level AppBar/Footer (hidden via App.vue).
 */
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import { useScrollReveal } from './composables/useScrollReveal'

import LandingNav from './sections/LandingNav.vue'
import HeroSection from './sections/HeroSection.vue'
import PipelineSection from './sections/PipelineSection.vue'
import FeaturesBento from './sections/FeaturesBento.vue'
import EvalTypesSection from './sections/EvalTypesSection.vue'
import TechSection from './sections/TechSection.vue'
import CtaSection from './sections/CtaSection.vue'
import LandingFooter from './sections/LandingFooter.vue'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)

// Initialize scroll-reveal animations for all [data-reveal] elements
useScrollReveal()
</script>

<style scoped>
.landing-page {
  /* CSS custom properties for landing page theming */
  --landing-text-primary: #2c3e2d;
  --landing-text-secondary: #5a6b5c;
  --landing-bg: #faf8f4;
  --landing-bg-alt: #f3f0ea;
  --landing-card-bg: rgba(255, 255, 255, 0.7);
  --landing-card-border: rgba(176, 202, 151, 0.2);

  background: var(--landing-bg);
  min-height: 100vh;
  overflow-x: hidden;
}

.landing-page.dark-mode {
  --landing-text-primary: #e0e0e0;
  --landing-text-secondary: #a0a0a0;
  --landing-bg: #1a1a1a;
  --landing-bg-alt: #212121;
  --landing-card-bg: rgba(40, 40, 40, 0.8);
  --landing-card-border: rgba(176, 202, 151, 0.12);
}

/* Skip link for keyboard accessibility */
.skip-link {
  position: absolute;
  top: -100%;
  left: 16px;
  z-index: 200;
  background: #b0ca97;
  color: #2c3e2d;
  padding: 8px 16px;
  border-radius: 0 0 8px 8px;
  font-weight: 500;
  text-decoration: none;
  transition: top 0.2s ease;
}

.skip-link:focus {
  top: 0;
}
</style>

<!-- Global scroll-reveal animations (unscoped to work in child components) -->
<style>
/* Scroll-reveal base state */
[data-reveal] {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}

/* Revealed state */
[data-reveal].revealed {
  opacity: 1;
  transform: translateY(0);
}

/* Reduced motion: skip animation entirely */
@media (prefers-reduced-motion: reduce) {
  [data-reveal] {
    opacity: 1 !important;
    transform: none !important;
    transition: none !important;
  }
}
</style>
