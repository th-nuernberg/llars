<template>
  <div class="docs-page">
    <!-- Hero Section -->
    <div class="docs-hero">
      <div class="hero-content">
        <h1 class="hero-title">LLARS Dokumentation</h1>
        <p class="hero-subtitle">Learning & Labeling AI Rating System</p>
        <div class="hero-badges">
          <LTag variant="primary" prepend-icon="mdi-tag">v2.9</LTag>
          <LTag variant="accent" prepend-icon="mdi-open-source-initiative">Open Source</LTag>
          <LTag variant="success" prepend-icon="mdi-school">TH Nürnberg</LTag>
        </div>
      </div>
    </div>

    <div class="docs-container">
      <!-- Sidebar Navigation -->
      <aside class="docs-sidebar">
        <div class="sidebar-card">
          <h3 class="sidebar-title">
            <v-icon size="18">mdi-format-list-bulleted</v-icon>
            Inhaltsverzeichnis
          </h3>
          <nav class="toc-nav">
            <a href="#overview" class="toc-link" :class="{ active: activeSection === 'overview' }">
              <span class="toc-number">1</span>
              Überblick
            </a>
            <a href="#features" class="toc-link" :class="{ active: activeSection === 'features' }">
              <span class="toc-number">2</span>
              Funktionen
            </a>
            <a href="#architecture" class="toc-link" :class="{ active: activeSection === 'architecture' }">
              <span class="toc-number">3</span>
              Architektur
            </a>
            <a href="#installation" class="toc-link" :class="{ active: activeSection === 'installation' }">
              <span class="toc-number">4</span>
              Installation
            </a>
            <a href="#authentication" class="toc-link" :class="{ active: activeSection === 'authentication' }">
              <span class="toc-number">5</span>
              Authentifizierung
            </a>
            <a href="#modules" class="toc-link" :class="{ active: activeSection === 'modules' }">
              <span class="toc-number">6</span>
              Module
            </a>
            <a href="#api" class="toc-link" :class="{ active: activeSection === 'api' }">
              <span class="toc-number">7</span>
              API-Referenz
            </a>
            <a href="#troubleshooting" class="toc-link" :class="{ active: activeSection === 'troubleshooting' }">
              <span class="toc-number">8</span>
              Troubleshooting
            </a>
            <a href="#contact" class="toc-link" :class="{ active: activeSection === 'contact' }">
              <span class="toc-number">9</span>
              Kontakt
            </a>
          </nav>

          <div class="sidebar-links">
            <a :href="mkdocsUrl" target="_blank" class="sidebar-link">
              <v-icon size="16">mdi-book-open-variant</v-icon>
              Technische Docs
            </a>
            <router-link to="/Impressum" class="sidebar-link">
              <v-icon size="16">mdi-information</v-icon>
              Impressum
            </router-link>
            <router-link to="/Datenschutz" class="sidebar-link">
              <v-icon size="16">mdi-shield-lock</v-icon>
              Datenschutz
            </router-link>
          </div>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="docs-content">
        <!-- 1. Überblick -->
        <section id="overview" class="docs-section">
          <div class="section-header">
            <span class="section-number">01</span>
            <h2>Überblick</h2>
          </div>
          <div class="section-body">
            <p>
              <strong>LLARS</strong> (Learning & Labeling AI Rating System) ist eine umfassende Plattform zur Bewertung,
              Analyse und Verbesserung von KI-generierten Inhalten, insbesondere im Kontext der
              E-Beratung und digitalen Kommunikation.
            </p>
            <p>
              Das System wurde entwickelt, um Forschern, Entwicklern und Beratern die Möglichkeit zu geben,
              KI-Modelle systematisch zu evaluieren, zu vergleichen und zu optimieren.
            </p>
            <div class="info-card">
              <v-icon color="info" size="20">mdi-account-group</v-icon>
              <div>
                <strong>Zielgruppe</strong>
                <p>Forscher, KI-Entwickler, E-Berater, Datenwissenschaftler</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 2. Funktionen -->
        <section id="features" class="docs-section">
          <div class="section-header">
            <span class="section-number">02</span>
            <h2>Funktionen</h2>
          </div>
          <div class="section-body">
            <div class="feature-grid">
              <div class="feature-card">
                <div class="feature-icon" style="background-color: var(--llars-primary);">
                  <v-icon color="white">mdi-chart-bar-stacked</v-icon>
                </div>
                <h3>Ranking</h3>
                <p>Vergleichen und bewerten Sie verschiedene Antworten und ordnen Sie diese nach Qualität.</p>
              </div>

              <div class="feature-card">
                <div class="feature-icon" style="background-color: var(--llars-accent);">
                  <v-icon color="white">mdi-timeline-text-outline</v-icon>
                </div>
                <h3>Verlaufsbewertung</h3>
                <p>Bewerten Sie komplette KI-generierte Mail-Verläufe und analysieren Sie deren Qualität.</p>
              </div>

              <div class="feature-card">
                <div class="feature-icon" style="background-color: var(--llars-secondary);">
                  <v-icon color="white">mdi-robot</v-icon>
                </div>
                <h3>Chatbot</h3>
                <LTag variant="warning" size="small">Alpha</LTag>
                <p>Interagieren Sie direkt mit LLars und testen Sie verschiedene Konversationsszenarien.</p>
              </div>

              <div class="feature-card">
                <div class="feature-icon" style="background-color: #98d4bb;">
                  <v-icon color="white">mdi-text-search</v-icon>
                </div>
                <h3>Prompt Engineering</h3>
                <LTag variant="info" size="small">Beta</LTag>
                <p>Entwickeln Sie kollaborativ Prompts mit Echtzeit-Synchronisation über Yjs.</p>
              </div>

              <div class="feature-card">
                <div class="feature-icon" style="background-color: #a8c5e2;">
                  <v-icon color="white">mdi-compare-horizontal</v-icon>
                </div>
                <h3>Gegenüberstellung</h3>
                <p>Vergleichen Sie zwei KI-Modelle direkt nebeneinander und bewerten Sie die Qualität.</p>
              </div>

              <div class="feature-card">
                <div class="feature-icon" style="background-color: #e8a087;">
                  <v-icon color="white">mdi-shield-account</v-icon>
                </div>
                <h3>Admin-Dashboard</h3>
                <p>Verwalten Sie Benutzer, überwachen Sie Fortschritte und konfigurieren Sie Einstellungen.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 3. Architektur -->
        <section id="architecture" class="docs-section">
          <div class="section-header">
            <span class="section-number">03</span>
            <h2>Architektur</h2>
          </div>
          <div class="section-body">
            <p>LLARS basiert auf einer modernen Microservices-Architektur:</p>

            <div class="tech-stack">
              <div class="tech-category">
                <h4>
                  <v-icon size="18">mdi-monitor</v-icon>
                  Frontend
                </h4>
                <ul>
                  <li><LTag variant="primary" size="small">Vue.js 3</LTag> Composition API</li>
                  <li><LTag variant="secondary" size="small">Vuetify 3</LTag> UI-Library</li>
                  <li><LTag variant="accent" size="small">Vite</LTag> Build-Tool</li>
                  <li><LTag variant="info" size="small">Yjs</LTag> Echtzeit-Kollaboration</li>
                </ul>
              </div>

              <div class="tech-category">
                <h4>
                  <v-icon size="18">mdi-server</v-icon>
                  Backend
                </h4>
                <ul>
                  <li><LTag variant="primary" size="small">Flask</LTag> Python Framework</li>
                  <li><LTag variant="secondary" size="small">MariaDB</LTag> Datenbank</li>
                  <li><LTag variant="accent" size="small">SQLAlchemy</LTag> ORM</li>
                  <li><LTag variant="info" size="small">Authentik</LTag> OIDC Auth</li>
                </ul>
              </div>
            </div>

            <h4 class="subsection-title">Services</h4>
            <div class="services-table">
              <div class="service-row header">
                <span>Service</span>
                <span>Port</span>
                <span>Beschreibung</span>
              </div>
              <div class="service-row">
                <span><code>nginx-service</code></span>
                <span>80</span>
                <span>Reverse Proxy & Load Balancer</span>
              </div>
              <div class="service-row">
                <span><code>frontend-vue-service</code></span>
                <span>5173</span>
                <span>Vue.js Frontend</span>
              </div>
              <div class="service-row">
                <span><code>backend-flask-service</code></span>
                <span>8081</span>
                <span>Flask REST API</span>
              </div>
              <div class="service-row">
                <span><code>db-maria-service</code></span>
                <span>3310</span>
                <span>MariaDB Datenbank</span>
              </div>
              <div class="service-row">
                <span><code>yjs-service</code></span>
                <span>8082</span>
                <span>WebSocket Server für Echtzeit</span>
              </div>
            </div>

            <div class="warning-card">
              <v-icon color="warning" size="20">mdi-alert</v-icon>
              <div>
                <strong>Wichtig</strong>
                <p>Alle Services werden über Docker Compose orchestriert.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 4. Installation & Setup -->
        <section id="installation" class="docs-section">
          <div class="section-header">
            <span class="section-number">04</span>
            <h2>Installation & Setup</h2>
          </div>
          <div class="section-body">
            <h4 class="subsection-title">Voraussetzungen</h4>
            <div class="requirements-grid">
              <div class="requirement-item">
                <v-icon size="20" color="primary">mdi-docker</v-icon>
                <span>Docker & Docker Compose</span>
              </div>
              <div class="requirement-item">
                <v-icon size="20" color="primary">mdi-git</v-icon>
                <span>Git</span>
              </div>
              <div class="requirement-item">
                <v-icon size="20" color="primary">mdi-memory</v-icon>
                <span>Mindestens 8 GB RAM</span>
              </div>
              <div class="requirement-item">
                <v-icon size="20" color="primary">mdi-harddisk</v-icon>
                <span>~10 GB Speicherplatz</span>
              </div>
            </div>

            <h4 class="subsection-title">Installation</h4>
            <div class="code-block">
              <div class="code-header">
                <span>Terminal</span>
                <button class="copy-btn" @click="copyCode('install')">
                  <v-icon size="16">mdi-content-copy</v-icon>
                </button>
              </div>
              <pre><code id="install"># Repository klonen
