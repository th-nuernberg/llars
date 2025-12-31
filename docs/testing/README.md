# LLARS Testdokumentation

**Version:** 1.1 | **Stand:** 30. Dezember 2025

**Implementierungsstatus:** 🟡 In Arbeit

---

## Übersicht

Diese Dokumentation enthält alle Testanforderungen für das LLARS-System (LLM Assisted Research System). Sie dient als vollständige Referenz für:

- Was getestet werden muss
- Wie es getestet werden soll
- Welche Priorität jeder Test hat
- Wer für welche Tests verantwortlich ist

### Quick Start: Tests ausführen

```bash
# Alle Tests ausführen
cd /path/to/llars
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

| Bereich | Dokumente | Tests | Priorität | Status |
|---------|-----------|-------|-----------|--------|
| **Backend Auth** | 1 | ~35 | P0 | ✅ Implementiert |
| **Backend Permissions** | 1 | ~25 | P0 | ✅ Implementiert |
| **Backend API Routes** | 1 | ~40 | P0-P1 | ✅ Implementiert |
| **Frontend Seiten** | 5 | ~150 | P0-P2 | ⏳ Geplant |
| **Frontend UI/UX** | 6 | ~400 | P1-P2 | ⏳ Geplant |
| **Features** | 4 | ~120 | P0-P1 | ⏳ Geplant |
| **Security** | 2 | ~80 | P0 | 🟡 Teilweise |
| **Checklisten** | 3 | ~200 | P0-P1 | ✅ Dokumentiert |
| **Gesamt** | 22 | ~1050 | - | ~10% ✅ |

### Implementierte Test-Dateien

```
tests/
├── conftest.py                                  # ✅ Fixtures & Setup
├── unit/
│   ├── auth/
│   │   └── test_decorators.py                   # ✅ 25 Tests
│   └── services/
│       └── permission/
│           └── test_permission_service.py       # ✅ 18 Tests
└── integration/
    ├── auth/
    │   └── test_login.py                        # ✅ 12 Tests
    └── api/
        └── test_route_protection.py             # ✅ 15 Tests
```

### Frontend UI/UX Details

| Dokument | Inhalt | Testanzahl |
|----------|--------|------------|
| 06_UI_KOMPONENTEN | 20+ LLARS Komponenten (LBtn, LSlider, etc.) | ~80 |
| 07_DIALOGE_MODALS | 10 Dialog-Komponenten | ~50 |
| 08_TOOLTIPS_QUICKLINKS | 100+ Tooltips, 20+ Quicklinks, 15 Shortcuts | ~135 |
| 09_ACCESSIBILITY | WCAG 2.1 AA, Keyboard, Screen Reader, Kontrast | ~75 |
| 10_EDGE_CASES_ERRORS | Empty States, Errors, Limits, Network | ~40 |
| 11_VISUAL_RESPONSIVE | Breakpoints, Dark Mode, Browser, Animationen | ~50 |

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

**Letzte Aktualisierung:** 30. Dezember 2025
