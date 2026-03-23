<template>
  <section class="pipeline-section" :class="{ 'dark-mode': isDarkMode }">
    <div class="section-inner">
      <h2 class="section-title" data-reveal>{{ $t('landing.pipeline.title') }}</h2>
      <p class="section-subtitle" data-reveal data-reveal-delay="100">
        {{ $t('landing.pipeline.subtitle') }}
      </p>

      <div class="pipeline-flow">
        <!-- Step 1: Prompt Engineering -->
        <div class="pipeline-step" data-reveal data-reveal-delay="0">
          <div class="step-card" style="--accent: #b0ca97">
            <v-icon size="36" color="#b0ca97">mdi-pencil-ruler</v-icon>
            <h3>{{ $t('landing.pipeline.steps.prompt.title') }}</h3>
            <p>{{ $t('landing.pipeline.steps.prompt.desc') }}</p>
          </div>
        </div>

        <div class="pipeline-arrow" data-reveal data-reveal-delay="100" aria-hidden="true">
          <v-icon :size="isMobile ? 24 : 28" color="#b0ca97">
            {{ isMobile ? 'mdi-arrow-down' : 'mdi-arrow-right' }}
          </v-icon>
        </div>

        <!-- Step 2: Batch Generation -->
        <div class="pipeline-step" data-reveal data-reveal-delay="150">
          <div class="step-card" style="--accent: #D1BC8A">
            <v-icon size="36" color="#D1BC8A">mdi-cog-transfer</v-icon>
            <h3>{{ $t('landing.pipeline.steps.generation.title') }}</h3>
            <p>{{ $t('landing.pipeline.steps.generation.desc') }}</p>
          </div>
        </div>

        <div class="pipeline-arrow" data-reveal data-reveal-delay="200" aria-hidden="true">
          <v-icon :size="isMobile ? 24 : 28" color="#D1BC8A">
            {{ isMobile ? 'mdi-arrow-down' : 'mdi-arrow-right' }}
          </v-icon>
        </div>

        <!-- Step 3: Hybrid Evaluation -->
        <div class="pipeline-step" data-reveal data-reveal-delay="300">
          <div class="step-card" style="--accent: #88c4c8">
            <v-icon size="36" color="#88c4c8">mdi-chart-bar</v-icon>
            <h3>{{ $t('landing.pipeline.steps.evaluation.title') }}</h3>
            <p>{{ $t('landing.pipeline.steps.evaluation.desc') }}</p>
          </div>
        </div>
      </div>

      <p class="flow-note" data-reveal data-reveal-delay="400">
        {{ $t('landing.pipeline.note') }}
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import { useMobile } from '@/composables/useMobile'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { isMobile } = useMobile()
</script>

<style scoped>
.pipeline-section {
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
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.pipeline-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.pipeline-step {
  flex: 1;
  max-width: 300px;
}

.step-card {
  background: var(--landing-card-bg);
  border: 1px solid var(--landing-card-border);
  border-radius: 16px 4px 16px 4px;
  padding: 32px 24px;
  text-align: center;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.step-card:hover {
  border-color: var(--accent);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.step-card h3 {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--landing-text-primary);
  margin: 16px 0 8px;
}

.step-card p {
  font-size: 0.9rem;
  color: var(--landing-text-secondary);
  line-height: 1.5;
  margin: 0;
}

.pipeline-arrow {
  flex-shrink: 0;
  opacity: 0.5;
}

.flow-note {
  text-align: center;
  font-size: 0.85rem;
  color: var(--landing-text-secondary);
  margin-top: 32px;
  font-style: italic;
  opacity: 0.8;
}

/* Responsive: stack vertically on mobile */
@media (max-width: 768px) {
  .pipeline-flow {
    flex-direction: column;
    gap: 8px;
  }

  .pipeline-step {
    max-width: 100%;
    width: 100%;
  }

  .pipeline-section {
    padding: 60px 16px;
  }
}
</style>
