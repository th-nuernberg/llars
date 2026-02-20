<template>
  <div class="video-page">
    <div class="video-page__container">
      <video class="video-page__player" controls preload="metadata">
        <source :src="demoVideoPath" type="video/mp4" />
        {{ $t('home.videoPage.fallback') }}
      </video>

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
        <div class="video-page__meta">
          <span class="video-page__meta-item">
            <v-icon size="16" class="mr-1">mdi-open-in-new</v-icon>
            Live demo:
            <a
              href="https://llars.e-beratungsinstitut.de"
              target="_blank"
              rel="noopener"
            >llars.e-beratungsinstitut.de</a>
          </span>
        </div>
        <p class="video-page__disclosure">
          Disclosure: The voice-over narration in this video was generated using a
          Qwen3 TTS 0.6B model.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
const demoVideoPath = '/videos/llars_demo.mp4'
</script>

<style scoped>
.video-page {
  height: calc(100vh - 94px);
  display: flex;
  justify-content: center;
  padding: 24px 16px;
  background-color: rgb(var(--v-theme-background));
  overflow-y: auto;
}

.video-page__container {
  width: min(1280px, 100%);
}

.video-page__player {
  width: 100%;
  max-height: calc(100vh - 300px);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  background: #000;
}

.video-page__info {
  padding: 16px 4px 24px;
}

.video-page__title {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.4;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 12px;
}

.video-page__description {
  font-size: 0.9rem;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 16px;
}

.video-page__meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.video-page__meta-item {
  display: inline-flex;
  align-items: center;
  font-size: 0.85rem;
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
  font-size: 0.8rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-style: italic;
}
</style>