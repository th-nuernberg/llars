# LLARS Test-Implementierung - Vollständiger Leitfaden

**Version:** 3.0 | **Erstellt:** 30. Dezember 2025 | **Status:** Referenz-Dokument

---

## Quick Start - Sofort loslegen

### In 5 Minuten startklar

```bash
# 1. Backend Test-Dependencies installieren
pip install -r requirements-test.txt

# 2. Ersten Unit Test ausführen
pytest tests/unit/auth/ -v

# 3. Frontend Test-Dependencies installieren
cd llars-frontend && npm install -D vitest @vue/test-utils

# 4. Ersten Frontend Test ausführen
npm run test

# 5. Coverage Report generieren
pytest --cov=app --cov-report=html
```

### Nächste Schritte nach dem Setup

| Schritt | Befehl | Dauer |
|---------|--------|-------|
| Backend Unit Tests schreiben | `pytest tests/unit/ -v` | ~30 min |
| Frontend Tests einrichten | `npm run test:watch` | ~20 min |
| E2E Setup | `npx playwright install` | ~10 min |
| CI Pipeline aktivieren | Push to `develop` | ~5 min |

---

## Tool-Stack Empfehlungen

### Backend Testing

| Tool | Version | Zweck | Warum? |
|------|---------|-------|--------|
| **pytest** | 8.3+ | Test Framework | Standard, flexibel, große Community |
| **pytest-flask** | 1.3+ | Flask Integration | Native Test-Client Support |
| **pytest-cov** | 6.0+ | Coverage | Detaillierte Coverage-Reports |
| **pytest-asyncio** | 0.24+ | Async Tests | Für async Endpoints |
| **pytest-mock** | 3.14+ | Mocking | Einfaches Patching |
| **factory-boy** | 3.3+ | Test Data | Komplexe Test-Objekte |
| **freezegun** | 1.4+ | Time Mocking | Zeitabhängige Tests |
| **responses** | 0.25+ | HTTP Mocking | Externe API Mocks |

### Frontend Testing

| Tool | Version | Zweck | Warum? |
|------|---------|-------|--------|
| **Vitest** | 2.0+ | Test Framework | Schnell, Vite-nativ, ESM |
| **Vue Test Utils** | 2.4+ | Vue Testing | Offizielle Vue Library |
| **happy-dom** | 15+ | DOM Environment | Schneller als jsdom |
| **@testing-library/vue** | 8+ | User-centric Testing | Best Practices |
| **MSW** | 2.0+ | API Mocking | Request Interception |

### E2E Testing

| Tool | Version | Zweck | Warum? |
|------|---------|-------|--------|
| **Playwright** | 1.48+ | E2E Framework | Multi-Browser, Auto-Wait |
| **@playwright/test** | 1.48+ | Test Runner | Parallel, Fixtures |

### Warum diese Tools?

- **pytest > unittest**: Fixtures, Plugins, bessere Assertions
- **Vitest > Jest**: Native Vite-Integration, schneller HMR
- **Playwright > Cypress**: Multi-Browser, bessere Netzwerk-Kontrolle
- **happy-dom > jsdom**: 10x schneller, weniger Speicher

---

## Test-Ziele und Metriken

### Testing-Pyramide mit Ziel-Anzahl

```
                    ┌─────────────────┐
                   │    E2E Tests     │  ~27 Tests (10%)
                   │   (Playwright)   │  Kritische User Journeys
                  ├───────────────────┤
                 │  Integration Tests │  ~93 Tests (30%)
                │      (pytest)       │  API, DB, Socket.IO
               ├───────────────────────┤
              │      Unit Tests        │  ~190 Tests (60%)
             │   (pytest + Vitest)     │  Services, Models, Components
            └───────────────────────────┘

            GESAMT: ~310 Tests für vollständige Coverage
```

### Coverage-Ziele

| Bereich | Minimum | Ziel | Priorität |
|---------|---------|------|-----------|
| Auth/Permissions | 90% | 95% | P0 |
| RAG Pipeline | 85% | 90% | P0 |
| API Routes | 80% | 85% | P1 |
| Services | 80% | 85% | P1 |
| Models | 75% | 80% | P1 |
| Frontend Components | 70% | 80% | P1 |
| Frontend Composables | 80% | 85% | P1 |

---

## 12-Wochen Implementierungs-Roadmap

### Phase 1: Foundation (Woche 1-2)

**Ziel:** Test-Infrastruktur aufbauen

| Woche | Aufgabe | Deliverable |
|-------|---------|-------------|
| **1** | Backend Setup | `requirements-test.txt`, `pytest.ini`, `conftest.py` |
| **1** | Fixture-System | `tests/fixtures/` mit Auth, RAG, Judge Fixtures |
| **2** | Frontend Setup | `vitest.config.js`, `setup.js`, Mocks |
| **2** | E2E Setup | `playwright.config.ts`, Auth Fixtures |

**Checkpoints:**
- [ ] `pytest tests/ -v` läuft ohne Fehler
- [ ] `npm run test` läuft ohne Fehler
- [ ] `npx playwright test` läuft ohne Fehler

### Phase 2: Core Unit Tests (Woche 3-4)

**Ziel:** Kritische Backend-Logik abdecken

| Woche | Aufgabe | Tests |
|-------|---------|-------|
| **3** | Auth Unit Tests | ~25 Tests |
| **3** | Permission Service Tests | ~20 Tests |
| **4** | RAG Service Tests | ~30 Tests |
| **4** | Model Tests | ~20 Tests |

**Checkpoints:**
- [ ] Auth Coverage > 80%
- [ ] Permission Coverage > 85%
- [ ] ~95 Backend Unit Tests

### Phase 3: Integration Tests (Woche 5-6)

**Ziel:** API Endpoints und DB-Interaktionen testen

| Woche | Aufgabe | Tests |
|-------|---------|-------|
| **5** | Auth Flow Tests | ~15 Tests |
| **5** | User API Tests | ~10 Tests |
| **6** | RAG API Tests | ~20 Tests |
| **6** | Chatbot API Tests | ~15 Tests |

**Checkpoints:**
- [ ] Alle API Endpoints getestet
- [ ] ~60 Integration Tests

### Phase 4: Frontend Tests (Woche 7-8)

**Ziel:** Vue Components und Composables testen

| Woche | Aufgabe | Tests |
|-------|---------|-------|
| **7** | Common Components (LBtn, LTag, etc.) | ~25 Tests |
| **7** | Composables (useAuth, usePermissions) | ~15 Tests |
| **8** | Feature Components (Ranker, Rater) | ~20 Tests |
| **8** | Service Tests | ~10 Tests |

**Checkpoints:**
- [ ] Frontend Coverage > 70%
- [ ] ~70 Frontend Tests

### Phase 5: E2E & Spezial-Tests (Woche 9-10)

**Ziel:** User Journeys und Real-time Features testen

| Woche | Aufgabe | Tests |
|-------|---------|-------|
| **9** | Auth E2E (Login/Logout) | ~5 Tests |
| **9** | Chatbot E2E (Create/Chat) | ~5 Tests |
| **10** | Judge E2E | ~5 Tests |
| **10** | YJS Collaboration E2E | ~5 Tests |

**Checkpoints:**
- [ ] Kritische User Journeys abgedeckt
- [ ] ~20 E2E Tests

### Phase 6: CI/CD & Optimierung (Woche 11-12)

**Ziel:** Automatisierung und Performance

| Woche | Aufgabe | Deliverable |
|-------|---------|-------------|
| **11** | GitHub Actions Pipeline | `.github/workflows/test.yml` |
| **11** | Coverage Reports | Codecov Integration |
| **12** | Performance Tests | ~5 Benchmark Tests |
| **12** | Dokumentation | Finales Review |

**Checkpoints:**
- [ ] CI Pipeline grün auf `main`
- [ ] Coverage Badge im README
- [ ] ~310 Tests insgesamt

### Roadmap-Übersicht

```
Woche:  1   2   3   4   5   6   7   8   9  10  11  12
        ├───┴───┼───┴───┼───┴───┼───┴───┼───┴───┼───┴───┤
Phase:  │ Setup │ Unit  │ Integ │ Front │  E2E  │ CI/CD │
        │ Infra │ Tests │ Tests │ Tests │ Tests │  Opt  │
        └───────┴───────┴───────┴───────┴───────┴───────┘
Tests:    0      95     155    225     245     310
```

---

## LLARS-spezifische Architektur

### Codebase-Übersicht

| Bereich | Umfang | Test-Relevanz |
|---------|--------|---------------|
| **Backend Blueprints** | 38 Routes | Jeder Blueprint braucht Integration Tests |
| **DB Models** | 20+ Models | Unit Tests für Constraints, Serialisierung |
| **Services** | 40+ Services | Unit Tests für Business Logic |
| **Socket.IO Events** | 15+ Namespaces | Integration Tests für Real-time |
| **Frontend Components** | 60+ Components | Unit Tests für kritische UI |
| **Composables** | 20+ Composables | Unit Tests für Logik |

### Kritische Test-Bereiche (P0 - Höchste Priorität)

#### Auth & Permissions

