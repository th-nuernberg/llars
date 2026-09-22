<template>
  <section ref="heroRef" class="hero-section" :class="{ 'dark-mode': isDarkMode }">
    <!-- Paint Strokes Background (same as Login.vue) -->
    <div class="paint-strokes" aria-hidden="true">
      <div v-for="n in 10" :key="n"></div>
    </div>

    <!-- Cursor Glow -->
    <div
      class="cursor-glow"
      :style="{
        background: `radial-gradient(600px circle at ${glowX}% ${glowY}%, ${isDarkMode ? 'rgba(176,202,151,0.06)' : 'rgba(176,202,151,0.08)'}, transparent 60%)`
      }"
      aria-hidden="true"
    />

    <!-- Content -->
    <div class="hero-content">
      <div class="hero-badges" data-reveal data-reveal-delay="0">
        <!-- Points at the arXiv preprint for now. REPLACE with the official
             IJCAI proceedings URL once the paper is published there — the
             preprint stays valid, but the proceedings entry is the citable
             one. The label itself already says "IJCAI", so only the href
             changes. -->
        <a
          class="hero-badge-link"
          :href="PAPER_URL"
          target="_blank"
          rel="noopener noreferrer"
        >
          <LTag variant="accent" size="md">
            <v-icon size="14" class="mr-1">mdi-trophy</v-icon>
            {{ $t('landing.hero.badge') }}
            <v-icon size="12" class="ml-1">mdi-open-in-new</v-icon>
          </LTag>
        </a>
        <LTag variant="success" size="md">
          <v-icon size="14" class="mr-1">mdi-open-source-initiative</v-icon>
          {{ $t('landing.hero.openSource') }}
        </LTag>
      </div>

      <h1 class="hero-headline" data-reveal data-reveal-delay="100">
        {{ $t('landing.hero.headline') }}
      </h1>

      <p class="hero-subtitle" data-reveal data-reveal-delay="200">
        {{ $t('landing.hero.subtitle') }}
      </p>

      <div class="hero-actions" data-reveal data-reveal-delay="300">
        <LBtn variant="primary" size="large" prepend-icon="mdi-rocket-launch" @click="$router.push('/register')">
          {{ $t('landing.hero.cta') }}
        </LBtn>
        <LBtn
          variant="secondary"
          size="large"
          prepend-icon="mdi-play-circle-outline"
          @click="openDemo"
        >
          {{ $t('landing.hero.demo') }}
        </LBtn>
      </div>

      <a
        class="hero-github"
        href="https://github.com/th-nuernberg/llars"
        target="_blank"
        rel="noopener noreferrer"
        data-reveal
        data-reveal-delay="400"
      >
        <v-icon size="18">mdi-github</v-icon>
        {{ $t('landing.hero.github') }}
      </a>
    </div>

    <!-- Bear Mascot (decorative) -->
    <img
      src="@/assets/llars_the_bear/llars_transparent.png"
      alt=""
      aria-hidden="true"
      class="hero-bear"
      loading="lazy"
    />

    <!-- Scroll hint -->
    <button
      type="button"
      class="hero-scroll-hint"
      :aria-label="$t('landing.hero.scrollHint')"
      @click="scrollToNext"
    >
      <v-icon size="28">mdi-chevron-down</v-icon>
    </button>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useCursorGlow } from '../composables/useCursorGlow'

/**
 * The LLARS paper — IJCAI-26 (Demo Track), doi:10.24963/ijcai.2026/995.
 *
 * One constant, so the badge, the footer and anything else pointing at the
 * paper move together. The arXiv preprint of the same paper stays reachable
 * under arXiv:2605.10593, but the proceedings version is what we cite.
 */
const PAPER_URL = 'https://doi.org/10.24963/ijcai.2026/995'

const router = useRouter()
const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)

const heroRef = ref(null)
const { glowX, glowY } = useCursorGlow(heroRef)

function openDemo() {
  // Open the self-hosted LLARS demo video page (plays /videos/llars_demo.mp4).
  // YouTube is now only a backup link ON that page, not the primary target.
  router.push({ name: 'DemoVideoPage' })
}

function scrollToNext() {
  // Programmatic smooth-scroll wird von prefers-reduced-motion NICHT
  // automatisch deaktiviert — daher explizit prüfen.
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const next = heroRef.value?.nextElementSibling
  next?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' })
}
</script>

<style scoped>
.hero-section {
  position: relative;
  min-height: 100vh;
  /* svh: stabile Viewport-Höhe auf Mobile (dynamische Browser-UI) */
  min-height: 100svh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 80px 24px 60px;
}

/* ============================================
   Paint Strokes (adapted from Login.vue)
   ============================================ */
.paint-strokes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  /* Weicher Gesamt-Fade beim Seitenaufruf, während die Blobs einfliegen */
  animation: strokesFadeIn 1.1s ease both;
}

/* Jeder Blob bekommt ZWEI Animationen: einen einmaligen Fly-in von links/
 * rechts (fill both hält Start-/Endzustand) und den endlosen Drift-Loop.
 * Der Drift startet erst NACH dem Fly-in (Delay = Fly-Delay + 1.25s),
 * sonst würde seine transform-Definition den Einflug sofort überschreiben. */
