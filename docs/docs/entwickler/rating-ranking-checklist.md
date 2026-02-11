# Developer-Checkliste: Neues Rating/Ranking

Kurze Checkliste für das Hinzufügen neuer Rating- oder Ranking-Varianten (Preset, UI, Logik).

---

## 1) Umfang festlegen

- Neues Preset innerhalb bestehender Typen (meistens) oder neuer Evaluationstyp?
- Betrifft es nur die UI-Konfiguration oder auch Backend-Logik und Datenformat?

## 2) Schema-Ground-Truth prüfen

- Evaluation-Input-Schema: `app/schemas/evaluation_data_schemas.py`
- Frontend-Validation: `llars-frontend/src/schemas/evaluationSchemas.js`
- Falls neue Felder oder Typen nötig sind, beide Seiten synchron ändern.

## 3) Presets und Defaults ergänzen

- Backend-Presets: `app/services/evaluation/rating_preset_service.py`
- Frontend-Presets: `llars-frontend/src/views/ScenarioManager/config/evaluationPresets.js`
- IDs, Labels (DE/EN) und Defaults konsistent halten.

## 4) Schema-Adapter/Transformer aktualisieren

- DB → Schema: `app/services/evaluation/schema_transformer_service.py`
- Legacy/Adapter-Logik: `app/services/evaluation/schema_adapter_service.py`
- Export für Wizard/AI: `app/services/evaluation/schema_export_service.py`

## 5) Backend-Routes und Services

- Rating/Ranking-Endpoints: `app/routes/rating/rating_routes.py`, `app/routes/rating/ranking_routes.py`
- Presets-API: `app/routes/evaluation_routes.py`
- Pflicht: `@require_permission` + `@handle_api_errors`
- Route-Registrierung: `app/routes/registry.py`

## 6) Frontend-UI

- Scenario Wizard/Manager: `llars-frontend/src/views/ScenarioManager/`
- Config-Editoren: `components/config/RatingConfigEditor.vue`, `RankingConfigEditor.vue`
- Preview & Validation: `EvaluationPreview.vue`, `DataFormatGuide.vue`
- Permissions: `usePermissions()` verwenden

## 7) Daten, Migrationen, Seeds

- Neue DB-Felder? → Migration + Model-Anpassung
- Seeds für Demo-Szenarien: `app/db/seeders/scenarios.py`

## 8) Tests

- Backend: `tests/` (Service- und API-Tests)
- Frontend: `llars-frontend/tests/` (Komponenten, Composables)
- E2E: `llars-frontend` Playwright (optional)

## 9) Doku & Beispiele

- Datenformate: `docs/docs/entwickler/evaluation-datenformate.md`
- Scenario Wizard/Manager Guides bei Bedarf ergänzen
- Changelog bei größeren Änderungen aktualisieren
