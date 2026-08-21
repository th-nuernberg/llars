# Szenario Manager

**Version:** 2.0 | **Stand:** Januar 2026

Der Szenario Manager ist die zentrale Verwaltungsoberfläche für Evaluations-Szenarien in LLARS. Hier können Forscher ihre Szenarien verwalten, den Fortschritt überwachen und Ergebnisse analysieren.

---

## Übersicht

Der Szenario Manager besteht aus zwei Hauptbereichen:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Szenario Manager                               [+ Neues Szenario]  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │  Meine Szenarien (3) │  │  Einladungen (2)     │                 │
│  └──────────────────────┘  └──────────────────────┘                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │ Szenario-Karte │  │ Szenario-Karte │  │ Szenario-Karte │        │
│  └────────────────┘  └────────────────┘  └────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tab: Meine Szenarien

Zeigt alle Szenarien, die Sie erstellt haben.

### Szenario-Karte

```
┌────────────────────────────────────────┐
│  [⭐] Summary-Qualität Studie   [Menu]  │
│  Rating · Evaluierung läuft             │
│                                         │
│  ████████████░░░░  75%                  │
│                                         │
│  👥 5 Evaluatoren  ·  🤖 2 LLMs         │
│  Erstellt: 15.01.2026  ·  150 Threads   │
└────────────────────────────────────────┘
```

| Element | Beschreibung |
|---------|--------------|
| **Icon** | Evaluationstyp (⭐ Rating, ↕️ Ranking, etc.) |
| **Name** | Szenario-Name |
| **Typ** | Evaluationstyp + Status-Badge |
| **Fortschritt** | Gesamtfortschritt aller Evaluatoren |
| **Team** | Anzahl menschliche Evaluatoren + LLMs |
| **Datum** | Erstellungsdatum |
| **Threads** | Anzahl Threads/Items |
| **Menu** | Aktionen (3-Punkte-Menü) |

### Status-Badges

| Status | Farbe | Bedeutung |
|--------|-------|-----------|
| **Entwurf** | Grau | Noch nicht gestartet |
| **Daten sammeln** | Blau | Items werden importiert |
| **Evaluierung läuft** | Blau | Bewertungen werden gesammelt |
| **Analyse** | Gelb | Ergebnisse werden analysiert |
| **Abgeschlossen** | Grün | Alle Bewertungen fertig |
| **Archiviert** | Grau | Inaktiv |

### Aktionen

| Aktion | Beschreibung |
|--------|--------------|
| **Öffnen** | Klick auf Karte → Workspace |
| **Einstellungen** | Szenario-Konfiguration ändern |
| **Duplizieren** | Kopie mit neuen Daten erstellen |
| **Archivieren** | Szenario deaktivieren |
| **Löschen** | Szenario und alle Daten löschen |

---

## Tab: Einladungen

Zeigt Szenarien, zu denen Sie als Evaluator eingeladen wurden.

### Einladungs-Karte

```
┌────────────────────────────────────────┐
│  [↕️] LLM-Vergleich Benchmark           │
│  Ranking · Eingeladen von admin         │
│                                         │
│  Dein Fortschritt: 12/20 (60%)          │
│  ████████████░░░░░░░░                   │
│                                         │
│  [Ablehnen] [Annehmen]                  │
│  (nach Annahme: [Zur Evaluation]        │
│   + Option "Verlassen")                 │
└────────────────────────────────────────┘
```

!!! warning "Eingeschränkte Sicht"
    Eingeladene Evaluatoren werden zur **Evaluation-Übersicht** geleitet und sehen **nur den eigenen Fortschritt**, nicht den Gesamtfortschritt oder Ergebnisse anderer.

### Einladungs-Status

| Status | Beschreibung |
|--------|--------------|
| **Ausstehend** | Einladung noch nicht angenommen |
| **Akzeptiert** | Einladung angenommen, Evaluation möglich |
| **Abgelehnt** | Einladung abgelehnt |

---

## Workspace

Nach Klick auf eine Szenario-Karte öffnet sich der **Workspace** mit mehreren Tabs:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Summary-Qualität Studie                                   [⚙️]     │
├───────────┬───────────┬───────────┬───────────┬────────────────────┤
│ Übersicht │   Daten   │ Evaluation│   Team    │                    │
└───────────┴───────────┴───────────┴───────────┴────────────────────┘
```

| Tab | Beschreibung |
|-----|--------------|
| **Übersicht** | Schneller Überblick, Fortschritt, Quick Actions |
| **Daten** | Items importieren und verwalten |
| **Evaluation** | Live-Statistiken, Metriken, Export |
| **Team** | Evaluatoren und LLMs verwalten |

!!! note "Einstellungen"
    Das Zahnrad-Icon (⚙️) oben rechts öffnet den Einstellungen-Dialog für das Szenario.
    Eingeladene Evaluatoren sehen diesen Workspace nicht.

---

### Tab: Übersicht

Schneller Überblick über das Szenario:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Zusammenfassung                                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Typ:          Rating (Multi-Dimensional)                           │
│  Items:        150                                                  │
│  Dimensionen:  Kohärenz, Flüssigkeit, Relevanz, Konsistenz         │
│  Skala:        1-5 (Likert)                                        │
├─────────────────────────────────────────────────────────────────────┤
│  Gesamtfortschritt                                                  │
│  ████████████████░░░░░░░░░░░░░░░░  45%                             │
│  675 / 1500 Bewertungen                                             │
├─────────────────────────────────────────────────────────────────────┤
│  [Zur Evaluation]  [LLM-Evaluation starten]  [Export]              │
└─────────────────────────────────────────────────────────────────────┘
```