| Was | Warum kritisch | Test-Fokus |
|-----|---------------|------------|
| JWT Token Validation | Sicherheits-Gateway | Gültige/Ungültige/Expired Tokens |
| `@authentik_required` | Schützt alle Routes | Header-Handling, User-Creation |
| Permission Service | RBAC-Kern | Deny-by-Default, Role-Override, User-Override |
| `check_permission()` | Wird überall genutzt | Admin-Bypass, Granulare Permissions |

#### RAG Pipeline

| Was | Warum kritisch | Test-Fokus |
|-----|---------------|------------|
| Document Upload | Daten-Eingang | File-Typen, Size-Limits, Chunking |
| Embedding Service | Kern-Funktionalität | Model-Fallback, Dimensionen |
| Search Service | User-Feature | Query-Processing, Ranking |
| Collection Access | Datenschutz | Owner/Public/Shared Logic |

### Kritische Test-Bereiche (P1 - Hohe Priorität)

#### Judge System

| Was | Warum kritisch | Test-Fokus |
|-----|---------------|------------|
| Session Management | Workflow-Steuerung | Status-Übergänge, Config |
| Comparison Queue | Performance | Ordering, Worker-Verteilung |
| LLM Integration | Externe Abhängigkeit | Retry-Logic, Timeout-Handling |

#### Chatbot Wizard

| Was | Warum kritisch | Test-Fokus |
|-----|---------------|------------|
| Multi-Step Flow | UX-kritisch | State-Management, Validation |
| Collection-Binding | Feature-Kern | RAG-Integration |
| LLM Config | Funktionalität | Model-Selection, Parameters |

### Kritische Test-Bereiche (P2 - Wichtig)

#### YJS Collaboration

| Was | Warum kritisch | Test-Fokus |
|-----|---------------|------------|
| Document Sync | Multi-User | CRDT-Merge, Conflict Resolution |
| Presence/Awareness | UX | Cursor-Sync, User-Anzeige |
| Reconnection | Reliability | Offline-Handling, State-Recovery |

---

## Über dieses Dokument

### Zweck & Zielgruppe

Dieses Dokument ist der **zentrale und vollständige Leitfaden** zur Implementierung und Wartung der LLARS Test-Suite. Es richtet sich an:

- **Neue Entwickler**: Schneller Einstieg in die Test-Infrastruktur
- **Bestehende Entwickler**: Referenz für neue Feature-Tests
- **DevOps**: CI/CD Pipeline Konfiguration
- **Reviewer**: Qualitätssicherung von Test-Code

### Was dieses Dokument bietet

| Aspekt | Beschreibung |
|--------|--------------|
| **Fahrplan** | Schritt-für-Schritt Anleitung mit Checkboxen |
| **Referenz** | Code-Beispiele für jeden Test-Typ |
| **Architektur** | Klare Struktur ohne Monolith-Dateien |
| **Best Practices** | Namenskonventionen, Patterns, Anti-Patterns |
| **Erweiterbarkeit** | Anleitung für Tests bei neuen Features |
| **CI/CD** | Vollständige Pipeline-Konfiguration |

### Dokumentstruktur

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LLARS TEST-LEITFADEN                             │
├─────────────────────────────────────────────────────────────────────────┤
│  TEIL 1: GRUNDLAGEN                                                     │
│  ├── 1.1 Test-Philosophie & Strategie                                   │
│  ├── 1.2 Test-Architektur & Dateistruktur                               │
│  ├── 1.3 Namenskonventionen & Code-Organisation                         │
│  └── 1.4 Was wird getestet? (Test-Matrix)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  TEIL 2: SETUP & INFRASTRUKTUR                                          │
│  ├── 2.1 Backend Setup (pytest)                                         │
│  ├── 2.2 Frontend Setup (Vitest)                                        │
│  ├── 2.3 E2E Setup (Playwright)                                         │
│  └── 2.4 Docker Test-Umgebung                                           │
├─────────────────────────────────────────────────────────────────────────┤
│  TEIL 3: BACKEND TESTS                                                  │
│  ├── 3.1 Unit Tests (Services, Models, Utils)                           │
│  ├── 3.2 Integration Tests (API, DB, External Services)                 │
│  └── 3.3 Socket.IO Tests                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  TEIL 4: FRONTEND TESTS                                                 │
│  ├── 4.1 Component Tests                                                │
│  ├── 4.2 Composable Tests                                               │
│  └── 4.3 Service Tests                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  TEIL 5: E2E TESTS                                                      │
│  ├── 5.1 User Journey Tests                                             │
│  ├── 5.2 Critical Path Tests                                            │
│  └── 5.3 Multi-User & Collaboration Tests                               │
├─────────────────────────────────────────────────────────────────────────┤
│  TEIL 6: SPEZIAL-TESTS                                                  │
│  ├── 6.1 WebSocket & Real-time Tests                                    │
│  ├── 6.2 YJS/CRDT Collaboration Tests                                   │
│  └── 6.3 Performance & Load Tests                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  TEIL 7: CI/CD INTEGRATION                                              │
│  ├── 7.1 GitHub Actions Pipeline                                        │
│  ├── 7.2 Coverage Reports                                               │
│  └── 7.3 Automatisierung                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  TEIL 8: NEUE FEATURES TESTEN                                           │
│  ├── 8.1 Checkliste für neue Features                                   │
│  ├── 8.2 Test-Templates                                                 │
│  └── 8.3 Review-Kriterien                                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ANHANG                                                                 │
│  ├── A. Referenzen & Links                                              │
│  ├── B. Troubleshooting                                                 │
│  └── C. Fortschritts-Tracker                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# TEIL 1: GRUNDLAGEN

## 1.1 Test-Philosophie & Strategie

### Warum testen wir?

| Ziel | Beschreibung |
|------|--------------|
| **Regression verhindern** | Änderungen brechen keine bestehende Funktionalität |
| **Schnelles Deployment** | Vertrauen in Code ohne manuelle Tests |
| **Lebende Dokumentation** | Tests zeigen wie Code verwendet werden soll |
| **Frühe Fehlererkennung** | Bugs im Entwicklungszyklus finden, nicht in Produktion |

### Testing-Pyramide

```
                        ┌─────────────┐
                       │   E2E Tests  │  10-15%
                       │  (Playwright) │  - Kritische User Journeys
                      ├───────────────┤  - Langsam, teuer
                     │  Integration   │  25-30%
                    │     Tests       │  - API, DB, Services
                   │    (pytest)      │  - Mittel schnell
                  ├───────────────────┤
                 │    Unit Tests      │  55-65%
                │  (pytest + Vitest)  │  - Funktionen, Komponenten
               │                      │  - Schnell, günstig
              └────────────────────────┘
```

### Kernprinzipien

1. **Schnelles Feedback**: Unit Tests < 100ms, Integration < 5s, E2E < 60s
2. **Isolation**: Jeder Test ist unabhängig, keine Reihenfolge-Abhängigkeit
3. **Determinismus**: Gleicher Input = Gleicher Output, immer
4. **Klarheit**: Test-Name beschreibt was getestet wird und was erwartet wird
5. **Wartbarkeit**: DRY durch Fixtures, aber nicht auf Kosten der Lesbarkeit

---

## 1.2 Test-Architektur & Dateistruktur

### Keine Monolithen!

**Prinzip:** Jede Test-Datei testet **eine logische Einheit**. Maximale Dateigröße: **300 Zeilen**.

### Backend Struktur

```
tests/
├── conftest.py                    # Globale Fixtures (max 200 Zeilen)
├── fixtures/                      # Geteilte Test-Fixtures
│   ├── __init__.py
│   ├── auth_fixtures.py           # Auth-spezifische Fixtures
│   ├── rag_fixtures.py            # RAG-spezifische Fixtures
│   ├── judge_fixtures.py          # Judge-spezifische Fixtures
│   └── data/                      # Test-Dateien (PDFs, etc.)
│       ├── test_document.pdf
│       └── test_document.txt
│
├── unit/                          # Unit Tests
│   ├── conftest.py                # Unit-spezifische Fixtures
│   │
│   ├── auth/                      # Auth-Modul Tests
│   │   ├── __init__.py
│   │   ├── test_token_validation.py
│   │   ├── test_decorators.py
│   │   └── test_user_creation.py
│   │
│   ├── services/                  # Service Tests
│   │   ├── __init__.py
│   │   ├── permission/
│   │   │   ├── test_check_permission.py
│   │   │   ├── test_grant_revoke.py
│   │   │   └── test_audit_log.py
│   │   ├── rag/
│   │   │   ├── test_embedding_service.py
│   │   │   ├── test_document_service.py
│   │   │   └── test_search_service.py
│   │   ├── chatbot/
│   │   │   ├── test_chat_service.py
│   │   │   └── test_wizard_service.py
│   │   └── judge/
│   │       ├── test_session_service.py
│   │       └── test_comparison_service.py
│   │
│   ├── models/                    # Model Tests
│   │   ├── __init__.py
│   │   ├── test_user.py
│   │   ├── test_rag_document.py
│   │   ├── test_chatbot.py
│   │   └── test_judge_session.py
│   │
│   └── workers/                   # Worker Tests
│       ├── __init__.py
│       ├── test_embedding_worker.py
│       └── test_judge_worker.py
│
├── integration/                   # Integration Tests
│   ├── conftest.py                # Integration-spezifische Fixtures
│   │
│   ├── auth/
│   │   └── test_auth_flow.py
│   │
│   ├── api/                       # API Endpoint Tests
│   │   ├── test_user_api.py
│   │   ├── test_rag_api.py
│   │   ├── test_chatbot_api.py
│   │   └── test_judge_api.py
│   │
│   ├── db/
│   │   ├── test_transactions.py
│   │   └── test_constraints.py
│   │
│   └── socket/
│       ├── test_chat_events.py
│       ├── test_rag_events.py
│       └── test_judge_events.py
│
└── performance/                   # Performance Tests
    ├── test_rag_throughput.py
    └── test_concurrent_users.py
```

