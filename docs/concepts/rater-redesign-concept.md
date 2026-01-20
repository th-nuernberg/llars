# Rating UI Redesign Konzept

**Status:** Entwurf | **Stand:** Januar 2026

---

## Übersicht

LLARS unterscheidet **zwei verschiedene Rating-Typen**, die unterschiedliche UIs benötigen:

| Typ | function_type_id | Zweck | Was wird bewertet? |
|-----|------------------|-------|-------------------|
| **Feature Rating** | 2 (`rating`) | LLM-Outputs bewerten | GPT-4 Zusammenfassung, Claude Kategorie, etc. |
| **Mail/Text Rating** | 3 (`mail_rating`) | Original-Text bewerten | E-Mail-Verlauf auf Dimensionen (Freundlichkeit, Klarheit, etc.) |

**Der Ranker (function_type_id=1) bleibt unverändert.**

---

## Teil 1: Feature Rating (type=rating)

### Use Case

> "Bewerte die LLM-generierten Features zu diesem E-Mail-Verlauf"

- **Input:** E-Mail-Thread + mehrere LLM-generierte Features (Zusammenfassung, Kategorie, Betreff, etc.)
- **Aufgabe:** Jedes Feature einzeln auf einer Likert-Skala bewerten
- **Beispiel-Szenario:** "Demo Rating Szenario" (ID: 1)

### Aktuelles Layout

```
/Rater/:id → RaterDetail.vue (Feature-Liste)
    └── /Rater/:id/:feature → RaterDetailFeature.vue (Einzelbewertung)

┌──────────────────────────────────────────────────────────────┐
│ Features                       │ E-Mail Verlauf              │
├────────────────────────────────┼─────────────────────────────┤
│ ▼ Zusammenfassung              │ Kunde (15:34)               │
│   ┌─────────────────────────┐  │ "Hallo, ich habe..."        │
│   │ GPT-4: [Klick → Detail] │  │                             │
│   │ Claude: [Klick → Detail]│  │ Berater (16:34)             │
│   └─────────────────────────┘  │ "Gerne helfe ich..."        │
│                                │                             │
│ ▼ Kategorie                    │                             │
│   ┌─────────────────────────┐  │                             │
│   │ GPT-4: [Klick → Detail] │  │                             │
│   └─────────────────────────┘  │                             │
└────────────────────────────────┴─────────────────────────────┘
```

**Problem:** Jedes Feature erfordert Klick auf separate Seite → 4+ Klicks pro Bewertung

### Neues Layout: Inline Feature Rating

```
┌──────────────────────────────────────────────────────────────┐
│ ← Szenario    Feature Rating: Anfrage #42        3/15 ▶     │
├────────────────────────────────┬─────────────────────────────┤
│ 📧 E-MAIL KONTEXT              │ 🤖 FEATURES BEWERTEN         │
│                                │                             │
│ ┌────────────────────────────┐ │   Fortschritt: ████░░ 4/6   │
│ │ Kunde (15:34)              │ │                             │
│ │ Hallo, ich habe eine Frage │ │ ┌──────────────────────────┐│
│ │ zu meiner Bestellung...    │ │ │ ZUSAMMENFASSUNG          ││
│ │                            │ │ ├──────────────────────────┤│
│ │ Berater (16:34)            │ │ │ 🤖 GPT-4                  ││
│ │ Gerne helfe ich Ihnen      │ │ │ "Der Kunde erkundigt     ││
│ │ bei Ihrer Anfrage...       │ │ │  sich nach Bestellung"   ││
│ │                            │ │ │                          ││
│ │ Kunde (17:34)              │ │ │ ●──●──●──○──○    [3/5]   ││
│ │ Vielen Dank für die        │ │ │ Gut    Neutral  Schlecht ││
│ │ schnelle Hilfe!            │ │ └──────────────────────────┘│
│ └────────────────────────────┘ │                             │
│                                │ ┌──────────────────────────┐│
│                                │ │ 🤖 Claude                 ││
│                                │ │ "Lieferanfrage zu        ││
│                                │ │  Bestellung #1234"       ││
│                                │ │                          ││
│                                │ │ ○──○──○──○──○    [-/5]   ││
│                                │ └──────────────────────────┘│
│                                │                             │
│                                │ ┌──────────────────────────┐│
│                                │ │ KATEGORIE                ││
│                                │ ├──────────────────────────┤│
│                                │ │ 🤖 GPT-4: "Lieferanfrage" ││
│                                │ │ ●──●──○──○──○    [2/5]   ││
│                                │ └──────────────────────────┘│
└────────────────────────────────┴─────────────────────────────┘
│ Auto-Save ✓ │ Tastatur: 1-5 bewerten, Tab nächstes Feature   │
└──────────────────────────────────────────────────────────────┘
```

### Feature Rating - Komponenten

```
views/Evaluation/
└── FeatureRatingSession.vue         # Hauptcontainer

components/Evaluation/FeatureRating/
├── FeatureRatingContext.vue         # Links: E-Mail-Verlauf
├── FeatureRatingList.vue            # Rechts: Feature-Liste
├── FeatureRatingCard.vue            # Einzelnes Feature + Likert
└── InlineLikertScale.vue            # Kompakte Likert-Skala
```

