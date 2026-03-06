# Test Coverage Plan: 21% -> 50% (Backend) | 14% -> 40% (Frontend)

**Stand:** 2026-03-05
**Erstellt von:** Claude Code

---

## Ist-Zustand

### Backend (pytest + coverage)
| Metrik | Wert |
|--------|------|
| Coverage aktuell | ~21% |
| Test-Dateien | 50 |
| Test-Zeilen | ~28.900 |
| Service-Coverage | 19% (33/176 Services) |
| Route-Coverage | <1% (1/153 Route-Dateien) |
| Model-Coverage | 3% (1/32 Models) |

### Frontend (vitest + v8)
| Metrik | Wert |
|--------|------|
| Coverage aktuell | ~14% |
| Test-Dateien | 37 |
| Composable-Coverage | 39% (13/33) |
| L-Component-Coverage | 47% (18/38) |
| View-Coverage | 0% (0/50+) |
| Service-Coverage | 0% (0/12) |
| Utility-Coverage | 0% (0/10) |

---

## Strategie

### Prinzipien
1. **High-Impact zuerst** - Grosse Dateien mit Business-Logik bringen mehr Coverage pro Test
2. **Services > Routes** - Services enthalten die Logik, Routes sind Glue-Code
3. **Composables > Components > Views** - Im Frontend sinkt der ROI von links nach rechts
4. **Utilities sind Quick Wins** - Klein, rein funktional, leicht testbar
5. **Keine View-Tests noetig** - Views testen wir via E2E, nicht Unit-Tests

### Coverage-Rechnung

**Backend:** ~126.000 Zeilen in `app/`. Von 21% auf 50% = ~36.500 zusaetzliche Zeilen abdecken.
**Frontend:** ~193.000 Zeilen in `src/`. Von 14% auf 40% = ~50.000 zusaetzliche Zeilen abdecken.

---

## Phase 1: Quick Wins (Woche 1-2)

**Ziel: Backend 28% | Frontend 22%**

### Backend - Utilities & Kleine Services (~40 Tests)

| Datei | Zeilen | Aufwand | Prioritaet |
|-------|--------|---------|------------|
| `app/services/feature_rating_service.py` | 55 | S | Rein funktional |
| `app/services/user_profile_service.py` | 53 | S | Rein funktional |
| `app/services/llm_registry_service.py` | 87 | S | Rein funktional |
| `app/services/system_event_service.py` | 95 | S | Rein funktional |
| `app/services/system_settings_service.py` | 147 | S | DB-CRUD |
| `app/services/debug_log_service.py` | 176 | S | Logging-Logik |
| `app/services/db_explorer_service.py` | 98 | S | DB-Queries |
| `app/services/feature_service.py` | 231 | M | Feature-Flags |
| `app/services/presence_service.py` | 229 | M | Status-Tracking |
| `app/services/call_transcription_service.py` | 145 | S | Audio-Pipeline |

### Frontend - Utilities & Schemas (~30 Tests)

| Datei | Zeilen | Aufwand | Prioritaet |
|-------|--------|---------|------------|
| `src/utils/formatters.js` | 363 | M | Reiner JS-Code |
| `src/utils/colorHelpers.js` | 127 | S | Reiner JS-Code |
| `src/utils/userUtils.js` | 92 | S | Reiner JS-Code |
| `src/utils/sanitize.js` | 67 | S | Security-relevant! |
| `src/utils/generationOutputParser.js` | 47 | S | Parser-Logik |
| `src/utils/jwt.js` | 16 | S | Token-Parsing |
| `src/utils/authStorage.js` | 73 | S | Storage-Wrapper |
| `src/schemas/evaluationSchemas.js` | 589 | M | Schema-Validation |
| `src/composables/useSnackbar.js` | 104 | S | State-Management |
| `src/composables/useLanguage.js` | 110 | S | i18n-Logik |
| `src/composables/useModelRegistry.js` | 87 | S | Registry-Lookup |

### Frontend - Fehlende L-Komponenten (~50 Tests)

| Komponente | Zeilen | Aufwand |
|------------|--------|---------|
| `LStatusChip.vue` | 24 | S |
| `LViewToggle.vue` | 110 | S |
| `LLanguageToggle.vue` | 171 | S |
| `LSwitch.vue` | 175 | S |
| `LRadio.vue` | 209 | S |
| `LRadioGroup.vue` | 167 | S |
| `LCheckbox.vue` | 321 | M |
| `LStatCard.vue` | 256 | M |
| `LRatingScale.vue` | 411 | M |
| `LCardSkeleton.vue` | 355 | M |

---

## Phase 2: Core Business Logic (Woche 3-6)

**Ziel: Backend 38% | Frontend 32%**

### Backend - Kern-Services (~80 Tests)