### Frontend Struktur

```
llars-frontend/src/
├── test/                          # Test-Infrastruktur
│   ├── setup.js                   # Vitest Setup
│   ├── mocks/                     # Globale Mocks
│   │   ├── socketService.js
│   │   ├── api.js
│   │   └── router.js
│   └── utils/                     # Test-Utilities
│       ├── renderWithPlugins.js
│       └── createTestStore.js
│
├── components/
│   ├── common/
│   │   ├── LBtn.vue
│   │   ├── __tests__/             # Tests neben Komponenten
│   │   │   ├── LBtn.test.js
│   │   │   ├── LTag.test.js
│   │   │   └── LSlider.test.js
│   │   └── ...
│   │
│   ├── Ranker/
│   │   ├── Ranker.vue
│   │   ├── __tests__/
│   │   │   └── Ranker.test.js
│   │   └── ...
│   │
│   └── ...
│
├── composables/
│   ├── useAuth.js
│   ├── __tests__/
│   │   ├── useAuth.test.js
│   │   ├── usePermissions.test.js
│   │   └── useBuilderState.test.js
│   └── ...
│
└── services/
    ├── socketService.js
    ├── __tests__/
    │   └── socketService.test.js
    └── ...
```

### E2E Struktur

```
e2e/
├── fixtures/                      # E2E Fixtures
│   ├── auth.ts                    # Login/Logout Helpers
│   ├── test-data.ts               # Test-Daten
│   └── files/                     # Upload-Dateien
│       └── test-document.pdf
│
├── pages/                         # Page Objects (optional)
│   ├── LoginPage.ts
│   ├── HomePage.ts
│   └── ChatbotPage.ts
│
├── auth/                          # Auth Tests
│   ├── login.spec.ts
│   └── logout.spec.ts
│
├── rating/                        # Rating Feature Tests
│   ├── rating-workflow.spec.ts
│   └── ranking-workflow.spec.ts
│
├── chatbot/                       # Chatbot Tests
│   ├── chatbot-creation.spec.ts
│   └── chatbot-chat.spec.ts
│
├── judge/                         # Judge Tests
│   └── judge-session.spec.ts
│
└── collaboration/                 # Collab Tests
    ├── markdown-collab.spec.ts
    └── latex-collab.spec.ts
```

---

## 1.3 Namenskonventionen & Code-Organisation

### Dateinamen

| Typ | Pattern | Beispiel |
|-----|---------|----------|
| Unit Test | `test_<modul>.py` | `test_permission_service.py` |
| Integration Test | `test_<feature>_flow.py` | `test_auth_flow.py` |
| E2E Test | `<feature>.spec.ts` | `login.spec.ts` |
| Frontend Test | `<Component>.test.js` | `LBtn.test.js` |
| Fixture | `<domain>_fixtures.py` | `rag_fixtures.py` |

### Test-Funktionsnamen

**Pattern:** `test_<was>_<bedingung>_<ergebnis>`

```python
# GUTE Namen
def test_login_with_valid_credentials_returns_token():
def test_login_with_expired_token_returns_401():
def test_permission_check_for_admin_allows_all():
def test_document_upload_without_auth_returns_401():

# SCHLECHTE Namen
def test_login():           # Zu vage
def test_1():               # Nichtssagend
def test_it_works():        # Kein Kontext
```

### Klassen-Organisation

```python
class TestUserAuthentication:
    """Tests für User-Authentifizierung"""

    # =========================================================================
    # POSITIVE TESTS (Happy Path)
    # =========================================================================

    def test_valid_login_returns_token(self):
        """Gültiger Login gibt JWT Token zurück"""
        pass

    def test_valid_token_allows_api_access(self):
        """Gültiger Token erlaubt API-Zugriff"""
        pass

    # =========================================================================
    # NEGATIVE TESTS (Error Cases)
    # =========================================================================

    def test_invalid_password_returns_401(self):
        """Falsches Passwort gibt 401 zurück"""
        pass

    def test_locked_account_returns_403(self):
        """Gesperrter Account gibt 403 zurück"""
        pass

    # =========================================================================
    # EDGE CASES
    # =========================================================================

    def test_empty_username_returns_400(self):
        """Leerer Username gibt 400 zurück"""
        pass
```

### Maximum pro Datei

| Element | Maximum | Grund |
|---------|---------|-------|
| Zeilen | 300 | Lesbarkeit |
| Test-Funktionen | 15 | Fokus auf eine Einheit |
| Fixtures pro Datei | 5 | Wiederverwendung in separaten Dateien |
| Assertions pro Test | 5 | Ein Konzept pro Test |

### Wann aufteilen?

**Teile eine Test-Datei auf, wenn:**
- Mehr als 300 Zeilen
- Mehr als 15 Tests
- Tests verschiedene Aspekte einer Klasse testen
- Scrolling nötig um Zusammenhang zu verstehen

**Beispiel Aufteilung:**

```
# VORHER: test_permission_service.py (500 Zeilen)

# NACHHER:
tests/unit/services/permission/
├── __init__.py
├── test_check_permission.py      # check_permission() Tests
├── test_grant_revoke.py          # grant/revoke Tests
├── test_role_inheritance.py      # Rollen-Vererbung Tests
└── test_audit_log.py             # Audit-Logging Tests
```

---

## 1.4 Was wird getestet? (Test-Matrix)

### Backend Test-Matrix

| Modul | Unit | Integration | E2E | Priorität |
|-------|------|-------------|-----|-----------|
| **Auth/Decorators** | ✅ | ✅ | ✅ | P0 |
| **Permission Service** | ✅ | ✅ | - | P0 |
| **User Model** | ✅ | - | - | P0 |
| **RAG Pipeline** | ✅ | ✅ | ✅ | P0 |
| **Embedding Service** | ✅ | ✅ | - | P0 |
| **Search Service** | ✅ | ✅ | - | P1 |
| **Chatbot Service** | ✅ | ✅ | ✅ | P1 |
| **Wizard Service** | ✅ | ✅ | - | P1 |
| **Judge Service** | ✅ | ✅ | ✅ | P1 |
| **Rating Routes** | - | ✅ | ✅ | P1 |
| **Socket.IO Events** | ✅ | ✅ | - | P2 |
| **Crawler Service** | ✅ | ✅ | - | P2 |
| **Collab (YJS)** | - | ✅ | ✅ | P2 |

### Frontend Test-Matrix

| Komponente/Modul | Unit | E2E | Priorität |
|------------------|------|-----|-----------|
| **useAuth** | ✅ | ✅ | P0 |
| **usePermissions** | ✅ | - | P0 |
| **LBtn, LTag, LSlider** | ✅ | - | P1 |
| **LCard, LTabs** | ✅ | - | P1 |
| **Ranker/Rater** | ✅ | ✅ | P1 |
| **ChatWithBots** | ✅ | ✅ | P1 |
| **useBuilderState** | ✅ | - | P1 |
| **JudgeSession** | ✅ | ✅ | P2 |
| **MarkdownCollab** | - | ✅ | P2 |

### Kritische Pfade (Müssen immer getestet sein)

```
1. Login → Token → API-Zugriff → Logout
2. Document Upload → Chunking → Embedding → Search
3. Chatbot erstellen → Konfigurieren → Chat
4. Judge Session → Comparisons → Evaluation → Ergebnisse
5. Rating/Ranking → Speichern → Statistiken
```

---

# TEIL 2: SETUP & INFRASTRUKTUR

## 2.1 Backend Setup (pytest)

### 2.1.1 Dependencies

- [ ] **Schritt 1:** Requirements-Datei erstellen

```bash
# Datei erstellen
touch requirements-test.txt
```

```txt
# requirements-test.txt

# Core Testing Framework
pytest==8.3.4
pytest-flask==1.3.0
pytest-cov==6.0.0
pytest-asyncio==0.24.0

# Mocking & Isolation
pytest-mock==3.14.0
pytest-socket==0.7.0
responses==0.25.3

# Performance & Parallel
pytest-xdist==3.5.0
pytest-timeout==2.3.1

# Test Data
factory-boy==3.3.1
freezegun==1.4.0
Faker==33.1.0

# Flask Testing
flask-testing==0.8.1
```