git clone &lt;repository-url&gt;
cd llars

# .env Datei erstellen
cp .env.template.development .env

# Docker Container starten
./start_llars.sh

# Logs verfolgen
docker compose logs -f</code></pre>
            </div>

            <h4 class="subsection-title">Erster Start</h4>
            <ol class="numbered-list">
              <li>Warten Sie, bis alle Services hochgefahren sind (ca. 5-10 Minuten)</li>
              <li>Öffnen Sie <code>http://localhost:55080</code> im Browser</li>
              <li>Melden Sie sich mit den Standard-Zugangsdaten an</li>
            </ol>

            <div class="success-card">
              <v-icon color="success" size="20">mdi-lightbulb</v-icon>
              <div>
                <strong>Tipp</strong>
                <p>Verwenden Sie <code>docker compose ps</code> um den Status aller Services zu überprüfen.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 5. Authentifizierung -->
        <section id="authentication" class="docs-section">
          <div class="section-header">
            <span class="section-number">05</span>
            <h2>Authentifizierung</h2>
          </div>
          <div class="section-body">
            <p>
              LLARS nutzt <strong>Authentik</strong> für die Authentifizierung (OIDC Authorization Code Flow).
              Dies ermöglicht eine nahtlose Anmeldung direkt in der LLARS-Oberfläche.
            </p>

            <h4 class="subsection-title">Benutzerrollen</h4>
            <div class="roles-grid">
              <div class="role-card">
                <LTag variant="info" prepend-icon="mdi-account">User</LTag>
                <p>Zugriff auf alle Standard-Funktionen (Ranking, Rating, Chatbot, etc.)</p>
              </div>
              <div class="role-card">
                <LTag variant="danger" prepend-icon="mdi-shield-crown">Admin</LTag>
                <p>Zusätzlich Zugriff auf Admin-Dashboard und Benutzerverwaltung</p>
              </div>
            </div>

            <h4 class="subsection-title">Token-Verwaltung</h4>
            <p>Authentifizierungs-Tokens werden sicher in <code>sessionStorage</code> gespeichert:</p>
            <ul class="token-list">
              <li><code>auth_token</code> — Access Token (JWT)</li>
              <li><code>auth_refreshToken</code> — Refresh Token</li>
              <li><code>auth_idToken</code> — ID Token</li>
            </ul>

            <div class="info-card">
              <v-icon color="info" size="20">mdi-shield-check</v-icon>
              <div>
                <strong>Sicherheit</strong>
                <p>Bei Inaktivität oder ungültigen Tokens werden Sie automatisch ausgeloggt.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 6. Module & Funktionen -->
        <section id="modules" class="docs-section">
          <div class="section-header">
            <span class="section-number">06</span>
            <h2>Module & Funktionen</h2>
          </div>
          <div class="section-body">
            <div class="module-accordion">
              <v-expansion-panels variant="accordion">
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="module-title">
                      <v-icon>mdi-chart-bar-stacked</v-icon>
                      <span>Ranking</span>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <p>
                      Das Ranking-Modul ermöglicht es Ihnen, verschiedene KI-generierte Antworten zu vergleichen
                      und nach Qualität zu ordnen.
                    </p>
                    <h5>Verwendung:</h5>
                    <ol>
                      <li>Navigieren Sie zu "Ranking" auf der Startseite</li>
                      <li>Wählen Sie ein Ranking-Projekt aus</li>
                      <li>Bewerten Sie die Antworten durch Drag & Drop</li>
                      <li>Speichern Sie Ihre Rankings</li>
                    </ol>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="module-title">
                      <v-icon>mdi-timeline-text-outline</v-icon>
                      <span>Verlaufsbewertung</span>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <p>
                      Bewerten Sie komplette E-Mail-Verläufe, die von KI-Systemen generiert wurden.
                    </p>
                    <h5>Bewertungskriterien:</h5>
                    <ul>
                      <li>Empathie und Einfühlungsvermögen</li>
                      <li>Fachliche Korrektheit</li>
                      <li>Sprachliche Qualität</li>
                      <li>Hilfreiche Informationen</li>
                    </ul>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="module-title">
                      <v-icon>mdi-robot</v-icon>
                      <span>Chatbot</span>
                      <LTag variant="warning" size="small" class="ml-2">Alpha</LTag>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <p>
                      Der integrierte Chatbot ermöglicht direkte Interaktion mit LLARS.
                      Testen Sie verschiedene Prompts und analysieren Sie die Antwortqualität.
                    </p>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="module-title">
                      <v-icon>mdi-text-search</v-icon>
                      <span>Prompt Engineering</span>
                      <LTag variant="info" size="small" class="ml-2">Beta</LTag>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <p>
                      Das Prompt Engineering Modul nutzt Yjs für kollaboratives Arbeiten in Echtzeit.
                    </p>
                    <h5>Features:</h5>
                    <ul>
                      <li><strong>Echtzeit-Synchronisation:</strong> Änderungen werden sofort übertragen</li>
                      <li><strong>Versionshistorie:</strong> Alle Änderungen werden protokolliert</li>
                      <li><strong>Visuelle Editoren:</strong> Graph-basierte Prompt-Entwicklung</li>
                      <li><strong>Template-Bibliothek:</strong> Vorgefertigte Prompt-Templates</li>
                    </ul>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="module-title">
                      <v-icon>mdi-compare-horizontal</v-icon>
                      <span>Gegenüberstellung</span>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <p>
                      Vergleichen Sie zwei verschiedene KI-Modelle direkt nebeneinander.
                    </p>
                    <h5>Workflow:</h5>
                    <ol>
                      <li>Erstellen Sie eine neue Vergleichs-Session</li>
                      <li>Wählen Sie zwei KI-Modelle aus</li>
                      <li>Geben Sie eine Persona und ein Szenario ein</li>
                      <li>Starten Sie die Konversation</li>
                      <li>Bewerten Sie die Antworten beider Modelle</li>
                    </ol>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
          </div>
        </section>

        <!-- 7. API-Referenz -->
        <section id="api" class="docs-section">
          <div class="section-header">
            <span class="section-number">07</span>
            <h2>API-Referenz</h2>
          </div>
          <div class="section-body">
            <p>LLARS bietet eine REST-API für die Integration in andere Systeme.</p>

            <h4 class="subsection-title">Base URL</h4>
            <div class="code-block small">
              <pre><code>http://localhost:55080/api</code></pre>
            </div>

            <h4 class="subsection-title">Authentifizierung</h4>
            <p>Alle API-Anfragen benötigen einen Bearer Token:</p>
            <div class="code-block small">
              <pre><code>Authorization: Bearer &lt;access_token&gt;</code></pre>
            </div>

            <h4 class="subsection-title">Wichtige Endpoints</h4>
            <div class="api-table">
              <div class="api-row header">
                <span>Endpoint</span>
                <span>Methode</span>
                <span>Beschreibung</span>
              </div>
              <div class="api-row">
                <code>/api/email_threads/rankings</code>
                <LTag variant="primary" size="small">GET</LTag>
                <span>Ranking-Threads abrufen</span>
              </div>
              <div class="api-row">
                <code>/api/email_threads/ratings</code>
                <LTag variant="primary" size="small">GET</LTag>
                <span>Rating-Threads abrufen</span>
              </div>
              <div class="api-row">
                <code>/api/save_ranking/:id</code>
                <LTag variant="success" size="small">POST</LTag>
                <span>Ranking speichern</span>
              </div>
              <div class="api-row">
                <code>/api/judge/sessions</code>
                <LTag variant="primary" size="small">GET</LTag>
                <span>Judge-Sessions abrufen</span>
              </div>
              <div class="api-row">
                <code>/api/chatbots</code>
                <LTag variant="primary" size="small">GET</LTag>
                <span>Chatbots auflisten</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 8. Troubleshooting -->
        <section id="troubleshooting" class="docs-section">
          <div class="section-header">
            <span class="section-number">08</span>
            <h2>Troubleshooting</h2>
          </div>
          <div class="section-body">
            <h4 class="subsection-title">Häufige Probleme</h4>

            <v-expansion-panels variant="accordion" class="troubleshoot-panels">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon color="warning" class="mr-2">mdi-alert-circle</v-icon>
                  Services starten nicht
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <ul>
                    <li>Überprüfen Sie die Docker-Logs: <code>docker compose logs</code></li>
                    <li>Stellen Sie sicher, dass alle Ports frei sind</li>
                    <li>Prüfen Sie die <code>.env</code> Datei</li>
                    <li>Neustart: <code>docker compose down && docker compose up -d</code></li>
                  </ul>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon color="warning" class="mr-2">mdi-alert-circle</v-icon>
                  Anmeldung schlägt fehl
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <ul>
                    <li>Überprüfen Sie, ob Authentik läuft</li>
                    <li>Löschen Sie den Browser-Cache und sessionStorage</li>
                    <li>Prüfen Sie die Authentik-Konfiguration</li>
                  </ul>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon color="warning" class="mr-2">mdi-alert-circle</v-icon>
                  Datenbank-Verbindungsfehler
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <ul>
                    <li>Warten Sie, bis die Datenbank gestartet ist (Healthcheck)</li>
                    <li>Prüfen Sie die Datenbank-Credentials in <code>.env</code></li>
                    <li>Logs prüfen: <code>docker compose logs db-maria-service</code></li>
                  </ul>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>

            <h4 class="subsection-title">Logs analysieren</h4>
            <div class="code-block">
              <pre><code># Alle Service-Logs
