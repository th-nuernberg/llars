<template>
  <section class="cta-section" :class="{ 'dark-mode': isDarkMode }">
    <!-- Blob-Finale: kräftige Paint-Strokes fliegen beim Scrollen ein -->
    <PaintStrokesReveal :strength="1.4" />

    <div class="cta-inner" data-reveal>
      <h2 class="cta-headline">{{ $t('landing.cta.headline') }}</h2>
      <p class="cta-subtitle">{{ $t('landing.cta.subtitle') }}</p>
      <div class="cta-actions">
        <LBtn variant="primary" size="large" prepend-icon="mdi-login" @click="$router.push('/login')">
          {{ $t('auth.login') }}
        </LBtn>
        <LBtn variant="secondary" size="large" prepend-icon="mdi-account-plus" @click="$router.push('/register')">
          {{ $t('landing.cta.register') }}
        </LBtn>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import PaintStrokesReveal from '../components/PaintStrokesReveal.vue'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
</script>

<style scoped>
.cta-section {
  position: relative;
  overflow: hidden;
  padding: 120px 24px;
  background: var(--landing-bg-alt);
}

.cta-inner {
  position: relative;
  z-index: 1;
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.cta-headline {
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  font-weight: 300;
  color: var(--landing-text-primary);
  margin: 0 0 16px;
}

.cta-subtitle {
  font-size: 1.05rem;
  color: var(--landing-text-secondary);
  margin: 0 0 36px;
}

.cta-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

@media (max-width: 600px) {
  .cta-section {
    padding: 60px 16px;
  }
}
</style>
