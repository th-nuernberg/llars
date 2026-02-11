# Rating/Ranking Übersicht

Diese Seite zeigt die wichtigsten Dateien und Datenflüsse für Ratings und Rankings im LLARS‑Stack.

---

## Systemkarte (Flow)

```mermaid
flowchart LR
  subgraph FE[Frontend]
    FE_Wizard[Scenario Wizard/Manager<br/>llars-frontend/src/views/ScenarioManager]
    FE_Presets[Presets & Config UI<br/>evaluationPresets.js, RatingConfigEditor.vue, RankingConfigEditor.vue]
    FE_Session[EvaluationSession.vue]
    FE_Rating[RatingInterface.vue<br/>useDimensionalRating.js]
    FE_Ranking[RankingInterface.vue<br/>useRankingEvaluation.js]
  end

  subgraph BE[Backend]
    BE_Schemas[evaluation_data_schemas.py<br/>Schema Ground Truth]
    BE_Transform[SchemaTransformer<br/>schema_transformer_service.py]
    BE_SchemaAPI[Scenario Schema API<br/>scenario_schema_api.py]
    BE_Presets[rating_preset_service.py]
    BE_RatingSvc[DimensionalRatingService<br/>dimensional_rating_service.py]
    BE_RankingSvc[RankingService<br/>ranking_service.py]
    BE_Routes[Routes<br/>rating_routes.py, ranking_routes.py]
    BE_DB[(MariaDB<br/>evaluation_items, scenario_items,<br/>item_dimension_ratings, user_feature_rankings)]
  end

  FE_Wizard --> FE_Presets
  FE_Presets --> BE_Presets
  BE_Presets --> FE_Presets

  BE_Schemas --> BE_Transform
  BE_Transform --> BE_SchemaAPI
  BE_SchemaAPI --> FE_Wizard

  FE_Session --> FE_Rating --> BE_Routes --> BE_RatingSvc --> BE_DB
  FE_Session --> FE_Ranking --> BE_Routes --> BE_RankingSvc --> BE_DB

  BE_DB --> BE_Transform
```

---

## Wichtige Dateien (Kurzliste)

**Schema & Konventionen**
- `app/schemas/evaluation_data_schemas.py`
- `llars-frontend/src/schemas/evaluationSchemas.js`

**Presets & Konfiguration**
- `app/services/evaluation/rating_preset_service.py`
- `llars-frontend/src/views/ScenarioManager/config/evaluationPresets.js`

**Schema-API & Adapter**
- `app/services/evaluation/schema_transformer_service.py`
- `app/services/evaluation/schema_adapter_service.py`
- `app/routes/scenarios/scenario_schema_api.py`

**Rating/Ranking Runtime**
- `app/routes/rating/rating_routes.py`
- `app/routes/rating/ranking_routes.py`
- `app/services/evaluation/dimensional_rating_service.py`
- `app/services/ranking_service.py`
- `llars-frontend/src/views/Evaluation/EvaluationSession.vue`
- `llars-frontend/src/views/Evaluation/interfaces/RatingInterface.vue`
- `llars-frontend/src/views/Evaluation/interfaces/RankingInterface.vue`
- `llars-frontend/src/composables/useDimensionalRating.js`
- `llars-frontend/src/composables/useRankingEvaluation.js`

**Datenbank (Core-Tabellen)**
- `evaluation_items` (früher EmailThread)
- `scenario_items` (früher ScenarioThreads)
- `item_dimension_ratings`
- `user_feature_rankings`

---

## Typische Änderungen bei neuen Varianten

- Preset hinzufügen (Backend + Frontend)
- Schema/Transformer anpassen (wenn neue Felder nötig sind)
- UI-Editor erweitern (RatingConfigEditor/RankingConfigEditor)
- API- und Service-Logik prüfen
- Tests und Doku ergänzen