docker compose logs -f

# Nur Backend
docker compose logs -f backend-flask-service

# Letzte 100 Zeilen
docker compose logs --tail=100</code></pre>
            </div>
          </div>
        </section>

        <!-- 9. Kontakt & Support -->
        <section id="contact" class="docs-section">
          <div class="section-header">
            <span class="section-number">09</span>
            <h2>Kontakt & Support</h2>
          </div>
          <div class="section-body">
            <p>Bei Fragen, Problemen oder Feedback wenden Sie sich bitte an:</p>

            <div class="contact-grid">
              <a href="mailto:info@e-beratungsinstitut.de" class="contact-card">
                <v-icon size="32" color="primary">mdi-email</v-icon>
                <h4>E-Mail</h4>
                <p>info@e-beratungsinstitut.de</p>
              </a>
              <a href="https://www.e-beratungsinstitut.de" target="_blank" class="contact-card">
                <v-icon size="32" color="accent">mdi-web</v-icon>
                <h4>Website</h4>
                <p>www.e-beratungsinstitut.de</p>
              </a>
            </div>

            <div class="success-card mt-6">
              <v-icon color="success" size="20">mdi-open-source-initiative</v-icon>
              <div>
                <strong>Open Source</strong>
                <p>LLARS ist ein Open-Source-Projekt der Technischen Hochschule Nürnberg.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Footer -->
        <div class="docs-footer">
          <p>
            Letzte Aktualisierung: {{ new Date().toLocaleDateString('de-DE') }}
            <span class="separator">•</span>
            Version 2.9
          </p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';