- [ ] **Schritt 2:** Installation

```bash
pip install -r requirements-test.txt
```

- [ ] **Schritt 3:** Verifizierung

```bash
pytest --version
# Ausgabe: pytest 8.3.4
```

### 2.1.2 Verzeichnisstruktur erstellen

- [ ] **Schritt 1:** Verzeichnisse anlegen

```bash
# Hauptstruktur
mkdir -p tests/{unit,integration,performance,fixtures}

# Unit Test Module
mkdir -p tests/unit/{auth,services,models,workers}
mkdir -p tests/unit/services/{permission,rag,chatbot,judge}

# Integration Test Module
mkdir -p tests/integration/{auth,api,db,socket}

# Init-Dateien
find tests -type d -exec touch {}/__init__.py \;
```

### 2.1.3 Globale Fixtures (conftest.py)

- [ ] **Schritt 1:** Haupt-conftest.py erstellen

```python
# tests/conftest.py
"""
LLARS Test Configuration - Globale Fixtures

Diese Datei enthält nur die wichtigsten, überall benötigten Fixtures.
Spezifische Fixtures gehören in tests/fixtures/<domain>_fixtures.py
"""

import pytest
import os
from flask import Flask
from app.main import create_app
from app.db.db import db as _db


# =============================================================================
# APP & DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope='session')
def app():
    """
    Flask Test-App (Session-Scope)

    Erstellt einmal pro Test-Session eine App mit SQLite in-memory.
    """
    os.environ['TESTING'] = 'true'

    _app = create_app(testing=True)
    _app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'AUTHENTIK_DISABLED': True,
        'SECRET_KEY': 'test-secret-key',
    })

    with _app.app_context():
        _db.create_all()
        _seed_base_data(_db)
        yield _app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """
    Database Session mit automatischem Rollback (Function-Scope)

    Jeder Test bekommt eine saubere DB-Session.
    Änderungen werden nach dem Test zurückgerollt.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        options = {'bind': connection, 'binds': {}}
        session = _db.create_scoped_session(options=options)
        _db.session = session

        yield _db

        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def client(app):
    """Flask Test-Client"""
    return app.test_client()


# =============================================================================
# AUTH FIXTURES (Basis)
# =============================================================================

@pytest.fixture
def auth_headers():
    """Standard Authorization Header"""
    return {'Authorization': 'Bearer test-token'}


# =============================================================================
# HELPERS
# =============================================================================

def _seed_base_data(db):
    """Erstellt Basis-Daten für alle Tests"""
    from app.db.models import Role

    roles = [
        Role(name='admin', description='Administrator'),
        Role(name='researcher', description='Researcher'),
        Role(name='viewer', description='Viewer'),
        Role(name='chatbot_manager', description='Chatbot Manager'),
    ]

    for role in roles:
        if not Role.query.filter_by(name=role.name).first():
            db.session.add(role)

    db.session.commit()


# =============================================================================
# PYTEST PLUGINS
# =============================================================================

# Lade domain-spezifische Fixtures
pytest_plugins = [
    'tests.fixtures.auth_fixtures',
    'tests.fixtures.rag_fixtures',
    'tests.fixtures.judge_fixtures',
]
```

- [ ] **Schritt 2:** Auth Fixtures erstellen

```python
# tests/fixtures/auth_fixtures.py
"""Auth-spezifische Test-Fixtures"""

import pytest
from unittest.mock import patch, MagicMock
from app.db.models import User, Role


@pytest.fixture
def mock_user(db):
    """Standard Test-User (Viewer-Rolle)"""
    viewer_role = Role.query.filter_by(name='viewer').first()

    user = User(
        username='test_user',
        email='test@llars.local',
        is_active=True,
        account_status='active'
    )
    user.roles.append(viewer_role)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db):
    """Admin Test-User"""
    admin_role = Role.query.filter_by(name='admin').first()

    user = User(
        username='admin_test',
        email='admin@llars.local',
        is_active=True,
        account_status='active'
    )
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def researcher_user(db):
    """Researcher Test-User"""
    researcher_role = Role.query.filter_by(name='researcher').first()

    user = User(
        username='researcher_test',
        email='researcher@llars.local',
        is_active=True,
        account_status='active'
    )
    user.roles.append(researcher_role)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def authenticated_client(app, client, mock_user):
    """Client mit gemockter Authentifizierung"""
    with patch('app.auth.decorators.validate_token') as mock_validate:
        with patch('app.auth.decorators.get_or_create_user') as mock_get_user:
            mock_validate.return_value = {
                'sub': mock_user.username,
                'preferred_username': mock_user.username,
                'email': mock_user.email
            }
            mock_get_user.return_value = mock_user
            yield client
```

- [ ] **Schritt 3:** RAG Fixtures erstellen

```python
# tests/fixtures/rag_fixtures.py
"""RAG-spezifische Test-Fixtures"""

import pytest
from app.db.models import RAGCollection, RAGDocument, RAGDocumentChunk


@pytest.fixture
def rag_collection(db, mock_user):
    """Test RAG Collection"""
    collection = RAGCollection(
        name='Test Collection',
        description='Collection for testing',
        owner_id=mock_user.id,
        source_type='upload',
        is_public=False
    )
    db.session.add(collection)
    db.session.commit()
    return collection


@pytest.fixture
def rag_document(db, rag_collection):
    """Test RAG Document"""
    document = RAGDocument(
        collection_id=rag_collection.id,
        title='Test Document',
        content='This is test content. ' * 100,
        source_type='upload',
        embedding_status='pending'
    )
    db.session.add(document)
    db.session.commit()
    return document


@pytest.fixture
def rag_document_with_chunks(db, rag_document):
    """Document mit Chunks"""
    for i in range(5):
        chunk = RAGDocumentChunk(
            document_id=rag_document.id,
            chunk_index=i,
            content=f'Chunk {i} content here.',
            embedding_status='completed'
        )
        db.session.add(chunk)
    db.session.commit()
    return rag_document
```

- [ ] **Schritt 4:** Judge Fixtures erstellen

```python
# tests/fixtures/judge_fixtures.py
"""Judge-spezifische Test-Fixtures"""

import pytest
from app.db.models import JudgeSession, JudgeComparison


@pytest.fixture
def judge_session(db, mock_user):
    """Test Judge Session"""
    session = JudgeSession(
        name='Test Session',
        creator_id=mock_user.id,
        status='draft',
        config_json={
            'pillar_ids': [1, 2],
            'model': 'gpt-4',
            'workers': 2
        }
    )
    db.session.add(session)
    db.session.commit()
    return session


@pytest.fixture
def judge_session_with_comparisons(db, judge_session):
    """Session mit Comparisons"""
    for i in range(3):
        comparison = JudgeComparison(
            session_id=judge_session.id,
            thread_a_id=i * 2 + 1,
            thread_b_id=i * 2 + 2,
            status='pending'
        )
        db.session.add(comparison)
    db.session.commit()
    return judge_session
```

### 2.1.4 pytest.ini Konfiguration

- [ ] **Schritt 1:** pytest.ini erstellen

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    -v
    --tb=short
    --strict-markers
    -ra
    --color=yes

markers =
    unit: Unit tests (keine externen Dependencies)
    integration: Integration tests (braucht DB)
    e2e: End-to-end tests (braucht volle Umgebung)
    slow: Langsame Tests (>5s)
    auth: Authentication tests
    rag: RAG pipeline tests
    judge: Judge system tests
    chatbot: Chatbot tests

filterwarnings =
    ignore::DeprecationWarning

asyncio_mode = auto
timeout = 30
```

---

## 2.2 Frontend Setup (Vitest)

### 2.2.1 Dependencies installieren

- [ ] **Schritt 1:** Installation

```bash
cd llars-frontend

npm install -D vitest @vitest/coverage-v8 @vitest/ui
npm install -D @vue/test-utils happy-dom
npm install -D @testing-library/vue @testing-library/user-event
npm install -D msw
```

### 2.2.2 Vitest Konfiguration

- [ ] **Schritt 1:** vitest.config.js erstellen

```javascript
// llars-frontend/vitest.config.js
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'url'

export default defineConfig({
  plugins: [vue()],

  test: {
    globals: true,
    environment: 'happy-dom',

    include: [
      'src/**/*.{test,spec}.{js,ts}',
      'src/**/__tests__/**/*.{js,ts}'
    ],

    exclude: ['node_modules', 'dist'],

    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{js,ts,vue}'],
      exclude: [
        'src/**/*.test.{js,ts}',
        'src/test/**',
        'src/main.js'
      ],
      thresholds: {
        statements: 60,
        branches: 50,
        functions: 60,
        lines: 60
      }
    },

    setupFiles: ['./src/test/setup.js'],
    testTimeout: 10000,
    reporters: ['verbose'],
    mockReset: true
  },

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
```

### 2.2.3 Test Setup

- [ ] **Schritt 1:** Setup-Datei erstellen

```javascript
// llars-frontend/src/test/setup.js
import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// =============================================================================
// GLOBALE MOCKS
// =============================================================================

// Socket.IO
vi.mock('@/services/socketService', () => ({
  default: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    emit: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    connected: true
  }
}))

