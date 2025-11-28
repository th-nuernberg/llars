"""
DEPRECATED: Use app.db.models instead.

This file is kept for backwards compatibility.
All models are re-exported from app.db.models.

Example:
    # Old way (deprecated):
    from app.db.tables import User, Permission

    # New way (recommended):
    from app.db.models import User, Permission
"""

import warnings

# Show deprecation warning when this module is imported directly
warnings.warn(
    "Importing from app.db.tables is deprecated. Use app.db.models instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all models for backwards compatibility
from db.models import *
