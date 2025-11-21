<template>
  <v-container class="mt-5 documentation">
    <v-row justify="center">
      <v-col cols="12" md="10">
        <h1>LLars Dokumentation</h1>
        <p class="subtitle">Learning & Labeling AI Rating System</p>
        <v-divider class="my-4"></v-divider>

        <!-- Table of Contents -->
        <v-card class="mb-6 pa-4" elevation="2">
          <h2>Inhaltsverzeichnis</h2>
          <ul class="toc">
            <li><a href="#overview">1. Überblick</a></li>
            <li><a href="#features">2. Funktionen</a></li>
            <li><a href="#architecture">3. Architektur</a></li>
            <li><a href="#installation">4. Installation & Setup</a></li>
            <li><a href="#authentication">5. Authentifizierung</a></li>
            <li><a href="#modules">6. Module & Funktionen</a>
              <ul>
                <li><a href="#ranking">6.1 Ranking</a></li>
                <li><a href="#history-rating">6.2 Verlaufsbewertung</a></li>
                <li><a href="#chatbot">6.3 Chatbot</a></li>
                <li><a href="#prompt-engineering">6.4 Prompt Engineering</a></li>
                <li><a href="#comparison">6.5 Gegenüberstellung</a></li>
              </ul>
            </li>
            <li><a href="#api">7. API-Referenz</a></li>
            <li><a href="#troubleshooting">8. Troubleshooting</a></li>
            <li><a href="#contact">9. Kontakt & Support</a></li>
          </ul>
        </v-card>

        <!-- 1. Überblick -->
        <section id="overview">
          <h2>1. Überblick</h2>
          <p>
            LLars (Learning & Labeling AI Rating System) ist eine umfassende Plattform zur Bewertung,
            Analyse und Verbesserung von KI-generierten Inhalten, insbesondere im Kontext der
            E-Beratung und digitalen Kommunikation.
          </p>
          <p>
            Das System wurde entwickelt, um Forschern, Entwicklern und Beratern die Möglichkeit zu geben,
            KI-Modelle systematisch zu evaluieren, zu vergleichen und zu optimieren.
          </p>
          <v-alert type="info" class="my-4">
            <strong>Zielgruppe:</strong> Forscher, KI-Entwickler, E-Berater, Datenwissenschaftler
          </v-alert>
        </section>

        <!-- 2. Funktionen -->
        <section id="features">
          <h2>2. Funktionen</h2>
          <v-row>
            <v-col cols="12" md="6">
              <v-card class="pa-4 mb-4" elevation="1">
                <h3><v-icon>mdi-chart-bar-stacked</v-icon> Ranking</h3>
                <p>Vergleichen und bewerten Sie verschiedene Antworten und ordnen Sie diese nach Qualität.</p>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="pa-4 mb-4" elevation="1">
                <h3><v-icon>mdi-timeline-text-outline</v-icon> Verlaufsbewertung</h3>
                <p>Bewerten Sie komplette KI-generierte Mail-Verläufe und analysieren Sie deren Qualität.</p>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="pa-4 mb-4" elevation="1">
                <h3><v-icon>mdi-laptop-account</v-icon> Chatbot (Alpha)</h3>
                <p>Interagieren Sie direkt mit LLars und testen Sie verschiedene Konversationsszenarien.</p>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="pa-4 mb-4" elevation="1">
                <h3><v-icon>mdi-text-search</v-icon> Prompt Engineering (Beta)</h3>
                <p>Entwickeln Sie kollaborativ Prompts mit Echtzeit-Synchronisation über Yjs.</p>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="pa-4 mb-4" elevation="1">
                <h3><v-icon>mdi-compare-horizontal</v-icon> Gegenüberstellung</h3>
                <p>Vergleichen Sie zwei KI-Modelle direkt nebeneinander und bewerten Sie die Qualität der Antworten.</p>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="pa-4 mb-4" elevation="1">
                <h3><v-icon>mdi-shield-account</v-icon> Admin-Dashboard</h3>
                <p>Verwalten Sie Benutzer, überwachen Sie Fortschritte und konfigurieren Sie Systemeinstellungen.</p>
              </v-card>
            </v-col>
          </v-row>
        </section>

        <!-- 3. Architektur -->
        <section id="architecture">
          <h2>3. Architektur</h2>
          <p>LLars basiert auf einer modernen Microservices-Architektur:</p>

          <h3>Frontend</h3>
          <ul>
            <li><strong>Framework:</strong> Vue.js 3 (Composition API)</li>
            <li><strong>UI-Library:</strong> Vuetify 3</li>
            <li><strong>Build-Tool:</strong> Vite</li>
            <li><strong>Echtzeit-Kollaboration:</strong> Yjs für kollaboratives Prompt Engineering</li>
          </ul>

          <h3>Backend</h3>
          <ul>
            <li><strong>Framework:</strong> Flask (Python)</li>
            <li><strong>Datenbank:</strong> MariaDB</li>
            <li><strong>ORM:</strong> SQLAlchemy</li>
            <li><strong>Authentifizierung:</strong> Keycloak 26.0.7 (OpenID Connect)</li>
          </ul>

          <h3>Services</h3>
          <v-simple-table class="my-4">
            <template v-slot:default>
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Port</th>
                  <th>Beschreibung</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>nginx-service</td>
                  <td>80</td>
                  <td>Reverse Proxy & Load Balancer</td>
                </tr>
                <tr>
                  <td>frontend-vue-service</td>
                  <td>5173</td>
                  <td>Vue.js Frontend</td>
                </tr>
                <tr>
                  <td>backend-flask-service</td>
                  <td>8081</td>
                  <td>Flask REST API</td>
                </tr>
                <tr>
                  <td>db-maria-service</td>
                  <td>3310</td>
                  <td>MariaDB Datenbank</td>
                </tr>
                <tr>
                  <td>yjs-service</td>
                  <td>8082</td>
                  <td>Yjs WebSocket Server für Echtzeit-Kollaboration</td>
                </tr>
                <tr>
                  <td>backend-supervisor-service</td>
                  <td>-</td>
                  <td>Hintergrund-Aufgaben & Seeding</td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>

          <v-alert type="warning" class="my-4">
            <strong>Wichtig:</strong> Alle Services werden über Docker Compose orchestriert.
          </v-alert>
        </section>

        <!-- 4. Installation & Setup -->
        <section id="installation">
          <h2>4. Installation & Setup</h2>

          <h3>Voraussetzungen</h3>
          <ul>
            <li>Docker & Docker Compose</li>
            <li>Git</li>
            <li>Mindestens 8 GB RAM</li>
            <li>Freier Speicherplatz: ~10 GB</li>
          </ul>

          <h3>Installation</h3>
          <v-card class="code-block pa-4 my-4" color="#1e1e1e" dark>
            <pre><code># Repository klonen
