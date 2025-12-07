# LLARS Routes Structure

**Date:** 2025-12-07
**Refactored by:** Claude Code

## Overview

This directory contains all Flask route blueprints organized by feature.

## Structure

```
routes/
├── registry.py                 # Central blueprint registration
├── __init__.py                 # Package initialization and exports
│
├── auth/                       # Authentication & data management
│   ├── __init__.py
│   ├── auth_routes.py         # Login, register, logout
│   └── data_routes.py         # Email threads, CSV export
│
├── rating/                     # Rating & ranking features
│   ├── __init__.py
│   ├── rating_routes.py       # Feature ratings
│   ├── ranking_routes.py      # Feature rankings
│   ├── mail_rating_threads.py
│   ├── mail_rating_history.py
│   ├── mail_rating_messages.py
│   └── mail_rating_stats.py
│
├── permissions/                # Permission management
│   ├── __init__.py
│   └── permission_routes.py
│
├── comparison/                 # LLM comparisons
│   ├── __init__.py
│   └── comparison_routes.py
│
├── prompts/                    # User prompts
│   ├── __init__.py
│   └── prompt_routes.py
│
├── llm/                        # LLM model management
│   ├── __init__.py
│   └── llm_routes.py
│
├── judge/                      # LLM-as-Judge
│   ├── __init__.py
│   ├── session_routes.py
│   ├── comparison_routes.py
│   ├── statistics_routes.py
│   └── ... (14 sub-modules)
│
├── oncoco/                     # OnCoCo analysis
│   ├── __init__.py
│   └── ... (7 sub-modules)
│
├── rag/                        # RAG document management
│   ├── __init__.py
│   ├── collection_routes.py
│   ├── document_routes.py
│   ├── search_routes.py
│   └── admin_routes.py
│
├── chatbot/                    # Chatbot interface
│   ├── __init__.py
│   └── chatbot_routes.py
│
├── crawler/                    # Web crawler
│   ├── __init__.py
│   └── crawler_routes.py
│
├── scenarios/                  # Scenario management
│   ├── __init__.py
│   ├── scenario_crud.py
│   ├── scenario_management.py
│   ├── scenario_resources.py
│   └── scenario_stats.py
│
├── kaimo/                      # KAIMO project
│   ├── __init__.py
│   ├── kaimo_admin_routes.py
│   └── kaimo_user_routes.py
│
├── authentik_routes.py        # Authentik OIDC authentication
└── HelperFunctions.py         # Shared helper functions
```

## Blueprint Registry

All blueprints are registered via `routes/registry.py`:

```python
from routes.registry import register_all_blueprints

app = Flask(__name__)
register_all_blueprints(app)
```

## Blueprint Organization

### Core Blueprints

| Blueprint | Prefix | Description |
|-----------|--------|-------------|
| `auth_bp` | `/auth` | Legacy authentication |
| `data_bp` | `/api` | Data management (shared) |
| `authentik_auth_bp` | `/auth/authentik` | Authentik OIDC |

### Feature Blueprints

Many feature blueprints reuse `data_bp` for backwards compatibility:
- Rating, Ranking, Mail Rating
- Permissions
- Comparison
- Prompts
- Scenarios

### Dedicated Blueprints

| Blueprint | Prefix | Description |
|-----------|--------|-------------|
| `llm_bp` | `/api/llm` | LLM model management |
| `judge_bp` | `/api/judge` | LLM-as-Judge |
| `oncoco_bp` | `/api/oncoco` | OnCoCo analysis |
| `rag_bp` | `/api/rag` | RAG documents |
| `chatbot_bp` | `/api/chatbots` | Chatbot |
| `crawler_bp` | `/api/crawler` | Web crawler |
| `kaimo_bp` | `/api/kaimo` | KAIMO project |

## Import Pattern

Each feature module follows this pattern:

```python
# routes/feature/__init__.py
from flask import Blueprint

# Create or import blueprint
feature_bp = Blueprint('feature', __name__, url_prefix='/api/feature')

# Import route handlers (registers routes with blueprint)
from . import feature_routes

__all__ = ['feature_bp']
```

## Backwards Compatibility

The refactoring maintains backwards compatibility:

1. Original blueprints (`auth_blueprint`, `data_blueprint`) are still exported from `routes/__init__.py`
2. URL prefixes remain unchanged
3. All existing routes continue to work

## Migration from Old Structure

### Before (56 files in root)
```
routes/
├── RatingRoutes.py
├── RankingRoutes.py
├── PermissionRoutes.py
├── LLMComparisonRoutes.py
├── UserPromptRoutes.py
├── llm_routes.py
├── routes.py
├── authentik_routes.py
└── ... (many more)
```

### After (Feature-based)
```
routes/
├── registry.py
├── auth/
├── rating/
├── permissions/
├── comparison/
├── prompts/
├── llm/
└── ... (organized by feature)
```

## Benefits

1. **Clear Organization**: Features grouped logically
2. **Scalability**: Easy to add new features
3. **Maintainability**: Related code stays together
4. **Discoverability**: Clear feature boundaries
5. **Testability**: Features can be tested in isolation

## Adding New Features

1. Create feature directory: `routes/my_feature/`
2. Create `__init__.py` with blueprint
3. Create route files: `my_feature_routes.py`
4. Add to `registry.py`:

```python
def register_all_blueprints(app: Flask) -> None:
    # ... existing blueprints ...

    # My Feature
    from routes.my_feature import my_feature_bp
    app.register_blueprint(my_feature_bp, url_prefix='/api/my_feature')
```

## Notes

- `data_bp` is shared across multiple features for backwards compatibility
- Some blueprints define their own prefix (chatbot, crawler, judge, etc.)
- Legacy route files (RatingRoutes.py, etc.) should be removed after verification
- HelperFunctions.py remains at root level as shared utility

## Verification

To verify all routes are registered:

```python
from routes.registry import get_blueprint_info
info = get_blueprint_info()
print(info)
```
