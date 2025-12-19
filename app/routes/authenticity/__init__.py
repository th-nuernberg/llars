"""
Authenticity (Fake/Echt) Routes

Adds:
- User-facing endpoints to list threads and submit real/fake votes
- Admin import endpoint for dataset JSON in v6 format

All routes are attached to the shared /api blueprint (routes.auth.data_bp).
"""

# Import modules so they register their routes on data_bp
from . import authenticity_routes  # noqa: F401
from . import authenticity_admin  # noqa: F401