// Vue Router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn()
  }),
  useRoute: () => ({
    params: {},
    query: {},
    path: '/'
  })
}))

// =============================================================================
// VUETIFY STUBS
// =============================================================================

config.global.stubs = {
  'v-app': { template: '<div><slot /></div>' },
  'v-main': { template: '<main><slot /></main>' },
  'v-container': { template: '<div><slot /></div>' },
  'v-row': { template: '<div><slot /></div>' },
  'v-col': { template: '<div><slot /></div>' },
  'v-btn': { template: '<button><slot /></button>' },
  'v-icon': { template: '<span><slot /></span>' },
  'v-card': { template: '<div><slot /></div>' },
  'v-dialog': { template: '<div><slot /></div>' },
  'v-text-field': { template: '<input />' },
  'v-snackbar': { template: '<div><slot /></div>' },
  'transition': { template: '<div><slot /></div>' }
}

// =============================================================================
// BROWSER API MOCKS
// =============================================================================

// LocalStorage
const storage = {}
vi.stubGlobal('localStorage', {
  getItem: vi.fn(k => storage[k] || null),
  setItem: vi.fn((k, v) => { storage[k] = v }),
  removeItem: vi.fn(k => delete storage[k]),
  clear: vi.fn(() => Object.keys(storage).forEach(k => delete storage[k]))
})

// matchMedia
vi.stubGlobal('matchMedia', vi.fn(() => ({
  matches: false,
  addListener: vi.fn(),
  removeListener: vi.fn()
})))

// ResizeObserver
vi.stubGlobal('ResizeObserver', vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
})))

// =============================================================================
// CLEANUP
// =============================================================================

afterEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})
```

### 2.2.4 Test Utilities

- [ ] **Schritt 1:** Render-Helper erstellen

```javascript
// llars-frontend/src/test/utils/renderWithPlugins.js
import { render } from '@testing-library/vue'
import { createPinia } from 'pinia'

/**
 * Rendert Komponente mit allen nötigen Plugins
 */
export function renderWithPlugins(component, options = {}) {
  return render(component, {
    global: {
      plugins: [createPinia()],
      ...options.global
    },
    ...options
  })
}
```

### 2.2.5 package.json Scripts

- [ ] **Schritt 1:** Scripts hinzufügen

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui",
    "test:watch": "vitest --watch"
  }
}
```

---

## 2.3 E2E Setup (Playwright)

### 2.3.1 Installation

- [ ] **Schritt 1:** Playwright installieren

```bash
npm install -D @playwright/test
npx playwright install chromium firefox webkit
```

### 2.3.2 Konfiguration

- [ ] **Schritt 1:** playwright.config.ts erstellen

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  expect: { timeout: 10000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : 4,

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list']
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:55080',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1920, height: 1080 }
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } }
  ],

  webServer: {
    command: 'docker compose up -d && ./scripts/wait-for-healthy.sh',
    url: 'http://localhost:55080',
    reuseExistingServer: !process.env.CI,
    timeout: 180000
  }
})
```

### 2.3.3 Auth Fixture

- [ ] **Schritt 1:** Auth Fixture erstellen

```typescript
// e2e/fixtures/auth.ts
import { test as base, expect, Page } from '@playwright/test'

export const testUsers = {
  admin: { username: 'admin', password: 'admin123' },
  researcher: { username: 'researcher', password: 'admin123' },
  viewer: { username: 'viewer', password: 'admin123' }
}

export async function login(page: Page, user: typeof testUsers.admin) {
  await page.goto('/login')
  await page.fill('input[name="username"]', user.username)
  await page.fill('input[name="password"]', user.password)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/Home', { timeout: 30000 })
}

export const test = base.extend<{
  authenticatedPage: Page
  adminPage: Page
}>({
  authenticatedPage: async ({ page }, use) => {
    await login(page, testUsers.researcher)
    await use(page)
  },
  adminPage: async ({ page }, use) => {
    await login(page, testUsers.admin)
    await use(page)
  }
})

export { expect }
```

---

## 2.4 Docker Test-Umgebung

### 2.4.1 docker-compose.test.yml

- [ ] **Schritt 1:** Test-Compose erstellen

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  db:
    image: mariadb:11.2
    environment:
      MYSQL_ROOT_PASSWORD: test
      MYSQL_DATABASE: llars_test
      MYSQL_USER: test
      MYSQL_PASSWORD: test
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  chromadb:
    image: chromadb/chroma:0.5.20
    environment:
      ANONYMIZED_TELEMETRY: "false"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 10

  backend:
    build: .
    environment:
      - TESTING=true
      - DATABASE_URL=mysql://test:test@db:3306/llars_test
      - REDIS_URL=redis://redis:6379
      - CHROMA_HOST=chromadb
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
      chromadb: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/api/health"]
      interval: 10s
      timeout: 5s
      retries: 10

  frontend:
    build: ./llars-frontend
    depends_on: [backend]

  nginx:
    image: nginx:alpine
    ports: ["55080:80"]
    volumes: ["./nginx/test.conf:/etc/nginx/nginx.conf:ro"]
    depends_on: [backend, frontend]
```

---

# TEIL 3: BACKEND TESTS

## 3.1 Unit Tests

### 3.1.1 Auth Tests

- [ ] **Test-Datei:** `tests/unit/auth/test_token_validation.py`

```python
# tests/unit/auth/test_token_validation.py
"""
Token Validation Tests

Testet JWT Token Validierung:
- Gültige Tokens
- Abgelaufene Tokens
- Ungültige Signaturen
"""

import pytest
from unittest.mock import patch


class TestTokenValidation:
    """Token Validation Tests"""

    # =========================================================================
    # POSITIVE TESTS
    # =========================================================================

    @patch('app.auth.decorators.requests.get')
    def test_valid_token_returns_payload(self, mock_get, app):
        """Gültiger Token gibt Payload zurück"""
        from app.auth.decorators import validate_token

        mock_get.return_value.json.return_value = {
            'active': True,
            'sub': 'user123',
            'preferred_username': 'testuser',
            'email': 'test@llars.local'
        }
        mock_get.return_value.status_code = 200

        with app.app_context():
            result = validate_token('valid-token')

        assert result is not None
        assert result['sub'] == 'user123'

    # =========================================================================
    # NEGATIVE TESTS
    # =========================================================================

    @patch('app.auth.decorators.requests.get')
    def test_expired_token_raises_exception(self, mock_get, app):
        """Abgelaufener Token wirft Exception"""
        from app.auth.decorators import validate_token

        mock_get.return_value.json.return_value = {'active': False}
        mock_get.return_value.status_code = 200

        with app.app_context():
            with pytest.raises(Exception):
                validate_token('expired-token')

    def test_empty_token_raises_exception(self, app):
        """Leerer Token wirft Exception"""
        from app.auth.decorators import validate_token

        with app.app_context():
            with pytest.raises(Exception):
                validate_token('')

    # =========================================================================
    # EDGE CASES
    # =========================================================================

    @patch('app.auth.decorators.requests.get')
    def test_authentik_unavailable_raises_exception(self, mock_get, app):
        """Authentik nicht erreichbar wirft Exception"""
        from app.auth.decorators import validate_token

        mock_get.side_effect = ConnectionError("Connection refused")

        with app.app_context():
            with pytest.raises(Exception):
                validate_token('any-token')
```

- [ ] **Test-Datei:** `tests/unit/auth/test_decorators.py`

```python
# tests/unit/auth/test_decorators.py
"""
Auth Decorator Tests

Testet:
- @authentik_required
- @admin_required
- @roles_required
"""

import pytest
from unittest.mock import patch


class TestAuthentikRequired:
    """@authentik_required Decorator Tests"""

    def test_missing_header_returns_401(self, client):
        """Fehlender Auth-Header gibt 401"""
        response = client.get('/api/users/me')
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Ungültiger Token gibt 401"""
        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer invalid'}
        )
        assert response.status_code == 401

    @patch('app.auth.decorators.validate_token')
    @patch('app.auth.decorators.get_or_create_user')
    def test_valid_token_allows_access(self, mock_user, mock_validate, client, mock_user):
        """Gültiger Token erlaubt Zugriff"""
        mock_validate.return_value = {'sub': mock_user.username}
        mock_user.return_value = mock_user

        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer valid-token'}
        )
        assert response.status_code == 200


class TestAdminRequired:
    """@admin_required Decorator Tests"""

    def test_admin_allowed(self, authenticated_client, admin_user):
        """Admin hat Zugriff"""
        # Test mit Admin-Endpoint
        pass

    def test_non_admin_denied(self, authenticated_client, mock_user):
        """Nicht-Admin wird abgelehnt"""
        pass
```

### 3.1.2 Service Tests

- [ ] **Test-Datei:** `tests/unit/services/permission/test_check_permission.py`

