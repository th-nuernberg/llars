# LLM Evaluator Components

Vue 3 Frontend-Komponenten für das LLM Evaluator System in LLARS.

## Übersicht

Das Judge-System ermöglicht die automatisierte Bewertung und Vergleich von Prompt-Säulen mittels LLM-Evaluation.

## Komponenten

### 1. JudgeOverview.vue
**Route:** `/judge`

**Beschreibung:** Übersichtsseite mit Liste aller Judge-Sessions

**Features:**
- Session-Statistiken (Gesamt, Abgeschlossen, Laufend, In Warteschlange)
- Filterable Session-Tabelle
- Status-Anzeige mit Farb-Chips
- Progress-Anzeige für jede Session
- Quick-Actions (Details, Ergebnisse, Löschen)
- Löschen-Dialog mit Bestätigung

**API-Calls:**
- `GET /api/judge/sessions` - Liste aller Sessions
- `DELETE /api/judge/sessions/:id` - Session löschen

---

### 2. JudgeConfig.vue
**Route:** `/judge/config`

**Beschreibung:** Konfigurationsformular für neue Judge-Sessions

**Features:**
- Session-Name eingeben
- Säulen auswählen (1-5) mit Chips
- Vergleichs-Modus (all_pairs / specific)
- Samples pro Säule (Slider 1-50)
- Position-Swap Toggle
- Live-Berechnung der geschätzten Vergleiche
- Live-Zeitschätzung
- Zusammenfassungs-Card mit allen Parametern

**Berechnungen:**
- **Paare:** `n * (n - 1) / 2` (für n Säulen)
- **Vergleiche:** `Paare × Samples × (Swap ? 2 : 1)`
- **Dauer:** `≈ 10 Sekunden pro Vergleich`

**API-Calls:**
- `POST /api/judge/sessions` - Session erstellen

**Payload:**
```json
{
  "session_name": "string",
  "pillar_ids": [1, 2, 3],
  "comparison_mode": "all_pairs",
  "samples_per_pillar": 10,
  "position_swap": true
}
```

---

### 3. JudgeSession.vue
**Route:** `/judge/session/:id`

**Beschreibung:** Live-Evaluation View mit Echtzeit-Updates

**Features:**
- Session-Status und Fortschritt-Anzeige
- Start/Pause/Resume Controls
- Zwei-Spalten-Ansicht (Thread A vs Thread B)
- Zentrale LLM-Status-Anzeige
- Winner-Display mit Trophy-Icon
- Konfidenz-Score Anzeige
- Chain-of-Thought Expansion-Panel
- JSON-Preview expandierbar
- Vergleichs-Historie-Tabelle
- **Socket.IO Live-Updates:**
  - `session_update` - Session-Fortschritt
  - `comparison_update` - Aktueller Vergleich
  - `comparison_completed` - Neuer abgeschlossener Vergleich

**API-Calls:**
- `GET /api/judge/sessions/:id` - Session-Details
- `GET /api/judge/sessions/:id/current` - Aktueller Vergleich
- `GET /api/judge/sessions/:id/comparisons` - Alle Vergleiche
- `POST /api/judge/sessions/:id/start` - Session starten
- `POST /api/judge/sessions/:id/pause` - Session pausieren

**Socket.IO Events:**
```javascript
socket.emit('join_session', { session_id: sessionId })
socket.on('session_update', (data) => { ... })
socket.on('comparison_update', (data) => { ... })
socket.on('comparison_completed', (data) => { ... })
```

---

### 4. JudgeResults.vue
**Route:** `/judge/results/:id`

**Beschreibung:** Auswertungs-Dashboard mit detaillierten Ergebnissen

**Features:**
- **Statistik-Cards:**
  - Gesamt Vergleiche
  - Beste Säule
  - Ø Konfidenz
  - Laufzeit
- **Säulen-Ranking:**
  - Sortiert nach Score
  - Siege/Niederlagen-Anzeige
  - Win-Rate Chips
  - Rang-basierte Farben
- **Win-Matrix Heatmap:**
  - Zeile = Angreifer, Spalte = Verteidiger
  - Heatmap-Färbung basierend auf Siege
  - Hover-Effekte
