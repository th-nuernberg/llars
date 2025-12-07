"""
Scenario Management Module
Refactored from ScenarioRoutes.py into focused sub-modules.

Blueprint:
- scenarios_bp: Scenario management routes (/api/scenarios)
"""

# Uses data_bp from auth module
from routes.auth import data_bp as scenarios_bp

# Import all route modules to register them with the blueprint
from . import scenario_crud
from . import scenario_management
from . import scenario_resources
from . import scenario_stats

__all__ = ['scenarios_bp']