```python
# tests/unit/services/permission/test_check_permission.py
"""
Permission Check Tests

Testet check_permission() Funktion:
- Admin-Rechte
- Rollen-basierte Permissions
- Deny-by-Default
"""

import pytest
from app.services.permission_service import PermissionService


class TestCheckPermission:
    """check_permission() Tests"""

    @pytest.fixture
    def service(self, app, db):
        with app.app_context():
            return PermissionService()

    # =========================================================================
    # ADMIN TESTS
    # =========================================================================

    def test_admin_has_all_permissions(self, app, service, admin_user):
        """Admin hat alle Permissions"""
        with app.app_context():
            assert service.check_permission(admin_user, 'any:permission') is True

    # =========================================================================
    # ROLE TESTS
    # =========================================================================

    def test_viewer_has_view_permissions(self, app, service, mock_user):
        """Viewer hat View-Permissions"""
        with app.app_context():
            assert service.check_permission(mock_user, 'feature:ranking:view') is True

    def test_viewer_denied_edit_permissions(self, app, service, mock_user):
        """Viewer hat keine Edit-Permissions"""
        with app.app_context():
            assert service.check_permission(mock_user, 'feature:ranking:edit') is False

    # =========================================================================
    # DENY-BY-DEFAULT TESTS
    # =========================================================================

    def test_unknown_permission_denied(self, app, service, mock_user):
        """Unbekannte Permission wird verweigert"""
        with app.app_context():
            assert service.check_permission(mock_user, 'unknown:perm') is False
```

### 3.1.3 Model Tests

- [ ] **Test-Datei:** `tests/unit/models/test_user.py`

```python
# tests/unit/models/test_user.py
"""
User Model Tests

Testet:
- Erstellung
- Constraints
- Serialisierung
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.db.models import User, Role


class TestUserModel:
    """User Model Tests"""

    def test_user_creation(self, db):
        """User kann erstellt werden"""
        user = User(username='new_user', email='new@test.local')
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.created_at is not None

    def test_username_unique(self, db, mock_user):
        """Username muss eindeutig sein"""
        duplicate = User(username=mock_user.username, email='other@test.local')
        db.session.add(duplicate)

        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_to_dict_excludes_password(self, mock_user):
        """to_dict() schließt Passwort aus"""
        mock_user.password_hash = 'secret'
        result = mock_user.to_dict()

        assert 'password_hash' not in result
```

---

## 3.2 Integration Tests

### 3.2.1 API Tests

- [ ] **Test-Datei:** `tests/integration/api/test_user_api.py`

```python
# tests/integration/api/test_user_api.py
"""
User API Integration Tests

Testet /api/users/* Endpoints
"""

import pytest


class TestUserAPI:
    """User API Tests"""

    def test_get_current_user(self, authenticated_client):
        """GET /api/users/me gibt aktuellen User"""
        response = authenticated_client.get('/api/users/me')

        assert response.status_code == 200
        assert 'username' in response.json

    def test_update_user_settings(self, authenticated_client):
        """PATCH /api/users/me/settings aktualisiert Settings"""
        response = authenticated_client.patch(
            '/api/users/me/settings',
            json={'collab_color': '#FF0000'}
        )

        assert response.status_code == 200
```

- [ ] **Test-Datei:** `tests/integration/api/test_rag_api.py`

```python
# tests/integration/api/test_rag_api.py
"""
RAG API Integration Tests

Testet /api/rag/* Endpoints
"""

import pytest
from io import BytesIO


class TestRAGCollectionAPI:
    """Collection API Tests"""

    def test_create_collection(self, authenticated_client):
        """POST /api/rag/collections erstellt Collection"""
        response = authenticated_client.post(
            '/api/rag/collections',
            json={'name': 'Test Collection', 'description': 'Test'}
        )

        assert response.status_code == 201
        assert 'id' in response.json

    def test_list_collections(self, authenticated_client, rag_collection):
        """GET /api/rag/collections listet Collections"""
        response = authenticated_client.get('/api/rag/collections')

        assert response.status_code == 200
        assert len(response.json['collections']) >= 1


class TestRAGDocumentAPI:
    """Document API Tests"""

    def test_upload_document(self, authenticated_client, rag_collection):
        """POST /api/rag/collections/:id/documents lädt Dokument hoch"""
        response = authenticated_client.post(
            f'/api/rag/collections/{rag_collection.id}/documents',
            data={'file': (BytesIO(b'Test content'), 'test.txt')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 201
```

---

## 3.3 Socket.IO Tests

- [ ] **Test-Datei:** `tests/integration/socket/test_chat_events.py`

```python
# tests/integration/socket/test_chat_events.py
"""
Chat Socket.IO Event Tests
"""

import pytest
from flask_socketio import SocketIOTestClient


class TestChatEvents:
    """Chat Event Tests"""

    @pytest.fixture
    def socket_client(self, app):
        from app.main import socketio
        return SocketIOTestClient(app, socketio)

    def test_chat_stream_event(self, socket_client):
        """chat_stream Event funktioniert"""
        socket_client.emit('chat_stream', {
            'message': 'Hello',
            'chatbot_id': 1
        })

        received = socket_client.get_received()
        # Prüfe ob Response empfangen wurde
```

---

# TEIL 4: FRONTEND TESTS

## 4.1 Component Tests

### 4.1.1 Common Components

- [ ] **Test-Datei:** `llars-frontend/src/components/common/__tests__/LBtn.test.js`

```javascript
// LBtn.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LBtn from '../LBtn.vue'

describe('LBtn', () => {
  // ===========================================================================
  // RENDERING TESTS
  // ===========================================================================

  it('renders with default props', () => {
    const wrapper = mount(LBtn)
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('renders slot content', () => {
    const wrapper = mount(LBtn, {
      slots: { default: 'Click me' }
    })
    expect(wrapper.text()).toContain('Click me')
  })

  it('applies variant class', () => {
    const wrapper = mount(LBtn, { props: { variant: 'primary' } })
    expect(wrapper.classes()).toContain('l-btn--primary')
  })

  // ===========================================================================
  // INTERACTION TESTS
  // ===========================================================================

  it('emits click event', async () => {
    const wrapper = mount(LBtn)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('does not emit when disabled', async () => {
    const wrapper = mount(LBtn, { props: { disabled: true } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('does not emit when loading', async () => {
    const wrapper = mount(LBtn, { props: { loading: true } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeFalsy()
  })

  // ===========================================================================
  // ICON TESTS
  // ===========================================================================

  it('shows prepend icon', () => {
    const wrapper = mount(LBtn, { props: { prependIcon: 'mdi-plus' } })
    expect(wrapper.find('.v-icon').exists()).toBe(true)
  })
})
```

## 4.2 Composable Tests

- [ ] **Test-Datei:** `llars-frontend/src/composables/__tests__/useAuth.test.js`

```javascript
// useAuth.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuth } from '../useAuth'

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('isAuthenticated', () => {
    it('returns false without token', () => {
      const { isAuthenticated } = useAuth()
      expect(isAuthenticated.value).toBe(false)
    })

    it('returns true with valid token', () => {
      // Mock token with future expiry
      const token = createMockToken({ exp: Date.now() / 1000 + 3600 })
      localStorage.setItem('access_token', token)

      const { isAuthenticated } = useAuth()
      expect(isAuthenticated.value).toBe(true)
    })

    it('returns false with expired token', () => {
      const token = createMockToken({ exp: Date.now() / 1000 - 3600 })
      localStorage.setItem('access_token', token)

      const { isAuthenticated } = useAuth()
      expect(isAuthenticated.value).toBe(false)
    })
  })

  describe('logout', () => {
    it('clears token', () => {
      localStorage.setItem('access_token', 'test-token')

      const { logout } = useAuth()
      logout()

      expect(localStorage.getItem('access_token')).toBeNull()
    })
  })
})

// Helper
function createMockToken(payload) {
  const header = btoa(JSON.stringify({ alg: 'RS256' }))
  const body = btoa(JSON.stringify(payload))
  return `${header}.${body}.signature`
}
```

---

# TEIL 5: E2E TESTS

## 5.1 User Journey Tests

- [ ] **Test-Datei:** `e2e/auth/login.spec.ts`

```typescript
// login.spec.ts
import { test, expect, testUsers } from '../fixtures/auth'

test.describe('Login', () => {
  test('successful login redirects to Home', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[name="username"]', testUsers.researcher.username)
    await page.fill('input[name="password"]', testUsers.researcher.password)
    await page.click('button[type="submit"]')

    await expect(page).toHaveURL(/.*Home/)
  })

  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[name="username"]', 'wrong')
    await page.fill('input[name="password"]', 'wrong')
    await page.click('button[type="submit"]')

    await expect(page.locator('.error-message')).toBeVisible()
  })
})
```

## 5.2 Critical Path Tests

- [ ] **Test-Datei:** `e2e/chatbot/chatbot-creation.spec.ts`

