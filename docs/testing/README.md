# LLARS Testdokumentation

**Version:** 1.2 | **Stand:** 31. Dezember 2025

**Implementierungsstatus:** 🟢 Backend komplett, Frontend in Arbeit

---

## Übersicht

Diese Dokumentation enthält alle Testanforderungen für das LLARS-System (LLM Assisted Research System). Sie dient als vollständige Referenz für:

- Was getestet werden muss
- Wie es getestet werden soll
- Welche Priorität jeder Test hat
- Wer für welche Tests verantwortlich ist

### Quick Start: Tests ausführen

**Backend Tests (pytest):**
```bash
cd /path/to/llars

# Alle Backend Tests
pytest tests/

# Nur Unit Tests
pytest tests/unit/

# Nur Integration Tests
pytest tests/integration/

# Mit Coverage
pytest --cov=app --cov-report=html tests/

# Spezifische Test-Klasse
pytest tests/unit/auth/test_decorators.py::TestAuthentikRequired -v
```

**Frontend Tests (Vitest):**
```bash
cd /path/to/llars/llars-frontend

# Alle Frontend Tests (einmalig)
npm run test:run

# Watch Mode (interaktiv)
npm run test

# Mit Coverage
npm run test:coverage

# Vitest UI
npm run test:ui
```

---

## Dokumentenstruktur

```
docs/testing/
├── README.md                          # Diese Übersicht
│
├── leitfaden/                         # Implementierungsanleitungen
│   └── LLARS_TEST_LEITFADEN.md       # Hauptleitfaden (Setup, Patterns, Templates)
│
├── anforderungen/                     # Detaillierte Testanforderungen
│   ├── 00_UEBERSICHT.md              # Gesamtübersicht aller Anforderungen
│   │
│   ├── frontend/                      # Frontend-Testanforderungen (✅ komplett)
│   │   ├── 01_SEITEN_NAVIGATION.md   # Login, Home, Navigation Guards
│   │   ├── 02_EVALUATION_FEATURES.md # Ranking, Rating, Judge, OnCoCo, KAIMO
│   │   ├── 03_COLLAB_EDITOREN.md     # Markdown & LaTeX Collaboration + YJS
│   │   ├── 04_CHAT_CHATBOTS.md       # Chat-Interface & Chatbot-Wizard
│   │   ├── 05_ADMIN_DASHBOARD.md     # Docker, DB, Health, Users, Scenarios
│   │   ├── 06_UI_KOMPONENTEN.md      # LBtn, LTag, LSlider, LCard, etc.
│   │   ├── 07_DIALOGE_MODALS.md      # Alle 10 Dialog-Komponenten
│   │   ├── 08_TOOLTIPS_QUICKLINKS.md # 100+ Tooltips, Quicklinks, Shortcuts
│   │   ├── 09_ACCESSIBILITY.md       # WCAG 2.1 AA, Keyboard, Screen Reader
│   │   ├── 10_EDGE_CASES_ERRORS.md   # Empty States, Errors, Limits
│   │   └── 11_VISUAL_RESPONSIVE.md   # Breakpoints, Dark Mode, Browser
│   │
│   ├── backend/                       # Backend-Testanforderungen
│   │   ├── 01_AUTH_ROUTES.md         # Auth Decorators, Login, Token Validation
│   │   └── 02_SOCKETIO_EVENTS.md     # Alle WebSocket Events & Namespaces
│   │
│   ├── features/                      # Feature-spezifische Tests
│   │   ├── 01_RAG_PIPELINE.md        # Upload, Chunking, Embedding, Retrieval
│   │   ├── 02_LLM_INTEGRATION.md     # Models, Chat, Agent Modes, Judge
│   │   ├── 03_LATEX_KOMPILIERUNG.md  # PDF-Generierung, BibTeX, Collab
│   │   └── 04_ANONYMISIERUNG.md      # NER, Pseudonymisierung
│   │
│   └── security/                      # Sicherheits-Tests (✅ komplett)
│       ├── 01_BERECHTIGUNGEN.md      # RBAC, 43 Permissions, Decorators
│       └── 02_ROLLEN_MATRIX.md       # 4 Rollen, Feature-Zugriff
│
├── checklisten/                       # Ausführbare Checklisten (✅ komplett)
│   ├── SMOKE_TEST.md                 # 15-20 min Schnelltest
│   ├── RELEASE_CHECKLIST.md          # Pre/Post Release Schritte
│   └── REGRESSION_TESTS.md           # Vollständige Funktionsprüfung
│
└── CICD_SETUP.md                      # GitLab CI/CD Pipeline Setup
```

---

## Schnellstart

### 1. Für neue Entwickler
1. Lies den [Hauptleitfaden](leitfaden/LLARS_TEST_LEITFADEN.md)
2. Schaue dir die [Gesamtübersicht](anforderungen/00_UEBERSICHT.md) an
3. Beginne mit dem [Smoke Test](checklisten/SMOKE_TEST.md)