Zusätzlich gibt es Quick Actions für:
- Daten importieren
- LLM-Evaluation starten
- Ergebnisse anzeigen

---

### Tab: Evaluation

Live-Statistiken zur laufenden Evaluation:

#### Fortschritts-Übersicht

```
┌────────────────────────────────────────┐
│  Evaluator-Fortschritt                 │
├────────────────────────────────────────┤
│  admin        ████████████████  100%   │
│  researcher   ████████████░░░░   75%   │
│  evaluator1   ████████░░░░░░░░   50%   │
│  LLM-A        ████████████████  100%   │
│  LLM-B        ████████████████  100%   │
└────────────────────────────────────────┘
```

#### Agreement-Metriken & Heatmaps

Zeigt Übereinstimmung und Konsistenz zwischen Evaluatoren (z.B. Kappa/Alpha/ICC) sowie Heatmaps:

```
┌────────────────────────────────────────────────────────┐
│  Inter-Rater Agreement                                 │
├────────────────────────────────────────────────────────┤
│               admin  researcher  eval1  LLM-A  LLM-B  │
│  admin         -       0.82      0.75   0.88   0.85   │
│  researcher   0.82      -        0.78   0.84   0.81   │
│  evaluator1   0.75     0.78       -     0.79   0.77   │
│  LLM-A        0.88     0.84      0.79    -     0.91   │
│  LLM-B        0.85     0.81      0.77   0.91    -     │
└────────────────────────────────────────────────────────┘
```

!!! info "Agreement-Werte"
    - **> 0.8**: Hohe Übereinstimmung (grün)
    - **0.6-0.8**: Moderate Übereinstimmung (gelb)
    - **< 0.6**: Geringe Übereinstimmung (rot)

#### Dimensionen-Verteilung (Rating)

Zeigt die Verteilung der Bewertungen pro Dimension:

```
┌────────────────────────────────────────┐
│  Kohärenz                              │
│  1: ██░░░░░░░░  10%                    │
│  2: ████░░░░░░  20%                    │
│  3: ██████░░░░  30%                    │
│  4: ████████░░  25%                    │
│  5: ███░░░░░░░  15%                    │
│  Ø 3.2                                 │
└────────────────────────────────────────┘
```

---

### Tab: Team