| Datei | Zeilen | Aufwand | Warum kritisch |
|-------|--------|---------|----------------|
| `app/services/scenario_stats_service.py` | 4.356 | XL | Groesster Service, Kern-Statistiken |
| `app/services/permission_service.py` | 824 | L | RBAC-Kern, Security-relevant |
| `app/services/ranking_service.py` | 433 | M | Ranking/Bucket-Logik |
| `app/services/thread_service.py` | 427 | M | Item-Management |
| `app/services/user_service.py` | 335 | M | User-CRUD |
| `app/services/user_llm_provider_service.py` | 745 | L | Provider-Sharing-Logik |
| `app/services/referral_service.py` | 714 | L | Referral-System |
| `app/services/scenario_stats_cache_service.py` | 333 | M | Cache-Invalidierung |
| `app/services/messaging_service.py` | 574 | M | Messaging-Logik |
| `app/services/research_group_service.py` | 442 | M | Gruppen-Management |

**Strategie fuer scenario_stats_service.py (4.356 Zeilen):**
- In Teilbereiche aufteilen: progress_stats, evaluator_stats, irr_stats, export_stats
- Pro Teilbereich 10-15 Tests
- Mock: DB-Queries, Cache-Service
- Fokus: Korrekte Aggregation, Edge-Cases (leere Szenarien, fehlende Bewertungen)

### Backend - Evaluation Services (~40 Tests)

| Datei | Zeilen | Aufwand |
|-------|--------|---------|
| `app/services/evaluation/dimensional_rating_service.py` | ~400 | M |
| `app/services/evaluation/session_service.py` | ~350 | M |
| `app/services/evaluation/schema_adapter_service.py` | ~300 | M |
| `app/services/evaluation/schema_export_service.py` | ~250 | M |
| `app/services/evaluation/labeling_service.py` | ~200 | S |

### Frontend - Evaluation Composables (~60 Tests)

| Datei | Zeilen | Aufwand | Warum kritisch |
|-------|--------|---------|----------------|
| `src/composables/useEvaluationSession.js` | 398 | L | Session-Management |
| `src/composables/useDimensionalRating.js` | 462 | L | Multi-Dim Rating |
| `src/composables/useRankingEvaluation.js` | 292 | M | Ranking/Bucket-UI |
| `src/composables/useRatingEvaluation.js` | 314 | M | Rating-UI-Logik |
| `src/composables/useComparisonEvaluation.js` | 320 | M | Paarvergleich |
| `src/composables/useAuthenticityEvaluation.js` | 345 | M | Authentizitaet |
| `src/composables/useEvaluationSchema.js` | 310 | M | Schema-Parsing |
| `src/composables/useLLMEvaluation.js` | 502 | L | LLM-Judge UI |

### Frontend - Service/API Layer (~30 Tests)

| Datei | Zeilen | Aufwand |
|-------|--------|---------|
| `src/services/generationApi.js` | 263 | M |
| `src/services/kaimoApi.js` | 244 | M |
| `src/services/importService.js` | 225 | M |
| `src/services/socketService.js` | 226 | M |
| `src/services/pipelineApi.js` | 129 | S |
| `src/services/zoteroService.js` | 170 | S |

---

## Phase 3: API Routes & Integration (Woche 7-10)

**Ziel: Backend 45% | Frontend 37%**

### Backend - Route Tests (~100 Tests)

Route-Tests bringen viel Coverage, weil sie Services + Decorators + Auth durchlaufen.

**Prioritaet 1 - Kern-Routes:**

| Route-Datei | Zeilen | Tests |
|-------------|--------|-------|
| `routes/scenarios/scenario_manager_api.py` | 2.819 | 15-20 |
| `routes/scenarios/scenario_crud.py` | 701 | 10-15 |
| `routes/evaluation_routes.py` | 744 | 10-15 |
| `routes/rating/` (5 Dateien) | ~800 | 10-15 |
| `routes/llm/llm_routes.py` | ~400 | 8-10 |
| `routes/permissions/` | ~200 | 5-8 |

**Prioritaet 2 - Feature-Routes:**

| Route-Datei | Zeilen | Tests |
|-------------|--------|-------|
| `routes/prompts/prompt_routes.py` | 1.170 | 10-12 |
| `routes/generation/` (2 Dateien) | ~1.400 | 10-12 |
| `routes/chatbot/` (8 Dateien) | ~1.500 | 10-15 |
| `routes/rag/` (6 Dateien) | ~800 | 8-10 |
| `routes/data_import/import_routes.py` | 755 | 8-10 |

**Test-Pattern fuer Routes:**
```python
class TestScenarioManagerAPI:
    """Tests for /api/scenarios endpoints."""

    def test_SCEN_001_list_scenarios_as_admin(self, authenticated_client, admin_user):
        """Admin can list all scenarios."""
        response = authenticated_client.get('/api/scenarios')
        assert response.status_code == 200

    def test_SCEN_002_list_scenarios_as_evaluator(self, authenticated_client, mock_user):
        """Evaluator sees only assigned scenarios."""
        response = authenticated_client.get('/api/scenarios')
        assert response.status_code == 200

    def test_SCEN_003_create_scenario_unauthorized(self, client):
        """Unauthenticated request returns 401."""
        response = client.post('/api/scenarios', json={...})
        assert response.status_code == 401
```

