# Heatmap-Globalisierung Konzept

**Datum:** 25. Januar 2026
**Status:** Konzept zur Überprüfung

---

## 1. Ist-Analyse

### 1.1 Vorhandene Heatmap-Komponenten

| Komponente | Pfad | Status | Verwendung |
|------------|------|--------|------------|
| `LConfusionMatrix.vue` | `components/common/` | Global | ScenarioEvaluationTab (Authenticity) |
| `LRatingDistribution.vue` | `components/common/` | Global | ScenarioEvaluationTab (Dimensionen) |
| `AgreementHeatmap.vue` | `components/charts/` | Lokal | **Nicht verwendet** (standalone) |
| `TransitionHeatmap.vue` | `components/OnCoCo/` | Lokal | OnCoCoResults.vue |
| **Inline Heatmap** | ScenarioEvaluationTab.vue:800-870 | Inline | Inter-Rater Agreement |

### 1.2 Identifizierte Probleme

1. **Duplizierter Code**: ScenarioEvaluationTab enthält eine inline implementierte Heatmap (Zeilen 800-870) für Inter-Rater Agreement, obwohl `AgreementHeatmap.vue` bereits existiert

2. **Inkonsistente Farbschemata**:
   - `AgreementHeatmap`: Rot→Gelb→Grün (#e8a087 → #e8c87a → #b0ca97)
   - `TransitionHeatmap`: Weiß→Blau (linear gradient)
   - `LConfusionMatrix`: Grün/Rot basierend auf korrekt/inkorrekt
   - `LRatingDistribution`: Konfigurierbar (default: #b0ca97)
   - Inline Heatmap: Rot→Gelb→Grün (ähnlich AgreementHeatmap)

3. **Keine gemeinsame Basis**: Jede Komponente implementiert eigene Hover-Logik, Farbberechnung und Zellendarstellung

4. **Fehlende Wiederverwendbarkeit**: TransitionHeatmap ist OnCoCo-spezifisch benannt, könnte aber generisch sein

---

## 2. Ziel-Architektur

### 2.1 Komponentenhierarchie

```
components/common/
├── heatmap/
│   ├── LHeatmapBase.vue          # NEU: Basis-Komponente mit gemeinsamer Logik
│   ├── LHeatmapCell.vue          # NEU: Einzelne Zelle mit Hover, Farbe, Wert
│   └── useHeatmapColors.js       # NEU: Composable für Farbschemata
│
├── LConfusionMatrix.vue          # Bestehend (nutzt LHeatmapBase)
├── LRatingDistribution.vue       # Bestehend (nutzt LHeatmapBase)
├── LAgreementHeatmap.vue         # Verschoben aus charts/ und umbenannt
└── LTransitionMatrix.vue         # Verschoben aus OnCoCo/ und umbenannt
```

### 2.2 Farbschema-Standardisierung

```javascript
// useHeatmapColors.js - Color Presets

export const HEATMAP_COLOR_SCHEMES = {
  // Für Übereinstimmung/Qualität: Schlecht → Mittel → Gut
  agreement: {
    low: '#e8a087',      // LLARS Danger (Rot)
    mid: '#D1BC8A',      // LLARS Secondary (Gelb/Gold)
    high: '#98d4bb'      // LLARS Success (Grün)
  },

  // Für Häufigkeit/Intensität: Keine → Viel
  frequency: {
    zero: 'var(--v-theme-surface)',
    low: 'rgba(136, 196, 200, 0.3)',   // LLARS Accent leicht
    high: '#88c4c8'                     // LLARS Accent voll
  },

  // Für Korrektheit: Richtig/Falsch
  correctness: {
    correct: 'rgba(152, 212, 187, 0.6)',   // Grün
    incorrect: 'rgba(232, 160, 135, 0.6)'  // Rot
  },

  // Für Rating-Verteilung: Neutral → Primär
  distribution: {
    empty: '#f5f5f5',
    primary: '#b0ca97'  // LLARS Primary
  }
}
```

---

## 3. Änderungen im Detail

### 3.1 Neue Dateien erstellen

| Datei | Beschreibung |
|-------|--------------|
| `components/common/heatmap/LHeatmapBase.vue` | Basis-Komponente mit Grid-Layout, Achsen-Labels, Legende |
| `components/common/heatmap/LHeatmapCell.vue` | Einzelne Zelle mit konfigurierbarem Styling |
| `components/common/heatmap/useHeatmapColors.js` | Composable für Farbberechnung und Schemata |
| `components/common/heatmap/index.js` | Export der Heatmap-Module |

### 3.2 Bestehende Dateien ändern

| Datei | Änderung | Aufwand |
|-------|----------|---------|
| `components/charts/AgreementHeatmap.vue` | Verschieben nach `common/LAgreementHeatmap.vue`, auf LHeatmapBase umstellen | Mittel |
| `components/OnCoCo/TransitionHeatmap.vue` | Kopieren nach `common/LTransitionMatrix.vue`, Original als Wrapper | Mittel |
| `views/ScenarioManager/.../ScenarioEvaluationTab.vue` | Inline-Heatmap (800-870) durch `<LAgreementHeatmap>` ersetzen | Gering |
| `components/OnCoCo/OnCoCoResults.vue` | Import auf `LTransitionMatrix` ändern | Gering |
| `components/common/LConfusionMatrix.vue` | Optional: Auf LHeatmapBase refactorn | Optional |
| `components/common/LRatingDistribution.vue` | Optional: Auf LHeatmapBase refactorn | Optional |
| `components/common/index.js` | Neue Heatmap-Komponenten exportieren | Gering |

### 3.3 Prioritäten

**Phase 1 (Sofort):**
1. Inline-Heatmap in ScenarioEvaluationTab durch `AgreementHeatmap` ersetzen
2. `AgreementHeatmap.vue` nach `common/LAgreementHeatmap.vue` verschieben

**Phase 2 (Später):**
1. `useHeatmapColors.js` Composable erstellen
2. `LHeatmapBase.vue` und `LHeatmapCell.vue` erstellen
3. Bestehende Komponenten auf die Basis umstellen
4. `TransitionHeatmap` globalisieren

---

## 4. Detailierte Code-Änderungen

### 4.1 ScenarioEvaluationTab.vue - Inline Heatmap ersetzen

**Vorher (Zeilen 790-870):** Inline implementierte Heatmap

**Nachher:**
```vue
<template>
  <!-- Inter-Rater Agreement Heatmap (Right, centered) -->
  <div class="visualization-panel heatmap-panel" v-if="hasPairwiseAgreement">
    <h4 class="subsection-title">
      {{ $t('scenarioManager.results.interRaterAgreement') }}
      <LTooltip :text="$t('scenarioManager.tooltips.interRaterAgreement')" location="top">
        <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
      </LTooltip>
    </h4>

    <LAgreementHeatmap
      :evaluators="pairwiseEvaluators"
      :agreements="pairwiseAgreements"
      :title="$t('scenarioManager.results.interRaterAgreement')"
      :show-values="true"
    />
  </div>
</template>

<script setup>
import { LAgreementHeatmap } from '@/components/common'

// Computed für die Heatmap-Daten
const pairwiseEvaluators = computed(() => {
  const pairwise = props.liveStats?.pairwiseAgreement
  if (!pairwise?.evaluators) return []
  return pairwise.evaluators.map(e => ({
    id: e.id,
    name: e.name,
    isLLM: e.isLLM || false
  }))
})

const pairwiseAgreements = computed(() => {
  const pairwise = props.liveStats?.pairwiseAgreement
  if (!pairwise?.matrix) return {}
  return pairwise.matrix  // Format: { 'id1-id2': agreementValue }
})
</script>
```

### 4.2 LAgreementHeatmap.vue - Verschieben und Anpassen

```bash
# Verschieben
mv llars-frontend/src/components/charts/AgreementHeatmap.vue \
   llars-frontend/src/components/common/LAgreementHeatmap.vue
```

Änderungen in der Datei:
- Prefix `L` hinzufügen
- LLARS Design System Farben verwenden
- Export in `components/common/index.js` hinzufügen

### 4.3 components/common/index.js - Exports erweitern

```javascript
// Heatmap/Matrix Components
export { default as LConfusionMatrix } from './LConfusionMatrix.vue'
export { default as LRatingDistribution } from './LRatingDistribution.vue'
export { default as LAgreementHeatmap } from './LAgreementHeatmap.vue'  // NEU
```

---

## 5. Zu löschende Code-Bereiche

### ScenarioEvaluationTab.vue

**Template (zu entfernen/ersetzen):**
- Zeilen 800-870: Inline `heatmap-matrix` Implementation

**Script (zu entfernen):**
- `getAgreementCellStyle()` Funktion
- `getShortEvaluatorName()` Funktion (falls nur für Heatmap)
- `highlightedAgreementCell` ref
- `onAgreementCellHover()` / `onAgreementCellLeave()` Funktionen

**Styles (zu entfernen):**
- Zeilen 3586-3620: `.agreement-heatmap-container`, `.heatmap-matrix`, etc.

---

## 6. Testplan

| Test | Beschreibung |
|------|--------------|
| Visual Regression | Screenshot-Vergleich vor/nach für ScenarioEvaluationTab |
| Hover-Interaktion | Tooltip und Highlight bei Zellen-Hover |
| Responsive | Heatmap-Darstellung auf verschiedenen Bildschirmgrößen |
| LLM-Markierung | Robot-Icon bei LLM-Evaluatoren sichtbar |
| Farb-Gradient | Korrekte Farbdarstellung von 0% bis 100% |

---

## 7. Zusammenfassung der Änderungen

| Kategorie | Anzahl |
|-----------|--------|
| Neue Dateien | 1 (Phase 1), +4 (Phase 2) |
| Geänderte Dateien | 3 (Phase 1) |
| Gelöschte Code-Zeilen | ~150 (Inline-Heatmap + Styles) |
| Geschätzter Aufwand | Phase 1: 1-2h, Phase 2: 4-6h |

---

## 8. Entscheidungspunkte

1. **Soll Phase 2 implementiert werden?**
   - Pro: Einheitliche Codebasis, einfachere Wartung
   - Contra: Größerer Aufwand, bestehende Komponenten funktionieren

2. **Soll TransitionHeatmap globalisiert werden?**
   - Aktuell nur in OnCoCo verwendet
   - Könnte für andere Übergangsmatrizen nützlich sein

3. **Soll LConfusionMatrix auf LHeatmapBase umgestellt werden?**
   - Bereits gut strukturiert
   - Könnte von gemeinsamer Farblogik profitieren