### 2. Für Feature-Entwicklung
1. Finde die passende Anforderungsdatei in `anforderungen/`
2. Implementiere Tests gemäß den Templates im Leitfaden
3. Führe die [Regression Tests](checklisten/REGRESSION_TESTS.md) aus

### 3. Für Releases
1. Führe die [Release Checklist](checklisten/RELEASE_CHECKLIST.md) durch
2. Stelle sicher, dass alle kritischen Tests grün sind
3. Dokumentiere Testergebnisse

---

## Zusammenfassung der Testbereiche

| Bereich | Tests | Status |
|---------|-------|--------|
| **Backend Unit Tests** | 768 | ✅ Implementiert |
| **Backend Integration Tests** | 342 | ✅ Implementiert |
| **Frontend Component Tests** | 1.733 | ✅ Implementiert |
| **E2E Tests (Playwright)** | 0 | ⏳ Geplant |
| **Gesamt** | **2.843** | ~95% ✅ |

### Implementierte Backend Test-Dateien

```
tests/
├── conftest.py                                  # ✅ Fixtures & Setup
├── unit/                                        # ✅ 768 Tests
│   ├── auth/
│   │   └── test_decorators.py                   # Auth Decorators
│   └── services/
│       ├── chatbot/test_chatbot_service.py      # Chatbot Service
│       ├── comparison/test_comparison_service.py
│       ├── crawler/test_crawler_service.py      # Web Crawler
│       ├── judge/test_judge_service.py          # LLM-as-Judge
│       ├── latex/test_latex_compile_service.py  # LaTeX Compilation
│       ├── llm/test_llm_service.py              # LLM Integration
│       ├── oncoco/test_oncoco_service.py        # OnCoCo
│       ├── permission/test_permission_service.py
│       ├── rag/                                 # RAG Pipeline Tests
│       │   ├── test_access_service.py
│       │   ├── test_collection_embedding_service.py
│       │   ├── test_document_service.py
│       │   ├── test_embedding_model_service.py
│       │   ├── test_lumber_chunker.py
│       │   └── test_reranker.py
│       ├── ranking/test_ranking_service.py
│       ├── thread/test_thread_service.py
│       ├── user/test_user_service.py
│       └── wizard/test_wizard_session_service.py
└── integration/                                 # ✅ 342 Tests
    ├── auth/test_login.py                       # Login Flow
    ├── rag/                                     # RAG Integration
    │   ├── test_rag_collections.py
    │   ├── test_rag_documents.py
    │   └── test_rag_search.py
    └── socketio/                                # WebSocket Events
        ├── test_socketio_chat.py
        ├── test_socketio_connection.py
        ├── test_socketio_crawler.py
        ├── test_socketio_judge.py
        ├── test_socketio_oncoco.py
        └── test_socketio_prompts.py
```

### Implementierte Frontend Test-Dateien

```
llars-frontend/tests/
├── setup.js                                     # ✅ Vitest Setup
├── utils/test-helpers.js                        # ✅ Test Utilities
├── components/                                  # ✅ 958 Tests
│   ├── LBtn.spec.js                             # 30 Tests (COMP_BTN_001-030)
│   ├── LTag.spec.js                             # 25 Tests (COMP_TAG_001-025)
│   ├── LSlider.spec.js                          # 25 Tests (COMP_SLD_001-025)
│   ├── LCard.spec.js                            # 50 Tests (COMP_CRD_001-050)
│   ├── LTabs.spec.js                            # 40 Tests (COMP_TAB_001-040)
│   ├── LTooltip.spec.js                         # 35 Tests (COMP_TTP_001-035)
│   ├── LActionGroup.spec.js                     # 48 Tests (COMP_ACT_001-048)
│   ├── LIconBtn.spec.js                         # 45 Tests (COMP_ICB_001-045)
│   ├── LAvatar.spec.js                          # 55 Tests (COMP_AVT_001-055)
│   ├── LLoading.spec.js                         # 40 Tests (COMP_LDG_001-040)
│   ├── LMessage.spec.js                         # 45 Tests (COMP_MSG_001-045)
│   ├── LThemeToggle.spec.js                     # 40 Tests (COMP_THM_001-040)
│   ├── LInfoTooltip.spec.js                     # 40 Tests (COMP_ITT_001-040)
│   ├── LMessageList.spec.js                     # 45 Tests (COMP_MLS_001-045)
│   ├── LUserSearch.spec.js                      # 50 Tests (COMP_USR_001-050)
│   ├── LGauge.spec.js                           # 55 Tests (COMP_GAU_001-055)
│   ├── LChart.spec.js                           # 50 Tests (COMP_CHT_001-050)
│   ├── LEvaluationLayout.spec.js                # 55 Tests (COMP_EVL_001-055)
│   ├── LEvaluationStatus.spec.js                # 45 Tests (COMP_EVS_001-045)
│   ├── KatexFormula.spec.js                     # 40 Tests (COMP_KTX_001-040)
│   ├── AppSidebar.spec.js                       # 55 Tests (COMP_SDB_001-055)
│   └── AnalyticsConsentBanner.spec.js           # 45 Tests (COMP_ACB_001-045)
└── composables/                                 # ✅ 775 Tests
    ├── useAuth.spec.js                          # 60 Tests (AUTH_001-060)
    ├── usePermissions.spec.js                   # 55 Tests (PERM_001-055)
    ├── usePanelResize.spec.js                   # 45 Tests (RESIZE_001-045)
    ├── useAppTheme.spec.js                      # 50 Tests (THEME_001-050)
    ├── useMobile.spec.js                        # 55 Tests (MOBILE_001-055)
    ├── useSkeletonLoading.spec.js               # 60 Tests (SKEL_001-060)
    ├── useBuilderValidation.spec.js             # 60 Tests (BVAL_001-060)
    ├── useBuilderState.spec.js                  # 85 Tests (BSTATE_001-085)
    ├── useWizardSession.spec.js                 # 70 Tests (WSESS_001-070)
    ├── useKIAStatusCache.spec.js                # 55 Tests (KIA_001-055)
    ├── useAnalyticsMetrics.spec.js              # 70 Tests (AM_001-070)
    ├── useFieldGenerationService.spec.js        # 60 Tests (FGS_001-060)
    └── useSplitPaneResize.spec.js               # 50 Tests (SPR_001-050)
```