git clone &lt;repository-url&gt;
cd llars

# .env Datei erstellen
cp .env.example .env

# .env Datei anpassen
# Wichtig: MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, KEYCLOAK Einstellungen

# Docker Container starten
docker compose up -d --build

# Logs verfolgen
docker compose logs -f</code></pre>
          </v-card>

          <h3>Erster Start</h3>
          <ol>
            <li>Warten Sie, bis alle Services hochgefahren sind (ca. 5-10 Minuten)</li>
            <li>Öffnen Sie <code>http://localhost</code> im Browser</li>
            <li>Bei der ersten Anmeldung wird ein Admin-Benutzer erstellt</li>
          </ol>

          <v-alert type="success" class="my-4">
            <strong>Tipp:</strong> Verwenden Sie <code>docker compose ps</code> um den Status aller Services zu überprüfen.
          </v-alert>
        </section>

        <!-- 5. Authentifizierung -->
        <section id="authentication">
          <h2>5. Authentifizierung</h2>
          <p>
            LLars verwendet Keycloak für die Authentifizierung mit dem Resource Owner Password Credentials Flow
            (Direct Access Grant). Dies ermöglicht eine nahtlose Anmeldung direkt in der LLars-Oberfläche.
          </p>

          <h3>Anmeldung</h3>
          <ol>
            <li>Öffnen Sie die LLars-Startseite</li>
            <li>Geben Sie Ihren Benutzernamen und Ihr Passwort ein</li>
            <li>Klicken Sie auf "Anmelden"</li>
          </ol>

          <h3>Benutzerrollen</h3>
          <ul>
            <li><strong>User:</strong> Zugriff auf alle Standard-Funktionen (Ranking, Rating, etc.)</li>
            <li><strong>Admin:</strong> Zusätzlich Zugriff auf Admin-Dashboard und Benutzerverwaltung</li>
          </ul>

          <h3>Token-Verwaltung</h3>
          <p>
            Authentifizierungs-Tokens werden sicher in <code>sessionStorage</code> gespeichert:
          </p>
          <ul>
            <li><code>kc_token</code> - Access Token (JWT)</li>
            <li><code>kc_refreshToken</code> - Refresh Token</li>
            <li><code>kc_idToken</code> - ID Token</li>
          </ul>

          <v-alert type="info" class="my-4">
            <strong>Sicherheit:</strong> Bei Inaktivität oder ungültigen Tokens werden Sie automatisch ausgeloggt.
          </v-alert>
        </section>

        <!-- 6. Module & Funktionen -->
        <section id="modules">
          <h2>6. Module & Funktionen</h2>

          <!-- 6.1 Ranking -->
          <div id="ranking">
            <h3>6.1 Ranking</h3>
            <p>
              Das Ranking-Modul ermöglicht es Ihnen, verschiedene KI-generierte Antworten zu vergleichen
              und nach Qualität zu ordnen.
            </p>
            <h4>Verwendung:</h4>
            <ol>
              <li>Navigieren Sie zu "Ranking" auf der Startseite</li>
              <li>Wählen Sie ein Ranking-Projekt aus oder erstellen Sie ein neues</li>
              <li>Bewerten Sie die präsentierten Antworten durch Drag & Drop</li>
              <li>Speichern Sie Ihre Rankings</li>
            </ol>
          </div>

          <!-- 6.2 Verlaufsbewertung -->
          <div id="history-rating">
            <h3>6.2 Verlaufsbewertung</h3>
            <p>
              Bewerten Sie komplette E-Mail-Verläufe, die von KI-Systemen generiert wurden.
              Dies ist besonders relevant für die Evaluierung von E-Beratungs-Szenarien.
            </p>
            <h4>Bewertungskriterien:</h4>
            <ul>
              <li>Empathie und Einfühlungsvermögen</li>
              <li>Fachliche Korrektheit</li>
              <li>Sprachliche Qualität</li>
              <li>Hilfreiche Informationen</li>
              <li>Angemessener Ton und Stil</li>
            </ul>
          </div>

          <!-- 6.3 Chatbot -->
          <div id="chatbot">
            <h3>6.3 Chatbot (Alpha)</h3>
            <p>
              Der integrierte Chatbot ermöglicht direkte Interaktion mit LLars.
              Testen Sie verschiedene Prompts und analysieren Sie die Antwortqualität.
            </p>
            <v-alert type="warning" class="my-4">
              <strong>Alpha-Version:</strong> Diese Funktion befindet sich noch in der Entwicklung.
            </v-alert>
          </div>

          <!-- 6.4 Prompt Engineering -->
          <div id="prompt-engineering">
            <h3>6.4 Prompt Engineering (Beta)</h3>
            <p>
              Das Prompt Engineering Modul nutzt Yjs für kollaboratives Arbeiten in Echtzeit.
              Mehrere Benutzer können gleichzeitig an Prompts arbeiten.
            </p>
            <h4>Features:</h4>
            <ul>
              <li><strong>Echtzeit-Synchronisation:</strong> Änderungen werden sofort an alle Teilnehmer übertragen</li>
              <li><strong>Versionshistorie:</strong> Alle Änderungen werden protokolliert</li>
              <li><strong>Visuelle Editoren:</strong> Graph-basierte Prompt-Entwicklung</li>
              <li><strong>Template-Bibliothek:</strong> Vorgefertigte Prompt-Templates</li>
            </ul>
          </div>

          <!-- 6.5 Gegenüberstellung -->
          <div id="comparison">
            <h3>6.5 Gegenüberstellung</h3>
            <p>
              Vergleichen Sie zwei verschiedene KI-Modelle direkt nebeneinander.
              Beide Modelle erhalten dieselben Eingaben, und Sie können die Antworten bewerten.
            </p>
            <h4>Workflow:</h4>
            <ol>
              <li>Erstellen Sie eine neue Vergleichs-Session</li>
              <li>Wählen Sie zwei KI-Modelle aus</li>
              <li>Geben Sie eine Persona und ein Szenario ein</li>
              <li>Starten Sie die Konversation</li>
              <li>Bewerten Sie die Antworten beider Modelle</li>
              <li>Analysieren Sie die Ergebnisse</li>
            </ol>
          </div>
        </section>

        <!-- 7. API-Referenz -->
        <section id="api">
          <h2>7. API-Referenz</h2>
          <p>
            LLars bietet eine REST-API für die Integration in andere Systeme.
          </p>

          <h3>Base URL</h3>
          <v-card class="code-block pa-4 my-4" color="#1e1e1e" dark>
            <pre><code>http://localhost/api</code></pre>
          </v-card>

          <h3>Authentifizierung</h3>
          <p>Alle API-Anfragen benötigen einen Bearer Token im Authorization Header:</p>
          <v-card class="code-block pa-4 my-4" color="#1e1e1e" dark>
            <pre><code>Authorization: Bearer &lt;access_token&gt;</code></pre>
          </v-card>

          <h3>Wichtige Endpoints</h3>
          <v-simple-table class="my-4">
            <template v-slot:default>
              <thead>
                <tr>
                  <th>Endpoint</th>
                  <th>Methode</th>
                  <th>Beschreibung</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>/api/ranking</td>
                  <td>GET</td>
                  <td>Liste aller Rankings abrufen</td>
                </tr>
                <tr>
                  <td>/api/ranking/:id</td>
                  <td>GET</td>
                  <td>Einzelnes Ranking abrufen</td>
                </tr>
                <tr>
                  <td>/api/rating</td>
                  <td>POST</td>
                  <td>Neue Bewertung erstellen</td>
                </tr>
                <tr>
                  <td>/api/history-generation</td>
                  <td>GET</td>
                  <td>Mail-Verläufe abrufen</td>
                </tr>
                <tr>
                  <td>/api/prompt-engineering</td>
                  <td>GET/POST</td>
                  <td>Prompt-Projekte verwalten</td>
                </tr>
                <tr>
                  <td>/api/comparison</td>
                  <td>GET/POST</td>
                  <td>Vergleichs-Sessions verwalten</td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>

          <v-alert type="info" class="my-4">
            <strong>Hinweis:</strong> Detaillierte API-Dokumentation finden Sie unter <code>/api/docs</code> (Swagger UI).
          </v-alert>
        </section>

        <!-- 8. Troubleshooting -->
        <section id="troubleshooting">
          <h2>8. Troubleshooting</h2>

          <h3>Häufige Probleme</h3>

          <v-expansion-panels class="my-4">
            <v-expansion-panel>
              <v-expansion-panel-title>
                Services starten nicht
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p><strong>Lösung:</strong></p>
                <ul>
                  <li>Überprüfen Sie die Docker-Logs: <code>docker compose logs</code></li>
                  <li>Stellen Sie sicher, dass alle Ports frei sind (80, 3310, 8081, 8082, 5173)</li>
                  <li>Prüfen Sie die <code>.env</code> Datei auf fehlende oder fehlerhafte Einträge</li>
                  <li>Stoppen Sie alle Container und starten Sie neu: <code>docker compose down && docker compose up -d --build</code></li>
                </ul>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-title>
                Anmeldung schlägt fehl
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p><strong>Lösung:</strong></p>
                <ul>
                  <li>Überprüfen Sie, ob Keycloak läuft</li>
                  <li>Löschen Sie den Browser-Cache und sessionStorage</li>
                  <li>Prüfen Sie die Keycloak-Konfiguration in der <code>.env</code> Datei</li>
                  <li>Stellen Sie sicher, dass der Benutzer in Keycloak existiert</li>
                </ul>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-title>
                Datenbank-Verbindungsfehler
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p><strong>Lösung:</strong></p>
                <ul>
                  <li>Warten Sie, bis die Datenbank vollständig gestartet ist (Healthcheck)</li>
                  <li>Prüfen Sie die Datenbank-Credentials in der <code>.env</code></li>
                  <li>Überprüfen Sie die MariaDB-Logs: <code>docker compose logs db-maria-service</code></li>
                  <li>Bei Problemen: Datenbank-Volume löschen und neu starten (ACHTUNG: Datenverlust!)</li>
                </ul>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-title>
                Yjs Echtzeit-Synchronisation funktioniert nicht
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p><strong>Lösung:</strong></p>
                <ul>
                  <li>Überprüfen Sie die WebSocket-Verbindung in den Browser-Entwicklertools</li>
                  <li>Prüfen Sie, ob der yjs-service läuft: <code>docker compose ps yjs-service</code></li>
                  <li>Firewall-Einstellungen überprüfen (Port 8082)</li>
                  <li>Browser-Konsole auf WebSocket-Fehler prüfen</li>
                </ul>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-title>
                Beim Navigieren werde ich ausgeloggt
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p><strong>Lösung:</strong></p>
                <ul>
                  <li>Löschen Sie sessionStorage und localStorage im Browser</li>
                  <li>Melden Sie sich erneut an</li>
                  <li>Überprüfen Sie die Token-Gültigkeit (Standard: 5 Minuten Access Token)</li>
                  <li>Browser-Konsole auf Fehler prüfen</li>
                </ul>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <h3>Logs analysieren</h3>
          <v-card class="code-block pa-4 my-4" color="#1e1e1e" dark>
            <pre><code># Alle Service-Logs
