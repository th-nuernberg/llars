"""
OnCoCo Analysis API Routes (DEPRECATED).

This file is deprecated and kept only for backward compatibility.
All functionality has been split into smaller, focused modules:

- oncoco_info_routes.py - Model and label information
- oncoco_pillar_routes.py - Pillar data management
- oncoco_analysis_routes.py - Analysis CRUD and execution
- oncoco_results_routes.py - Results and statistics
- oncoco_matrix_routes.py - Matrix comparison metrics
- oncoco_debug_routes.py - Debug and admin endpoints

Import from routes.oncoco directly instead:
    from routes.oncoco import oncoco_bp

The oncoco_bp blueprint is now composed of sub-blueprints registered in __init__.py.
"""

import warnings

# Issue deprecation warning when this file is imported directly
warnings.warn(
    "Importing from oncoco_routes.py is deprecated. "
    "Import from routes.oncoco instead: from routes.oncoco import oncoco_bp",
    DeprecationWarning,
    stacklevel=2
)

# Re-export the blueprint for backward compatibility
from routes.oncoco import oncoco_bp

__all__ = ['oncoco_bp']