---

## Teil 2: Mail/Text Rating (type=mail_rating)

### Use Case

> "Bewerte diesen E-Mail-Verlauf auf verschiedenen Dimensionen"

- **Input:** E-Mail-Thread + vordefinierte Bewertungsdimensionen
- **Aufgabe:** Den gesamten Thread auf jeder Dimension bewerten
- **Dimensionen:** z.B. Freundlichkeit, Klarheit, Professionalität, Lösungsorientierung
- **Beispiel-Szenario:** "Demo Verlauf Bewerter Szenario" (ID: 3)

### Unterschied zu Feature Rating

| Aspekt | Feature Rating | Mail Rating |
|--------|---------------|-------------|
| **Was wird bewertet?** | LLM-generierte Outputs | Der Original-Text selbst |
| **Dimensionen** | Feature-Typen (Summary, Kategorie) | Qualitätskriterien (Freundlichkeit, Klarheit) |
| **Anzahl Items** | Variabel (je nach LLMs) | Fix (definierte Dimensionen) |
| **Kontext** | E-Mail ist Kontext für Features | E-Mail IST das zu Bewertende |

### Neues Layout: Dimension Rating

```
┌──────────────────────────────────────────────────────────────┐
│ ← Szenario    E-Mail Bewertung: Anfrage #42      3/15 ▶     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📧 ZU BEWERTENDER E-MAIL-VERLAUF                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Kunde (15:34)                                          │  │
│  │ Hallo, ich habe eine Frage zu meiner Bestellung.      │  │
│  │ Die Lieferung sollte gestern ankommen, aber...        │  │
│  │                                                        │  │
│  │ Berater (16:34)                                        │  │
│  │ Gerne helfe ich Ihnen bei Ihrer Anfrage. Ich habe     │  │
│  │ nachgeschaut und sehe, dass...                        │  │
│  │                                                        │  │
│  │ Kunde (17:34)                                          │  │
│  │ Vielen Dank für die schnelle Hilfe!                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  📊 BEWERTUNGSDIMENSIONEN                    3 von 4 bewertet │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │  Freundlichkeit                                        │  │
│  │  Wie freundlich ist der Ton der Kommunikation?        │  │
│  │  ●━━━━━●━━━━━●━━━━━○━━━━━○    [3/5]                   │  │
│  │  Sehr gut    Gut    Neutral   Schlecht   Sehr schlecht │  │
│  │                                                        │  │
│  │  ─────────────────────────────────────────────────────│  │
│  │                                                        │  │
│  │  Klarheit                                              │  │
│  │  Wie klar und verständlich ist die Kommunikation?     │  │
│  │  ●━━━━━●━━━━━○━━━━━○━━━━━○    [2/5]                   │  │
│  │                                                        │  │
│  │  ─────────────────────────────────────────────────────│  │
│  │                                                        │  │
│  │  Lösungsorientierung                                   │  │
│  │  Wurde das Problem des Kunden gelöst?                 │  │
│  │  ●━━━━━●━━━━━●━━━━━●━━━━━○    [4/5]                   │  │
│  │                                                        │  │
│  │  ─────────────────────────────────────────────────────│  │
│  │                                                        │  │
│  │  Professionalität                                      │  │
│  │  Wie professionell ist die Beratung?                  │  │
│  │  ○━━━━━○━━━━━○━━━━━○━━━━━○    [-/5]                   │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  [Weiter →]                             Auto-Save: ✓         │
└──────────────────────────────────────────────────────────────┘
```

### Mail Rating - Komponenten

```
views/Evaluation/
└── MailRatingSession.vue              # Hauptcontainer

components/Evaluation/MailRating/
├── MailRatingContent.vue              # Oben: E-Mail-Verlauf (das zu Bewertende)
├── MailRatingDimensions.vue           # Unten: Dimensionen-Liste
├── DimensionRatingRow.vue             # Einzelne Dimension + Likert
└── LikertScaleHorizontal.vue          # Horizontale Likert-Skala mit Labels
```

---

## Teil 3: Vergleich der Layouts

### Feature Rating vs Mail Rating

```
FEATURE RATING (type=2)              MAIL RATING (type=3)
┌─────────────┬─────────────┐        ┌─────────────────────────┐
│   KONTEXT   │  FEATURES   │        │   ZU BEWERTENDER TEXT   │
│             │             │        │                         │
│  E-Mail     │ ┌─────────┐ │        │  E-Mail-Verlauf         │
│  Verlauf    │ │Feature 1│ │        │  (scrollbar)            │
│  (hilft     │ │ ●●●○○   │ │        │                         │
│   beim      │ └─────────┘ │        ├─────────────────────────┤
│   Bewerten) │ ┌─────────┐ │        │   DIMENSIONEN           │
│             │ │Feature 2│ │        │                         │
│             │ │ ○○○○○   │ │        │  Freundlichkeit ●●●○○   │
│             │ └─────────┘ │        │  Klarheit       ●●○○○   │
│             │             │        │  Lösung         ●●●●○   │
└─────────────┴─────────────┘        └─────────────────────────┘

Zwei Spalten:                        Eine Spalte:
Links = Kontext                      Oben = Das zu Bewertende
Rechts = Was bewertet wird           Unten = Bewertungskriterien
```

