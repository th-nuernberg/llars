# Code Quality & Documentation

This page documents the current code quality, docstring coverage, and refactoring progress of the LLARS project.

## Docstring coverage statistics

!!! info "As of January 2026"
    The statistics are updated regularly.
    Source: `docs/metrics/*.json`, update via `scripts/metrics/update_docs.py`.

### Backend (Python)

!!! info "Automatically updated: 04.01.2026 13:03"

| Area | Functions | With docstring | Coverage |
|------|-----------|----------------|----------|
| **Services** | 920 | 775 | ✅ 84.2% |
| **Routes** | 498 | 398 | ✅ 79.9% |
| **Workers** | 119 | 118 | ✅ 99.2% |
| **Models** | 53 | 31 | ⚠️ 58.5% |
| **Auth** | 30 | 22 | ✅ 73.3% |
| **Decorators** | 26 | 8 | ❌ 30.8% |

**Overall:** ✅ 82.1% functions, 74.8% classes, 93.0% modules

### Frontend (Vue.js)

!!! info "Automatically updated: 03.01.2026 07:44"

| Area | Files | With JSDoc | Coverage |
|------|-------|------------|----------|
| **Components** | 256 | 80 | ❌ 31% |
| **Composables** | 13 | 9 | ⚠️ 69% |
| **Views** | 18 | 12 | ⚠️ 67% |
| **Services** | 6 | 3 | ⚠️ 50% |

**Overall:** ❌ 35% of files have JSDoc headers

### Critical areas without sufficient documentation

| File | Lines | Issue |
|------|-------|-------|
| `useAuth.js` | 476 | No JSDoc header for core auth logic |
| `useAnalyticsMetrics.js` | 415 | No JSDoc header |
| `useFieldGenerationService.js` | 388 | No JSDoc header |
| `ChatbotEditor.vue` | 1966 | Only minimal inline comments |
| `LatexEditorPane.vue` | 1883 | Only minimal inline comments |

---

## Test coverage

### Current coverage

| Area | Coverage | Target |
|------|----------|--------|
| **Backend Unit Tests** | 21% | 50% |
| **Frontend Tests** | 14% | 40% |
| **E2E Tests** | 2 Specs | 8 Specs |

### Files without tests (critical)

| File | Lines | Risk |
|------|-------|------|
| ~~`embedding_worker.py`~~ | ~~825~~ | ✅ Tests added |
| `crawler_core.py` | 924 | ❌ High - complex crawler logic |
| `judge_worker.py` | 505 | ❌ High - comparison logic |

### Well-tested areas

| Area | Tests | Coverage |
|------|-------|----------|
| `agent_modes/` | 74 tests | ~100% |
| `auth/decorators.py` | 15 tests | ~85% |
| `permission_service.py` | 20 tests | ~70% |

---

## Refactoring progress

### Completed refactorings (January 2026)

| Date | File | Before | After | Modules |
|------|------|--------|-------|---------|
| 01.01. | `ChatWithBots.vue` | 3299 | 774 | 6 components + CSS |
| 01.01. | `chat_service.py` | 1657 | 590 | 4 modules |
| 01.01. | `latex_collab_routes.py` | 1514 | 56 | 7 modules |
| 01.01. | `agent_chat_service.py` | 1263 | 301 | 7 modules |
| 01.01. | `JudgeSession.vue` | 2174 | 579 | CSS extracted |
| 02.01. | `LatexCollabWorkspace.vue` | 3085 | 1259 | 5 composables + 5 components |
| 02.01. | `chatbot_routes.py` | 1273 | 35 | 6 modules |
| 02.01. | `markdown_collab_routes.py` | 798 | 24 | 4 modules |
| 02.01. | `anonymize_service.py` | 1275 | 445 | 6 modules |
| 02.01. | `crawler_service.py` | 1415 | 666 | 7 modules |
| 02.01. | `judge_worker_pool.py` | 1067 | 618 | 6 modules |
| 02.01. | `collection_embedding_service.py` | 1046 | 606 | 6 modules |
| 02.01. | `embedding_worker.py` | 825 | 67 | 7 modules |

### Open refactoring tasks

#### Backend

| File | Lines | Priority |
|------|-------|----------|
| `crawler_core.py` | 924 | HIGH |
| `playwright_crawler.py` | 782 | MEDIUM |
| `permission_service.py` | 739 | LOW (well documented) |
| `zotero_routes.py` | 736 | MEDIUM |
| `content_extractor.py` | 728 | MEDIUM |
| `oncoco_service.py` | 719 | MEDIUM |

#### Frontend

| File | Lines | Priority |
|------|-------|----------|
| `ChatbotEditor.vue` | 1966 | CRITICAL |
| `LatexEditorPane.vue` | 1883 | CRITICAL |
| `ChatbotBuilderWizard.vue` | 1623 | HIGH |
| `AuthenticityStatsDialog.vue` | 1510 | HIGH |
| `AdminDockerMonitorSection.vue` | 1419 | HIGH |

---

## Code metrics

### Current values

```
Large files (>1000 lines backend): 10 ⚠️
Large components (>1500 lines frontend): 10 ⚠️
Security issues fixed: 3/3 ✓
```

### Goals Q1 2026

- [ ] Backend test coverage > 50%
- [ ] Frontend test coverage > 40%
- [ ] No files > 700 lines (backend)
- [ ] No components > 1000 lines (frontend)
- [ ] JSDoc coverage > 70% (composables)

---

## Docstring standards

### Python (backend)

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Short description of the function.

    Longer description if needed, explaining what the function
    does and why.

    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter

    Returns:
        Description of the return value

    Raises:
        ValueError: If param1 is empty
        TypeError: If param2 is not a number

    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
        True
    """
    pass
```

### JavaScript/Vue (frontend)

```javascript
/**
 * Description of the composable.
 *
 * @description Longer description if needed
 *
 * @param {Object} options - Configuration options
 * @param {string} options.name - Resource name
 * @param {number} [options.timeout=5000] - Optional timeout
 *
 * @returns {Object} Composable state and methods
 * @property {Ref<boolean>} loading - Loading state
 * @property {Function} fetch - Fetch function
 *
 * @example
 * const { loading, fetch } = useMyComposable({ name: 'test' })
 */
export function useMyComposable(options) {
  // ...
}
```

---

## Automated quality checks

### Pre-commit hooks

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

### CI/CD pipeline

The GitLab CI/CD pipeline runs the following quality checks:

| Stage | Job | Description |
|-------|-----|-------------|
| lint | `lint:backend` | flake8 check |
| lint | `lint:frontend` | eslint check |