.paint-strokes div {
  position: absolute;
  filter: blur(55px);
  opacity: 0.55;
  will-change: transform;
}

.paint-strokes div:nth-child(1) {
  background: rgba(176, 202, 151, 0.7);
  top: -24%;
  left: -22%;
  width: 62%;
  height: 56%;
  border-radius: 65% 35% 70% 30% / 55% 45% 60% 40%;
  animation: heroFlyLeft 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0s both,
             floatStroke1 26s ease-in-out 1.25s infinite;
}

.paint-strokes div:nth-child(2) {
  background: rgba(209, 188, 138, 0.6);
  top: -15%;
  right: -18%;
  width: 55%;
  height: 50%;
  border-radius: 40% 60% 35% 65% / 50% 55% 45% 50%;
  animation: heroFlyRight 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.08s both,
             floatStroke2 30s ease-in-out 1.33s infinite;
}

.paint-strokes div:nth-child(3) {
  background: rgba(136, 196, 200, 0.55);
  bottom: -20%;
  left: -15%;
  width: 50%;
  height: 48%;
  border-radius: 55% 45% 60% 40% / 65% 35% 55% 45%;
  animation: heroFlyLeft 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.16s both,
             floatStroke3 34s ease-in-out 1.41s infinite;
}

.paint-strokes div:nth-child(4) {
  background: rgba(232, 200, 122, 0.5);
  top: 30%;
  right: 5%;
  width: 35%;
  height: 35%;
  border-radius: 45% 55% 50% 50% / 40% 60% 40% 60%;
  animation: heroFlyRight 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.1s both,
             floatStroke4 28s ease-in-out 1.35s infinite;
}

.paint-strokes div:nth-child(5) {
  background: rgba(152, 212, 187, 0.6);
  bottom: -10%;
  right: -12%;
  width: 45%;
  height: 42%;
  border-radius: 60% 40% 45% 55% / 50% 50% 55% 45%;
  animation: heroFlyRight 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.22s both,
             floatStroke5 32s ease-in-out 1.47s infinite;
}

.paint-strokes div:nth-child(6) {
  background: rgba(168, 197, 226, 0.55);
  top: 10%;
  left: 20%;
  width: 30%;
  height: 30%;
  border-radius: 50% 50% 40% 60% / 55% 45% 50% 50%;
  animation: heroFlyLeft 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.14s both,
             floatStroke6 36s ease-in-out 1.39s infinite;
}

.paint-strokes div:nth-child(7) {
  background: rgba(232, 160, 135, 0.45);
  bottom: 5%;
  left: 30%;
  width: 28%;
  height: 28%;
  border-radius: 40% 60% 55% 45% / 60% 40% 45% 55%;
  animation: heroFlyLeft 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.28s both,
             floatStroke7 38s ease-in-out 1.53s infinite;
}

.paint-strokes div:nth-child(8) {
  background: rgba(201, 168, 226, 0.4);
  top: -5%;
  left: 50%;
  width: 32%;
  height: 32%;
  border-radius: 55% 45% 50% 50% / 45% 55% 50% 50%;
  animation: heroFlyRight 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.2s both,
             floatStroke8 24s ease-in-out 1.45s infinite;
}

.paint-strokes div:nth-child(9) {
  background: rgba(176, 202, 151, 0.35);
  bottom: -15%;
  right: 20%;
  width: 38%;
  height: 36%;
  border-radius: 50% 50% 45% 55% / 55% 45% 50% 50%;
  animation: heroFlyRight 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.12s both,
             floatStroke9 30s ease-in-out 1.37s infinite;
}

.paint-strokes div:nth-child(10) {
  background: rgba(209, 188, 138, 0.3);
  top: 50%;
  left: -10%;
  width: 25%;
  height: 25%;
  border-radius: 45% 55% 55% 45% / 50% 50% 45% 55%;
  animation: heroFlyLeft 1.25s cubic-bezier(0.16, 0.84, 0.4, 1) 0.26s both,
             floatStroke10 34s ease-in-out 1.51s infinite;
}

/* Dark mode paint strokes */
.dark-mode .paint-strokes div {
  filter: blur(80px);
  opacity: 0.35;
}

.dark-mode .paint-strokes div:nth-child(1) { background: rgba(140, 170, 120, 0.5); }
.dark-mode .paint-strokes div:nth-child(2) { background: rgba(180, 160, 110, 0.45); }
.dark-mode .paint-strokes div:nth-child(3) { background: rgba(100, 160, 165, 0.4); }
.dark-mode .paint-strokes div:nth-child(4) { background: rgba(200, 170, 90, 0.35); }
.dark-mode .paint-strokes div:nth-child(5) { background: rgba(120, 180, 155, 0.45); }
.dark-mode .paint-strokes div:nth-child(6) { background: rgba(135, 165, 195, 0.4); }
.dark-mode .paint-strokes div:nth-child(7) { background: rgba(200, 130, 105, 0.3); }
.dark-mode .paint-strokes div:nth-child(8) { background: rgba(170, 140, 195, 0.3); }
.dark-mode .paint-strokes div:nth-child(9) { background: rgba(140, 170, 120, 0.25); }
.dark-mode .paint-strokes div:nth-child(10) { background: rgba(180, 160, 110, 0.2); }

