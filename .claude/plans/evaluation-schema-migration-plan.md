# Migration Plan: Unified Evaluation Data Schemas

**Version:** 1.0
**Datum:** 2026-01-27
**Basis:** evaluation-data-schemas.md

---

## Übersicht

Dieser Plan beschreibt die schrittweise Migration zu den neuen einheitlichen Evaluation-Schemas. Ziel ist eine zentrale Schema-Definition, die von Backend und Frontend referenziert wird.

---

## Phase 1: Schema-Definitionen erstellen

### 1.1 Backend: Pydantic Models

**Datei:** `app/schemas/evaluation_schemas.py`

```python
from enum import Enum
from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel, Field

class SchemaVersion(str, Enum):
    V1_0 = "1.0"

class EvaluationType(str, Enum):
    RANKING = "ranking"
    RATING = "rating"
    MAIL_RATING = "mail_rating"
    COMPARISON = "comparison"
    AUTHENTICITY = "authenticity"
    LABELING = "labeling"

class SourceType(str, Enum):
    HUMAN = "human"
    LLM = "llm"
    UNKNOWN = "unknown"

class ContentType(str, Enum):
    TEXT = "text"
    CONVERSATION = "conversation"

# === Basis-Strukturen ===

class LocalizedString(BaseModel):
    de: str
    en: str

class Source(BaseModel):
    type: SourceType
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationContent(BaseModel):
    type: str = "conversation"
    messages: List[Message]

class Reference(BaseModel):
    type: ContentType
    label: str
    content: Union[str, List[Message]]
    metadata: Optional[Dict[str, Any]] = None

class Item(BaseModel):
    id: str
    label: str
    source: Source
    content: Union[str, ConversationContent]
    group: Optional[str] = None  # Für Multi-Group Ranking

class GroundTruth(BaseModel):
    value: Union[str, int, float, List[str], Dict[str, str]]
    source: Optional[Source] = None
    confidence: Optional[float] = None

# === Ranking ===

class Bucket(BaseModel):
    id: str
    label: LocalizedString
    color: str
    order: int

class RankingGroup(BaseModel):
    id: str
    label: LocalizedString
    description: Optional[LocalizedString] = None
    buckets: List[Bucket]
    allow_ties: bool = True

class SimpleRankingConfig(BaseModel):
    mode: str = "simple"
    buckets: List[Bucket]
    allow_ties: bool = True
    require_complete: bool = True

class MultiGroupRankingConfig(BaseModel):
    mode: str = "multi_group"
    groups: List[RankingGroup]
    require_complete: bool = True

# === Rating ===

class ScaleLabels(BaseModel):
    labels: Dict[str, LocalizedString]  # "1": {"de": "Sehr schlecht", ...}

class Scale(BaseModel):
    min: int = 1
    max: int = 5
    step: int = 1
    labels: Optional[Dict[str, LocalizedString]] = None

class Dimension(BaseModel):
    id: str
    label: LocalizedString
    description: Optional[LocalizedString] = None
    weight: float = 0.25

class RatingConfig(BaseModel):
    scale: Scale
    dimensions: List[Dimension]
    show_overall: bool = True

class MailRatingConfig(RatingConfig):
    focus_role: Optional[str] = None

# === Comparison ===

class ComparisonConfig(BaseModel):
    question: LocalizedString
    criteria: Optional[List[str]] = None
    allow_tie: bool = True
    show_source: bool = False

# === Authenticity ===

class AuthenticityOption(BaseModel):
    id: str
    label: LocalizedString

class AuthenticityConfig(BaseModel):
    options: List[AuthenticityOption]
    show_confidence: bool = True

# === Labeling ===

class LabelOption(BaseModel):
    id: str
    label: LocalizedString
    description: Optional[LocalizedString] = None
    color: Optional[str] = None

class LabelingConfig(BaseModel):
    mode: str  # "single" | "multi"
    labels: List[LabelOption]
    allow_other: bool = False
    min_labels: Optional[int] = None
    max_labels: Optional[int] = None

# === Haupt-Schema ===

class EvaluationData(BaseModel):
    schema_version: SchemaVersion = SchemaVersion.V1_0
    type: EvaluationType
    reference: Optional[Reference] = None
    items: List[Item]
    config: Union[
        SimpleRankingConfig,
        MultiGroupRankingConfig,
        RatingConfig,
        MailRatingConfig,
        ComparisonConfig,
        AuthenticityConfig,
        LabelingConfig
    ]
    ground_truth: Optional[GroundTruth] = None
```

**Datei:** `app/schemas/__init__.py`

