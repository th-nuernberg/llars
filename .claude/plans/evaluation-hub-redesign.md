# Konzept: Evaluation Hub Redesign

## Aktuelle Struktur (ALT)

```
/evaluation                    → Hub mit Kategorien (Ranking, Rating, etc.)
  └── Klick auf Kategorie
        ├── /Rater            → Liste von Rating-Szenarien
        ├── /Ranker           → Liste von Ranking-Szenarien
        └── etc.
              └── Klick auf Szenario
                    └── /Rater/:id  → Einzelne Items bewerten
```

**Problem:** Zu viele Navigationsebenen, unnötige Trennung nach Typ.

---

## Neue Struktur (NEU)

```
/evaluation                    → Alle Szenarien als Karten (kein Kategorie-Split)
  └── Klick auf Szenario-Karte
        └── /evaluation/:id    → Items des Szenarios als Kacheln
              └── Klick auf Item-Kachel
                    └── /evaluation/:id/item/:itemId  → Bewertungs-Interface
```

**Vorteile:**
- Eine Navigationsebene weniger
- Alle Szenarien auf einen Blick
- Konsistente UX für alle Typen

---

## Komponenten-Struktur

### 1. EvaluationHub.vue (NEU)

**Route:** `/evaluation`

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Evaluierungen                              [Filter ▼]  │
│  Alle Szenarien, an denen Sie teilnehmen               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 🏷️ Rating   │  │ 📊 Ranking  │  │ ⚖️ Vergleich│     │
│  │             │  │             │  │             │     │
│  │ LLM-Judge   │  │ Demo        │  │ A vs B      │     │
│  │ Demo        │  │ Ranking     │  │ Test        │     │
│  │             │  │             │  │             │     │
│  │ 3/12 ✓      │  │ 5/20 ✓      │  │ 0/8         │     │
│  │ 4 Dims      │  │ 3 Buckets   │  │ 10 Paare    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ ✅ Labeling │  │ 📧 Mail     │  │ 🔍 Echt/    │     │
│  │             │  │ Rating      │  │ Fake        │     │
│  │ Sentiment   │  │             │  │             │     │
│  │ Analyse     │  │ Beratungs-  │  │ Authenticity│     │
│  │             │  │ qualität    │  │ Check       │     │
│  │ 10/10 ✓     │  │ 2/15 ✓      │  │ 7/12 ✓      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Alle Szenarien in einem Grid
- Farbiges Icon/Badge zeigt Typ (Rating, Ranking, etc.)
- Fortschrittsanzeige pro Szenario
- Optional: Filter nach Typ, Status

---

### 2. EvaluationScenario.vue (NEU)

**Route:** `/evaluation/:scenarioId`