### Frontend - Verbleibende Composables (~40 Tests)

| Datei | Zeilen | Aufwand |
|-------|--------|---------|
| `useGeneration.js` | 680 | L |
| `useGitStatus.js` | 676 | L |
| `useReferralSystem.js` | 574 | L |
| `useGitDiff.js` | 277 | M |
| `useCollabMembers.js` | 185 | M |
| `useAIAssist.js` | 166 | S |
| `useLLMModels.js` | 156 | S |
| `useCommunicationAdmin.js` | 110 | S |
| `usePresenceHeartbeat.js` | 95 | S |

### Frontend - Verbleibende L-Komponenten (~30 Tests)

| Komponente | Zeilen | Aufwand |
|------------|--------|---------|
| `LConfusionMatrix.vue` | 838 | L |
| `LAgreementHeatmap.vue` | 756 | L |
| `LFloatingWindow.vue` | 685 | L |
| `LSkeleton.vue` | 523 | M |
| `LListTable.vue` | 419 | M |
| `LRatingDistribution.vue` | 340 | M |
| `LlmModelSelect.vue` | 337 | M |
| `LIcon.vue` | 1.390 | L (Icon-Registry, testbar) |
| `LAIFieldButton.vue` | 177 | S |
| `LUserSearch.vue` | 199 | S |

---

## Phase 4: Feinschliff & Haertung (Woche 11-12)

**Ziel: Backend 50% | Frontend 40%**

### Backend - Verbleibende Luecken

| Bereich | Dateien | Tests |
|---------|---------|-------|
| `services/generation/` (6 Dateien) | ~4.500 Zeilen | 15-20 |
| `services/judge/` (7 Dateien) | ~4.000 Zeilen | 15-20 |
| `services/chatbot/` (13 ungetestete) | ~8.000 Zeilen | 20-25 |
| `services/data_import/` (7 Dateien) | ~2.500 Zeilen | 10-12 |
| `services/anonymize/` (9 ungetestete) | ~3.000 Zeilen | 10-12 |
| Auth/Decorator edge cases | ~5.000 Zeilen | 10-15 |

### Frontend - Edge Cases & Stores

| Bereich | Tests |
|---------|-------|
| `src/services/aiWritingService.js` (288 Zeilen) | 8-10 |
| Store-Tests (falls vorhanden) | 5-10 |
| Error-Handling in Services | 5-10 |

---

## Aufwandsschaetzung

| Phase | Backend Tests | Frontend Tests | Geschaetzte Dauer |
|-------|---------------|----------------|-------------------|
| Phase 1: Quick Wins | ~40 | ~80 | 2 Wochen |
| Phase 2: Core Logic | ~120 | ~90 | 4 Wochen |
| Phase 3: Routes & Integration | ~100 | ~70 | 4 Wochen |
| Phase 4: Feinschliff | ~80 | ~25 | 2 Wochen |
| **Gesamt** | **~340** | **~265** | **~12 Wochen** |

---

## Ausfuehrungshinweise

### Test-Reihenfolge pro Datei
1. Happy-Path Tests (Normalfall)
2. Edge Cases (leere Inputs, fehlende Daten)
3. Permission/Auth Tests (403, 401)
4. Error Cases (500, Exceptions)

### Test-ID Konvention (bestehend)
```
AUTH_001, PERM_001       - Auth/Permissions
COMP_BTN_001             - L-Komponenten
LLM_001, AGREE_001       - Services
SCEN_001                 - Szenarien (neu)
EVAL_001                 - Evaluation (neu)
RANK_001                 - Ranking (neu)
UTIL_001                 - Utilities (neu)
```

### Backend Mocking-Strategie
- DB: SQLite in-memory via conftest.py (bereits vorhanden)
- External APIs: `unittest.mock.patch` fuer LLM-Calls, Authentik, ChromaDB
- Services: Mock auf Service-Layer wenn Route getestet wird
- Fixtures: Bestehende `mock_user`, `admin_user`, `authenticated_client` nutzen

### Frontend Mocking-Strategie
- HTTP: `vi.mock('axios')` (bereits etabliert)
- Composables: `vi.mock('@/composables/useAuth')` etc.
- Socket.IO: `createMockSocket()` aus test-helpers.js
- Components: `shallowMountWithVuetify()` fuer isolierte Tests
- Router: `vi.mock('vue-router')`

### CI Integration
- Coverage-Reports werden bereits als Cobertura-XML generiert
- GitLab zeigt Coverage im MR-Diff (welche Zeilen getestet sind)
- Coverage-Threshold optional: `--cov-fail-under=50` fuer Backend

---

## Nicht im Scope

- **View-Tests** (Vue-Seiten): Zu komplex fuer Unit-Tests, von E2E abgedeckt
- **E2E-Tests**: Bereits via Playwright in Nightly-Pipeline
- **Model-Tests** (SQLAlchemy): Modelle sind deklarativ, wenig Logik
- **100% Coverage**: Nicht sinnvoll (siehe Erklaerung im Gespraech)