```typescript
// chatbot-creation.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Chatbot Creation', () => {
  test('create chatbot via wizard', async ({ adminPage }) => {
    await adminPage.goto('/Admin/AdminChatbots')

    // Start wizard
    await adminPage.click('button:has-text("Neuer Chatbot")')

    // Step 1: Name
    await adminPage.fill('input[name="name"]', 'E2E Test Bot')
    await adminPage.click('button:has-text("Weiter")')

    // Step 2: Upload
    await adminPage.setInputFiles('input[type="file"]', './e2e/fixtures/files/test.txt')
    await expect(adminPage.locator('.upload-success')).toBeVisible({ timeout: 30000 })
    await adminPage.click('button:has-text("Weiter")')

    // Step 3: Embedding (wait)
    await expect(adminPage.locator('.embedding-complete')).toBeVisible({ timeout: 120000 })
    await adminPage.click('button:has-text("Weiter")')

    // Step 4: Config & Finish
    await adminPage.click('button:has-text("Fertigstellen")')

    await expect(adminPage.locator('.v-snackbar')).toContainText('erfolgreich')
  })
})
```

---

# TEIL 6: SPEZIAL-TESTS

## 6.1 WebSocket Tests

```typescript
// e2e/websocket/reconnection.spec.ts
import { test, expect } from '../fixtures/auth'

test('auto-reconnect after disconnect', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/ChatWithBots')

  // Verify connected
  await expect(authenticatedPage.locator('.connection-status')).toContainText('Connected')

  // Simulate disconnect
  await authenticatedPage.context().setOffline(true)
  await expect(authenticatedPage.locator('.connection-status')).toContainText('Disconnected')

  // Reconnect
  await authenticatedPage.context().setOffline(false)
  await expect(authenticatedPage.locator('.connection-status')).toContainText('Connected', {
    timeout: 30000
  })
})
```

## 6.2 YJS/CRDT Tests

```typescript
// e2e/collaboration/markdown-collab.spec.ts
import { test, expect, testUsers, login } from '../fixtures/auth'

test('real-time sync between users', async ({ browser }) => {
  const context1 = await browser.newContext()
  const context2 = await browser.newContext()
  const page1 = await context1.newPage()
  const page2 = await context2.newPage()

  await login(page1, testUsers.researcher)
  await login(page2, testUsers.admin)

  // Both open same workspace
  await page1.goto('/MarkdownCollabWorkspace/1')
  await page2.goto('/MarkdownCollabWorkspace/1')

  // User 1 types
  await page1.locator('.editor').type('Hello from User 1')

  // User 2 sees update
  await expect(page2.locator('.editor')).toContainText('Hello from User 1', {
    timeout: 5000
  })

  await context1.close()
  await context2.close()
})
```

## 6.3 Performance Tests

```python
# tests/performance/test_rag_throughput.py
import pytest
import time

class TestRAGThroughput:
    """RAG Performance Tests"""

    def test_embedding_throughput(self, app, db, rag_collection):
        """Min 10 docs/minute embedding"""
        from app.workers.embedding_worker import process_document
        from app.db.models import RAGDocument

        # Create 10 docs
        docs = []
        for i in range(10):
            doc = RAGDocument(
                collection_id=rag_collection.id,
                title=f'Doc {i}',
                content='Lorem ipsum ' * 500
            )
            db.session.add(doc)
            docs.append(doc)
        db.session.commit()

        # Measure
        start = time.time()
        for doc in docs:
            process_document(doc.id)
        duration = time.time() - start

        throughput = 10 / (duration / 60)
        assert throughput >= 10, f'Throughput {throughput:.1f}/min < 10'

    def test_search_latency_p95(self, client, rag_collection):
        """p95 Latency < 500ms"""
        latencies = []

        for _ in range(100):
            start = time.time()
            client.post(f'/api/rag/collections/{rag_collection.id}/search',
                       json={'query': 'test', 'top_k': 10})
            latencies.append((time.time() - start) * 1000)

        p95 = sorted(latencies)[94]
        assert p95 < 500, f'p95 {p95:.0f}ms > 500ms'
```

---

# TEIL 7: CI/CD INTEGRATION

## 7.1 GitHub Actions Pipeline

- [ ] **Datei:** `.github/workflows/test.yml`

```yaml
name: LLARS Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-group: [auth, services, models]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest tests/unit/${{ matrix.test-group }}/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v4

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd llars-frontend && npm ci && npm run test:coverage
      - uses: codecov/codecov-action@v4

  integration-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests]
    services:
      mariadb:
        image: mariadb:11.2
        env:
          MYSQL_ROOT_PASSWORD: test
          MYSQL_DATABASE: llars_test
        ports: ['3306:3306']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest tests/integration/ --cov

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [integration-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm install -D @playwright/test && npx playwright install chromium
      - run: docker compose -f docker-compose.test.yml up -d
      - run: ./scripts/wait-for-healthy.sh
      - run: npx playwright test --project=chromium
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

# TEIL 8: NEUE FEATURES TESTEN

## 8.1 Checkliste für neue Features

Wenn du ein **neues Feature** implementierst, nutze diese Checkliste:

### Vor der Implementierung

- [ ] Feature verstehen und in testbare Einheiten aufteilen
- [ ] Welche Tests brauche ich? (Unit / Integration / E2E)
- [ ] Fixtures identifizieren die ich brauche

### Während der Implementierung

- [ ] **Unit Tests** für neue Services/Functions schreiben
- [ ] **Unit Tests** für neue Models schreiben
- [ ] Tests nach dem Schreiben ausführen (`pytest tests/unit/...`)

### Nach der Implementierung

- [ ] **Integration Tests** für neue API Endpoints
- [ ] **E2E Test** wenn kritischer User-Pfad betroffen
- [ ] Coverage prüfen (`pytest --cov`)
- [ ] Alle Tests grün? (`pytest`)

## 8.2 Test-Templates

### Neuer Service Test

```python
# tests/unit/services/<modul>/test_<neuer_service>.py
"""
<Service Name> Tests

Testet:
- <Funktion 1>
- <Funktion 2>
"""

import pytest
from app.services.<modul>.<neuer_service> import NeuerService


class TestNeuerService:
    """<Service Name> Tests"""

    @pytest.fixture
    def service(self, app, db):
        with app.app_context():
            return NeuerService()

    # =========================================================================
    # POSITIVE TESTS
    # =========================================================================

    def test_<funktion>_with_valid_input(self, app, service):
        """<Funktion> mit gültigem Input funktioniert"""
        with app.app_context():
            result = service.<funktion>(valid_input)
            assert result is not None

    # =========================================================================
    # NEGATIVE TESTS
    # =========================================================================

    def test_<funktion>_with_invalid_input_raises(self, app, service):
        """<Funktion> mit ungültigem Input wirft Exception"""
        with app.app_context():
            with pytest.raises(ValueError):
                service.<funktion>(invalid_input)

    # =========================================================================
    # EDGE CASES
    # =========================================================================

    def test_<funktion>_with_empty_input(self, app, service):
        """<Funktion> mit leerem Input"""
        pass
```

### Neuer API Endpoint Test

```python
# tests/integration/api/test_<neue_api>.py
"""
<API Name> Integration Tests
"""

import pytest


class Test<API>:
    """<API> Endpoint Tests"""

    def test_get_<resource>(self, authenticated_client):
        """GET /api/<resource> funktioniert"""
        response = authenticated_client.get('/api/<resource>')
        assert response.status_code == 200

    def test_create_<resource>(self, authenticated_client):
        """POST /api/<resource> erstellt Resource"""
        response = authenticated_client.post(
            '/api/<resource>',
            json={'name': 'Test'}
        )
        assert response.status_code == 201

    def test_<resource>_requires_auth(self, client):
        """<Resource> braucht Authentifizierung"""
        response = client.get('/api/<resource>')
        assert response.status_code == 401
```

### Neue Vue Component Test

```javascript
// __tests__/<Component>.test.js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Component from '../Component.vue'

