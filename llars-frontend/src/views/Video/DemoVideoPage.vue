<template>
  <div class="video-page">
    <video class="video-page__player" controls preload="metadata">
      <source :src="demoVideoPath" type="video/mp4" />
      {{ $t('home.videoPage.fallback') }}
    </video>
  </div>
</template>

<script setup>
const demoVideoPath = '/videos/llars_demo.mp4'
</script>

<style scoped>
.video-page {
  height: calc(100vh - 94px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background-color: rgb(var(--v-theme-background));
}

.video-page__player {
  width: min(1280px, 100%);
  max-height: calc(100vh - 118px);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  background: #000;
}
</style>