const activeSection = ref('overview');

// MkDocs URL aus Umgebungsvariable oder Fallback
const mkdocsUrl = computed(() => {
  return import.meta.env.VITE_MKDOCS_URL || 'http://localhost:55800';
});

// Intersection Observer for active section tracking
let observer = null;

onMounted(() => {
  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Track active section
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          activeSection.value = entry.target.id;
        }
      });
    },
    { rootMargin: '-20% 0px -80% 0px' }
  );

  document.querySelectorAll('.docs-section').forEach((section) => {
    observer.observe(section);
  });
});

onUnmounted(() => {
  if (observer) {
    observer.disconnect();
  }
});

const copyCode = (id) => {
  const code = document.getElementById(id);
  if (code) {
    navigator.clipboard.writeText(code.textContent);
  }
};
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
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 2.5rem;
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

/* Container Layout */
.docs-container {
  display: flex;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  gap: 32px;
}

/* Sidebar */
.docs-sidebar {
  width: 280px;
  flex-shrink: 0;
  position: sticky;
  top: 88px;
  height: fit-content;
}

.sidebar-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}

.toc-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toc-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px 2px 8px 2px;
  text-decoration: none;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.toc-link:hover {
  background: rgba(176, 202, 151, 0.15);
  color: var(--llars-primary);
}