```python
from .evaluation_schemas import (
    EvaluationData,
    EvaluationType,
    Item,
    Reference,
    Source,
    Message,
    # ... alle exports
)
```

### 1.2 Frontend: TypeScript + Zod

**Datei:** `llars-frontend/src/schemas/evaluationSchemas.ts`

```typescript
import { z } from 'zod'

// === Enums ===
export const SchemaVersion = z.enum(['1.0'])
export const EvaluationType = z.enum(['ranking', 'rating', 'mail_rating', 'comparison', 'authenticity', 'labeling'])
export const SourceType = z.enum(['human', 'llm', 'unknown'])
export const ContentType = z.enum(['text', 'conversation'])

// === Basis-Strukturen ===
export const LocalizedString = z.object({
  de: z.string(),
  en: z.string()
})

export const Source = z.object({
  type: SourceType,
  name: z.string().optional(),
  metadata: z.record(z.any()).optional()
})

export const Message = z.object({
  role: z.string(),
  content: z.string(),
  timestamp: z.string().optional(),
  metadata: z.record(z.any()).optional()
})

export const ConversationContent = z.object({
  type: z.literal('conversation'),
  messages: z.array(Message)
})

export const Reference = z.object({
  type: ContentType,
  label: z.string(),
  content: z.union([z.string(), z.array(Message)]),
  metadata: z.record(z.any()).optional()
})

export const Item = z.object({
  id: z.string(),
  label: z.string(),
  source: Source,
  content: z.union([z.string(), ConversationContent]),
  group: z.string().optional()
})

// ... Rest der Schemas (siehe evaluation-data-schemas.md)

// === Type Exports ===
export type EvaluationData = z.infer<typeof EvaluationDataSchema>
export type Item = z.infer<typeof Item>
export type Reference = z.infer<typeof Reference>
// ...
```

**Datei:** `llars-frontend/src/schemas/index.ts`

```typescript
export * from './evaluationSchemas'
export * from './validation'
```

---

## Phase 2: Transformation Service

### 2.1 Backend: Data Transformer

**Datei:** `app/services/evaluation/schema_transformer.py`

```python
"""
Transformiert Datenbank-Modelle in das neue Schema-Format.
"""

from typing import Optional, List, Dict, Any
from db.models import (
    EvaluationItem, Message, Feature, RatingScenarios,
    ScenarioThreads, FeatureType, LLM
)
from schemas.evaluation_schemas import (
    EvaluationData, EvaluationType, Item, Reference,
    Source, SourceType, Message as SchemaMessage
)

class SchemaTransformer:
    """Transformiert DB-Modelle in Schema-Format."""

    @staticmethod
    def transform_scenario_item(
        scenario: RatingScenarios,
        thread_id: int
    ) -> EvaluationData:
        """
        Transformiert ein Szenario-Item in das neue Schema-Format.

        Args:
            scenario: Das Szenario
            thread_id: Die Thread/Item ID

        Returns:
            EvaluationData im neuen Schema-Format
        """
        eval_type = SchemaTransformer._get_evaluation_type(scenario.function_type_id)

        if eval_type == EvaluationType.RANKING:
            return SchemaTransformer._transform_ranking(scenario, thread_id)
        elif eval_type == EvaluationType.RATING:
            return SchemaTransformer._transform_rating(scenario, thread_id)
        elif eval_type == EvaluationType.MAIL_RATING:
            return SchemaTransformer._transform_mail_rating(scenario, thread_id)
        elif eval_type == EvaluationType.COMPARISON:
            return SchemaTransformer._transform_comparison(scenario, thread_id)
        elif eval_type == EvaluationType.AUTHENTICITY:
            return SchemaTransformer._transform_authenticity(scenario, thread_id)
        elif eval_type == EvaluationType.LABELING:
            return SchemaTransformer._transform_labeling(scenario, thread_id)
        else:
            raise ValueError(f"Unknown evaluation type: {eval_type}")

    @staticmethod
    def _transform_ranking(scenario: RatingScenarios, thread_id: int) -> EvaluationData:
        """Transformiert Ranking-Daten."""
        eval_item = EvaluationItem.query.get(thread_id)
        messages = Message.query.filter_by(item_id=thread_id).order_by(Message.timestamp).all()
        features = Feature.query.filter_by(item_id=thread_id).all()

        # Reference: Original-Text oder Konversation (aus Messages)
        reference = SchemaTransformer._build_reference(eval_item, messages)

        # Items: Features zum Ranken
        items = SchemaTransformer._build_items_from_features(features)

        # Config aus Szenario
        config = SchemaTransformer._build_ranking_config(scenario)

        return EvaluationData(
            schema_version="1.0",
            type=EvaluationType.RANKING,
            reference=reference,
            items=items,
            config=config
        )

    @staticmethod
    def _build_reference(
        eval_item: EvaluationItem,
        messages: List[Message]
    ) -> Optional[Reference]:
        """Baut Reference aus Messages."""
        if not messages:
            return None

        # Wenn nur eine Message ohne Konversations-Charakter → Text
        if len(messages) == 1 and messages[0].sender in ('article', 'Original Article', 'source'):
            return Reference(
                type="text",
                label="Original-Artikel",
                content=messages[0].content
            )

        # Mehrere Messages → Konversation
        return Reference(
            type="conversation",
            label=eval_item.subject or "Konversation",
            content=[
                SchemaMessage(
                    role=msg.sender,
                    content=msg.content,
                    timestamp=msg.timestamp.isoformat() if msg.timestamp else None
                )
                for msg in messages
            ]
        )

    @staticmethod
    def _build_items_from_features(features: List[Feature]) -> List[Item]:
        """Baut Items aus Features."""
        items = []
        for idx, feature in enumerate(features, 1):
            llm_name = feature.llm.name if feature.llm else None
            feature_type = feature.feature_type.name if feature.feature_type else "feature"

            source_type = SourceType.LLM if llm_name else SourceType.HUMAN

            items.append(Item(
                id=f"item_{idx}",
                label=f"{feature_type.capitalize()} {idx}",
                source=Source(type=source_type, name=llm_name),
                content=feature.content,
                group=feature_type if feature_type else None
            ))

        return items

    @staticmethod
    def _build_ranking_config(scenario: RatingScenarios) -> dict:
        """Baut Ranking-Config aus Szenario."""
        config = scenario.config_json or {}
        eval_config = config.get('eval_config', {}).get('config', {})

        buckets = eval_config.get('buckets', [
            {"id": "good", "label": {"de": "Gut", "en": "Good"}, "color": "#98d4bb", "order": 1},
            {"id": "moderate", "label": {"de": "Moderat", "en": "Moderate"}, "color": "#D1BC8A", "order": 2},
            {"id": "poor", "label": {"de": "Schlecht", "en": "Poor"}, "color": "#e8a087", "order": 3}
        ])

        return {
            "mode": "simple",
            "buckets": buckets,
            "allow_ties": eval_config.get('allowTies', True),
            "require_complete": True
        }

    # ... weitere Transform-Methoden für andere Typen
```

