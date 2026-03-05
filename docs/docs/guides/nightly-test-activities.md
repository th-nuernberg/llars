# Nightly Test Activities

Diese Seite beschreibt die konkreten Aktivitäten, die im Nightly-Lauf automatisiert geprueft werden.

## Ziel

Vor jedem produktiven Umschalten der Blue-Green-Deploymentfarbe wird geprueft, dass zentrale Nutzerinteraktionen sowie Cross-Role-Uebergaben weiterhin funktionieren.

---

## Kachel-Aktivitaeten (Tile-by-Tile)

### Prompt Engineering

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| PE-CREATE-001 | Neues Prompt anlegen | Prompt-Karte erscheint in der Liste |
| PE-BLOCK-001 | Block anlegen und Text bearbeiten | Block mit Inhalt sichtbar |
| PE-TEST-001 | Test-Dialog starten | LLM-Antwort wird angezeigt |
| PE-EXPORT-001 | Prompt als JSON exportieren | Datei-Download startet |
| PE-IMPORT-001 | Prompt-Bloecke aus JSON importieren | Importierter Block in der Liste |
| PE-SHARE-001 | Prompt fuer Evaluator freigeben | Evaluator in Shared-Liste sichtbar |
| PE-SHARED-VISIBLE-001 | Geteiltes Prompt als Evaluator oeffnen | Prompt oeffnet sich im Detail-View |
| PE-UNSHARE-001 | Freigabe wieder entfernen | Evaluator verschwindet aus Shared-Liste |
| PE-CLEANUP-001 | Test-Prompt loeschen | Kein Test-Artefakt verbleibt |

### Batch Generation

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| BG-WIZ-ENTRY-001 | Generation Hub oeffnen, Wizard-Einstieg pruefen | Neuer-Job-Button und Wizard sichtbar |
| BG-WIZ-HANDOFF-001 | Uebergang zum Szenario Wizard pruefen | Wizard/Scenario-Handoff erreichbar |

### Scenario Manager

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| SCN-ASSIGN-SETUP-001 | Nightly-Test-Szenario per API erzeugen | Szenario-ID zurueckgegeben |
| SCN-ASSIGN-INVITE-001 | Evaluator per UI einladen | Evaluator in Member-Karte sichtbar |
| SCN-ASSIGN-ROLE-001 | Rolle im Team-Tab aendern | Rollenbezeichnung aktualisiert sich |
| SCN-ASSIGN-VISIBLE-001 | Einladung als Evaluator sehen und annehmen | Einladungskarte mit Accept-Button |
| SCN-ASSIGN-EVAL-001 | Evaluator springt in die Evaluation | Evaluation-Route wird erreicht |
| SCN-ASSIGN-CLEANUP-001 | Nightly-Szenario loeschen | Kein Test-Artefakt verbleibt |

### LaTeX Collab

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| LTX-RESIZE-001 | Resizer per Drag ziehen | Divider-Position verschiebt sich messbar |

### Conference Manager

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| CONF-REQ-SETUP-001 | Nightly-Forschungsgruppe anlegen | Gruppen-ID zurueckgegeben |
| CONF-REQ-SUBMIT-001 | Access-Request als Researcher senden | Erfolgsmeldung angezeigt |
| CONF-REQ-VISIBLE-001 | Request im Members-Bereich sichtbar | Zeile mit Researcher-Username |
| CONF-REQ-APPROVE-001 | Access-Request genehmigen | Request verschwindet, Mitglied erscheint |
| CONF-REQ-MEMBER-001 | Researcher ist Mitglied | Member-Eintrag sichtbar |
| CONF-REQ-CLEANUP-001 | Nightly-Forschungsgruppe loeschen | Kein Test-Artefakt verbleibt |
| CONF-TABS-001 | Alle 5 Tabs durchklicken (Conferences, Papers, Calendar, Timeline, Kanban) | Jeder Tab zeigt eigenen Content |

### User Settings

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| SETTINGS-NAV-001 | Settings-Seite oeffnen | Sidebar mit Tabs sichtbar |
| SETTINGS-TABS-001 | Alle Sidebar-Tabs durchklicken | Jeder Tab zeigt passenden Content |
| SETTINGS-THEME-001 | Theme-Toggle pruefen | Toggle-Button vorhanden und klickbar |

### Anonymization Pipeline

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| ANON-VIEW-001 | Pipeline-Manager oeffnen | Seite laedt ohne Fehler |
| ANON-TOGGLE-001 | View-Toggle (Cards/List) umschalten | Darstellung wechselt |

### Chatbot Manager

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| CBM-ACCESS-001 | chatbot_manager oeffnet /chatbot-manager | Chatbot-Manager-Seite sichtbar |
| CBM-TABS-001 | Tabs durchklicken (Chatbots, RAG, Crawler) | Tab-Inhalte sichtbar |

### Markdown Collab