.toc-link.active {
  background: var(--llars-primary);
  color: white;
}

.toc-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px 2px 6px 2px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  font-size: 0.75rem;
  font-weight: 600;
}

.toc-link.active .toc-number {
  background: rgba(255, 255, 255, 0.3);
}

.sidebar-links {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  text-decoration: none;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.85rem;
  transition: all 0.2s ease;
}

.sidebar-link:hover {
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: var(--llars-primary);
}

/* Main Content */
.docs-content {
  flex: 1;
  min-width: 0;
}

.docs-section {
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.section-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--llars-primary);
  opacity: 0.6;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.section-body {
  padding: 24px;
}

.section-body p {
  line-height: 1.8;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 16px;
}

.subsection-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 24px 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Info/Warning/Success Cards */
.info-card, .warning-card, .success-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 12px 4px 12px 4px;
  margin: 16px 0;
}

.info-card {
  background: rgba(168, 197, 226, 0.15);
  border-left: 3px solid #a8c5e2;
}

.warning-card {
  background: rgba(232, 200, 122, 0.15);
  border-left: 3px solid #e8c87a;
}

.success-card {
  background: rgba(152, 212, 187, 0.15);
  border-left: 3px solid #98d4bb;
}

.info-card p, .warning-card p, .success-card p {
  margin: 4px 0 0 0;
  font-size: 0.9rem;
}

