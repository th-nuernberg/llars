<template>
  <div class="docs-page">
    <!-- Hero Section -->
    <div class="docs-hero">
      <div class="hero-content">
        <h1 class="hero-title">{{ $t('docs.hero.title') }}</h1>
        <p class="hero-subtitle">{{ $t('docs.hero.subtitle') }}</p>
        <div class="hero-badges">
          <LTag variant="primary" prepend-icon="mdi-tag">{{ $t('docs.hero.version') }}</LTag>
          <LTag variant="accent" prepend-icon="mdi-open-source-initiative">{{ $t('docs.hero.openSource') }}</LTag>
          <LTag variant="success" prepend-icon="mdi-school">{{ $t('docs.hero.organization') }}</LTag>
        </div>
      </div>
    </div>

    <div class="docs-container">
      <!-- Main Content -->
      <main class="docs-content">
        <!-- Überblick -->
        <section class="docs-section">
          <div class="section-header">
            <LIcon size="24">mdi-information-outline</LIcon>
            <h2>{{ $t('docs.overview.title') }}</h2>
          </div>
          <div class="section-body">
            <i18n-t keypath="docs.overview.body" tag="p">
              <strong>{{ $t('docs.hero.title') }}</strong>
            </i18n-t>
          </div>
        </section>

        <!-- Hauptfunktionen -->
        <section class="docs-section">
          <div class="section-header">
            <LIcon size="24">mdi-apps</LIcon>
            <h2>{{ $t('docs.features.title') }}</h2>
          </div>
          <div class="section-body">
            <div class="feature-grid">
              <div class="feature-item">
                <LIcon color="primary">mdi-chart-bar-stacked</LIcon>
                <span>{{ $t('docs.features.items.rankingRating') }}</span>
              </div>
              <div class="feature-item">
                <LIcon color="primary">mdi-sword-cross</LIcon>
                <span>{{ $t('docs.features.items.chatbotArena') }}</span>
              </div>
              <div class="feature-item">
                <LIcon color="primary">mdi-robot</LIcon>
                <span>{{ $t('docs.features.items.ragChatbots') }}</span>
              </div>
              <div class="feature-item">
                <LIcon color="primary">mdi-text-search</LIcon>
                <span>{{ $t('docs.features.items.promptEngineering') }}</span>
              </div>
              <div class="feature-item">
                <LIcon color="primary">mdi-account-multiple</LIcon>
                <span>{{ $t('docs.features.items.realtimeCollaboration') }}</span>
              </div>
              <div class="feature-item">
                <LIcon color="primary">mdi-shield-account</LIcon>
                <span>{{ $t('docs.features.items.anonymization') }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Technische Dokumentation - Prominent! -->
        <section class="docs-section highlight">
          <div class="section-header">
            <LIcon size="24">mdi-book-open-variant</LIcon>
            <h2>{{ $t('docs.technical.title') }}</h2>
          </div>
          <div class="section-body">
            <p>
              {{ $t('docs.technical.body') }}
            </p>
            <div class="mkdocs-link-container">
              <a href="/mkdocs/" class="mkdocs-link" @click="openMkDocs">
                <LIcon size="32">mdi-book-open-page-variant</LIcon>
                <div class="mkdocs-link-text">
                  <span class="mkdocs-link-title">{{ $t('docs.technical.linkTitle') }}</span>
                  <span class="mkdocs-link-url">/mkdocs/</span>
                </div>
                <LIcon>mdi-open-in-new</LIcon>
              </a>
            </div>
            <div class="doc-topics">
              <LTag variant="info" size="small">{{ $t('docs.technical.tags.agenticAI') }}</LTag>
              <LTag variant="info" size="small">{{ $t('docs.technical.tags.ragPipeline') }}</LTag>
              <LTag variant="info" size="small">{{ $t('docs.technical.tags.hybridSearch') }}</LTag>
              <LTag variant="info" size="small">{{ $t('docs.technical.tags.chatbotArena') }}</LTag>
              <LTag variant="info" size="small">{{ $t('docs.technical.tags.apiReference') }}</LTag>
              <LTag variant="info" size="small">{{ $t('docs.technical.tags.installation') }}</LTag>
            </div>
          </div>
        </section>

        <!-- Quick Start -->
        <section class="docs-section">
          <div class="section-header">
            <LIcon size="24">mdi-rocket-launch</LIcon>
            <h2>{{ $t('docs.quickStart.title') }}</h2>
          </div>
          <div class="section-body">
            <div class="code-block">
              <pre><code>{{ $t('docs.quickStart.code') }}</code></pre>
            </div>
            <i18n-t keypath="docs.quickStart.hint" tag="p" class="hint-text">
              <code>http://localhost:55080</code>
            </i18n-t>
          </div>
        </section>

        <!-- Kontakt -->
        <section class="docs-section">
          <div class="section-header">
            <LIcon size="24">mdi-email-outline</LIcon>
            <h2>{{ $t('docs.contact.title') }}</h2>
          </div>
          <div class="section-body">
            <div class="contact-row">
              <a href="mailto:info@e-beratungsinstitut.de" class="contact-link">
                <LIcon>mdi-email</LIcon>
                <span>{{ $t('docs.contact.email') }}</span>
              </a>
              <a href="https://www.e-beratungsinstitut.de" target="_blank" class="contact-link">
                <LIcon>mdi-web</LIcon>
                <span>{{ $t('docs.contact.website') }}</span>
              </a>
            </div>
          </div>
        </section>

        <!-- Footer -->
        <div class="docs-footer">
          <p>{{ $t('docs.footer', { date: currentDate }) }}</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

// Explizit window.open verwenden um Vue Router zu umgehen
const openMkDocs = (event) => {
  event.preventDefault();
  window.open('/mkdocs/', '_blank');
};

const { locale } = useI18n();
const currentDate = computed(() => {
  return new Date().toLocaleDateString(locale.value || undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
});
</script>

<style scoped>
.docs-page {
  min-height: calc(100vh - 94px);
  background: rgb(var(--v-theme-background));
}

/* Hero Section */
.docs-hero {
  background: var(--llars-gradient-primary);
  padding: 48px 24px;
  text-align: center;
}

.hero-content {
  max-width: 600px;
  margin: 0 auto;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.hero-subtitle {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 16px;
}

.hero-badges {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* Container */
.docs-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

/* Sections */
.docs-section {
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.docs-section.highlight {
  border: 2px solid var(--llars-primary);
  box-shadow: 0 4px 16px rgba(176, 202, 151, 0.2);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.section-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.section-body {
  padding: 20px;
}

.section-body p {
  line-height: 1.7;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin: 0 0 16px 0;
}

.section-body p:last-child {
  margin-bottom: 0;
}

/* Feature Grid */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 8px 2px 8px 2px;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* MkDocs Link */
.mkdocs-link-container {
  margin: 20px 0;
}

.mkdocs-link {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--llars-primary);
  color: white;
  border-radius: 12px 4px 12px 4px;
  text-decoration: none;
  transition: all 0.2s ease;
}

.mkdocs-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(176, 202, 151, 0.4);
}

.mkdocs-link-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.mkdocs-link-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.mkdocs-link-url {
  font-size: 0.85rem;
  opacity: 0.8;
}

.doc-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

/* Code Block */
.code-block {
  background: #1e1e1e;
  border-radius: 8px 2px 8px 2px;
  overflow: hidden;
}

.code-block pre {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
}

.code-block code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85rem;
  line-height: 1.6;
  color: #e0e0e0;
}

.hint-text {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 12px !important;
}

.hint-text code {
  background: rgba(var(--v-theme-on-surface), 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85rem;
}

/* Contact */
.contact-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.contact-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 8px 2px 8px 2px;
  text-decoration: none;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.contact-link:hover {
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: var(--llars-primary);
}

/* Footer */
.docs-footer {
  text-align: center;
  padding: 20px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.85rem;
}

/* Responsive */
@media (max-width: 600px) {
  .hero-title {
    font-size: 2rem;
  }

  .hero-subtitle {
    font-size: 1rem;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .mkdocs-link {
    flex-direction: column;
    text-align: center;
  }

  .contact-row {
    flex-direction: column;
  }
}
</style>
