"""
Scenario Management Module
Refactored from ScenarioRoutes.py into focused sub-modules.

Blueprint:
- scenarios_bp: Scenario management routes (/api/scenarios)

SCHEMA GROUND TRUTH:
-------------------
Alle Evaluation-Daten werden über das einheitliche EvaluationData Schema
ausgeliefert. Die Schema-Definitionen befinden sich in:

- Backend: app/schemas/evaluation_data_schemas.py (Pydantic Models)
- Frontend: llars-frontend/src/schemas/evaluationSchemas.ts (TypeScript + Zod)

Die Schema-API ist in scenario_schema_api.py implementiert:
- GET /api/scenarios/{id}/schema - Szenario-Übersicht
- GET /api/scenarios/{id}/items/{item_id}/schema - Item im Schema-Format
- POST /api/scenarios/{id}/items/schema/batch - Batch-Abruf
- GET /api/schemas/evaluation/types - Verfügbare Evaluationstypen
- POST /api/schemas/evaluation/validate - Schema-Validierung

Dokumentation: .claude/plans/evaluation-data-schemas.md
"""

# Uses data_bp from auth module
from routes.auth import data_bp as scenarios_bp

# Import all route modules to register them with the blueprint
from . import scenario_crud
from . import scenario_management
from . import scenario_resources
from . import scenario_stats
from . import scenario_manager_api  # User-facing Scenario Manager API
from . import scenario_schema_api  # Schema-based API (unified format)

__all__ = ['scenarios_bp']
