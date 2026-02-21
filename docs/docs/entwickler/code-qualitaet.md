# Code-Qualität & Dokumentation

Diese Seite dokumentiert die aktuelle Code-Qualität, Docstring-Coverage und Refactoring-Fortschritt des LLARS-Projekts.

## Docstring-Coverage Statistik

!!! info "Stand: Januar 2026"
    Die Statistiken werden regelmäßig aktualisiert.
    Quelle: `docs/metrics/*.json`, aktualisieren mit `scripts/metrics/update_docs.py`.

### Backend (Python)

!!! info "Automatisch aktualisiert: 04.01.2026 13:03"

| Bereich | Funktionen | Mit Docstring | Coverage |
|---------|------------|---------------|----------|
| **Services** | 920 | 775 | ✅ 84.2% |
| **Routes** | 498 | 398 | ✅ 79.9% |
| **Workers** | 119 | 118 | ✅ 99.2% |
| **Models** | 53 | 31 | ⚠️ 58.5% |
| **Auth** | 30 | 22 | ✅ 73.3% |
| **Decorators** | 26 | 8 | ❌ 30.8% |

**Gesamt:** ✅ 82.1% Funktionen, 74.8% Klassen, 93.0% Module

### Frontend (Vue.js)

!!! info "Automatisch aktualisiert: 03.01.2026 07:44"

| Bereich | Dateien | Mit JSDoc | Coverage |
|---------|---------|-----------|----------|
| **Components** | 256 | 80 | ❌ 31% |
| **Composables** | 13 | 9 | ⚠️ 69% |
| **Views** | 18 | 12 | ⚠️ 67% |
| **Services** | 6 | 3 | ⚠️ 50% |

**Gesamt:** ❌ 35% der Dateien haben JSDoc-Header

### Kritische Bereiche ohne ausreichende Dokumentation

| Datei | Zeilen | Problem |
|-------|--------|---------|
| `useAuth.js` | 476 | Kein JSDoc-Header für Core-Auth-Logik |
| `useAnalyticsMetrics.js` | 415 | Kein JSDoc-Header |
| `useFieldGenerationService.js` | 388 | Kein JSDoc-Header |
| `ChatbotEditor.vue` | 1966 | Nur minimale Inline-Kommentare |
| `LatexEditorPane.vue` | 1883 | Nur minimale Inline-Kommentare |

---

## Test Coverage

### Aktuelle Coverage

| Bereich | Coverage | Ziel |
|---------|----------|------|
| **Backend Unit Tests** | 21% | 50% |
| **Frontend Tests** | 14% | 40% |
| **E2E Tests** | 2 Specs | 8 Specs |

### Dateien ohne Tests (Kritisch)

| Datei | Zeilen | Risiko |
|-------|--------|--------|
| ~~`embedding_worker.py`~~ | ~~825~~ | ✅ Tests hinzugefügt |
| `crawler_core.py` | 924 | ❌ Hoch - Komplexe Crawler-Logik |
| `judge_worker.py` | 505 | ❌ Hoch - Vergleichslogik |

### Gut getestete Bereiche

| Bereich | Tests | Coverage |
|---------|-------|----------|
| `agent_modes/` | 74 Tests | ~100% |
| `auth/decorators.py` | 15 Tests | ~85% |
| `permission_service.py` | 20 Tests | ~70% |

---

## Refactoring-Fortschritt

### Abgeschlossene Refactorings (Januar 2026)

| Datum | Datei | Vorher | Nachher | Module |
|-------|-------|--------|---------|--------|
| 01.01. | `ChatWithBots.vue` | 3299 | 774 | 6 Komponenten + CSS |
| 01.01. | `chat_service.py` | 1657 | 590 | 4 Module |
| 01.01. | `latex_collab_routes.py` | 1514 | 56 | 7 Module |
| 01.01. | `agent_chat_service.py` | 1263 | 301 | 7 Module |
| 01.01. | `JudgeSession.vue` | 2174 | 579 | CSS extrahiert |
| 02.01. | `LatexCollabWorkspace.vue` | 3085 | 1259 | 5 Composables + 5 Components |
| 02.01. | `chatbot_routes.py` | 1273 | 35 | 6 Module |
| 02.01. | `markdown_collab_routes.py` | 798 | 24 | 4 Module |
| 02.01. | `anonymize_service.py` | 1275 | 445 | 6 Module |
| 02.01. | `crawler_service.py` | 1415 | 666 | 7 Module |
| 02.01. | `judge_worker_pool.py` | 1067 | 618 | 6 Module |
| 02.01. | `collection_embedding_service.py` | 1046 | 606 | 6 Module |
| 02.01. | `embedding_worker.py` | 825 | 67 | 7 Module |