docker compose logs -f

# Nur Backend
docker compose logs -f backend-flask-service

# Nur Frontend
docker compose logs -f frontend-vue-service

# Letzte 100 Zeilen
docker compose logs --tail=100</code></pre>
          </v-card>
        </section>

        <!-- 9. Kontakt & Support -->
        <section id="contact">
          <h2>9. Kontakt & Support</h2>
          <p>
            Bei Fragen, Problemen oder Feedback wenden Sie sich bitte an:
          </p>

          <v-row class="my-4">
            <v-col cols="12" md="6">
              <v-card class="pa-4" elevation="2">
                <h3><v-icon>mdi-email</v-icon> E-Mail</h3>
                <p>
                  <a href="mailto:info@e-beratungsinstitut.de">info@e-beratungsinstitut.de</a>
                </p>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="pa-4" elevation="2">
                <h3><v-icon>mdi-web</v-icon> Website</h3>
                <p>
                  <a href="https://www.e-beratungsinstitut.de" target="_blank">www.e-beratungsinstitut.de</a>
                </p>
              </v-card>
            </v-col>
          </v-row>

          <h3>Weitere Informationen</h3>
          <ul>
            <li><router-link to="/Impressum">Impressum</router-link></li>
            <li><router-link to="/Datenschutz">Datenschutz</router-link></li>
            <li><router-link to="/Kontakt">Kontakt</router-link></li>
          </ul>

          <v-alert type="success" class="my-4">
            <strong>Open Source:</strong> LLars ist ein Open-Source-Projekt der Technischen Hochschule Nürnberg.
          </v-alert>
        </section>

        <v-divider class="my-6"></v-divider>

        <p class="text-center text-caption">
          Letzte Aktualisierung: {{ new Date().toLocaleDateString('de-DE') }}<br>
          Version: 1.0.0
        </p>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { onMounted } from 'vue';

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
});
</script>