### Frontend UI/UX Details

| Dokument | Inhalt | Geplant | Implementiert |
|----------|--------|---------|---------------|
| 06_UI_KOMPONENTEN | 20+ LLARS Komponenten | ~80 | ✅ 958 (22 Komponenten) |
| 07_DIALOGE_MODALS | 10 Dialog-Komponenten | ~50 | ⏳ 0 |
| 08_TOOLTIPS_QUICKLINKS | 100+ Tooltips, Quicklinks | ~135 | ⏳ 0 |
| 09_ACCESSIBILITY | WCAG 2.1 AA, Keyboard | ~75 | ⏳ 0 |
| 10_EDGE_CASES_ERRORS | Empty States, Errors | ~40 | ⏳ 0 |
| 11_VISUAL_RESPONSIVE | Breakpoints, Dark Mode | ~50 | ⏳ 0 |
| Composables | useAuth, usePermissions, etc. | ~120 | ✅ 775 (13 Composables) |

**Implementierte Komponenten (22/22):** ✅ Alle Komponenten getestet - LBtn, LTag, LSlider, LCard, LTabs, LTooltip, LActionGroup, LIconBtn, LAvatar, LLoading, LMessage, LThemeToggle, LInfoTooltip, LMessageList, LUserSearch, LGauge, LChart, LEvaluationLayout, LEvaluationStatus, KatexFormula, AppSidebar, AnalyticsConsentBanner

**Fehlende Komponenten:** Keine - alle Komponenten sind vollständig getestet!

**Implementierte Composables (13/13):** ✅ Alle Composables getestet - useAuth, usePermissions, usePanelResize, useAppTheme, useMobile, useSkeletonLoading, useBuilderValidation, useBuilderState, useWizardSession, useKIAStatusCache, useAnalyticsMetrics, useFieldGenerationService, useSplitPaneResize

**Fehlende Composables:** Keine - alle Composables sind vollständig getestet!

---

## Priorisierung

| Priorität | Bedeutung | Beispiele |
|-----------|-----------|-----------|
| **P0** | Kritisch - Blockiert Produktion | Auth, Permissions, Core Features |
| **P1** | Wichtig - Sollte vor Release getestet werden | Feature-Funktionalität, UI |
| **P2** | Nice-to-have - Wenn Zeit vorhanden | Edge Cases, Performance |

---

## Test-Arten

| Art | Tool | Ziel |
|-----|------|------|
| **Unit Tests** | pytest / Vitest | Isolierte Logik |
| **Integration Tests** | pytest | API + DB |
| **E2E Tests** | Playwright | User Journeys |
| **Visual Regression** | Playwright Screenshots | UI-Konsistenz |
| **Accessibility** | axe-core / Lighthouse | WCAG 2.1 AA |
| **Cross-Browser** | Playwright (Chromium, Firefox, WebKit) | Kompatibilität |
| **Manuell** | Checkliste | Komplexe Interaktionen |

---

## Kontakt

Bei Fragen zur Testdokumentation wende dich an das Entwicklungsteam.

---

**Letzte Aktualisierung:** 1. Januar 2026
