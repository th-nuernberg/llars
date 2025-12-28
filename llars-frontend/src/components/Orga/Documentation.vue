<template>
  <div class="docs-page">
    <!-- Hero Section -->
    <div class="docs-hero">
      <div class="hero-content">
        <h1 class="hero-title">LLARS</h1>
        <p class="hero-subtitle">LLM Assisted Research System</p>
        <div class="hero-badges">
          <LTag variant="primary" prepend-icon="mdi-tag">v3.0</LTag>
          <LTag variant="accent" prepend-icon="mdi-open-source-initiative">Open Source</LTag>
          <LTag variant="success" prepend-icon="mdi-school">TH Nürnberg</LTag>
        </div>
      </div>
    </div>

    <div class="docs-container">
      <!-- Main Content -->
      <main class="docs-content">
        <!-- Überblick -->
        <section class="docs-section">
          <div class="section-header">
            <v-icon size="24">mdi-information-outline</v-icon>
            <h2>Was ist LLARS?</h2>
          </div>
          <div class="section-body">
            <p>
              <strong>LLARS</strong> ist eine Plattform zur kollaborativen Bewertung von KI-generierten
              Inhalten. Das System ermöglicht systematische Evaluation, Vergleich und Optimierung
              von LLM-Antworten im Kontext der E-Beratung.
            </p>
          </div>
        </section>

        <!-- Hauptfunktionen -->
        <section class="docs-section">
          <div class="section-header">
            <v-icon size="24">mdi-apps</v-icon>
            <h2>Hauptfunktionen</h2>
          </div>
          <div class="section-body">
            <div class="feature-grid">
              <div class="feature-item">
                <v-icon color="primary">mdi-chart-bar-stacked</v-icon>
                <span>Ranking & Rating</span>
              </div>
              <div class="feature-item">
                <v-icon color="primary">mdi-scale-balance</v-icon>
                <span>LLM-as-Judge</span>
              </div>
              <div class="feature-item">
                <v-icon color="primary">mdi-robot</v-icon>
                <span>RAG-Chatbots</span>
              </div>
              <div class="feature-item">
                <v-icon color="primary">mdi-text-search</v-icon>
                <span>Prompt Engineering</span>
              </div>
              <div class="feature-item">
                <v-icon color="primary">mdi-account-multiple</v-icon>
                <span>Echtzeit-Kollaboration</span>
              </div>
              <div class="feature-item">
                <v-icon color="primary">mdi-shield-account</v-icon>
                <span>Anonymisierung</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Technische Dokumentation - Prominent! -->
        <section class="docs-section highlight">
          <div class="section-header">
            <v-icon size="24">mdi-book-open-variant</v-icon>
            <h2>Technische Dokumentation</h2>
          </div>
          <div class="section-body">
            <p>
              Die vollständige technische Dokumentation mit Architektur, API-Referenz,
              Agentic AI (RAG, ACT, ReACT, ReflAct), Installationsanleitungen und mehr
              finden Sie in unserer MkDocs-Dokumentation:
            </p>
            <div class="mkdocs-link-container">
              <a href="/mkdocs/" class="mkdocs-link" @click="openMkDocs">
                <v-icon size="32">mdi-book-open-page-variant</v-icon>
                <div class="mkdocs-link-text">
                  <span class="mkdocs-link-title">MkDocs Dokumentation öffnen</span>
                  <span class="mkdocs-link-url">/mkdocs/</span>
                </div>
                <v-icon>mdi-open-in-new</v-icon>
              </a>
            </div>
            <div class="doc-topics">
              <LTag variant="info" size="small">Agentic AI</LTag>
              <LTag variant="info" size="small">RAG Pipeline</LTag>
              <LTag variant="info" size="small">Hybrid Search</LTag>
              <LTag variant="info" size="small">LLM-as-Judge</LTag>
              <LTag variant="info" size="small">API Reference</LTag>
              <LTag variant="info" size="small">Installation</LTag>
            </div>
          </div>
        </section>

        <!-- Quick Start -->
        <section class="docs-section">
          <div class="section-header">
            <v-icon size="24">mdi-rocket-launch</v-icon>
            <h2>Schnellstart</h2>
          </div>
          <div class="section-body">
            <div class="code-block">
              <pre><code># Repository klonen und starten
git clone &lt;repository-url&gt;
cd llars
cp .env.template.development .env
./start_llars.sh</code></pre>
            </div>
            <p class="hint-text">
              Nach dem Start ist LLARS unter <code>http://localhost:55080</code> erreichbar.
            </p>
          </div>
        </section>

        <!-- Kontakt -->
        <section class="docs-section">
          <div class="section-header">
            <v-icon size="24">mdi-email-outline</v-icon>
            <h2>Kontakt</h2>
          </div>
          <div class="section-body">
            <div class="contact-row">
              <a href="mailto:info@e-beratungsinstitut.de" class="contact-link">
                <v-icon>mdi-email</v-icon>
                <span>info@e-beratungsinstitut.de</span>
              </a>
              <a href="https://www.e-beratungsinstitut.de" target="_blank" class="contact-link">
                <v-icon>mdi-web</v-icon>
                <span>e-beratungsinstitut.de</span>
              </a>
            </div>
          </div>
        </section>

        <!-- Footer -->
        <div class="docs-footer">
          <p>Stand: {{ currentDate }} | Version 3.0 | TH Nürnberg</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

// Explizit window.open verwenden um Vue Router zu umgehen
const openMkDocs = (event) => {
  event.preventDefault();
  window.open('/mkdocs/', '_blank');
};

const currentDate = computed(() => {
  return new Date().toLocaleDateString('de-DE', {
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