/* Feature Grid */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.feature-card {
  padding: 20px;
  border-radius: 12px 4px 12px 4px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  transition: all 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px 4px 12px 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.feature-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  line-height: 1.6;
  margin: 0;
}

/* Tech Stack */
.tech-stack {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.tech-category {
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 12px 4px 12px 4px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.tech-category h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.tech-category ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tech-category li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Services Table */
.services-table, .api-table {
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  margin: 16px 0;
}

.service-row, .api-row {
  display: grid;
  grid-template-columns: 1fr 80px 2fr;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  align-items: center;
  gap: 12px;
}

.service-row:last-child, .api-row:last-child {
  border-bottom: none;
}

.service-row.header, .api-row.header {
  background: rgba(var(--v-theme-on-surface), 0.05);
  font-weight: 600;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Requirements Grid */
.requirements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin: 16px 0;
}

.requirement-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px 2px 8px 2px;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Code Blocks */
.code-block {
  background: #1e1e1e;
  border-radius: 12px 4px 12px 4px;
  margin: 16px 0;
  overflow: hidden;
}

.code-block.small {
  margin: 8px 0;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  font-size: 0.75rem;
  color: #888;
}

.copy-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #888;
  padding: 4px;
  border-radius: 4px;
}

.copy-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
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

/* Numbered List */
.numbered-list {
  counter-reset: list-counter;
  list-style: none;
  padding: 0;
  margin: 16px 0;
}

.numbered-list li {
  counter-increment: list-counter;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.numbered-list li::before {
  content: counter(list-counter);
  min-width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--llars-primary);
  color: white;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.75rem;
  font-weight: 600;
}

/* Roles Grid */
.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
  margin: 16px 0;
}