### 2.2 Frontend: Composable

**Datei:** `llars-frontend/src/composables/useEvaluationSchema.js`

```javascript
import { ref, computed } from 'vue'
import { EvaluationDataSchema } from '@/schemas/evaluationSchemas'

/**
 * Composable für Schema-basierte Evaluation-Daten.
 */
export function useEvaluationSchema() {
  const data = ref(null)
  const error = ref(null)
  const isValid = ref(false)

  /**
   * Validiert und setzt Evaluation-Daten.
   */
  function setData(rawData) {
    try {
      data.value = EvaluationDataSchema.parse(rawData)
      isValid.value = true
      error.value = null
    } catch (e) {
      error.value = e.errors
      isValid.value = false
    }
  }

  /**
   * Gibt Items nach Gruppe gruppiert zurück (für Multi-Group Ranking).
   */
  const groupedItems = computed(() => {
    if (!data.value?.items) return {}

    const groups = {}
    for (const item of data.value.items) {
      const groupId = item.group || 'default'
      if (!groups[groupId]) groups[groupId] = []
      groups[groupId].push(item)
    }
    return groups
  })

  /**
   * Gibt Gruppen-Definitionen zurück (für Tabs).
   */
  const groups = computed(() => {
    if (data.value?.config?.mode !== 'multi_group') return []
    return data.value.config.groups || []
  })

  /**
   * Prüft ob Multi-Group Modus aktiv ist.
   */
  const isMultiGroup = computed(() => {
    return data.value?.config?.mode === 'multi_group'
  })

  return {
    data,
    error,
    isValid,
    setData,
    groupedItems,
    groups,
    isMultiGroup
  }
}
```

---

## Phase 3: API Endpoints anpassen

### 3.1 Neuer Endpoint für Schema-Daten

**Datei:** `app/routes/scenarios/scenario_evaluation_api.py`