- **Detaillierte Metriken-Tabelle:**
  - Win-Rate mit Progress-Bar
  - Durchschnittliche Konfidenz
  - Score-Anzeige
- **Alle Vergleiche-Tabelle:**
  - Vollständige Historie
  - Paarungen mit Chips
  - Winner-Anzeige
  - Konfidenz-Scores
- **Export-Funktionen:**
  - CSV-Download
  - JSON-Download

**API-Calls:**
- `GET /api/judge/sessions/:id` - Session-Info
- `GET /api/judge/sessions/:id/results` - Aggregierte Ergebnisse
- `GET /api/judge/sessions/:id/comparisons` - Alle Vergleiche
- `GET /api/judge/sessions/:id/export/csv` - CSV-Export
- `GET /api/judge/sessions/:id/export/json` - JSON-Export

**Ergebnis-Struktur:**
```json
{
  "total_comparisons": 30,
  "pillar_metrics": [
    {
      "pillar_id": 1,
      "name": "Säule 1",
      "wins": 12,
      "losses": 8,
      "win_rate": 0.6,
      "avg_confidence": 0.85,
      "score": 4.2,
      "total_comparisons": 20
    }
  ],
  "win_matrix": {
    "1_vs_2": 5,
    "1_vs_3": 7,
    "2_vs_1": 3,
    ...
  }
}
```

---

## Verwendung

### Installation
Die Komponenten sind bereits im Router registriert:
```javascript
import JudgeOverview from "@/components/Judge/JudgeOverview.vue";
import JudgeConfig from "@/components/Judge/JudgeConfig.vue";
import JudgeSession from "@/components/Judge/JudgeSession.vue";
import JudgeResults from "@/components/Judge/JudgeResults.vue";
```

### Navigation
```javascript
// Zur Übersicht
router.push({ name: 'JudgeOverview' })

// Zur Konfiguration
router.push({ name: 'JudgeConfig' })

// Zu Session-Details
router.push({ name: 'JudgeSession', params: { id: sessionId } })

// Zu Ergebnissen
router.push({ name: 'JudgeResults', params: { id: sessionId } })
```

### Home-Integration
Ein Link zum Judge-System ist bereits in der Home-Komponente verfügbar:
```javascript
{
  title: 'LLM-as-Judge',
  description: "Automatisierte Bewertung und Vergleich von Prompt-Säulen mit KI",
  route: '/judge',
  icon: 'mdi-gavel',
  permission: null  // Für alle verfügbar
}
```

---

## Status-Werte

| Status | Farbe | Icon | Beschreibung |
|--------|-------|------|--------------|
| `created` | grey | mdi-file-document | Neu erstellt, noch nicht gestartet |
| `queued` | warning | mdi-clock-outline | In Warteschlange |
| `running` | info | mdi-play-circle | Aktiv in Bearbeitung |
| `paused` | orange | mdi-pause-circle | Pausiert |
| `completed` | success | mdi-check-circle | Erfolgreich abgeschlossen |
| `failed` | error | mdi-alert-circle | Fehlgeschlagen |

---

## Technologie-Stack

- **Vue 3** - Composition API mit `<script setup>`
- **Vuetify 3** - Material Design Komponenten
- **Axios** - HTTP-Client für API-Calls
- **Socket.IO Client** - Echtzeit-Updates
- **Vue Router** - Navigation

---

## Stil-Konventionen

- Alle Komponenten folgen dem LLARS-Theme (Light/Dark Mode Support)
- Vuetify 3 Komponenten für UI-Konsistenz
- Responsive Design (Mobile-First)
- Hover-Effekte für interaktive Elemente
- Loading-States für alle API-Calls
- Error-Handling mit Try-Catch

---

## Nächste Schritte

1. **Backend-API implementieren** (siehe Backend-Tasks)
2. **Socket.IO Server konfigurieren** für Live-Updates
3. **Permissions hinzufügen** (optional)
4. **Tests schreiben** für Komponenten
5. **Dokumentation erweitern** mit Screenshots

---

**Erstellt:** 2025-11-25
**Version:** 1.0
**Entwickler:** LLARS Team