Verwalten Sie die Evaluatoren:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Team-Mitglieder                                    [+ Einladen]    │
├─────────────────────────────────────────────────────────────────────┤
│  👤 admin           Owner        100%  ████████████████             │
│  👤 researcher      Evaluator     75%  ████████████░░░░             │
│  👤 evaluator1      Evaluator     50%  ████████░░░░░░░░             │
│  🤖 LLM-Modell A     LLM          100%  ████████████████            │
│  🤖 LLM-Modell B     LLM          100%  ████████████████            │
└─────────────────────────────────────────────────────────────────────┘
```

#### Rollen

Szenario-Rollen haben **zwei unabhängige Achsen** auf `ScenarioUsers`
(`app/db/models/scenario.py`):

- **Manager-Rolle** (`manager_role`) — Zugriff auf den Scenario Manager:
  `owner` (volle Kontrolle, löschen) · `editor` (Settings + Team, kein Löschen) ·
  `viewer` (read-only Analyse/IRR, **kein** Bearbeiten) · `none`.
- **Evaluations-Rolle** (`evaluation_role`) — Teilnahme an der Bewertung:
  `assessor` (bewertet Items) · `viewer` (sieht Items read-only) · `none`.

Eine Person kann beide Achsen kombinieren — z. B. der **read-only Manager-Viewer**
(`manager_role='viewer'`), der die live aggregierte Analyse sieht, aber nichts
bearbeitet oder umkonfiguriert. Genau diese Kombination vergibt der
[IJCAI-Demo-Link](../human_studies/ijcai-demo.md) (Assessor **und** Manager-Viewer
auf denselben Szenarien).

| Rolle (Anzeige) | Bedeutung |
|-----------------|-----------|
| **Owner** | Szenario-Ersteller, volle Rechte |
| **Editor** | Settings + Team verwalten, kein Löschen |
| **Viewer** | Read-only Manager: sieht Analyse/IRR + Roh-Export, bearbeitet nichts |
| **Assessor** | Bewertet Items |
| **Eval. Viewer** | Sieht Items read-only, gibt keine Bewertung ab |

#### LLM-Evaluation

!!! tip "LLM-Modelle hinzufügen"
    LLM-Evaluatoren werden aktuell beim Erstellen des Szenarios im Wizard ausgewählt. Der Team-Tab zeigt sie an; Add/Remove im Team-Tab ist noch nicht vollständig umgesetzt.

#### Einladungs-Status

Einladungen werden als Status-Badges an den Team-Karten angezeigt (ausstehend, akzeptiert, abgelehnt). Abgelehnte Einladungen können erneut versendet werden.

#### Export-Funktionen

Im Evaluation-Tab können Ergebnisse direkt exportiert werden:

| Format | Beschreibung |
|--------|--------------|
| **CSV** | Alle Bewertungen als Tabelle |
| **JSON** | Strukturierte Daten |

#### Evaluator-Filter

Toggle zwischen:
- **Alle** - Alle Evaluatoren
- **Mensch** - Nur menschliche Bewerter
- **LLM** - Nur KI-Evaluatoren

---

### Tab: Daten

Verwalten Sie die zu bewertenden Items:

- Items hochladen (JSON, JSONL, CSV/TSV, XLSX)
- Vorhandene Threads/Items ansehen
- Threads/Items löschen

---

### Einstellungen-Dialog

Über das Zahnrad-Icon (⚙️) erreichbar:

- **Name & Beschreibung** bearbeiten
- **Zeitraum** (Start/Ende)
- **Verteilung** konfigurieren
- **Reihenfolge** (fixed/random)
- **Sichtbarkeit** und **Status**
- **Szenario löschen**

---

## Neues Szenario erstellen

1. Klicken Sie auf **"+ Neues Szenario"** oben rechts
2. Der [Szenario Wizard](scenario-wizard.md) öffnet sich
3. Folgen Sie den 5 Schritten

---

## Berechtigungen

### Owner (Ersteller)

| Aktion | Erlaubt |
|--------|---------|
| Workspace öffnen | ✅ |
| Gesamtfortschritt sehen | ✅ |
| Team verwalten | ✅ |
| Statistiken/Ergebnisse sehen | ✅ |
| Einstellungen ändern | ✅ |
| LLM-Evaluation starten | ✅ |
| Szenario löschen | ✅ |

### Evaluator (Eingeladen)

| Aktion | Erlaubt |
|--------|---------|
| Evaluation durchführen | ✅ |
| Eigenen Fortschritt sehen | ✅ |
| Evaluation-Übersicht öffnen | ✅ |
| Workspace öffnen | ❌ |
| Gesamtfortschritt sehen | ❌ |
| Team sehen | ❌ |
| Ergebnisse sehen | ❌ |

### Viewer (read-only Manager)

Der Manager-Viewer (`manager_role='viewer'`) sieht die Analyse, darf aber nichts
ändern:

| Aktion | Erlaubt |
|--------|---------|
| Workspace / Analyse + IRR sehen | ✅ |
| Roh-Ergebnisse exportieren | ✅ |
| Einstellungen ändern | ❌ |
| Team verwalten | ❌ |
| Szenario löschen | ❌ |

### Eval. Viewer (Eingeladen, read-only)

| Aktion | Erlaubt |
|--------|---------|
| Evaluation ansehen | ✅ |
| Bewertungen abgeben | ❌ |
| Eigenen Fortschritt sehen | ✅ |
| Workspace öffnen | ❌ |

!!! warning "Autorisierungs-Härtung"
    - **Roh-Export** (`GET /api/scenarios/:id/export`) ist auf
      **Owner / Editor / Viewer / Admin** beschränkt. Reine Assessor:innen
      können **nicht** die per-User-Rohbewertungen aller anderen lesen
      (Rater-Blinding bleibt gewahrt).
    - **Entfernte / abgelehnte Mitglieder verlieren den Zugriff:**
      `membership_status=ARCHIVED` (soft-entfernt) und
      `invitation_status=REJECTED` gelten nicht mehr als Mitglieder
      (`require_scenario_membership` in `app/auth/access_control.py`).

---

## API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/scenarios` | GET | Liste aller Szenarien |
| `/api/scenarios` | POST | Neues Szenario erstellen |
| `/api/scenarios/:id` | GET | Szenario-Details |
| `/api/scenarios/:id` | PUT | Szenario aktualisieren |
| `/api/scenarios/:id` | DELETE | Szenario löschen |
| `/api/scenarios/:id/stats` | GET | Live-Statistiken |
| `/api/scenarios/:id/export` | GET | Ergebnisse exportieren |

---

## Siehe auch

- [Szenario Wizard](scenario-wizard.md) - Szenarien erstellen
- [Evaluation](evaluation.md) - Bewertungen durchführen
- [Berechtigungssystem](permission-system.md) - Zugriffsrechte
