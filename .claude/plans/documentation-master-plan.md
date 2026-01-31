# LLARS Dokumentation - Master-Plan

## Status: In Analyse
**Erstellt:** 30. Januar 2026
**Ziel:** Einheitliche, vollständige und aktuelle Dokumentation

---

## 1. IST-Analyse

### 1.1 Dateien-Übersicht

| Bereich | Anzahl | Status |
|---------|--------|--------|
| `docs/docs/` (MkDocs) | 52 | Teilweise aktuell |
| `docs/concepts/` | 12 | VERALTET - außerhalb MkDocs |
| `docs/testing/` | 24 | Nicht in Navigation |
| `docs/konzepte/` | 1 | VERALTET |
| **Gesamt** | **116** | Unstrukturiert |

### 1.2 Dokumentierte Features

| Feature | Doku vorhanden | Aktuell | Qualität |
|---------|----------------|---------|----------|
| Szenario Wizard | ✅ | ✅ (gerade aktualisiert) | Gut |
| Szenario Manager | ✅ | ✅ (gerade aktualisiert) | Gut |
| Evaluation | ✅ | ✅ (gerade aktualisiert) | Gut |
| LLM-as-Judge | ✅ | ❓ | Zu prüfen |
| Chatbot & RAG | ✅ | ❓ | Zu prüfen |
| KAIMo | ✅ | ❓ | Zu prüfen |
| Authentik | ✅ | ✅ | Okay |
| Permission System | ✅ | ❓ | Zu prüfen |

### 1.3 FEHLENDE Dokumentation (kritisch!)

| Feature | Priorität | Komplexität | Status |
|---------|-----------|-------------|--------|
| **Prompt Engineering** | 🔴 Hoch | Hoch | FEHLT KOMPLETT |
| **Batch Generation** | 🔴 Hoch | Mittel | FEHLT KOMPLETT |
| **Chatbot Wizard** | 🔴 Hoch | Hoch | FEHLT KOMPLETT |
| **LaTeX Collaboration** | 🟡 Mittel | Hoch | FEHLT KOMPLETT |
| **Markdown Collaboration** | 🟡 Mittel | Mittel | Nur Konzept vorhanden |
| **Admin Dashboard** | 🟡 Mittel | Mittel | FEHLT KOMPLETT |
| **Anonymisierung Tool** | 🟡 Mittel | Mittel | Nur Anforderungen |
| **Benutzer-Einstellungen** | 🟢 Niedrig | Niedrig | FEHLT |

---

## 2. Strukturelle Probleme

### 2.1 Inkonsistente Verzeichnisstruktur

```
PROBLEM:
docs/
├── concepts/          ← AUSSERHALB MkDocs! Veraltet!
├── konzepte/          ← DOPPELT! Nur 1 Datei
├── testing/           ← NICHT in Navigation
└── docs/              ← Eigentliche MkDocs-Inhalte
    └── projekte/
        └── konzepte/  ← NOCHMAL konzepte!
```

### 2.2 Fehlende Hierarchie-Ebenen

**Problem:** Alle Features auf gleicher Ebene, obwohl unterschiedlich komplex

```
AKTUELL (flach):              BESSER (hierarchisch):
├── Szenario Wizard           ├── Szenarien & Evaluation
├── Szenario Manager          │   ├── Wizard
├── Evaluation                │   ├── Manager
├── Prompt Engineering ???    │   └── Durchführung
├── Chatbot Wizard ???        ├── Prompt Engineering
└── Collab Farben ???         │   ├── Workspace
                              │   └── Batch Generation
                              └── Chatbots
                                  ├── Wizard
                                  └── Chat
```

### 2.3 Fehlende Querverweise

- Keine "Siehe auch" Sektionen (außer in neuen Docs)
- Keine Breadcrumbs
- Keine thematischen Verlinkungen

---

## 3. SOLL-Struktur (Vorschlag)

### 3.1 Neue Navigation

