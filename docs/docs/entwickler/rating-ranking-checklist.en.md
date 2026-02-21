# Developer Checklist: New Rating/Ranking

Short checklist for adding new rating or ranking variants (preset, UI, logic).

---

## 1) Define the scope

- New preset within existing types (most common) or a new evaluation type?
- UI-only change or backend logic/data format changes as well?

## 2) Check the schema ground truth

- Evaluation input schema: `app/schemas/evaluation_data_schemas.py`
- Frontend validation: `llars-frontend/src/schemas/evaluationSchemas.js`
- If new fields or types are needed, update both sides in sync.

## 3) Add presets and defaults

- Backend presets: `app/services/evaluation/rating_preset_service.py`
- Frontend presets: `llars-frontend/src/views/ScenarioManager/config/evaluationPresets.js`
- Keep IDs, labels (DE/EN), and defaults consistent.

## 4) Update schema adapter/transformer

- DB → schema: `app/services/evaluation/schema_transformer_service.py`
- Legacy/adapter logic: `app/services/evaluation/schema_adapter_service.py`
- Export for wizard/AI: `app/services/evaluation/schema_export_service.py`

## 5) Backend routes and services

- Rating/Ranking endpoints: `app/routes/rating/rating_routes.py`, `app/routes/rating/ranking_routes.py`
- Presets API: `app/routes/evaluation_routes.py`
- Required: `@require_permission` + `@handle_api_errors`
- Route registration: `app/routes/registry.py`

## 6) Frontend UI

- Scenario Wizard/Manager: `llars-frontend/src/views/ScenarioManager/`
- Config editors: `components/config/RatingConfigEditor.vue`, `RankingConfigEditor.vue`
- Preview & validation: `EvaluationPreview.vue`, `DataFormatGuide.vue`
- Permissions: use `usePermissions()`

## 7) Data, migrations, seeds

- New DB fields? Add migration + update models
- Demo seeds: `app/db/seeders/scenarios.py`

## 8) Tests

- Backend: `tests/` (service and API tests)
- Frontend: `llars-frontend/tests/` (components, composables)
- E2E: Playwright in `llars-frontend` (optional)

## 9) Docs and examples

- Data formats: `docs/docs/entwickler/evaluation-datenformate.md`
- Extend Scenario Wizard/Manager guides if needed
- Update changelog for larger changes
