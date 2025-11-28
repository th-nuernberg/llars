"""
DEPRECATED: This file has been split into multiple modules.

The routes have been moved to:
- session_routes.py: Session CRUD and control
- comparison_routes.py: Comparison retrieval and queue
- statistics_routes.py: Results and statistics
- pillar_routes.py: Pillar management
- export_routes.py: Data export
- kia_sync_routes.py: KIA GitLab synchronization

Import from routes.judge instead:
    from routes.judge import judge_bp
"""

import warnings

warnings.warn(
    "Importing from routes.judge.judge_routes is deprecated. "
    "Use routes.judge instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backwards compatibility
from routes.judge import judge_bp

__all__ = ['judge_bp']
