"""
Scenario Management Module
Refactored from ScenarioRoutes.py into focused sub-modules.
"""

# Import all route modules to register them with the blueprint
from . import scenario_crud
from . import scenario_management
from . import scenario_resources
from . import scenario_stats

__all__ = ['scenario_crud', 'scenario_management', 'scenario_resources', 'scenario_stats']
