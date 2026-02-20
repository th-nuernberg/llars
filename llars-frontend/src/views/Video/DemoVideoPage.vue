<template>
  <div class="video-page">
    <div class="video-page__container">
      <div class="video-page__player-wrapper">
        <v-skeleton-loader
          v-if="!videoReady"
          type="image"
          class="video-page__skeleton"
        />
        <video
          ref="videoEl"
          class="video-page__player"
          :class="{ 'video-page__player--hidden': !videoReady }"
          controls
          preload="metadata"
          @loadedmetadata="videoReady = true"
        >
          <source :src="demoVideoPath" type="video/mp4" />
          {{ $t('home.videoPage.fallback') }}
        </video>
      </div>

      <div class="video-page__info">
        <h1 class="video-page__title">
          LLARS Demo: Prompting, Batch Generation &amp; Hybrid Evaluation
        </h1>
        <p class="video-page__description">
          In this demo we present LLARS, an open-source platform that bridges domain experts
          and developers when building LLM-based systems. LLARS supports collaborative prompt
          engineering (real-time co-authoring, versioning, instant testing), batch generation
          across prompts × models × data, and hybrid evaluation combining human and LLM-based
          assessment with agreement metrics and provenance analysis.
        </p>
        <div class="video-page__footer">
          <span class="video-page__meta-item">
            <v-icon size="14" class="mr-1">mdi-open-in-new</v-icon>
            Live demo:
            <a
              href="https://llars.e-beratungsinstitut.de"
              target="_blank"
              rel="noopener"
            >llars.e-beratungsinstitut.de</a>
          </span>
          <span class="video-page__disclosure">
            Disclosure: The voice-over narration was generated using a Qwen3 TTS 0.6B model.
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const demoVideoPath = '/videos/llars_demo.mp4'
const videoEl = ref(null)
const videoReady = ref(false)
</script>

<style scoped>
.video-page {
  height: calc(100vh - 94px);
  display: flex;
  justify-content: center;
  padding: 20px 16px 12px;
  background-color: rgb(var(--v-theme-background));
  overflow: hidden;
}

.video-page__container {
  width: min(1280px, 100%);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.video-page__player-wrapper {
  flex: 1;
  min-height: 0;
  position: relative;
  /* Video aspect ratio: 3600x2260 ≈ 1.593 */
}

.video-page__skeleton {
  width: 100%;
  height: 100%;
  border-radius: 12px;
}

.video-page__skeleton :deep(.v-skeleton-loader__image) {
  height: 100%;
}

.video-page__player {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  background: #000;
}

.video-page__player--hidden {
  position: absolute;
  inset: 0;
  opacity: 0;
}

.video-page__info {
  flex-shrink: 0;
  padding: 12px 4px 0;
}

.video-page__title {
  font-size: 1.15rem;
  font-weight: 600;
  line-height: 1.3;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
}

.video-page__description {
  font-size: 0.85rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 8px;
}

.video-page__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.video-page__meta-item {
  display: inline-flex;
  align-items: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.video-page__meta-item a {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  margin-left: 4px;
}

.video-page__meta-item a:hover {
  text-decoration: underline;
}

.video-page__disclosure {
  font-size: 0.75rem;
  line-height: 1.4;
  color: rgba(var(--v-theme-on-surface), 0.45);
  font-style: italic;
}
</style>