/* Entrance: Blobs fliegen beim Seitenaufruf von links/rechts ein */
@keyframes heroFlyLeft {
  from { transform: translateX(-150%); }
  to { transform: translateX(0); }
}

@keyframes heroFlyRight {
  from { transform: translateX(150%); }
  to { transform: translateX(0); }
}

@keyframes strokesFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Paint stroke animations */
@keyframes floatStroke1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(3%, 5%) scale(1.05); }
  66% { transform: translate(-2%, 3%) scale(0.98); }
}

@keyframes floatStroke2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-4%, 3%) scale(1.03); }
  66% { transform: translate(2%, -4%) scale(0.97); }
}

@keyframes floatStroke3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(5%, -3%) scale(1.04); }
  66% { transform: translate(-3%, 5%) scale(0.96); }
}

@keyframes floatStroke4 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-3%, -4%) scale(1.06); }
  66% { transform: translate(4%, 2%) scale(0.95); }
}

@keyframes floatStroke5 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(4%, 4%) scale(1.03); }
  66% { transform: translate(-5%, -2%) scale(0.98); }
}

@keyframes floatStroke6 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-2%, 5%) scale(1.05); }
  66% { transform: translate(3%, -3%) scale(0.97); }
}

@keyframes floatStroke7 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(5%, -2%) scale(1.02); }
  66% { transform: translate(-4%, 4%) scale(0.99); }
}

@keyframes floatStroke8 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-3%, 3%) scale(1.04); }
  66% { transform: translate(2%, -5%) scale(0.96); }
}

@keyframes floatStroke9 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(3%, -4%) scale(1.03); }
  66% { transform: translate(-2%, 3%) scale(0.98); }
}

@keyframes floatStroke10 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-4%, 2%) scale(1.05); }
  66% { transform: translate(3%, -3%) scale(0.97); }
}

/* ============================================
   Cursor Glow
   ============================================ */
.cursor-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  transition: background 0.1s ease;
}

/* ============================================
   Hero Content
   ============================================ */
.hero-content {
  position: relative;
  z-index: 2;
  text-align: center;
  max-width: 800px;
}

.hero-badges {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

/* The badge is a link now; keep it looking like the badge next to it and only
   hint at the affordance on hover. */
.hero-badge-link {
  text-decoration: none;
  display: inline-flex;
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.hero-badge-link:hover {
  transform: translateY(-1px);
  opacity: 0.88;
}

@media (prefers-reduced-motion: reduce) {
  .hero-badge-link {
    transition: none;
  }
  .hero-badge-link:hover {
    transform: none;
  }
}

.hero-headline {
  font-size: clamp(2rem, 4vw + 1rem, 3.5rem);
  font-weight: 300;
  line-height: 1.15;
  color: var(--landing-text-primary);
  margin: 0 0 20px;
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: clamp(1rem, 1.5vw + 0.5rem, 1.25rem);
  color: var(--landing-text-secondary);
  line-height: 1.6;
  margin: 0 0 36px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.hero-github {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 24px;
  color: var(--landing-text-secondary);
  font-size: 0.9rem;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: color 0.2s ease, border-color 0.2s ease;
}

.hero-github:hover {
  color: var(--landing-text-primary);
  border-bottom-color: currentColor;
}

/* ============================================
   Bear Mascot
   ============================================ */
.hero-bear {
  position: absolute;
  bottom: 40px;
  right: 40px;
  width: 280px;
  opacity: 0.15;
  pointer-events: none;
  z-index: 1;
  animation: bearBob 7s ease-in-out infinite;
}

/* Sehr dezentes Auf-und-Ab des Maskottchens */
@keyframes bearBob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* ============================================
   Scroll Hint
   ============================================ */
.hero-scroll-hint {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
  background: transparent;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: var(--landing-text-secondary);
  opacity: 0.7;
  animation: hintBounce 2.2s ease-in-out infinite;
  transition: opacity 0.2s ease, color 0.2s ease;
}

.hero-scroll-hint:hover {
  opacity: 1;
  color: var(--landing-text-primary);
}

@keyframes hintBounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(6px); }
}

/* ============================================
   Responsive
   ============================================ */
@media (max-width: 960px) {
  .hero-bear {
    width: 180px;
    bottom: 20px;
    right: 20px;
    opacity: 0.1;
  }
}

@media (max-width: 600px) {
  .hero-section {
    padding: 100px 16px 40px;
    min-height: 90vh;
  }

  .hero-bear {
    display: none;
  }

  .paint-strokes div {
    filter: blur(40px);
    opacity: 0.35;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .paint-strokes,
  .paint-strokes div,
  .hero-bear,
  .hero-scroll-hint {
    animation: none !important;
  }

  .cursor-glow {
    display: none;
  }
}
</style>
