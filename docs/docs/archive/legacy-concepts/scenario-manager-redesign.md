# Szenario Manager Redesign

**Status:** In Entwicklung
**Erstellt:** 2026-01-16

---

## Problemstellung

Der aktuelle Szenario Manager hat folgende Probleme:

1. **Zu komplex:** 3 Filter-Kategorien mit 15+ Optionen überwältigen den User
2. **Keine klare Trennung:** Eigene Szenarien und Einladungen sind vermischt
3. **Zu viel Einblick:** Evaluatoren können Details/Stats fremder Szenarien sehen
4. **Unklare Hierarchie:** Nicht sofort ersichtlich was "meine" Szenarien sind

---

## Designziele

1. **Einfachheit:** Weniger ist mehr - nur das Wesentliche zeigen
2. **Klare Trennung:** Eigene Szenarien vs. Einladungen deutlich unterscheiden
3. **Zugriffskontrolle:** Evaluatoren sehen nur das Nötigste
4. **Konsistenz:** LLARS Design-Patterns einhalten

---

## Neues Design

### Struktur

```
┌─────────────────────────────────────────────────────────────────────┐
│  Szenario Manager                               [+ Neues Szenario]  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │  Meine Szenarien (3) │  │  Einladungen (2)     │                 │
│  └──────────────────────┘  └──────────────────────┘                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Szenario-Karten hier...                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Tab 1: "Meine Szenarien" (Default)

**Was wird angezeigt:**
- Nur Szenarien die der User selbst erstellt hat (`is_owner = true`)
- Sortiert nach: Zuletzt bearbeitet

**Karten-Layout:**

```
┌────────────────────────────────────────┐
│  [Icon] Szenario-Name          [Menu]  │
│  Authenticity · Aktiv                  │
│                                        │
│  ████████████░░░░  75%                 │
│                                        │
│  👥 5 Evaluatoren  ·  🤖 2 LLMs        │
│  Erstellt: 15.01.2026                  │
└────────────────────────────────────────┘
```

**Karten-Inhalte:**
- Szenario-Name mit Typ-Icon
- Typ-Label + Status-Badge
- Fortschrittsbalken (gesamt)
- Evaluator-Count (Human + LLM)
- Erstellungsdatum

**Aktionen:**
- **Klick auf Karte:** → Öffnet `/scenarios/:id` (Workspace)
- **3-Dot-Menü:** Einstellungen, Duplizieren, Archivieren, Löschen

**"Neues Szenario" Button:**
- Nur in diesem Tab sichtbar
- Öffnet Wizard-Dialog

---

### Tab 2: "Einladungen"

**Was wird angezeigt:**
- Szenarien wo User als Evaluator/Rater eingeladen wurde
- Gruppiert: Ausstehend oben, Akzeptiert unten

**Karten-Layout (eingeschränkt):**

```
┌────────────────────────────────────────┐
│  [Icon] Szenario-Name                  │
│  Rating · Eingeladen von admin         │
│                                        │
│  Dein Fortschritt: 12/20 (60%)         │
│  ████████████░░░░░░░░                  │
│                                        │
│  [Annehmen]  [Ablehnen]    oder        │
│  [Zur Evaluation →]                    │
└────────────────────────────────────────┘
```

**Karten-Inhalte:**
- Szenario-Name mit Typ-Icon
- Typ-Label + "Eingeladen von [Username]"
- **Nur eigener Fortschritt** (nicht Gesamt!)
- Einladungs-Status

**Aktionen:**
- **Ausstehende Einladung:** Annehmen / Ablehnen Buttons
- **Akzeptierte Einladung:** "Zur Evaluation" Button
- **Klick:** → Öffnet `/evaluate/:scenarioId` (NICHT Workspace!)

**KEIN Zugriff auf:**
- Gesamt-Fortschritt des Szenarios
- Stats anderer Evaluatoren
- Ergebnisse/Agreement-Metriken
- Team-Übersicht
- Einstellungen

---

## Zugriffskontrolle

### Routing

| Route | Owner | Evaluator |
|-------|-------|-----------|
| `/scenarios` | ✅ Beide Tabs | ✅ Beide Tabs |
| `/scenarios/:id` | ✅ Workspace | ❌ Redirect zu `/evaluate/:id` |
| `/evaluate/:id` | ✅ Evaluation | ✅ Evaluation |

### Berechtigungen im Detail

| Aktion | Owner | Evaluator |
|--------|-------|-----------|
| Szenario erstellen | ✅ | ❌ |
| Szenario löschen | ✅ | ❌ |
| Workspace öffnen | ✅ | ❌ |
| Eigene Evaluation durchführen | ✅ | ✅ |
| Gesamt-Fortschritt sehen | ✅ | ❌ |
| Stats/Results einsehen | ✅ | ❌ |
| Team verwalten | ✅ | ❌ |
| Einstellungen ändern | ✅ | ❌ |
| LLM-Evaluation starten | ✅ | ❌ |

---

## Komponenten-Struktur

```
ScenarioManagerHome.vue (überarbeitet)
├── Header (Titel + "Neues Szenario" Button)
├── LTabs (2 Tabs)
│   ├── Tab: Meine Szenarien
│   │   └── ScenarioOwnerCard.vue (neu)
│   └── Tab: Einladungen
│       └── ScenarioInviteCard.vue (neu)
├── EmptyState (pro Tab unterschiedlich)
└── ScenarioWizard (Dialog, unverändert)
```

### Neue Komponenten

**ScenarioOwnerCard.vue**
- Volle Informationen
- 3-Dot-Menü mit allen Aktionen
- Navigiert zu Workspace

**ScenarioInviteCard.vue**
- Eingeschränkte Informationen
- Annehmen/Ablehnen oder "Zur Evaluation"
- Navigiert zu Evaluation-Interface

---

## Design-Details

### Farben & Styling (LLARS Design System)

```css
/* Typ-Icons */
Ranking:      mdi-sort-variant      #b0ca97
Rating:       mdi-star-outline      #D1BC8A
Comparison:   mdi-compare           #88c4c8
Authenticity: mdi-shield-search     #c4a0d4
Mail:         mdi-email-outline     #e8a087