```python
@scenario_bp.get('/<int:scenario_id>/items/<int:item_id>/schema')
@authentik_required
@handle_api_errors(logger_name='scenario')
def get_item_schema_data(scenario_id: int, item_id: int):
    """
    Liefert Item-Daten im neuen Schema-Format.

    Returns:
        JSON im EvaluationData Schema-Format
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Prüfe ob Item zum Szenario gehört
    thread = ScenarioThreads.query.filter_by(
        scenario_id=scenario_id,
        thread_id=item_id
    ).first()
    if not thread:
        raise NotFoundError(f'Item {item_id} not in scenario {scenario_id}')

    # Transformiere in Schema-Format
    from services.evaluation.schema_transformer import SchemaTransformer
    schema_data = SchemaTransformer.transform_scenario_item(scenario, item_id)

    return jsonify(schema_data.model_dump())
```

### 3.2 Batch-Endpoint für alle Items

```python
@scenario_bp.get('/<int:scenario_id>/schema')
@authentik_required
@handle_api_errors(logger_name='scenario')
def get_scenario_schema_data(scenario_id: int):
    """
    Liefert Szenario-Metadaten und Liste der Item-IDs im Schema-Format.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    threads = ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()

    return jsonify({
        "scenario_id": scenario_id,
        "name": scenario.scenario_name,
        "type": SchemaTransformer._get_evaluation_type(scenario.function_type_id).value,
        "item_ids": [t.thread_id for t in threads],
        "config": scenario.config_json
    })
```

---

## Phase 4: UI-Komponenten aktualisieren

### 4.1 Generische EvaluationView

**Datei:** `llars-frontend/src/views/Evaluation/EvaluationView.vue`

```vue
<template>
  <div class="evaluation-view">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <v-progress-circular indeterminate />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <v-alert type="error">{{ error }}</v-alert>
    </div>

    <!-- Content -->
    <component
      v-else-if="data"
      :is="interfaceComponent"
      :data="data"
      :scenario-id="scenarioId"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useEvaluationSchema } from '@/composables/useEvaluationSchema'
import RankingInterface from './interfaces/RankingInterface.vue'
import RatingInterface from './interfaces/RatingInterface.vue'
import ComparisonInterface from './interfaces/ComparisonInterface.vue'
// ...

const props = defineProps({
  scenarioId: { type: Number, required: true },
  itemId: { type: Number, required: true }
})

const { data, error, setData } = useEvaluationSchema()
const loading = ref(true)

// Dynamische Interface-Komponente basierend auf Typ
const interfaceComponent = computed(() => {
  switch (data.value?.type) {
    case 'ranking': return RankingInterface
    case 'rating': return RatingInterface
    case 'mail_rating': return RatingInterface
    case 'comparison': return ComparisonInterface
    case 'authenticity': return AuthenticityInterface
    case 'labeling': return LabelingInterface
    default: return null
  }
})

onMounted(async () => {
  try {
    const response = await axios.get(
      `/api/scenarios/${props.scenarioId}/items/${props.itemId}/schema`
    )
    setData(response.data)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>
```

### 4.2 RankingInterface mit Multi-Group Support

```vue
<template>
  <div class="ranking-interface">
    <!-- Multi-Group: Tabs -->
    <v-tabs v-if="isMultiGroup" v-model="activeTab">
      <v-tab v-for="group in groups" :key="group.id" :value="group.id">
        {{ group.label[locale] }}
      </v-tab>
    </v-tabs>

    <div class="ranking-content">
      <!-- Left: Buckets -->
      <div class="buckets-panel">
        <template v-if="isMultiGroup">
          <RankingBuckets
            v-for="group in groups"
            v-show="activeTab === group.id"
            :key="group.id"
            :buckets="group.buckets"
            :items="groupedItems[group.id] || []"
            @change="handleBucketChange(group.id, $event)"
          />
        </template>
        <RankingBuckets
          v-else
          :buckets="data.config.buckets"
          :items="data.items"
          @change="handleBucketChange('default', $event)"
        />
      </div>

      <!-- Right: Reference -->
      <div class="reference-panel">
        <ReferenceDisplay :reference="data.reference" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import RankingBuckets from './components/RankingBuckets.vue'
import ReferenceDisplay from './components/ReferenceDisplay.vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const { locale } = useI18n()
const activeTab = ref(null)

const isMultiGroup = computed(() => props.data.config?.mode === 'multi_group')
const groups = computed(() => props.data.config?.groups || [])
const groupedItems = computed(() => {
  const result = {}
  for (const item of props.data.items) {
    const groupId = item.group || 'default'
    if (!result[groupId]) result[groupId] = []
    result[groupId].push(item)
  }
  return result
})

// Set initial tab
if (isMultiGroup.value && groups.value.length > 0) {
  activeTab.value = groups.value[0].id
}
</script>
```

---

## Phase 5: Migrations-Schritte

### 5.1 Schritt-für-Schritt Vorgehen