<style scoped>
.documentation {
  font-family: 'Roboto', sans-serif;
  background-color: rgb(var(--v-theme-background));
  color: rgb(var(--v-theme-on-background));
}

.mt-5 {
  margin-top: 5rem;
}

.subtitle {
  font-size: 1.2rem;
  color: rgba(var(--v-theme-on-background), 0.7);
  margin-bottom: 1rem;
}

section {
  margin-bottom: 3rem;
}

h1 {
  color: rgb(var(--v-theme-primary));
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

h2 {
  color: rgb(var(--v-theme-on-background));
  font-size: 2rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgb(var(--v-theme-primary));
}

h3 {
  color: rgba(var(--v-theme-on-background), 0.9);
  font-size: 1.5rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

h4 {
  color: rgba(var(--v-theme-on-background), 0.8);
  font-size: 1.2rem;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

p {
  margin-bottom: 1rem;
  line-height: 1.8;
  color: rgb(var(--v-theme-on-background));
}

ul, ol {
  margin-bottom: 1rem;
  margin-left: 1.5rem;
  line-height: 1.8;
  color: rgb(var(--v-theme-on-background));
}

li {
  margin-bottom: 0.5rem;
}

.toc {
  list-style: none;
  margin-left: 0;
}

.toc li {
  margin-bottom: 0.75rem;
}

.toc a {
  color: rgb(var(--v-theme-info));
  text-decoration: none;
  font-weight: 500;
}

.toc a:hover {
  text-decoration: underline;
  color: rgb(var(--v-theme-primary));
}

.toc ul {
  margin-left: 1.5rem;
  margin-top: 0.5rem;
}

a {
  color: rgb(var(--v-theme-info));
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
  color: rgb(var(--v-theme-primary));
}

code {
  background-color: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  color: rgb(var(--v-theme-error));
}

.code-block {
  overflow-x: auto;
  border-radius: 4px;
  background-color: rgb(var(--v-theme-surface-variant));
}

.code-block pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
}

.code-block code {
  background-color: transparent;
  color: rgba(var(--v-theme-on-surface), 0.9);
  padding: 0;
}

.v-card h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0;
}

.v-expansion-panel-title {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.v-simple-table {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
}

.v-simple-table th {
  background-color: rgb(var(--v-theme-surface-variant));
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.v-simple-table td {
  color: rgba(var(--v-theme-on-surface), 0.8);
}

@media (max-width: 960px) {
  h1 {
    font-size: 2rem;
  }

  h2 {
    font-size: 1.5rem;
  }

  h3 {
    font-size: 1.25rem;
  }
}
</style>