/* Status-Badges */
Entwurf:      gray
Aktiv:        primary (#b0ca97)
Abgeschlossen: success
Archiviert:   gray

/* Einladungs-Status */
Ausstehend:   warning (orange)
Akzeptiert:   success (grün)
Abgelehnt:    gray
```

### Layout

- **Desktop:** 2-3 Spalten Grid (`minmax(320px, 1fr)`)
- **Tablet:** 2 Spalten
- **Mobile:** 1 Spalte
- **Karten-Höhe:** Auto (content-based)
- **Gap:** 16px

### Responsive

```css
/* Desktop */
.scenarios-grid {
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
}

/* Tablet */
@media (max-width: 900px) {
  grid-template-columns: repeat(2, 1fr);
}

/* Mobile */
@media (max-width: 600px) {
  grid-template-columns: 1fr;
}
```

---

## Implementierungsschritte

1. **ScenarioManagerHome.vue** komplett neu schreiben
   - Tab-Navigation mit LTabs
   - Getrennte Listen für eigene/eingeladene
   - Kein Filter-Panel mehr

2. **ScenarioOwnerCard.vue** erstellen
   - Karte für eigene Szenarien
   - Volle Informationen + Menü

3. **ScenarioInviteCard.vue** erstellen
   - Karte für Einladungen
   - Eingeschränkte Infos + Aktionen

4. **Routing anpassen**
   - Redirect für Nicht-Owner bei `/scenarios/:id`
   - `/evaluate/:id` Route prüfen/erstellen

5. **Backend-Check**
   - API liefert `is_owner` Flag ✅
   - API liefert `invitation` Objekt ✅
   - Eigener Fortschritt für Evaluator abrufbar?

6. **Alte Komponenten entfernen**
   - `ScenarioCard.vue` → ersetzt durch neue Karten
   - Filter-Logic entfernen

---

## Nicht im Scope

- Evaluation-Interface (`/evaluate/:id`) - existiert bereits
- Wizard - bleibt unverändert
- Workspace - bleibt unverändert (nur Zugriffskontrolle)

---

## Offene Fragen

1. ~~Sollen abgelehnte Einladungen im Tab "Einladungen" bleiben?~~ **Ja, mit "Erneut annehmen" Option**
2. ~~Braucht es einen Status-Filter?~~ **Nein, zu komplex**
3. Existiert `/evaluate/:id` Route bereits? → Prüfen
