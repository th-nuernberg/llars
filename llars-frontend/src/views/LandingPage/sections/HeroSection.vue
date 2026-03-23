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
      <LTag variant="accent" size="md" class="hero-badge" data-reveal data-reveal-delay="0">
        <v-icon size="14" class="mr-1">mdi-trophy</v-icon>
        {{ $t('landing.hero.badge') }}
      </LTag>

      <h1 class="hero-headline" data-reveal data-reveal-delay="100">
        {{ $t('landing.hero.headline') }}
      </h1>

      <p class="hero-subtitle" data-reveal data-reveal-delay="200">
        {{ $t('landing.hero.subtitle') }}
      </p>

      <div class="hero-actions" data-reveal data-reveal-delay="300">
        <LBtn variant="primary" size="large" prepend-icon="mdi-rocket-launch" @click="$router.push('/login')">
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
    </div>

    <!-- Bear Mascot (decorative) -->
    <img
      src="@/assets/llars_the_bear/llars_transparent.png"
      alt=""
      aria-hidden="true"
      class="hero-bear"
      loading="lazy"
    />
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'
import { useCursorGlow } from '../composables/useCursorGlow'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)

const heroRef = ref(null)
const { glowX, glowY } = useCursorGlow(heroRef)

function openDemo() {
  window.open('https://www.youtube.com/watch?v=5YXPqh5JklA', '_blank')
}
</script>

<style scoped>
.hero-section {
  position: relative;
  min-height: 100vh;
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
}

.paint-strokes div {
  position: absolute;
  filter: blur(55px);
  opacity: 0.55;
}

.paint-strokes div:nth-child(1) {
  background: rgba(176, 202, 151, 0.7);
  top: -24%;
  left: -22%;
  width: 62%;
  height: 56%;
  border-radius: 65% 35% 70% 30% / 55% 45% 60% 40%;
  animation: floatStroke1 26s ease-in-out infinite;
}

.paint-strokes div:nth-child(2) {
  background: rgba(209, 188, 138, 0.6);
  top: -15%;
  right: -18%;
  width: 55%;
  height: 50%;
  border-radius: 40% 60% 35% 65% / 50% 55% 45% 50%;
  animation: floatStroke2 30s ease-in-out infinite;
}

.paint-strokes div:nth-child(3) {
  background: rgba(136, 196, 200, 0.55);
  bottom: -20%;
  left: -15%;
  width: 50%;
  height: 48%;
  border-radius: 55% 45% 60% 40% / 65% 35% 55% 45%;
  animation: floatStroke3 34s ease-in-out infinite;
}

.paint-strokes div:nth-child(4) {
  background: rgba(232, 200, 122, 0.5);
  top: 30%;
  right: 5%;
  width: 35%;
  height: 35%;
  border-radius: 45% 55% 50% 50% / 40% 60% 40% 60%;
  animation: floatStroke4 28s ease-in-out infinite;
}

.paint-strokes div:nth-child(5) {
  background: rgba(152, 212, 187, 0.6);
  bottom: -10%;
  right: -12%;
  width: 45%;
  height: 42%;
  border-radius: 60% 40% 45% 55% / 50% 50% 55% 45%;
  animation: floatStroke5 32s ease-in-out infinite;
}

.paint-strokes div:nth-child(6) {
  background: rgba(168, 197, 226, 0.55);
  top: 10%;
  left: 20%;
  width: 30%;
  height: 30%;
  border-radius: 50% 50% 40% 60% / 55% 45% 50% 50%;
  animation: floatStroke6 36s ease-in-out infinite;
}

.paint-strokes div:nth-child(7) {
  background: rgba(232, 160, 135, 0.45);
  bottom: 5%;
  left: 30%;
  width: 28%;
  height: 28%;
  border-radius: 40% 60% 55% 45% / 60% 40% 45% 55%;
  animation: floatStroke7 38s ease-in-out infinite;
}

.paint-strokes div:nth-child(8) {
  background: rgba(201, 168, 226, 0.4);
  top: -5%;
  left: 50%;
  width: 32%;
  height: 32%;
  border-radius: 55% 45% 50% 50% / 45% 55% 50% 50%;
  animation: floatStroke8 24s ease-in-out infinite;
}

.paint-strokes div:nth-child(9) {
  background: rgba(176, 202, 151, 0.35);
  bottom: -15%;
  right: 20%;
  width: 38%;
  height: 36%;
  border-radius: 50% 50% 45% 55% / 55% 45% 50% 50%;
  animation: floatStroke9 30s ease-in-out infinite;
}

.paint-strokes div:nth-child(10) {
  background: rgba(209, 188, 138, 0.3);
  top: 50%;
  left: -10%;
  width: 25%;
  height: 25%;
  border-radius: 45% 55% 55% 45% / 50% 50% 45% 55%;
  animation: floatStroke10 34s ease-in-out infinite;
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

.hero-badge {
  margin-bottom: 24px;
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
  .paint-strokes div {
    animation: none !important;
  }

  .cursor-glow {
    display: none;
  }
}
</style>
