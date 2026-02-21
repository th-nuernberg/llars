<template>
  <div class="data-format-guide">
    <!-- Quick Start Section -->
    <LCard
      class="mb-4"
      title="Schnellstart"
      icon="mdi-rocket-launch-outline"
      color="#98d4bb"
    >
      <p class="intro-text">
        Wähle einen Evaluationstyp und kopiere das Minimalbeispiel als Startpunkt.
        Die vollständigen Beispiele zeigen alle verfügbaren Optionen.
      </p>

      <div class="type-overview">
        <div
          v-for="evalType in evaluationTypes"
          :key="evalType.id"
          class="type-chip"
          :class="{ active: activeType === evalType.id }"
          @click="activeType = evalType.id"
        >
          <LIcon size="18" :color="evalType.color">{{ evalType.icon }}</LIcon>
          <span>{{ evalType.name }}</span>
        </div>
      </div>
    </LCard>

    <!-- Type-specific Documentation -->
    <LCard
      :title="currentType.name"
      :icon="currentType.icon"
      :color="currentType.color"
    >
      <div class="type-content">
        <p class="type-description">{{ currentType.description }}</p>

        <!-- UI Layout Info -->
        <div class="layout-info">
          <LIcon size="16">mdi-view-dashboard-outline</LIcon>
          <span><strong>UI-Layout:</strong> {{ currentType.layout }}</span>
        </div>

        <!-- Tabs for Minimal/Complete -->
        <LTabs v-model="exampleTab" :tabs="exampleTabs" variant="underlined" class="mt-4" />

        <!-- Minimal Example -->
        <div v-if="exampleTab === 'minimal'" class="example-section">
          <div class="example-header">
            <span class="example-label">
              <LIcon size="16" class="mr-1">mdi-lightning-bolt</LIcon>
              Minimalbeispiel
            </span>
            <LBtn variant="text" size="small" @click="copyToClipboard(currentType.minimalExample)">
              <LIcon size="16">mdi-content-copy</LIcon>
              Kopieren
            </LBtn>
          </div>
          <pre class="code-block">{{ formatJson(currentType.minimalExample) }}</pre>
        </div>

        <!-- Complete Example -->
        <div v-if="exampleTab === 'complete'" class="example-section">
          <div class="example-header">
            <span class="example-label">
              <LIcon size="16" class="mr-1">mdi-file-document-outline</LIcon>
              Vollständiges Beispiel
            </span>
            <LBtn variant="text" size="small" @click="copyToClipboard(currentType.completeExample)">
              <LIcon size="16">mdi-content-copy</LIcon>
              Kopieren
            </LBtn>
          </div>
          <pre class="code-block">{{ formatJson(currentType.completeExample) }}</pre>
        </div>

        <!-- Config Reference -->
        <div class="config-reference mt-4">
          <h4>
            <LIcon size="18" class="mr-1">mdi-cog-outline</LIcon>
            Config-Referenz
          </h4>
          <table class="config-table">
            <thead>
              <tr>
                <th>Feld</th>
                <th>Typ</th>
                <th>Beschreibung</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="field in currentType.configFields" :key="field.name">
                <td><code>{{ field.name }}</code></td>
                <td><code>{{ field.type }}</code></td>
                <td>{{ field.description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </LCard>

    <!-- Link to full documentation -->
    <div class="docs-link">
      <LIcon size="18" class="mr-1">mdi-book-open-variant</LIcon>
      <span>Vollständige Dokumentation: </span>
      <a href="/mkdocs/entwickler/evaluation-datenformate/" target="_blank">
        MkDocs → Entwickler → Evaluation Datenformate
      </a>
    </div>

    <!-- Snackbar for copy feedback -->
    <v-snackbar v-model="showCopySnackbar" :timeout="2000" color="success">
      In Zwischenablage kopiert
    </v-snackbar>
  </div>
</template>

<script setup>
/**
 * DataFormatGuide.vue - Comprehensive Schema Documentation
 *
 * SCHEMA GROUND TRUTH:
 * Uses central schemas from @/schemas/evaluationSchemas.js
 * All examples are generated using the factory functions to ensure consistency.
 */
import { ref, computed } from 'vue'
import {
  EvaluationType,
  SchemaVersion,
  SourceType,
  RankingMode,
  LabelingMode,
  createDefaultRankingBuckets,
  createDefaultScale,
  createDefaultRatingDimensions,
  createDefaultAuthenticityOptions
} from '@/schemas/evaluationSchemas'

const activeType = ref('ranking')
const exampleTab = ref('minimal')
const showCopySnackbar = ref(false)

const exampleTabs = [
  { value: 'minimal', label: 'Minimal' },
  { value: 'complete', label: 'Vollständig' }
]

// Generate examples using central schema factory functions
const defaultBuckets = createDefaultRankingBuckets()
const defaultScale = createDefaultScale()
const defaultDimensions = createDefaultRatingDimensions()
const defaultAuthOptions = createDefaultAuthenticityOptions()

const evaluationTypes = [
  {
    id: EvaluationType.RANKING,
    name: 'Ranking',
    icon: 'mdi-sort',
    color: '#98d4bb',
    description: 'Items per Drag & Drop in Qualitätsbuckets (Gut/Moderat/Schlecht) einordnen.',
    layout: 'Links: Items zum Ranken | Rechts: Referenz/Kontext (optional)',
    minimalExample: {
      schema_version: SchemaVersion.V1_0,
      type: EvaluationType.RANKING,
      items: [
        { id: 'item_1', label: 'Text 1', content: 'Erster Text zum Ranken' },
        { id: 'item_2', label: 'Text 2', content: 'Zweiter Text zum Ranken' }
      ],
      config: {
        mode: RankingMode.SIMPLE,
        buckets: defaultBuckets.slice(0, 2), // Gut + Schlecht für Minimal
        allow_ties: true,
        require_complete: true
      }
    },
    completeExample: {
      schema_version: '1.0',
      type: 'ranking',
      reference: {
        type: 'text',
        label: 'Original-Artikel',
        content: 'Die Teilnehmer des Weltklimagipfels haben sich auf neue ambitionierte Ziele geeinigt...',
        metadata: { source: 'Reuters', date: '2024-01-15' }
      },
      items: [
        {
          id: 'item_1',
          label: 'Zusammenfassung 1',
          source: { type: 'llm', name: 'mistralai/Mistral-Small-3.2' },
          content: 'Auf dem Weltklimagipfel einigten sich die Teilnehmer auf eine CO2-Reduktion von 55%.'
        },
        {
          id: 'item_2',
          label: 'Zusammenfassung 2',
          source: { type: 'llm', name: 'openai/gpt-4' },
          content: 'Die Klimakonferenz beschloss neue Ziele zur Emissionsreduktion.'
        }
      ],
      config: {
        mode: 'simple',
        buckets: [
          { id: 'good', label: { de: 'Gut', en: 'Good' }, color: '#98d4bb', order: 1 },
          { id: 'moderate', label: { de: 'Moderat', en: 'Moderate' }, color: '#D1BC8A', order: 2 },
          { id: 'poor', label: { de: 'Schlecht', en: 'Poor' }, color: '#e8a087', order: 3 }
        ],
        allow_ties: true,
        require_complete: true
      }
    },
    configFields: [
      { name: 'mode', type: '"simple" | "multi_group"', description: 'Einfach oder mit Tabs' },
      { name: 'buckets', type: 'Bucket[]', description: 'Bucket-Definitionen' },
      { name: 'allow_ties', type: 'boolean', description: 'Mehrere Items pro Bucket erlaubt?' },
      { name: 'require_complete', type: 'boolean', description: 'Alle Items müssen zugeordnet werden?' }
    ]
  },
  {
    id: EvaluationType.RATING,
    name: 'Rating',
    icon: 'mdi-star-half-full',
    color: '#D1BC8A',
    description: 'Multi-dimensionale Bewertung auf Likert-Skala (LLM Evaluator Metriken).',
    layout: 'Links: Dimensionen mit Likert-Skalen | Rechts: Zu bewertender Text',
    minimalExample: {
      schema_version: SchemaVersion.V1_0,
      type: EvaluationType.RATING,
      items: [
        { id: 'item_1', label: 'Zu bewertender Text', content: 'Der Text, der bewertet werden soll.' }
      ],
      config: {
        scale: defaultScale,
        dimensions: [defaultDimensions[0]], // Nur erste Dimension für Minimal
        show_overall: false
      }
    },
    completeExample: {
      schema_version: '1.0',
      type: 'rating',
      reference: {
        type: 'text',
        label: 'Quelldokument',
        content: 'Ein führendes Technologieunternehmen hat heute einen bedeutenden Fortschritt vorgestellt...'
      },
      items: [
        {
          id: 'item_1',
          label: 'Generierte Zusammenfassung',
          source: { type: 'llm', name: 'mistralai/Mistral-Small-3.2' },
          content: 'Ein Tech-Konzern stellte eine KI vor, die wissenschaftliche Probleme lösen kann.'
        }
      ],
      config: {
        scale: {
          min: 1,
          max: 5,
          step: 1,
          labels: {
            1: { de: 'Sehr schlecht', en: 'Very poor' },
            3: { de: 'Akzeptabel', en: 'Acceptable' },
            5: { de: 'Sehr gut', en: 'Very good' }
          }
        },
        dimensions: [
          { id: 'coherence', label: { de: 'Kohärenz', en: 'Coherence' }, description: { de: 'Logischer Aufbau', en: 'Logical structure' }, weight: 0.25 },
          { id: 'fluency', label: { de: 'Flüssigkeit', en: 'Fluency' }, weight: 0.25 },
          { id: 'relevance', label: { de: 'Relevanz', en: 'Relevance' }, weight: 0.25 },
          { id: 'consistency', label: { de: 'Konsistenz', en: 'Consistency' }, weight: 0.25 }
        ],
        show_overall: true
      }
    },
    configFields: [
      { name: 'scale.min', type: 'number', description: 'Minimum (meist 1)' },
      { name: 'scale.max', type: 'number', description: 'Maximum (meist 5)' },
      { name: 'scale.labels', type: 'Record<number, I18nLabel>', description: 'Skalenbeschriftungen' },
      { name: 'dimensions', type: 'Dimension[]', description: 'Bewertungsdimensionen mit Gewichtung' },
      { name: 'show_overall', type: 'boolean', description: 'Gesamtscore anzeigen?' }
    ]
  },
  {
    id: EvaluationType.MAIL_RATING,
    name: 'Mail Rating',
    icon: 'mdi-email-outline',
    color: '#88c4c8',
    description: 'Gesamte E-Mail-Konversation bewerten (LLARS-spezifisch).',
    layout: 'Links: Dimensionen mit Likert-Skalen | Rechts: Der gesamte E-Mail-Verlauf',
    minimalExample: {
      schema_version: '1.0',
      type: 'mail_rating',
      items: [
        {
          id: 'item_1',
          label: 'E-Mail-Verlauf',
          content: {
            type: 'conversation',
            messages: [
              { role: 'Klient', content: 'Ich habe eine Frage zu meinem Mietvertrag.' },
              { role: 'Berater', content: 'Gerne helfe ich Ihnen weiter.' }
            ]
          }
        }
      ],
      config: {
        scale: { min: 1, max: 5, step: 1 },
        dimensions: [
          { id: 'quality', label: { de: 'Antwortqualität', en: 'Response Quality' }, weight: 1.0 }
        ],
        focus_role: 'Berater'
      }
    },
    completeExample: {
      schema_version: '1.0',
      type: 'mail_rating',
      reference: null,
      items: [
        {
          id: 'item_1',
          label: 'E-Mail-Verlauf #4521',
          source: { type: 'human' },
          content: {
            type: 'conversation',
            messages: [
              { role: 'Klient', content: 'Ich habe eine Frage zu meinem Mietvertrag. Der Vermieter verlangt 500€ Nachzahlung.', timestamp: '2024-01-10T09:00:00Z' },
              { role: 'Berater', content: 'Haben Sie die Nebenkostenabrechnung bereits geprüft?', timestamp: '2024-01-10T14:30:00Z' },
              { role: 'Klient', content: 'Danke, ich werde die Abrechnung nochmal prüfen.', timestamp: '2024-01-10T15:00:00Z' }
            ]
          }
        }
      ],
      config: {
        scale: { min: 1, max: 5, step: 1 },
        dimensions: [
          { id: 'response_quality', label: { de: 'Antwortqualität', en: 'Response Quality' }, weight: 0.3 },
          { id: 'solution_orientation', label: { de: 'Lösungsorientierung', en: 'Solution Orientation' }, weight: 0.3 },
          { id: 'communication', label: { de: 'Kommunikation', en: 'Communication' }, weight: 0.2 },
          { id: 'timeliness', label: { de: 'Zeitnähe', en: 'Timeliness' }, weight: 0.2 }
        ],
        focus_role: 'Berater'
      }
    },
    configFields: [
      { name: 'scale', type: 'Scale', description: 'Likert-Skala Konfiguration' },
      { name: 'dimensions', type: 'Dimension[]', description: 'Bewertungsdimensionen' },
      { name: 'focus_role', type: 'string', description: 'Welche Rolle wird bewertet? (z.B. "Berater")' }
    ]
  },
  {
    id: EvaluationType.COMPARISON,
    name: 'Comparison',
    icon: 'mdi-scale-balance',
    color: '#b0ca97',
    description: 'Paarweiser A/B-Vergleich: Welche Option ist besser?',
    layout: 'Links: Option A | Rechts: Option B | Unten: Auswahlbuttons',
    minimalExample: {
      schema_version: '1.0',
      type: 'comparison',
      items: [
        { id: 'item_a', label: 'Option A', content: 'Erste Option' },
        { id: 'item_b', label: 'Option B', content: 'Zweite Option' }
      ],
      config: {
        question: { de: 'Welche Option ist besser?', en: 'Which option is better?' },
        allow_tie: true,
        show_source: false
      }
    },
    completeExample: {
      schema_version: '1.0',
      type: 'comparison',
      reference: {
        type: 'text',
        label: 'Originaltext (Englisch)',
        content: 'The quick brown fox jumps over the lazy dog.'
      },
      items: [
        {
          id: 'item_a',
          label: 'Übersetzung A',
          source: { type: 'llm', name: 'deepl/translator' },
          content: 'Der schnelle braune Fuchs springt über den faulen Hund.'
        },
        {
          id: 'item_b',
          label: 'Übersetzung B',
          source: { type: 'llm', name: 'openai/gpt-4' },
          content: 'Der flinke braune Fuchs springt über den trägen Hund.'
        }
      ],
      config: {
        question: { de: 'Welche Übersetzung ist natürlicher?', en: 'Which translation is more natural?' },
        criteria: ['Natürlichkeit', 'Genauigkeit', 'Stil'],
        allow_tie: true,
        show_source: false
      }
    },
    configFields: [
      { name: 'question', type: 'I18nLabel', description: 'Die Vergleichsfrage' },
      { name: 'criteria', type: 'string[]', description: 'Optionale Bewertungskriterien' },
      { name: 'allow_tie', type: 'boolean', description: '"Gleich gut" Option erlauben?' },
      { name: 'show_source', type: 'boolean', description: 'LLM-Namen anzeigen?' }
    ]
  },
  {
    id: EvaluationType.AUTHENTICITY,
    name: 'Authenticity',
    icon: 'mdi-shield-check-outline',
    color: '#e8a087',
    description: 'Binäre Echt/Fake-Klassifikation: Wurde der Text von KI generiert?',
    layout: 'Mitte: Der zu bewertende Text | Unten: Zwei Buttons (Echt/Fake)',
    minimalExample: {
      schema_version: '1.0',
      type: 'authenticity',
      items: [
        { id: 'item_1', label: 'Text', source: { type: 'unknown' }, content: 'Ein Text, dessen Herkunft bewertet werden soll.' }
      ],
      config: {
        options: [
          { id: 'human', label: { de: 'Von Mensch', en: 'Human' } },
          { id: 'ai', label: { de: 'KI-generiert', en: 'AI-generated' } }
        ],
        show_confidence: false
      }
    },
    completeExample: {
      schema_version: '1.0',
      type: 'authenticity',
      reference: {
        type: 'text',
        label: 'Bewertungskriterien',
        content: 'Bewerten Sie, ob dieser Text von einem Menschen oder einer KI geschrieben wurde.'
      },
      items: [
        {
          id: 'item_1',
          label: 'Zu bewertender Text',
          source: { type: 'unknown' },
          content: 'Die Forschungsergebnisse zeigen eindeutig, dass regelmäßige Bewegung positive Auswirkungen auf die mentale Gesundheit hat.'
        }
      ],
      config: {
        options: [
          { id: 'human', label: { de: 'Von Mensch geschrieben', en: 'Written by human' } },
          { id: 'ai', label: { de: 'KI-generiert', en: 'AI-generated' } }
        ],
        show_confidence: true
      },
      ground_truth: {
        value: 'ai',
        source: { type: 'llm', name: 'openai/gpt-4' }
      }
    },
    configFields: [
      { name: 'options', type: 'Option[2]', description: 'Die zwei Auswahlmöglichkeiten' },
      { name: 'show_confidence', type: 'boolean', description: 'Konfidenz-Slider anzeigen?' }
    ]
  },
  {
    id: EvaluationType.LABELING,
    name: 'Labeling',
    icon: 'mdi-tag-multiple-outline',
    color: '#9B59B6',
    description: 'Kategorie(n) zuweisen: Single-Label oder Multi-Label Klassifikation.',
    layout: 'Links: Label-Optionen | Rechts: Zu klassifizierender Text',
    minimalExample: {
      schema_version: '1.0',
      type: 'labeling',
      items: [
        { id: 'item_1', label: 'Text', content: 'Zu klassifizierender Text' }
      ],
      config: {
        mode: 'single',
        labels: [
          { id: 'positive', label: { de: 'Positiv', en: 'Positive' } },
          { id: 'negative', label: { de: 'Negativ', en: 'Negative' } }
        ],
        allow_other: false
      }
    },
    completeExample: {
      schema_version: '1.0',
      type: 'labeling',
      items: [
        {
          id: 'item_1',
          label: 'Nachrichtenartikel',
          source: { type: 'human', name: 'Reuters' },
          content: 'Die EZB hat heute die Leitzinsen um 0,25 Prozentpunkte gesenkt.'
        }
      ],
      config: {
        mode: 'single',
        labels: [
          { id: 'politics', label: { de: 'Politik', en: 'Politics' }, color: '#4A90D9' },
          { id: 'economy', label: { de: 'Wirtschaft', en: 'Economy' }, color: '#50C878' },
          { id: 'sports', label: { de: 'Sport', en: 'Sports' }, color: '#FF6B6B' },
          { id: 'culture', label: { de: 'Kultur', en: 'Culture' }, color: '#9B59B6' },
          { id: 'science', label: { de: 'Wissenschaft', en: 'Science' }, color: '#F39C12' }
        ],
        allow_other: false
      },
      ground_truth: {
        value: 'economy'
      }
    },
    configFields: [
      { name: 'mode', type: '"single" | "multi"', description: 'Ein oder mehrere Labels?' },
      { name: 'labels', type: 'Label[]', description: 'Verfügbare Labels' },
      { name: 'allow_other', type: 'boolean', description: '"Sonstiges" Option?' },
      { name: 'min_labels', type: 'number', description: 'Minimum Labels (nur bei multi)' },
      { name: 'max_labels', type: 'number', description: 'Maximum Labels (nur bei multi)' }
    ]
  }
]

const currentType = computed(() => {
  return evaluationTypes.find(t => t.id === activeType.value) || evaluationTypes[0]
})

function formatJson(obj) {
  return JSON.stringify(obj, null, 2)
}

async function copyToClipboard(obj) {
  try {
    await navigator.clipboard.writeText(JSON.stringify(obj, null, 2))
    showCopySnackbar.value = true
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}
</script>

<style scoped>
.data-format-guide {
  max-width: 900px;
  margin: 0 auto;
}

.intro-text {
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 16px;
}

.type-overview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.type-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 16px 4px 16px 4px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
}

.type-chip:hover {
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.type-chip.active {
  background: rgba(var(--v-theme-primary), 0.15);
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
}

.type-description {
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 12px;
}

.layout-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 8px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.example-section {
  margin-top: 16px;
}

.example-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.example-label {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.code-block {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
}

.config-reference h4 {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.config-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.config-table th,
.config-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.config-table th {
  background: rgba(var(--v-theme-on-surface), 0.04);
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.config-table code {
  background: rgba(var(--v-theme-on-surface), 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.docs-link {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24px;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.docs-link a {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  margin-left: 4px;
}

.docs-link a:hover {
  text-decoration: underline;
}
</style>