### Offene Refactoring-Aufgaben

#### Backend

| Datei | Zeilen | Priorität |
|-------|--------|-----------|
| `crawler_core.py` | 924 | HOCH |
| `playwright_crawler.py` | 782 | MITTEL |
| `permission_service.py` | 739 | NIEDRIG (gut dokumentiert) |
| `zotero_routes.py` | 736 | MITTEL |
| `content_extractor.py` | 728 | MITTEL |
| `oncoco_service.py` | 719 | MITTEL |

#### Frontend

| Datei | Zeilen | Priorität |
|-------|--------|-----------|
| `ChatbotEditor.vue` | 1966 | KRITISCH |
| `LatexEditorPane.vue` | 1883 | KRITISCH |
| `ChatbotBuilderWizard.vue` | 1623 | HOCH |
| `AuthenticityStatsDialog.vue` | 1510 | HOCH |
| `AdminDockerMonitorSection.vue` | 1419 | HOCH |

---

## Code-Metriken

### Aktuelle Werte

```
Große Dateien (>1000 Zeilen Backend): 10 ⚠️
Große Komponenten (>1500 Zeilen Frontend): 10 ⚠️
Security Issues behoben: 3/3 ✓
```

### Ziele Q1 2026

- [ ] Backend Test Coverage > 50%
- [ ] Frontend Test Coverage > 40%
- [ ] Keine Dateien > 700 Zeilen (Backend)
- [ ] Keine Komponenten > 1000 Zeilen (Frontend)
- [ ] JSDoc Coverage > 70% (Composables)

---

## Docstring-Standards

### Python (Backend)

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Kurze Beschreibung der Funktion.

    Längere Beschreibung falls nötig, die erklärt was die
    Funktion tut und warum.

    Args:
        param1: Beschreibung des ersten Parameters
        param2: Beschreibung des zweiten Parameters

    Returns:
        Beschreibung des Rückgabewerts

    Raises:
        ValueError: Wenn param1 leer ist
        TypeError: Wenn param2 keine Zahl ist

    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
        True
    """
    pass
```

### JavaScript/Vue (Frontend)

```javascript
/**
 * Beschreibung des Composable.
 *
 * @description Längere Beschreibung falls nötig
 *
 * @param {Object} options - Konfigurationsoptionen
 * @param {string} options.name - Name der Ressource
 * @param {number} [options.timeout=5000] - Optionaler Timeout
 *
 * @returns {Object} Composable State und Methoden
 * @property {Ref<boolean>} loading - Loading-Status
 * @property {Function} fetch - Fetch-Funktion
 *
 * @example
 * const { loading, fetch } = useMyComposable({ name: 'test' })
 */
export function useMyComposable(options) {
  // ...
}
```

---

## Automatisierte Qualitätsprüfung

### Pre-Commit Hooks

```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pylint
      name: pylint
      entry: pylint app/
      language: system
      types: [python]

    - id: eslint
      name: eslint
      entry: npm run lint
      language: system
      types: [javascript, vue]
```

### CI/CD Pipeline

Die GitLab CI/CD Pipeline führt folgende Qualitätsprüfungen durch:

| Stage | Job | Beschreibung |
|-------|-----|--------------|
| lint | `lint:backend` | flake8 Prüfung |
| lint | `lint:frontend` | eslint Prüfung |
| test | `test:unit:backend` | pytest mit Coverage |
| test | `test:unit:frontend` | vitest mit Coverage |
| security | `security:scan` | Sicherheitsprüfung |

---

## Nächste Schritte

1. **Diese Woche**
   - [ ] `ChatbotEditor.vue` in Tab-Komponenten aufteilen
   - [ ] JSDoc zu `useAuth.js` hinzufügen

2. **Nächste Woche**
   - [ ] `LatexEditorPane.vue` Composables extrahieren
   - [ ] `crawler_core.py` modularisieren

3. **Diesen Monat**
   - [ ] Test Coverage > 35%
   - [ ] Docstring Coverage > 75%