---

## Teil 4: Gemeinsame Komponenten

Beide Rating-Typen teilen sich einige Basis-Komponenten:

```
components/Evaluation/shared/
├── LikertScale.vue                  # Basis Likert-Skala
├── RatingProgress.vue               # Fortschrittsanzeige
├── RatingKeyboardHints.vue          # Tastatur-Shortcuts Anzeige
└── AutoSaveIndicator.vue            # Speicher-Status

composables/
├── useRatingKeyboard.js             # Tastatur: 1-5, Tab, Enter
├── useRatingAutoSave.js             # Debounced Auto-Save
└── useRatingProgress.js             # Fortschritts-Tracking
```

### Gemeinsame Features

| Feature | Beschreibung |
|---------|-------------|
| **Tastatur-Navigation** | 1-5 zum Bewerten, Tab/Enter für nächstes |
| **Auto-Save** | Speichert 500ms nach letzter Änderung |
| **Fortschritt** | Zeigt X/Y bewertet |
| **Thread-Navigation** | ←/→ Pfeile für vorherigen/nächsten Thread |

---

## Teil 5: Routing

### Neue Routen

```javascript
// Feature Rating (type=2)
{
  path: '/scenarios/:scenarioId/rate/features/:threadId',
  name: 'FeatureRatingSession',
  component: () => import('@/views/Evaluation/FeatureRatingSession.vue')
},

// Mail Rating (type=3)
{
  path: '/scenarios/:scenarioId/rate/mail/:threadId',
  name: 'MailRatingSession',
  component: () => import('@/views/Evaluation/MailRatingSession.vue')
},

// Legacy Redirects
{
  path: '/Rater/:id',
  redirect: to => {
    // Ermittle Szenario-Typ und leite entsprechend weiter
    return { name: 'RaterLegacyRedirect', params: { id: to.params.id } }
  }
}
```

### Automatische Typ-Erkennung

```javascript
// In ScenarioEvaluationTab.vue
function startEvaluation(thread) {
  const route = scenario.function_type_id === 3
    ? { name: 'MailRatingSession', params: { scenarioId, threadId: thread.id } }
    : { name: 'FeatureRatingSession', params: { scenarioId, threadId: thread.id } }

  router.push(route)
}
```

---

## Teil 6: Implementierungsplan

### Phase 1: Shared Components
1. `LikertScale.vue` - Basis-Komponente
2. `useRatingKeyboard.js` - Tastatur-Support
3. `useRatingAutoSave.js` - Auto-Save Logik

### Phase 2: Feature Rating
1. `FeatureRatingSession.vue` - Hauptcontainer
2. `FeatureRatingContext.vue` - E-Mail Panel
3. `FeatureRatingList.vue` - Feature-Liste
4. `FeatureRatingCard.vue` - Einzelnes Feature

### Phase 3: Mail Rating
1. `MailRatingSession.vue` - Hauptcontainer
2. `MailRatingContent.vue` - E-Mail Display
3. `MailRatingDimensions.vue` - Dimensions-Liste
4. `DimensionRatingRow.vue` - Einzelne Dimension

### Phase 4: Migration
1. Routing aktualisieren
2. Legacy-Redirects einrichten
3. Alte Komponenten deprecaten

---

## Teil 7: Beispiel-Szenarien

### Feature Rating Beispiel
```
Szenario: "Demo Rating Szenario" (ID: 1)
Typ: rating (2)

Thread: "Kundenanfrage Bestellung #1234"
├── Feature: GPT-4 Zusammenfassung → Bewerte [1-5]
├── Feature: Claude Zusammenfassung → Bewerte [1-5]
├── Feature: GPT-4 Kategorie → Bewerte [1-5]
└── Feature: GPT-4 Betreff → Bewerte [1-5]
```

### Mail Rating Beispiel
```
Szenario: "Demo Verlauf Bewerter Szenario" (ID: 3)
Typ: mail_rating (3)

Thread: "Kundenanfrage Bestellung #1234"
├── Dimension: Freundlichkeit → Bewerte [1-5]
├── Dimension: Klarheit → Bewerte [1-5]
├── Dimension: Lösungsorientierung → Bewerte [1-5]
└── Dimension: Professionalität → Bewerte [1-5]
```

---

## Offene Fragen

1. **Dimensionen-Konfiguration:** Wo werden die Bewertungsdimensionen für Mail Rating definiert? (Szenario-Config?)
2. **Feature-Gruppierung:** Sollen Features nach Typ (Zusammenfassung, Kategorie) oder nach LLM (GPT-4, Claude) gruppiert werden?
3. **Vergleichsmodus:** Sollen bei Feature Rating mehrere LLM-Outputs desselben Typs nebeneinander angezeigt werden?