.role-card {
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 12px 4px 12px 4px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.role-card p {
  margin: 8px 0 0 0;
  font-size: 0.9rem;
}

/* Token List */
.token-list {
  list-style: none;
  padding: 0;
  margin: 12px 0;
}

.token-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.token-list code {
  background: rgba(var(--v-theme-on-surface), 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--llars-danger);
}

/* Module Accordion */
.module-accordion {
  margin: 16px 0;
}

.module-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Troubleshoot Panels */
.troubleshoot-panels {
  margin: 16px 0;
}

/* Contact Grid */
.contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin: 20px 0;
}

.contact-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 24px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 16px 4px 16px 4px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
}

.contact-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: var(--llars-primary);
}

.contact-card h4 {
  margin: 12px 0 4px 0;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.contact-card p {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Footer */
.docs-footer {
  text-align: center;
  padding: 24px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.85rem;
}

.docs-footer .separator {
  margin: 0 8px;
}

/* Inline Code */
code {
  background: rgba(var(--v-theme-on-surface), 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85rem;
  color: var(--llars-danger);
}

/* Responsive */
@media (max-width: 1024px) {
  .docs-sidebar {
    display: none;
  }

  .docs-container {
    padding: 16px;
  }
}

@media (max-width: 600px) {
  .hero-title {
    font-size: 1.75rem;
  }

  .hero-subtitle {
    font-size: 1rem;
  }

  .section-header {
    padding: 16px;
  }

  .section-body {
    padding: 16px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .service-row, .api-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .service-row.header, .api-row.header {
    display: none;
  }
}
</style>