```
Woche 1: Phase 1 - Schema-Definitionen
├── [ ] Backend: Pydantic Models erstellen
├── [ ] Frontend: TypeScript + Zod Schemas erstellen
├── [ ] Tests für Schema-Validierung
└── [ ] Code Review

Woche 2: Phase 2 - Transformation Service
├── [ ] SchemaTransformer implementieren
├── [ ] Alle 6 Typen transformieren
├── [ ] Unit Tests für jeden Typ
└── [ ] Frontend Composable

Woche 3: Phase 3 - API Endpoints
├── [ ] Neue /schema Endpoints
├── [ ] Bestehende Endpoints parallel laufen lassen
├── [ ] Integration Tests
└── [ ] Performance-Tests

Woche 4: Phase 4 - UI-Komponenten
├── [ ] Generische EvaluationView
├── [ ] RankingInterface mit Multi-Group
├── [ ] Alle anderen Interfaces anpassen
├── [ ] E2E Tests

Woche 5: Cleanup & Rollout
├── [ ] Alte Endpoints deprecaten
├── [ ] Dokumentation aktualisieren
├── [ ] Staging-Tests
└── [ ] Production Rollout
```

### 5.2 Backwards Compatibility

Während der Migration laufen alte und neue Endpoints parallel:

```python
# Alt (bleibt vorerst)
GET /api/scenarios/{id}/threads/{thread_id}

# Neu (Schema-basiert)
GET /api/scenarios/{id}/items/{item_id}/schema
```

Frontend prüft ob neuer Endpoint verfügbar:

```javascript
async function loadItemData(scenarioId, itemId) {
  try {
    // Versuche neues Schema-Format
    const response = await axios.get(`/api/scenarios/${scenarioId}/items/${itemId}/schema`)
    return { format: 'schema', data: response.data }
  } catch (e) {
    if (e.response?.status === 404) {
      // Fallback auf altes Format
      const response = await axios.get(`/api/scenarios/${scenarioId}/threads/${itemId}`)
      return { format: 'legacy', data: response.data }
    }
    throw e
  }
}
```

---

## Phase 6: Datei-Struktur

```
app/
├── schemas/
│   ├── __init__.py
│   ├── evaluation_schemas.py      # Pydantic Models
│   ├── validation.py              # Validierungs-Utilities
│   └── presets/
│       ├── ranking_presets.py     # Standard-Bucket-Sets
│       ├── rating_presets.py      # SummEval, LLM-Judge, etc.
│       └── labeling_presets.py    # Kategorie-Sets
│
├── services/
│   └── evaluation/
│       ├── schema_transformer.py  # DB → Schema
│       └── schema_exporter.py     # Schema → JSON/Export

llars-frontend/src/
├── schemas/
│   ├── evaluationSchemas.ts       # TypeScript + Zod
│   ├── validation.ts              # Runtime-Validierung
│   └── index.ts
│
├── composables/
│   └── useEvaluationSchema.js     # Schema-Composable
│
├── views/Evaluation/
│   ├── EvaluationView.vue         # Generische View
│   ├── interfaces/
│   │   ├── RankingInterface.vue   # Mit Multi-Group
│   │   ├── RatingInterface.vue
│   │   ├── ComparisonInterface.vue
│   │   ├── AuthenticityInterface.vue
│   │   └── LabelingInterface.vue
│   └── components/
│       ├── ReferenceDisplay.vue   # Reference anzeigen
│       ├── RankingBuckets.vue     # Drag & Drop Buckets
│       └── ItemCard.vue           # Item-Anzeige
```

---

## Risiken & Mitigationen

| Risiko | Mitigation |
|--------|------------|
| Daten-Inkompatibilität | Transformer mit Fallbacks, extensive Tests |
| Performance bei großen Szenarien | Lazy Loading, Pagination |
| Breaking Changes für bestehende Evaluationen | Parallele Endpoints, Feature Flags |
| Komplexität Multi-Group | Schrittweise Einführung, erst simple |

---

## Erfolgskriterien

- [ ] Alle 6 Evaluationstypen funktionieren mit neuem Schema
- [ ] Multi-Group Ranking funktioniert in UI
- [ ] Bestehende Evaluationen bleiben intakt
- [ ] Schema-Validierung verhindert ungültige Daten
- [ ] Performance: < 200ms für Item-Load
- [ ] Test Coverage: > 80% für Schema-Code

---

## Nächste Schritte

1. **Review dieses Plans** mit Team
2. **Phase 1 starten**: Schema-Definitionen
3. **Prototyp**: Ein Szenario-Typ vollständig migrieren (Ranking)
4. **Iterativ**: Weitere Typen hinzufügen