describe('Component', () => {
  // ===========================================================================
  // RENDERING
  // ===========================================================================

  it('renders correctly', () => {
    const wrapper = mount(Component)
    expect(wrapper.exists()).toBe(true)
  })

  it('renders props', () => {
    const wrapper = mount(Component, {
      props: { title: 'Test' }
    })
    expect(wrapper.text()).toContain('Test')
  })

  // ===========================================================================
  // INTERACTIONS
  // ===========================================================================

  it('emits event on action', async () => {
    const wrapper = mount(Component)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('action')).toBeTruthy()
  })

  // ===========================================================================
  // STATE
  // ===========================================================================

  it('updates state correctly', async () => {
    const wrapper = mount(Component)
    // Test state changes
  })
})
```

## 8.3 Review-Kriterien für Tests

Beim Code Review prüfen:

| Kriterium | Beschreibung |
|-----------|--------------|
| **Benennung** | Test-Name beschreibt was getestet wird |
| **Isolation** | Test ist unabhängig von anderen Tests |
| **Assertions** | Max 5 Assertions pro Test, eine Idee pro Test |
| **Setup** | Fixtures werden wiederverwendet |
| **Cleanup** | Keine Seiteneffekte nach Test |
| **Coverage** | Neue Funktionen sind abgedeckt |
| **Edge Cases** | Fehler-Fälle sind getestet |

---

# ANHANG

## A. Referenzen & Links

### Backend Testing

| Ressource | URL | Beschreibung |
|-----------|-----|--------------|
| pytest Docs | https://docs.pytest.org/ | Offizielle Dokumentation |
| pytest-flask | https://pytest-flask.readthedocs.io/ | Flask Test-Client Integration |
| Flask Testing | https://flask.palletsprojects.com/testing/ | Offizielle Flask Test-Anleitung |
| Factory Boy | https://factoryboy.readthedocs.io/ | Test Data Factory Pattern |
| pytest-cov | https://pytest-cov.readthedocs.io/ | Coverage Plugin |
| pytest-mock | https://pytest-mock.readthedocs.io/ | Mock/Patch Utilities |
| Real Python Testing | https://realpython.com/pytest-python-testing/ | Umfassendes Tutorial |
| Flask-SocketIO Testing | https://flask-socketio.readthedocs.io/en/latest/getting_started.html#testing | Socket.IO Test-Client |

### Frontend Testing

| Ressource | URL | Beschreibung |
|-----------|-----|--------------|
| Vitest Docs | https://vitest.dev/ | Offizielle Dokumentation |
| Vitest Features | https://vitest.dev/guide/features.html | Alle Vitest Features |
| Vue Test Utils | https://test-utils.vuejs.org/ | Offizielle Vue Testing Library |
| Testing Library Vue | https://testing-library.com/docs/vue-testing-library/intro | User-centric Testing |
| MSW (Mock Service Worker) | https://mswjs.io/ | API Mocking |
| Pinia Testing | https://pinia.vuejs.org/cookbook/testing.html | Store Testing |

### E2E Testing

| Ressource | URL | Beschreibung |
|-----------|-----|--------------|
| Playwright Docs | https://playwright.dev/ | Offizielle Dokumentation |
| Playwright Best Practices | https://playwright.dev/docs/best-practices | Best Practices Guide |
| Playwright Test Runner | https://playwright.dev/docs/test-intro | Test Runner Setup |
| Playwright Fixtures | https://playwright.dev/docs/test-fixtures | Fixture System |
| Playwright Network | https://playwright.dev/docs/network | Request Interception |
| Docker Integration | https://playwright.dev/docs/docker | Docker Setup |

### YJS & WebSocket Testing

| Ressource | URL | Beschreibung |
|-----------|-----|--------------|
| YJS Docs | https://docs.yjs.dev/ | Offizielle YJS Dokumentation |
| y-websocket | https://docs.yjs.dev/ecosystem/connection-provider/y-websocket | WebSocket Provider |
| YJS Testing | https://docs.yjs.dev/tutorials/testing-crdt | CRDT Testing Strategies |
| YJS Awareness | https://docs.yjs.dev/getting-started/adding-awareness | Presence Testing |
| Socket.IO Testing | https://socket.io/docs/v4/testing/ | Socket.IO Test Guide |

### CI/CD & DevOps

| Ressource | URL | Beschreibung |
|-----------|-----|--------------|
| GitHub Actions | https://docs.github.com/en/actions | CI/CD Platform |
| Codecov | https://docs.codecov.com/ | Coverage Reports |
| Docker Compose Testing | https://docs.docker.com/compose/gettingstarted/ | Container Testing |

### Artikel & Tutorials (Stand: Dezember 2025)

| Thema | Quelle | Link |
|-------|--------|------|
| Flask Testing Best Practices 2025 | Real Python | https://realpython.com/flask-testing/ |
| Vue 3 Testing with Vitest | Vue.js Blog | https://blog.vuejs.org/posts/vitest |
| E2E Testing Modern Web Apps | Playwright Blog | https://playwright.dev/blog |
| Testing CRDT Applications | YJS GitHub | https://github.com/yjs/yjs/tree/main/tests |
| pytest Fixtures Deep Dive | pytest Docs | https://docs.pytest.org/en/stable/how-to/fixtures.html |

---

## B. Troubleshooting

### Häufige Probleme

| Problem | Lösung |
|---------|--------|
| `ModuleNotFoundError` | `pip install -r requirements-test.txt` |
| Fixtures nicht gefunden | `pytest_plugins` in conftest.py prüfen |
| Tests hängen | `pytest --timeout=30` nutzen |
| DB Tests schlagen fehl | Rollback in Fixture prüfen |
| E2E Timeout | `--timeout=60000` in Playwright |

### Debug-Tipps

```bash
# Verbose Output
pytest -vvv tests/unit/auth/

# Nur fehlgeschlagene Tests
pytest --lf

# Mit print-Ausgabe
pytest -s

# Einzelnen Test
pytest tests/unit/auth/test_decorators.py::TestAuthentikRequired::test_valid_token

# Frontend Debug
npm run test:ui
```

---

## C. Fortschritts-Tracker

### Gesamtfortschritt nach Roadmap-Phasen

| Phase | Woche | Status | Tests | Erledigt |
|-------|-------|--------|-------|----------|
| **Phase 1:** Setup & Infrastruktur | 1-2 | ⬜ | 0 | 0/12 |
| **Phase 2:** Core Unit Tests | 3-4 | ⬜ | ~95 | 0/8 |
| **Phase 3:** Integration Tests | 5-6 | ⬜ | ~60 | 0/8 |
| **Phase 4:** Frontend Tests | 7-8 | ⬜ | ~70 | 0/8 |
| **Phase 5:** E2E & Spezial-Tests | 9-10 | ⬜ | ~20 | 0/8 |
| **Phase 6:** CI/CD & Optimierung | 11-12 | ⬜ | ~5 | 0/6 |

**Legende:** ⬜ Nicht begonnen | 🟨 In Arbeit | ✅ Fertig

### Detaillierter Fortschritt

#### Phase 1: Setup & Infrastruktur (Woche 1-2)

- [ ] `requirements-test.txt` erstellt
- [ ] `pytest.ini` konfiguriert
- [ ] `tests/conftest.py` erstellt
- [ ] `tests/fixtures/auth_fixtures.py` erstellt
- [ ] `tests/fixtures/rag_fixtures.py` erstellt
- [ ] `tests/fixtures/judge_fixtures.py` erstellt
- [ ] `llars-frontend/vitest.config.js` erstellt
- [ ] `llars-frontend/src/test/setup.js` erstellt
- [ ] Frontend Mocks erstellt
- [ ] `playwright.config.ts` erstellt
- [ ] `e2e/fixtures/auth.ts` erstellt
- [ ] `docker-compose.test.yml` erstellt

#### Phase 2: Core Unit Tests (Woche 3-4)

- [ ] Auth Unit Tests (~25 Tests)
  - [ ] Token Validation Tests
  - [ ] Decorator Tests
  - [ ] User Creation Tests
- [ ] Permission Service Tests (~20 Tests)
  - [ ] check_permission Tests
  - [ ] grant/revoke Tests
  - [ ] Role Inheritance Tests
- [ ] RAG Service Tests (~30 Tests)
  - [ ] Embedding Service Tests
  - [ ] Document Service Tests
  - [ ] Search Service Tests
- [ ] Model Tests (~20 Tests)
  - [ ] User Model Tests
  - [ ] RAG Document Tests
  - [ ] Chatbot Model Tests

#### Phase 3: Integration Tests (Woche 5-6)

- [ ] Auth Flow Tests (~15 Tests)
- [ ] User API Tests (~10 Tests)
- [ ] RAG API Tests (~20 Tests)
- [ ] Chatbot API Tests (~15 Tests)
- [ ] Judge API Tests (~10 Tests)
- [ ] Socket.IO Integration Tests

#### Phase 4: Frontend Tests (Woche 7-8)

- [ ] Common Components (~25 Tests)
  - [ ] LBtn Tests
  - [ ] LTag Tests
  - [ ] LSlider Tests
  - [ ] LCard Tests
  - [ ] LTabs Tests
- [ ] Composables (~15 Tests)
  - [ ] useAuth Tests
  - [ ] usePermissions Tests
  - [ ] useBuilderState Tests
- [ ] Feature Components (~20 Tests)
- [ ] Service Tests (~10 Tests)

#### Phase 5: E2E & Spezial-Tests (Woche 9-10)

- [ ] Auth E2E (~5 Tests)
- [ ] Chatbot E2E (~5 Tests)
- [ ] Judge E2E (~5 Tests)
- [ ] YJS Collaboration E2E (~5 Tests)
- [ ] WebSocket Reconnection Tests
- [ ] Performance Tests (~5 Tests)

#### Phase 6: CI/CD & Optimierung (Woche 11-12)

- [ ] GitHub Actions Pipeline
- [ ] Codecov Integration
- [ ] Coverage Badge im README
- [ ] Benchmark Tests
- [ ] Dokumentation Review
- [ ] Final Test Run

### Test-Metriken

| Metrik | Ziel | Aktuell |
|--------|------|---------|
| Gesamtanzahl Tests | ~310 | 0 |
| Backend Coverage | >80% | 0% |
| Frontend Coverage | >70% | 0% |
| E2E Kritische Pfade | 100% | 0% |
| CI Pipeline grün | Ja | - |

### Notizen

| Datum | Phase | Notiz |
|-------|-------|-------|
| | | |

---

**Letzte Aktualisierung:** _____________
**Version:** 3.0
**Erstellt:** 30. Dezember 2025