```yaml
nav:
  - Startseite: index.md

  # === BENUTZER-DOKUMENTATION ===
  - Erste Schritte:
      - Schnellstart: guides/quick-start.md
      - Login: guides/login-anleitung.md
      - Benutzeroberfläche: guides/ui-overview.md  # NEU

  - Szenarien & Evaluation:
      - Übersicht: guides/scenarios/index.md  # NEU
      - Szenario Wizard: guides/scenario-wizard.md
      - Szenario Manager: guides/scenario-manager.md
      - Evaluation durchführen: guides/evaluation.md
      - LLM-as-Judge: guides/llm-as-judge.md  # NEU (aus Projekte)

  - Prompt Engineering:  # NEU - KOMPLETT
      - Übersicht: guides/prompt-engineering/index.md
      - Workspace: guides/prompt-engineering/workspace.md
      - Batch Generation: guides/prompt-engineering/batch-generation.md
      - Prompt-Vorlagen: guides/prompt-engineering/templates.md

  - Chatbots:  # NEU - KOMPLETT
      - Übersicht: guides/chatbots/index.md
      - Chatbot Wizard: guides/chatbots/wizard.md
      - Chat mit Bots: guides/chatbots/chat.md
      - RAG-Konfiguration: guides/chatbots/rag-config.md

  - Kollaboration:  # NEU - KOMPLETT
      - Übersicht: guides/collaboration/index.md
      - Markdown Editor: guides/collaboration/markdown.md
      - LaTeX Editor: guides/collaboration/latex.md
      - AI-Kommentare: guides/collaboration/ai-comments.md

  - Tools:
      - Data Importer: guides/tools/data-importer.md
      - Anonymisierung: guides/tools/anonymize.md  # NEU

  - Einstellungen:  # NEU
      - Benutzer-Einstellungen: guides/settings/user.md
      - Berechtigungen: guides/permission-system.md

  # === ADMIN-DOKUMENTATION ===
  - Administration:  # NEU - KOMPLETT
      - Dashboard: admin/dashboard.md
      - Benutzer & Rollen: admin/users-roles.md
      - LLM-Modelle: admin/llm-models.md
      - Authentik: admin/authentik-setup.md

  # === ENTWICKLER-DOKUMENTATION ===
  - Entwickler:
      - API-Referenz: entwickler/api-referenz.md
      - Datenformate: entwickler/evaluation-datenformate.md
      - WebSocket API: entwickler/websocket-api.md
      - Datenbank: entwickler/datenbank-schema.md
      - Deployment: entwickler/production-deployment.md

  # === HINTERGRUND & KONZEPTE ===
  - Konzepte:
      - Agentic AI: konzepte/agentic-ai.md
      - RAG-Pipeline: konzepte/rag.md
      - Architektur: konzepte/architektur.md

  # === ARCHIV ===
  - Archiv:
      - Übersicht: archive/index.md
      # ... alte Dokumente
```

---

## 4. Einheitliches Dokument-Schema

### 4.1 Standard-Struktur für Benutzer-Guides

```markdown
# Feature-Name

**Version:** X.Y | **Stand:** Monat Jahr

Kurze Einführung (2-3 Sätze).

---

## Übersicht

[ASCII-Diagramm oder Screenshot-Beschreibung]

---

## Schnellstart

!!! tip "In 3 Schritten"
    1. Erster Schritt
    2. Zweiter Schritt
    3. Dritter Schritt

---

## Funktionen

### Funktion A

[Beschreibung mit Beispiel]

### Funktion B

[Beschreibung mit Beispiel]

---

## Häufige Fragen

??? question "Frage 1?"
    Antwort hier.

??? question "Frage 2?"
    Antwort hier.

---

## Siehe auch

- [Verwandtes Feature 1](link.md)
- [Verwandtes Feature 2](link.md)
```

### 4.2 Formatierungs-Regeln

| Element | Verwendung | Beispiel |
|---------|------------|----------|
| `!!! tip` | Hilfreiche Tipps | Keyboard-Shortcuts |
| `!!! warning` | Wichtige Hinweise | Datenverlust möglich |
| `!!! info` | Zusatzinfo | Technische Details |
| `!!! note` | Anmerkungen | Versionshinweise |
| `???` (collapsible) | Optionale Details | FAQ-Einträge |
| Tabellen | Vergleiche, Listen | Feature-Übersichten |
| Code-Blöcke | Beispiele | API-Calls, JSON |
| ASCII-Art | UI-Darstellung | Layout-Diagramme |

### 4.3 ASCII-Diagramm-Standards

```
┌─────────────────────────────────────────┐  ← Box mit Titel
│  Titel                          [Icon]  │
├─────────────────────────────────────────┤  ← Separator
│                                         │
│  Inhalt hier                            │
│                                         │
├─────────────────────────────────────────┤
│  [Button 1]  [Button 2]  [Button 3]     │  ← Footer mit Aktionen
└─────────────────────────────────────────┘
```

---

## 5. Implementierungs-Plan

### Phase 1: Aufräumen (1-2 Stunden)

- [ ] `docs/concepts/` → `docs/docs/archive/concepts/` verschieben
- [ ] `docs/konzepte/` → `docs/docs/archive/` verschieben
- [ ] Doppelte Dateien identifizieren und konsolidieren
- [ ] Veraltete Konzepte archivieren