| Activity-ID | Beschreibung | Erwartetes Ergebnis |
|---|---|---|
| MD-NAV-001 | Markdown Collab Home oeffnen | Workspace-Liste oder Empty-State |
| MD-WORKSPACE-001 | Workspace oeffnen (falls vorhanden) | Editor-Bereich sichtbar |

---

## Cross-Feature Interaktionen

### Prompt teilen und als anderer User sehen

**Flow:** Researcher erstellt Prompt -> teilt mit Evaluator -> Evaluator oeffnet geteiltes Prompt -> Researcher entfernt Freigabe

Getestet in: `Prompt Engineering Collaboration`

### Szenario-Einladung und Rollenwechsel

**Flow:** Admin erstellt Szenario -> laedt Evaluator ein -> Evaluator sieht Einladung -> nimmt an -> springt in Evaluation

Getestet in: `Scenario Manager Role Assignment`

### Batch Generation -> Szenario Wizard

**Flow:** Researcher oeffnet Batch Generation -> startet Wizard -> Uebergang zum Szenario Wizard

Getestet in: `Szenario Wizard`

### Conference Manager Zugangsanfrage

**Flow:** Admin erstellt Forschungsgruppe -> Researcher stellt Zugangsanfrage -> Admin sieht Anfrage -> genehmigt -> Researcher ist Mitglied

Getestet in: `Conference Manager Access Request`

### Conference Manager Tab-Navigation

**Flow:** Researcher oeffnet Conference Manager -> navigiert alle 5 Tabs (Conferences, Papers, Calendar, Timeline, Kanban)

Getestet in: `Conference Manager Tab Navigation`

### User Settings Navigation

**Flow:** User oeffnet Settings -> navigiert alle Sidebar-Tabs -> Theme-Toggle geprueft

Getestet in: `User Settings Navigation`

---

## Tile-Regression (Automatisch)

Jede Kachel wird pro Rolle geprueft:

| Pruefung | Beschreibung |
|---|---|
| Sichtbarkeit | Kachel ist fuer erlaubte Rollen sichtbar, fuer andere versteckt |
| Navigation | Klick auf Kachel fuehrt zur korrekten Route |
| Kein Login-Redirect | Authentifizierter User wird nicht auf /login umgeleitet |
| Kein 404 | Zielseite zeigt keinen NotFound |
| Kein 5xx | Keine Backend-API-Fehler waehrend Navigation |
| Safe Button Sweep | Nicht-destruktive Buttons auf Zielseite werden geklickt |

**Abgedeckte Kacheln:** Prompt Engineering, Batch Generation, Evaluation, Scenario Manager, Chatbot, Video, Markdown Collab, LaTeX Collab, Chatbot Arena, Anonymization, Anonymisierungs-Pipeline, KAIMO, OnCoCo, Admin Dashboard, Chatbot Admin, RAG Admin, Conference Manager, Pipeline, User Settings

**Rollen:** evaluator, researcher, chatbot_manager, admin

---

## Rollenabdeckung

Reihenfolge im Nightly-Lauf:

1. `test_evaluator`
2. `test_researcher`
3. `test_chatbot_manager`
4. `test_admin`

`ijcai_reviewer` ist explizit aus diesem Nightly-Lauf ausgeschlossen.

---

## Source of Truth

1. `llars-frontend/src/config/home_tiles.contract.json`
2. `llars-frontend/e2e/nightly/nightly_workflows.contract.json`
3. `llars-frontend/e2e/nightly/nightly_activities.contract.json`
4. `docs/testing/nightly/NIGHTLY_TILE_MATRIX.md`

## CI-Gate

`python3 scripts/testing/validate_nightly_coverage.py`

Der Check schlaegt fehl, wenn:

1. Home-Routen und Tile-Contract nicht uebereinstimmen.
2. Ein Kachelname keinen gleichnamigen Testtitel hat.
3. Ein Workflowname keinen gleichnamigen Testtitel hat.
4. Eine Pflicht-Activity-ID (`[ACT:<ID>]`) in den Nightly-Specs fehlt.
5. `Home.vue` oder der Tile-Contract geaendert wurde, aber Tests/Doku nicht mitgezogen wurden.

## Nightly VM-Housekeeping

Nach erfolgreichem Production-Smoke laeuft `maintenance:docker-cleanup`:

1. `docker image prune -af --filter "until=168h"`
2. `docker builder prune -af --filter "until=168h"`

Damit werden nur ungenutzte Artefakte aelter als 7 Tage entfernt und die VM laeuft nicht in Speicherengpaesse.

## Aenderungsvorgehen

Wenn eine Kachel oder Nutzerinteraktion geaendert wird:

1. Contract aktualisieren.
2. E2E-Testtitel unveraendert am Kachelnamen ausrichten.
3. Activity-Eintrag in der Matrix ergaenzen.
4. CI-Check lokal ausfuehren.