**Layout für alle Typen:**
```
┌─────────────────────────────────────────────────────────┐
│  ← Zurück    LLM-as-Judge Demo              [i] [⚙️]   │
│              Bewerten Sie LLM-Antworten                 │
│              Rating • 3/12 abgeschlossen                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ ✓ Done  │  │ ✓ Done  │  │ ◐ 2/4   │  │ ○ Offen │   │
│  │         │  │         │  │         │  │         │   │
│  │ Item 1  │  │ Item 2  │  │ Item 3  │  │ Item 4  │   │
│  │ "Was    │  │ "Wie    │  │ "Erkläre│  │ "Solar- │   │
│  │ ist ML?"│  │ Photo-  │  │ Relativ-│  │ energie"│   │
│  │         │  │ synthese│  │ ität"   │  │         │   │
│  │ Score:  │  │ Score:  │  │         │  │         │   │
│  │ 4.2/5   │  │ 3.8/5   │  │         │  │         │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ ○ Offen │  │ ○ Offen │  │ ○ Offen │  │ ○ Offen │   │
│  │ Item 5  │  │ Item 6  │  │ Item 7  │  │ Item 8  │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Klick auf Item-Kachel → Bewertungs-Interface (typ-spezifisch)**

---

## Typ-spezifische Item-Karten

### Rating (function_type_id = 2)

```
┌─────────────────────┐
│ ✓ Abgeschlossen     │  Status-Badge
├─────────────────────┤
│ Was ist ML?         │  Item-Titel/Subject
│                     │
│ "Maschinelles       │  Vorschau (erste 100 Zeichen)
│ Lernen ist ein      │
│ Teilgebiet..."      │
├─────────────────────┤
│ ⭐ 4.2/5            │  Gesamtbewertung
│ 4/4 Dimensionen     │  Dimensionen bewertet
└─────────────────────┘
```

**Bewertungs-Interface:** Links Text, Rechts Likert-Skalen

---

### Ranking (function_type_id = 1)

```
┌─────────────────────┐
│ ◐ In Bearbeitung    │
├─────────────────────┤
│ E-Mail Thread #42   │
│                     │
│ "Anfrage zur        │
│ Studienberatung..." │
├─────────────────────┤
│ 📊 3/5 Features     │  Features geranked
│ geranked            │
└─────────────────────┘
```

**Bewertungs-Interface:** Features in Buckets sortieren

---

### Comparison (function_type_id = 4)

```
┌─────────────────────┐
│ ○ Offen             │
├─────────────────────┤
│ Vergleich #7        │
│                     │
│ GPT-4 vs Claude     │  Modell-Paarung
│                     │
├─────────────────────┤
│ ⚖️ Noch keine       │
│ Präferenz           │
└─────────────────────┘
```

**Bewertungs-Interface:** A vs B Side-by-Side

---

### Labeling (function_type_id = 7)

```
┌─────────────────────┐
│ ✓ Gelabelt          │
├─────────────────────┤
│ Text #23            │
│                     │
│ "Der Service war    │
│ ausgezeichnet..."   │
├─────────────────────┤
│ 🏷️ Positiv          │  Zugewiesenes Label
└─────────────────────┘
```

**Bewertungs-Interface:** Label-Auswahl mit Kategorie-Chips

---

### Authenticity (function_type_id = 5)

```
┌─────────────────────┐
│ ✓ Bewertet          │
├─────────────────────┤
│ E-Mail #15          │
│                     │
│ "Sehr geehrte       │
│ Damen und Herren..."|
├─────────────────────┤
│ 🔍 Echt (85%)       │  Abstimmungsergebnis
└─────────────────────┘
```

**Bewertungs-Interface:** Echt/Fake Toggle mit Konfidenz

---

### Mail Rating (function_type_id = 3)

```
┌─────────────────────┐
│ ◐ 3/5 Dimensionen   │
├─────────────────────┤
│ Beratungs-Thread    │
│ #8                  │
│                     │
│ "Klient: Ich habe   │
│ Probleme mit..."    │
├─────────────────────┤
│ ⭐ 3.5/5            │
│ Empathie, Klarheit  │  Bewertete Dimensionen
└─────────────────────┘
```

**Bewertungs-Interface:** Wie Rating, aber mail-spezifisch

---

## Routing-Änderungen

### Alt → Neu

| Alt | Neu | Beschreibung |
|-----|-----|--------------|
| `/evaluation` | `/evaluation` | Hub mit allen Szenarien |
| `/Rater` | ❌ entfernt | Nicht mehr nötig |
| `/Rater/:id` | `/evaluation/:id` | Szenario-Detail mit Items |
| `/Rater/:id/:feature` | `/evaluation/:id/item/:itemId` | Bewertungs-Interface |
| `/Ranker` | ❌ entfernt | Nicht mehr nötig |
| `/Ranker/:id` | `/evaluation/:id` | Einheitlich |

### Neue Routen

```javascript
// router.js
{
  path: '/evaluation',
  name: 'EvaluationHub',
  component: EvaluationHub
},
{
  path: '/evaluation/:scenarioId',
  name: 'EvaluationScenario',
  component: EvaluationScenario,
  props: true
},
{
  path: '/evaluation/:scenarioId/item/:itemId',
  name: 'EvaluationItem',
  component: EvaluationItem,
  props: true
}
```

---

## Komponenten-Hierarchie

```
EvaluationHub.vue
├── ScenarioCard.vue (wiederverwendbar für alle Typen)
│   ├── ScenarioTypeBadge.vue
│   └── ProgressIndicator.vue
│
EvaluationScenario.vue
├── ScenarioHeader.vue
├── ItemGrid.vue
│   └── ItemCard.vue (typ-spezifisch)
│       ├── RatingItemCard.vue
│       ├── RankingItemCard.vue
│       ├── ComparisonItemCard.vue
│       ├── LabelingItemCard.vue
│       └── AuthenticityItemCard.vue
│
EvaluationItem.vue (Router-View für typ-spezifisches Interface)
├── RatingInterface.vue (bereits vorhanden)
├── RankingInterface.vue
├── ComparisonInterface.vue
├── LabelingInterface.vue
└── AuthenticityInterface.vue
```

---

## API-Endpunkte

### Bestehend (nutzen)

- `GET /api/scenarios` - Alle Szenarien des Users
- `GET /api/scenarios/:id` - Szenario-Details
- `GET /api/evaluation/rating/:id/items` - Items für Rating
- etc.

### Vereinheitlichen

Idealerweise ein generischer Endpunkt:
```
GET /api/evaluation/:scenarioId/items
```
Der je nach `function_type_id` die richtigen Items zurückgibt.

---

## Implementierungsreihenfolge

### Phase 1: EvaluationHub (NEU)
1. Neues `EvaluationHub.vue` erstellen
2. Alle Szenarien als Karten anzeigen
3. Filter-Funktion (optional)

### Phase 2: EvaluationScenario (NEU)
1. Neues `EvaluationScenario.vue` erstellen
2. Items als Kacheln laden
3. Typ-spezifische ItemCards

### Phase 3: Routing-Migration
1. Alte Routen (`/Rater`, `/Ranker`) als Redirects
2. Neue einheitliche Routen aktivieren

### Phase 4: Cleanup
1. Alte Komponenten entfernen oder deprecaten
2. Tests aktualisieren

---

## Offene Fragen

1. **Sollen alte Routen weiterhin funktionieren?**
   → Empfehlung: Redirects für Backward-Compatibility

2. **Filter im Hub?**
   → Typ-Filter, Status-Filter, Suchfeld?

3. **Sortierung?**
   → Nach Deadline, Fortschritt, zuletzt bearbeitet?

---

## Zusammenfassung

| Aspekt | Alt | Neu |
|--------|-----|-----|
| Hub | Kategorien | Alle Szenarien |
| Navigation | 3 Ebenen | 2 Ebenen |
| Routing | `/Rater/:id` | `/evaluation/:id` |
| Komponenten | Typ-spezifisch | Generisch + Typ-Adapter |