### Phase 2: Fehlende Guides erstellen (4-6 Stunden)

| Guide | Priorität | Geschätzte Zeit |
|-------|-----------|-----------------|
| Prompt Engineering | 🔴 | 45 min |
| Batch Generation | 🔴 | 30 min |
| Chatbot Wizard | 🔴 | 45 min |
| Chat mit Bots | 🔴 | 30 min |
| LaTeX Collaboration | 🟡 | 45 min |
| Markdown Collaboration | 🟡 | 30 min |
| Admin Dashboard | 🟡 | 30 min |
| Anonymisierung | 🟡 | 30 min |
| Benutzer-Einstellungen | 🟢 | 20 min |

### Phase 3: Bestehende Docs aktualisieren (2-3 Stunden)

- [ ] LLM-as-Judge prüfen und aktualisieren
- [ ] Chatbot & RAG prüfen und aktualisieren
- [ ] KAIMo prüfen und aktualisieren
- [ ] Permission System prüfen und aktualisieren
- [ ] Alle "Projekte" prüfen - was ist aktuell, was archivieren?

### Phase 4: Formatierung vereinheitlichen (2-3 Stunden)

- [ ] Alle Docs auf einheitliches Schema bringen
- [ ] ASCII-Diagramme prüfen/korrigieren
- [ ] Admonitions (tip/warning/info) konsistent verwenden
- [ ] "Siehe auch" Sektionen hinzufügen
- [ ] Querverweise prüfen und ergänzen

### Phase 5: Navigation aktualisieren (30 min)

- [ ] mkdocs.yml mit neuer Struktur aktualisieren
- [ ] Neue Dateien in Navigation einbinden
- [ ] Archivierte Dateien aus Navigation entfernen

---

## 6. Kontext-Management für Claude

### Ansatz: Feature-weise Bearbeitung

Da 116 Dokumente nicht in einem Context passen:

1. **Session 1:** Phase 1 (Aufräumen) + Prompt Engineering Guides
2. **Session 2:** Chatbot Guides + LaTeX/Markdown Collab
3. **Session 3:** Admin + Tools + Settings
4. **Session 4:** Bestehende Docs prüfen
5. **Session 5:** Formatierung + Navigation

### Pro Session:
- Plan-Datei als Referenz lesen
- Nur relevante Code-Dateien lesen
- Dokumentation erstellen/aktualisieren
- Fortschritt in dieser Datei markieren

---

## 7. Qualitäts-Checkliste

Jedes Dokument muss:

- [ ] Versionsnummer und Datum haben
- [ ] Kurze Einführung (max 3 Sätze)
- [ ] Mindestens ein visuelles Element (ASCII, Tabelle, Diagramm)
- [ ] "Siehe auch" Sektion mit 2-3 Links
- [ ] Korrekte Admonitions verwenden
- [ ] Gegen aktuellen Code geprüft sein
- [ ] In mkdocs.yml Navigation sein

---

## 8. Nächste Schritte

1. **JETZT:** Plan reviewen und genehmigen
2. **Dann:** Phase 1 starten (Aufräumen)
3. **Danach:** Session für fehlende Guides starten

---

## Fortschritt

| Phase | Status | Abgeschlossen |
|-------|--------|---------------|
| Phase 1: Aufräumen | ✅ Fertig | 30.01.2026 |
| Phase 2: Neue Guides | ✅ Fertig | 30.01.2026 |
| Phase 3: Updates | ⏸️ Warten | - |
| Phase 4: Formatierung | ⏸️ Warten | - |
| Phase 5: Navigation | ✅ Fertig | 30.01.2026 |

### Phase 1 & 2 Ergebnisse (30.01.2026)

**Aufräumarbeiten:**
- `docs/concepts/` → `docs/docs/archive/legacy-concepts/` (12 Dateien)
- `docs/konzepte/` → `docs/docs/archive/` (1 Datei)
- Alte Verzeichnisse gelöscht
- Archive-Navigation aktualisiert

**Neue Guides erstellt:**
- `guides/prompt-engineering.md` - Kollaborativer Prompt-Editor
- `guides/batch-generation.md` - Massenhafte Prompt-Ausführung
- `guides/chatbot-wizard.md` - RAG-Chatbot Wizard
- `guides/latex-collaboration.md` - LaTeX Echtzeit-Kollaboration
- `guides/admin-dashboard.md` - Admin-Panel Dokumentation

**Navigation aktualisiert:**
- mkdocs.yml mit neuen Guides erweitert
- Guides-Index überarbeitet mit Kategorien
